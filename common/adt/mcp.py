"""A small Model Context Protocol client over stdio, standard library only.

Servers speak JSON-RPC 2.0, one message per line. This client starts a server as a subprocess, lists its tools, and calls them. A call
that does not answer within its timeout kills the server and starts a fresh one, and the call is reported as timed out: a tool that
ties its server up is a finding in itself, so it is returned as a result and never hidden.
"""
import json
import queue
import subprocess
import threading
import time

PROTOCOL = "2024-11-05"


class McpError(RuntimeError):
    """The server could not be started or did not complete the handshake."""


class McpServer:
    def __init__(self, cmd: list, cwd: str = None, env: dict = None, label: str = "", startup_s: float = 45.0, attempts: int = 3):
        self.cmd, self.cwd, self.env, self.label, self.startup_s, self.attempts = cmd, cwd, env, label or cmd[-1], startup_s, attempts
        self.proc, self._q, self._id, self.restarts, self.dead = None, queue.Queue(), 0, 0, False
        self.tools = []
        self.start()

    # ---- process ----
    def start(self):
        """Start the server and complete the handshake. A cold start (the first one after a reboot, or a busy machine) can be slow, so
        it is given a generous wait and a few tries before it is called a failure."""
        last = None
        for _ in range(self.attempts):
            try:
                self._start_once()
                self.dead = False
                return
            except (TimeoutError, McpError, OSError) as e:
                last = e
                self.close()
        self.dead = True
        raise McpError(f"{self.label}: could not start after {self.attempts} tries ({last})")

    def _start_once(self):
        import os
        env = {**os.environ, **(self.env or {})}
        self.proc = subprocess.Popen(self.cmd, cwd=self.cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     text=True, encoding="utf-8", bufsize=1)
        self._q = queue.Queue()
        threading.Thread(target=self._pump, args=(self.proc, self._q), daemon=True).start()
        self._id = 0
        self._rpc("initialize", {"protocolVersion": PROTOCOL, "capabilities": {}, "clientInfo": {"name": "adt", "version": "1"}}, self.startup_s)
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.tools = self._rpc("tools/list", {}, self.startup_s).get("tools", [])

    @staticmethod
    def _pump(proc, q):
        for line in proc.stdout:
            line = line.strip()
            if line.startswith("{"):
                try:
                    q.put(json.loads(line))
                except json.JSONDecodeError:
                    pass
        q.put(None)

    def _send(self, msg: dict):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def _rpc(self, method: str, params: dict, timeout: float) -> dict:
        self._id += 1
        mid = self._id
        self._send({"jsonrpc": "2.0", "id": mid, "method": method, "params": params})
        end = time.monotonic() + timeout
        while True:
            left = end - time.monotonic()
            if left <= 0:
                raise TimeoutError(f"{self.label}: no answer to {method} in {timeout:g}s")
            try:
                msg = self._q.get(timeout=left)
            except queue.Empty:
                raise TimeoutError(f"{self.label}: no answer to {method} in {timeout:g}s") from None
            if msg is None:
                raise McpError(f"{self.label}: server exited")
            if msg.get("id") == mid:
                if "error" in msg:
                    raise McpError(f"{self.label}: {msg['error'].get('message', msg['error'])}")
                return msg.get("result", {})

    # ---- use ----
    def call(self, name: str, args: dict, timeout: float = 10.0) -> dict:
        """Returns {"ok", "text", "ms", "timed_out"}. A timeout kills and restarts the server so the next call starts clean."""
        t0 = time.perf_counter()
        if self.dead:                                                    # an earlier restart failed: try once more before giving up on this call
            try:
                self.start()
            except McpError as e:
                return {"ok": False, "text": str(e), "ms": 0, "timed_out": False}
        try:
            res = self._rpc("tools/call", {"name": name, "arguments": args}, timeout)
            text = "".join(c.get("text", "") for c in res.get("content", []) if isinstance(c, dict))
            return {"ok": not res.get("isError", False), "text": text, "ms": round((time.perf_counter() - t0) * 1000), "timed_out": False}
        except TimeoutError as e:
            self.close()
            self.restarts += 1
            ms = round((time.perf_counter() - t0) * 1000)
            try:
                self.start()
            except McpError:
                pass                                                     # start() marked the server dead; the next call tries again
            return {"ok": False, "text": str(e), "ms": ms, "timed_out": True}
        except (McpError, BrokenPipeError, OSError) as e:
            return {"ok": False, "text": str(e), "ms": round((time.perf_counter() - t0) * 1000), "timed_out": False}

    def close(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.close()
            except OSError:
                pass
            self.proc.kill()
            self.proc.wait(timeout=5)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
