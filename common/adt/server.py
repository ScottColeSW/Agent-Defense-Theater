"""The local runner: the static site plus a small JSON API. Standard library only, bound to localhost.

API
  GET  /api/tests                 every runnable test, whether its prediction is committed, its last result
  GET  /api/status                runner, Ollama and GPU readiness, installed models
  GET  /api/gpu                   current temperature, recent history, limits, cooler state
  POST /api/jobs                  start a job: {tests, mode: scripted|live|exploratory, models, reviewer, max_temp, defenses}
  GET  /api/jobs/<id>             progress; POST /api/jobs/<id>/cancel
  GET  /api/reports               saved runs; GET /api/reports/<run_id> the detailed report

Protections: only local Host names are served (DNS rebinding), a POST needs a JSON content type and, when a browser sends an
Origin, it must be this server's own (so a page on another site cannot start runs on this machine), and model names must be
ones Ollama actually has.
"""
import collections
import functools
import http.server
import json
import socketserver
import threading
import time
import webbrowser
from urllib.parse import urlparse

from . import gpucooler, models, report
from .jobs import MANAGER, Busy
from .loader import ROOT
from .registry import list_tests

SITE = ROOT / "site"


class GpuMonitor:
    """Samples the GPU every couple of seconds for the live panel, whether or not a cooler is installed."""

    def __init__(self, every_s: float = 2.0, keep: int = 150, read=gpucooler.read_temp_c):
        self.every_s, self.read, self.history, self.last, self.available = every_s, read, collections.deque(maxlen=keep), None, None
        self._stop = threading.Event()

    def start(self):
        threading.Thread(target=self._loop, daemon=True, name="gpu-monitor").start()
        return self

    def _loop(self):
        while True:
            t = self.read()
            self.available = t is not None
            if t is not None:
                self.last = t
                self.history.append([round(time.time(), 1), t])
            if self._stop.wait(self.every_s):
                return

    def stop(self):
        self._stop.set()

    def snapshot(self) -> dict:
        c = gpucooler.active
        return {"available": bool(self.available), "temp_c": self.last, "history": list(self.history),
                "max_c": c.max_c if c else gpucooler.DEFAULT_MAX_C, "resume_c": c.resume_c if c else gpucooler.DEFAULT_MAX_C - gpucooler.DEFAULT_MARGIN_C,
                "cooler_active": bool(c), "paused": bool(c and c.paused), "cooler": c.stats() if c else None, "cooler_started": c.wall0 if c else None,
                "pause_events": list(c.pause_events) if c else []}


def make_handler(port: int, monitor: GpuMonitor):
    local_hosts = {f"localhost:{port}", f"127.0.0.1:{port}"}
    origins = {f"http://{h}" for h in local_hosts}

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _json(self, obj, code=200):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _local(self) -> bool:
            if self.headers.get("Host", "") not in local_hosts:
                self._json({"error": "this server only answers on localhost"}, 403)
                return False
            return True

        def do_GET(self):
            path = urlparse(self.path).path
            if not path.startswith("/api/"):
                return super().do_GET()
            if not self._local():
                return
            try:
                if path == "/api/tests":
                    return self._json({"tests": list_tests()})
                if path == "/api/status":
                    return self._json(self._status())
                if path == "/api/gpu":
                    return self._json(monitor.snapshot())
                if path == "/api/reports":
                    return self._json({"reports": report.list_reports()})
                if path.startswith("/api/reports/"):
                    r = report.build_report(path.rsplit("/", 1)[1])
                    return self._json(r) if r else self._json({"error": "no such run"}, 404)
                if path == "/api/jobs":
                    return self._json({"jobs": [MANAGER.view(j) for j in sorted(MANAGER.jobs.values(), key=lambda j: -j["created"])[:10]]})
                if path.startswith("/api/jobs/"):
                    j = MANAGER.get(path.rsplit("/", 1)[1])
                    return self._json(MANAGER.view(j)) if j else self._json({"error": "no such job"}, 404)
            except Exception as e:
                return self._json({"error": f"{type(e).__name__}: {e}"}, 500)
            self._json({"error": "not found"}, 404)

        def do_POST(self):
            path = urlparse(self.path).path
            if not path.startswith("/api/") or not self._local():
                return self._json({"error": "not found"}, 404)
            origin = self.headers.get("Origin")
            if origin and origin not in origins:
                return self._json({"error": "cross-site requests are refused"}, 403)
            if "application/json" not in self.headers.get("Content-Type", ""):
                return self._json({"error": "send application/json"}, 415)
            try:
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(min(n, 65536)) or b"{}")
            except (ValueError, json.JSONDecodeError):
                return self._json({"error": "invalid JSON"}, 400)
            try:
                if path == "/api/jobs":
                    return self._json(MANAGER.view(MANAGER.submit(body)), 201)
                if path.startswith("/api/jobs/") and path.endswith("/cancel"):
                    ok = MANAGER.cancel(path.split("/")[3])
                    return self._json({"cancelled": ok}, 200 if ok else 404)
            except Busy as e:
                return self._json({"error": str(e)}, 409)
            except ValueError as e:
                return self._json({"error": str(e)}, 400)
            except Exception as e:
                return self._json({"error": f"{type(e).__name__}: {e}"}, 500)
            self._json({"error": "not found"}, 404)

        @staticmethod
        def _status() -> dict:
            try:
                installed = [{"name": n, "size": s} for n, s in models.ollama_models()]
                up = True
            except OSError:
                installed, up = [], False
            return {"runner": True, "ollama": up, "models": installed, "gpu": monitor.snapshot()["available"],
                    "max_temp_default": gpucooler.DEFAULT_MAX_C}

    return functools.partial(Handler, directory=str(SITE))


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_server(port: int = 8765):
    monitor = GpuMonitor().start()
    srv = Server(("127.0.0.1", port), None)
    srv.RequestHandlerClass = make_handler(srv.server_address[1], monitor)
    srv.monitor = monitor
    return srv


def serve(port: int = 8765, open_browser: bool = False):
    srv = make_server(port)
    url = f"http://localhost:{srv.server_address[1]}/"
    print(f"Serving {SITE} at {url}  (Ctrl+C to stop)\nRunner UI: {url}start.html")
    if open_browser:
        webbrowser.open(url + "start.html")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        srv.monitor.stop()
