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
  mountTheme();
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
  for (let v = 0; v <= 1.0001; v += .2) s += `<line x1="${X(v)}" x2="${X(v)}" y1="${top - 6}" y2="${H - 24}" stroke="${T.grid}" stroke-opacity=".5"/><text x="${X(v)}" y="${H - 8}" text-anchor="middle" fill="${T.muted}" font-size="11">${Math.round(v * 100)}%</text>`;
  order.forEach((d, i) => {
    const r = summary.find(x => x.defense === d), sh = r.success, p = prediction[d], y = top + i * rowH + 8, ci = sh.ci;
    const t = esc(`<b>${d}</b><br>${sh.k} of ${sh.n} attack cases succeeded (${pct(sh.rate)})<br>95% interval ${pct(ci[0])} to ${pct(ci[1])}<br><span class="m">predicted ${pct(p.attack)} (${pct(p.lo)} to ${pct(p.hi)})</span>`);
    s += `<text x="${left - 12}" y="${y + 14}" text-anchor="end" fill="${T.text}" font-size="12">${esc(d)}</text>`;
    s += `<rect x="${X(p.lo)}" y="${y - 5}" width="${Math.max(2, X(p.hi) - X(p.lo))}" height="32" rx="4" fill="${tint(T.amber, .12)}" stroke="${tint(T.amber, .45)}"/>`;
    s += `<rect x="${X(0)}" y="${y + 2}" width="${Math.max(0, X(sh.rate || 0) - X(0))}" height="16" rx="3" fill="${T.red}" data-tip="${t}"/>`;
    s += `<line x1="${X(ci[0])}" x2="${X(ci[1])}" y1="${y + 10}" y2="${y + 10}" stroke="${T.text}" stroke-width="1.5"/><line x1="${X(ci[0])}" x2="${X(ci[0])}" y1="${y + 5}" y2="${y + 15}" stroke="${T.text}"/><line x1="${X(ci[1])}" x2="${X(ci[1])}" y1="${y + 5}" y2="${y + 15}" stroke="${T.text}"/>`;
    s += `<path d="M${X(p.attack)} ${y + 2} l6 8 l-6 8 l-6 -8z" fill="${T.amber}"/>`;
    s += `<text x="${W - right + 12}" y="${y + 14}" fill="${T.text}" font-size="12">${pct(sh.rate)}</text><text x="${W - right + 12}" y="${y + 28}" fill="${T.muted}" font-size="11">${sh.k}/${sh.n}</text>`;
  });
  el.innerHTML = s + "</svg>";
}

function latencyBars(el, summary) {
  const split = summary.every(r => r.split);
  if (!split) { el.innerHTML = `<p class="muted small">This run predates the latency split, so only the total per case is known.</p>` +
    summary.map(r => `<div class="small">${esc(r.defense)}: ${ms(r.latency_ms)} per case</div>`).join(""); return; }
  const max = Math.max(...summary.map(r => r.model_ms + r.review_ms + r.gate_ms)) || 1;
  const seg = (v, c, label) => `<i style="width:${(v / max * 100).toFixed(2)}%;background:${c}" data-tip="${esc(label + ": " + ms(v))}"></i>`;
  el.innerHTML = `<div class="small muted" style="margin-bottom:8px"><span style="color:${T.blue}">&#9632;</span> agent model &nbsp; <span style="color:${T.violet}">&#9632;</span> reviewer model &nbsp; <span style="color:${T.amber}">&#9632;</span> our code (gate) &nbsp; waiting for the GPU to cool is outside all three</div>` +
    `<div style="display:grid;grid-template-columns:190px 1fr 190px;gap:6px 10px;align-items:center;font-size:12px">` +
    summary.map(r => `<div>${esc(r.defense)}</div><div class="stacked">${seg(r.model_ms, "${T.blue}", "agent model")}${seg(r.review_ms, "${T.violet}", "reviewer model")}${seg(r.gate_ms, "${T.amber}", "our code")}</div>` +
      `<div class="muted small">defense adds <b style="color:${T.text}">${ms(r.review_ms + r.gate_ms)}</b>${r.thermal_wait_ms ? ` · waited ${ms(r.thermal_wait_ms)}` : ""}</div>`).join("") + "</div>";
}

function heat(el, rows, cols, cell) {
  let h = `<table><thead><tr><th></th>${cols.map(c => `<th>${esc(c.label)}${c.sub ? `<span class="tier ${c.sub}">${c.sub}</span>` : ""}</th>`).join("")}</tr></thead><tbody>`;
  rows.forEach(r => { h += `<tr><th class="rowh">${esc(r)}</th>` + cols.map(c => {
    const x = cell(r, c); if (!x) return "<td></td>";
    const bg = x.v == null ? "transparent" : x.v === 0 ? tint(T.green, .14) : tint(T.red, 0.15 + x.v * 0.6);
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
  for (let c = 40; c <= ymax; c += 10) s += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(c)}" y2="${Y(c)}" stroke="${T.grid}" stroke-opacity=".45"/><text x="${m.l - 6}" y="${Y(c) + 3}" text-anchor="end">${c}</text>`;
  (o.pauses || []).forEach(p => { const x0 = Math.max(X(p.x0), m.l), x1 = Math.min(X(p.x1), W - m.r); if (x1 > m.l && x0 < W - m.r) s += `<rect x="${x0}" y="${m.t}" width="${Math.max(3, x1 - x0)}" height="${H - m.t - m.b}" fill="${tint(T.amber, .22)}" data-tip="${esc(`<b>Paused to cool</b><br>${p.label || ""}`)}"/>`; });
  s += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(o.maxC)}" y2="${Y(o.maxC)}" stroke="${T.red}" stroke-dasharray="5 4"/><text x="${W - m.r}" y="${Y(o.maxC) - 4}" text-anchor="end" fill="${T.redInk}">limit ${o.maxC}</text>`;
  s += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(o.resumeC)}" y2="${Y(o.resumeC)}" stroke="${T.amber}" stroke-dasharray="2 4"/><text x="${W - m.r}" y="${Y(o.resumeC) + 11}" text-anchor="end" fill="${T.amberInk}">resume ${o.resumeC}</text>`;
  const pts = S.filter(p => p[0] >= xmin).map(p => `${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`);
  if (pts.length > 1) {
    const vis = S.filter(p => p[0] >= xmin), x0 = X(vis[0][0]), x1 = X(vis[vis.length - 1][0]);     // fill from the first reading, not from the axis
    s += `<polygon points="${x0},${H - m.b} ${pts.join(" ")} ${x1},${H - m.b}" fill="${tint(T.blue, .10)}"/><polyline points="${pts.join(" ")}" fill="none" stroke="${T.blue}" stroke-width="2"/>`;
    const l = vis[vis.length - 1]; s += `<circle cx="${X(l[0])}" cy="${Y(l[1])}" r="4" fill="${T.blue}"/>`; }
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


/* The trade-off every defense makes: attacks that got through (up is worse) against valid work completed (right is better).
   The corner to be in is the bottom right: protected, and still useful. */
function tradeoffChart(el, summary, L = {}) {
  const vx = L.valid_axis || "valid work completed (higher is better)", sy = L.success_axis || "attacks that got through (lower is better)";
  const rows = summary.filter(r => r.valid && r.valid.n && r.success && r.success.n);
  if (!rows.length) { el.innerHTML = `<p class="muted small" style="margin:0">This run has no valid-work cases to plot.</p>`; return; }
  const W = 720, H = 340, m = {l: 62, r: 24, t: 18, b: 46}, X = v => m.l + v * (W - m.l - m.r), Y = v => H - m.b - v * (H - m.t - m.b);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Attack success against valid work completed, one point per condition">`;
  s += `<rect x="${X(.5)}" y="${Y(.2)}" width="${X(1) - X(.5)}" height="${Y(0) - Y(.2)}" fill="${tint(T.green, .10)}"/>`;
  for (let v = 0; v <= 1.0001; v += .2) {
    s += `<line x1="${X(v)}" x2="${X(v)}" y1="${m.t}" y2="${H - m.b}" stroke="${T.grid}" stroke-opacity=".6"/><text x="${X(v)}" y="${H - m.b + 16}" text-anchor="middle" fill="${T.muted}" font-size="11">${Math.round(v * 100)}%</text>`;
    s += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="${T.grid}" stroke-opacity=".6"/><text x="${m.l - 8}" y="${Y(v) + 4}" text-anchor="end" fill="${T.muted}" font-size="11">${Math.round(v * 100)}%</text>`;
  }
  s += `<text x="${(W + m.l) / 2}" y="${H - 6}" text-anchor="middle" fill="${T.muted}" font-size="11">${esc(vx)}</text>`;
  s += `<text transform="translate(14 ${(H - m.b + m.t) / 2}) rotate(-90)" text-anchor="middle" fill="${T.muted}" font-size="11">${esc(sy)}</text>`;
  // Conditions with identical results share one point and one label. Labels are placed so they do not run over each other.
  const groups = {};
  rows.forEach(r => { const k = `${r.valid.k}/${r.valid.n}-${r.success.k}/${r.success.n}`; (groups[k] = groups[k] || {r, names: []}).names.push(r.defense); });
  const list = Object.values(groups).sort((p, q) => p.r.valid.rate - q.r.valid.rate || p.r.success.rate - q.r.success.rate);
  const boxes = list.map(g => ({x: X(g.r.valid.rate), y: Y(g.r.success.rate)})), placed = [];
  const hit = (a, b) => a.x0 < b.x1 && a.x1 > b.x0 && a.y0 < b.y1 && a.y1 > b.y0;
  list.forEach((g, i) => {
    const r = g.r, x = boxes[i].x, y = boxes[i].y, best = r.success.rate <= .15 && r.valid.rate >= .5, col = best ? T.green : r.success.rate >= .4 ? T.red : T.blue;
    const tipHtml = esc(`<b>${g.names.join("<br>")}</b><br>${L.valid || "valid work done"} ${pct(r.valid.rate)} (${r.valid.k}/${r.valid.n})<br>${L.success || "attacks that got through"} ${pct(r.success.rate)} (${r.success.k}/${r.success.n})`);
    s += `<line x1="${X(r.valid.ci[0])}" x2="${X(r.valid.ci[1])}" y1="${y}" y2="${y}" stroke="${col}" stroke-opacity=".35"/><line x1="${x}" x2="${x}" y1="${Y(r.success.ci[0])}" y2="${Y(r.success.ci[1])}" stroke="${col}" stroke-opacity=".35"/>`;
    s += `<circle cx="${x}" cy="${y}" r="7" fill="${col}" fill-opacity=".9" data-tip="${tipHtml}"/>`;
    const text = g.names[0] + (g.names.length > 1 ? ` +${g.names.length - 1}` : ""), w = text.length * 6.4;
    let spot = null;
    for (const side of (x + w + 14 < W - m.r ? [1, -1] : [-1, 1])) {
      for (const dy of [4, -13, 21, -30, 38, -47, 55, -64]) {
        const x0 = side > 0 ? x + 12 : x - 12 - w, box = {x0, x1: x0 + w, y0: y + dy - 11, y1: y + dy + 3};
        if (box.x0 < m.l - 4 || box.x1 > W - 2 || box.y0 < 4 || box.y1 > H - m.b + 2) continue;
        const dots = boxes.some(b => hit(box, {x0: b.x - 8, x1: b.x + 8, y0: b.y - 8, y1: b.y + 8}));
        if (!dots && !placed.some(q => hit(box, q))) { spot = {side, dy, box}; break; }
      }
      if (spot) break;
    }
    if (!spot) spot = {side: 1, dy: 4, box: {x0: x + 12, x1: x + 12 + w, y0: y - 7, y1: y + 7}};
    placed.push(spot.box);
    s += `<text x="${spot.side > 0 ? x + 12 : x - 12}" y="${y + spot.dy}" text-anchor="${spot.side > 0 ? "start" : "end"}" fill="${T.text}" font-size="11">${esc(text)}</text>`;
  });
  const groupsText = list.filter(g => g.names.length > 1).map(g => `<b>${esc(g.names[0])} +${g.names.length - 1}</b>: ${esc(g.names.slice(1).join(", "))} (same result)`).join("<br>");
  el.innerHTML = s + "</svg>" + (groupsText ? `<p class="muted small" style="margin:8px 0 0">${groupsText}</p>` : "");
}
