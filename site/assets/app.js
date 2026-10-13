/* Shared helpers for the runner and report pages. No dependencies. */
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const pct = v => v == null ? "n/a" : (Math.round(v * 1000) / 10) + "%";
const share = s => (s && s.n) ? `${pct(s.rate)} (${s.k}/${s.n})` : "n/a";
const ms = v => v == null ? "n/a" : v >= 1000 ? (v / 1000).toFixed(2) + " s" : (v >= 10 ? Math.round(v) : v.toFixed(1)) + " ms";
const dur = s => s == null ? "" : s < 90 ? Math.round(s) + " s" : Math.round(s / 60) + " min";
const when = iso => iso ? new Date(iso).toLocaleString([], {dateStyle: "medium", timeStyle: "short"}) : "";
const GH = "https://github.com/ScottColeSW/Agent-Defense-Theater/";

/* ---------- chrome ---------- */
function chrome(active) {
  const links = [["index.html", "Home"], ["start.html", "Tests"], ["about.html", "About"], ["books.html", "Books"]];
  $("nav").innerHTML = links.map(([h, t]) => `<a href="${h}" class="${h === active ? "on" : ""}">${t}</a>`).join("");
  $("foot").innerHTML = `<div class="wrap row"><p>Agent Defense Theater is a research foundation, not a product. MIT licensed. Built by Scott A. Cole.</p>
    <nav aria-label="Footer"><a href="about.html">About</a><a href="books.html">Books</a><a href="${GH}">GitHub</a></nav></div>`;
}

/* ---------- API, with a static fallback ---------- */
async function api(path, opts) {
  const r = await fetch(path, opts);
  let d = null;
  try { d = await r.json(); } catch (e) { /* not JSON */ }
  if (!r.ok) throw new Error((d && d.error) || `${r.status} ${r.statusText}`);
  return d;
}
const post = (path, body) => api(path, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body || {})});
async function runnerUp() { try { return await api("/api/status"); } catch (e) { return null; } }
async function loadReport(id) {
  try { return await api(`/api/reports/${encodeURIComponent(id)}`); }
  catch (e) { return await api(`data/reports/${encodeURIComponent(id)}.json`); }
}
async function loadReportList() {
  try { return {live: true, reports: (await api("/api/reports")).reports}; }
  catch (e) { try { return {live: false, reports: (await api("data/reports/index.json")).reports}; } catch (e2) { return {live: false, reports: []}; } }
}

/* ---------- tooltip ---------- */
document.body.insertAdjacentHTML("beforeend", '<div id="tip" role="tooltip"></div>');
const tip = $("tip");
function showTip(e, html) { tip.innerHTML = html; tip.style.opacity = 1; tip.style.left = Math.min(e.clientX + 14, innerWidth - 320) + "px"; tip.style.top = (e.clientY + 14) + "px"; }
document.addEventListener("mouseover", e => { const t = e.target.closest("[data-tip]"); if (t) showTip(e, t.dataset.tip); });
document.addEventListener("mousemove", e => { const t = e.target.closest("[data-tip]"); if (t) showTip(e, t.dataset.tip); });
document.addEventListener("mouseout", e => { if (e.target.closest("[data-tip]")) tip.style.opacity = 0; });

/* ---------- charts ---------- */
function predictionChart(el, summary, prediction) {
  const order = Object.keys(prediction).filter(d => summary.some(r => r.defense === d));
  const W = 720, left = 190, right = 120, top = 22, rowH = 44, H = top + order.length * rowH + 28, X = v => left + v * (W - left - right);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Attack success by condition with the committed prediction">`;
  for (let v = 0; v <= 1.0001; v += .2) s += `<line x1="${X(v)}" x2="${X(v)}" y1="${top - 6}" y2="${H - 24}" stroke="#334155" stroke-opacity=".5"/><text x="${X(v)}" y="${H - 8}" text-anchor="middle" fill="#94a3b8" font-size="11">${Math.round(v * 100)}%</text>`;
  order.forEach((d, i) => {
    const r = summary.find(x => x.defense === d), sh = r.success, p = prediction[d], y = top + i * rowH + 8, ci = sh.ci;
    const t = esc(`<b>${d}</b><br>${sh.k} of ${sh.n} attack cases succeeded (${pct(sh.rate)})<br>95% interval ${pct(ci[0])} to ${pct(ci[1])}<br><span class="m">predicted ${pct(p.attack)} (${pct(p.lo)} to ${pct(p.hi)})</span>`);
    s += `<text x="${left - 12}" y="${y + 14}" text-anchor="end" fill="#f8fafc" font-size="12">${esc(d)}</text>`;
    s += `<rect x="${X(p.lo)}" y="${y - 5}" width="${Math.max(2, X(p.hi) - X(p.lo))}" height="32" rx="4" fill="rgba(251,191,36,.12)" stroke="rgba(251,191,36,.45)"/>`;
    s += `<rect x="${X(0)}" y="${y + 2}" width="${Math.max(0, X(sh.rate || 0) - X(0))}" height="16" rx="3" fill="#f43f5e" data-tip="${t}"/>`;
    s += `<line x1="${X(ci[0])}" x2="${X(ci[1])}" y1="${y + 10}" y2="${y + 10}" stroke="#f8fafc" stroke-width="1.5"/><line x1="${X(ci[0])}" x2="${X(ci[0])}" y1="${y + 5}" y2="${y + 15}" stroke="#f8fafc"/><line x1="${X(ci[1])}" x2="${X(ci[1])}" y1="${y + 5}" y2="${y + 15}" stroke="#f8fafc"/>`;
    s += `<path d="M${X(p.attack)} ${y + 2} l6 8 l-6 8 l-6 -8z" fill="#fbbf24"/>`;
    s += `<text x="${W - right + 12}" y="${y + 14}" fill="#f8fafc" font-size="12">${pct(sh.rate)}</text><text x="${W - right + 12}" y="${y + 28}" fill="#94a3b8" font-size="11">${sh.k}/${sh.n}</text>`;
  });
  el.innerHTML = s + "</svg>";
}

function latencyBars(el, summary) {
  const split = summary.every(r => r.split);
  if (!split) { el.innerHTML = `<p class="muted small">This run predates the latency split, so only the total per case is known.</p>` +
    summary.map(r => `<div class="small">${esc(r.defense)}: ${ms(r.latency_ms)} per case</div>`).join(""); return; }
  const max = Math.max(...summary.map(r => r.model_ms + r.review_ms + r.gate_ms)) || 1;
  const seg = (v, c, label) => `<i style="width:${(v / max * 100).toFixed(2)}%;background:${c}" data-tip="${esc(label + ": " + ms(v))}"></i>`;
  el.innerHTML = `<div class="small muted" style="margin-bottom:8px"><span style="color:#38bdf8">&#9632;</span> agent model &nbsp; <span style="color:#a78bfa">&#9632;</span> reviewer model &nbsp; <span style="color:#fbbf24">&#9632;</span> our code (gate) &nbsp; waiting for the GPU to cool is outside all three</div>` +
    `<div style="display:grid;grid-template-columns:190px 1fr 190px;gap:6px 10px;align-items:center;font-size:12px">` +
    summary.map(r => `<div>${esc(r.defense)}</div><div class="stacked">${seg(r.model_ms, "#38bdf8", "agent model")}${seg(r.review_ms, "#a78bfa", "reviewer model")}${seg(r.gate_ms, "#fbbf24", "our code")}</div>` +
      `<div class="muted small">defense adds <b style="color:#f8fafc">${ms(r.review_ms + r.gate_ms)}</b>${r.thermal_wait_ms ? ` · waited ${ms(r.thermal_wait_ms)}` : ""}</div>`).join("") + "</div>";
}

function heat(el, rows, cols, cell) {
  let h = `<table><thead><tr><th></th>${cols.map(c => `<th>${esc(c.label)}${c.sub ? `<span class="tier ${c.sub}">${c.sub}</span>` : ""}</th>`).join("")}</tr></thead><tbody>`;
  rows.forEach(r => { h += `<tr><th class="rowh">${esc(r)}</th>` + cols.map(c => {
    const x = cell(r, c); if (!x) return "<td></td>";
    const bg = x.v == null ? "transparent" : x.v === 0 ? "rgba(52,211,153,.14)" : `rgba(244,63,94,${(0.15 + x.v * 0.75).toFixed(2)})`;
    return `<td style="background:${bg}" data-tip="${esc(x.tip || "")}">${esc(x.text)}</td>`; }).join("") + "</tr>"; });
  el.innerHTML = h + "</tbody></table>";
}

/* GPU temperature chart. samples: [[x, C]], pauses: [{x0, x1}]. */
function gpuChart(el, o) {
  const W = 640, H = 190, m = {l: 40, r: 14, t: 12, b: 26}, S = o.samples || [];
  if (S.length < 2) { el.innerHTML = `<p class="muted small" style="margin:0">Waiting for temperature readings.</p>`; return; }
  const xmin = o.xmin ?? S[0][0], xmax = o.xmax ?? S[S.length - 1][0], peak = Math.max(...S.map(p => p[1]), o.maxC);
  const ymin = 40, ymax = Math.max(85, peak + 3);
  const X = v => m.l + (v - xmin) / Math.max(1e-9, xmax - xmin) * (W - m.l - m.r), Y = c => m.t + (1 - (c - ymin) / (ymax - ymin)) * (H - m.t - m.b);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="GPU temperature over time with the limit and the pauses">`;
  for (let c = 40; c <= ymax; c += 10) s += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(c)}" y2="${Y(c)}" stroke="#334155" stroke-opacity=".45"/><text x="${m.l - 6}" y="${Y(c) + 3}" text-anchor="end">${c}</text>`;
  (o.pauses || []).forEach(p => { const x0 = Math.max(X(p.x0), m.l), x1 = Math.min(X(p.x1), W - m.r); if (x1 > m.l && x0 < W - m.r) s += `<rect x="${x0}" y="${m.t}" width="${Math.max(3, x1 - x0)}" height="${H - m.t - m.b}" fill="rgba(251,191,36,.22)" data-tip="${esc(`<b>Paused to cool</b><br>${p.label || ""}`)}"/>`; });
  s += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(o.maxC)}" y2="${Y(o.maxC)}" stroke="#f43f5e" stroke-dasharray="5 4"/><text x="${W - m.r}" y="${Y(o.maxC) - 4}" text-anchor="end" fill="#f43f5e">limit ${o.maxC}</text>`;
  s += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(o.resumeC)}" y2="${Y(o.resumeC)}" stroke="#fbbf24" stroke-dasharray="2 4"/><text x="${W - m.r}" y="${Y(o.resumeC) + 11}" text-anchor="end" fill="#fbbf24">resume ${o.resumeC}</text>`;
  const pts = S.filter(p => p[0] >= xmin).map(p => `${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`);
  if (pts.length > 1) {
    const vis = S.filter(p => p[0] >= xmin), x0 = X(vis[0][0]), x1 = X(vis[vis.length - 1][0]);     // fill from the first reading, not from the axis
    s += `<polygon points="${x0},${H - m.b} ${pts.join(" ")} ${x1},${H - m.b}" fill="rgba(56,189,248,.10)"/><polyline points="${pts.join(" ")}" fill="none" stroke="#38bdf8" stroke-width="2"/>`;
    const l = vis[vis.length - 1]; s += `<circle cx="${X(l[0])}" cy="${Y(l[1])}" r="4" fill="#38bdf8"/>`; }
  s += `<text x="${m.l}" y="${H - 8}">${esc(o.leftLabel || "")}</text><text x="${W - m.r}" y="${H - 8}" text-anchor="end">${esc(o.rightLabel || "")}</text></svg>`;
  el.innerHTML = s;
}

const gpuShell = () => `<div class="gpu"><div><div><span class="big" data-g="temp">--</span><span class="unit">&deg;C</span></div>
  <div style="margin-top:8px" data-g="state"></div><div class="therm" data-g="therm"><span class="mark" data-g="mresume"></span><span class="mark" data-g="mlimit"></span><span class="needle" data-g="needle"></span></div>
  <div class="small muted" style="display:flex;justify-content:space-between"><span>30</span><span>90 &deg;C</span></div></div>
  <div><div data-g="chart"></div><div class="gpu-stats" data-g="stats"></div></div></div>`;
const g = (root, k) => root.querySelector(`[data-g="${k}"]`);

function gpuDraw(root, v) {            // v: {temp, available, paused, maxC, resumeC, coolerOn, samples, pauses, xmin, xmax, leftLabel, rightLabel, peak, pauseCount, pausedS}
  g(root, "temp").textContent = v.temp ?? "--";
  const hot = v.temp != null && v.temp > v.maxC;
  const state = !v.available ? ["No GPU reading", "dim"] : v.paused ? ["Cooling: model calls paused", "warn pulse"] :
    hot ? [v.coolerOn ? "Over the limit" : "Hot, no cooler running", "bad"] : v.temp >= v.resumeC ? ["Warm", "warn"] : ["Cool, fine to run", "ok"];
  g(root, "state").innerHTML = `<span class="chip ${state[1]}">${state[0]}</span>` + (v.coolerOn ? ` <span class="chip info">cooler on</span>` : ` <span class="chip dim">cooler off</span>`);
  const pos = c => Math.max(0, Math.min(100, (c - 30) / 60 * 100)) + "%";
  g(root, "needle").style.left = `calc(${pos(v.temp ?? 30)} - 2px)`; g(root, "mresume").style.left = pos(v.resumeC); g(root, "mlimit").style.left = pos(v.maxC);
  gpuChart(g(root, "chart"), {samples: v.samples, pauses: v.pauses, maxC: v.maxC, resumeC: v.resumeC, xmin: v.xmin, xmax: v.xmax, leftLabel: v.leftLabel, rightLabel: v.rightLabel});
  g(root, "stats").innerHTML = `<span>peak <b>${v.peak ?? "n/a"}&deg;C</b></span><span>pauses <b>${v.pauseCount ?? 0}</b></span><span>paused <b>${(v.pausedS ?? 0).toFixed(1)} s</b></span>` +
    `<span>limit <b>${v.maxC}&deg;C</b>, resume <b>${v.resumeC}&deg;C</b></span>`;
}

/* Live panel: polls the runner's GPU monitor. Returns {stop}. */
function gpuLive(root) {
  root.innerHTML = gpuShell();
  let alive = true;
  const tick = async () => {
    if (!alive) return;
    try {
      const s = await api("/api/gpu"), now = Date.now() / 1000, win = 300;
      const pauses = (s.pause_events || []).map(p => ({x0: s.cooler_started + p.start_s, x1: s.cooler_started + p.start_s + p.seconds, label: `${p.seconds}s, ${p.from_c} to ${p.to_c}&deg;C`}));
      const peak = Math.max(...(s.history.length ? s.history.map(p => p[1]) : [0]), s.cooler ? (s.cooler.peak_c || 0) : 0) || null;
      gpuDraw(root, {temp: s.temp_c, available: s.available, paused: s.paused, maxC: s.max_c, resumeC: s.resume_c, coolerOn: s.cooler_active, samples: s.history,
        pauses, xmin: now - win, xmax: now, leftLabel: "5 min ago", rightLabel: "now", peak, pauseCount: s.cooler ? s.cooler.pauses : 0, pausedS: s.cooler ? s.cooler.paused_s : 0});
    } catch (e) { /* runner went away; the page shows that elsewhere */ }
    if (alive) setTimeout(tick, 1500);
  };
  tick();
  return {stop() { alive = false; }};
}

/* Static panel for a saved run: its recorded timeline. */
function gpuStatic(root, gpu) {
  root.innerHTML = gpuShell();
  const S = gpu.samples, last = S.length ? S[S.length - 1] : [0, null];
  gpuDraw(root, {temp: last[1], available: true, paused: false, maxC: gpu.max_c, resumeC: gpu.resume_c, coolerOn: true, samples: S,
    pauses: (gpu.pause_events || []).map(p => ({x0: p.start_s, x1: p.start_s + p.seconds, label: `${p.seconds}s, ${p.from_c} to ${p.to_c}&deg;C`})),
    leftLabel: "run start", rightLabel: `${dur(last[0])} into the run`, peak: gpu.peak_c, pauseCount: gpu.pauses, pausedS: gpu.paused_s});
  g(root, "state").insertAdjacentHTML("afterbegin", `<span class="chip dim">last reading of the run</span> `);
}
