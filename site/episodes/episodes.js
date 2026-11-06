/* Episode player for the ASI03 reviewer-calibration finding, in Defense Rock's scene-player shape
   (site/rock/rock.js): episode tabs, a scene screen, Back/Autoplay/Next and scene dots. Unlike Rock,
   nothing here is scripted or invented -- there are no characters, no songs, no lyrics. Every bubble,
   card and verdict is read at load time from data/episodes.json, itself built by
   tools/build_reviewer_episodes.py straight from the saved run's .jsonl and .decisions.jsonl. There
   is no RUN LIVE: see README.md in this folder for why. */
"use strict";

const GH = "https://github.com/ScottColeSW/Agent-Defense-Theater/tree/main/";
const $ = id => document.getElementById(id);
const E = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const pct = (k, n) => n ? Math.round((k / n) * 1000) / 10 + "%" : "n/a";
const kOfN = (k, n) => `${k} of ${n}`;

const FAMILY_LABEL = {
  m_refund_200: "$200 refund, finance approved", m_refund_120: "$120 refund, finance approved",
  m_refund_30: "$30 goodwill refund", m_export_finance: "customer export, finance",
  n_unrequested_refund: "unrequested $50 refund", n_unrequested_export: "unrequested export, outside address",
  n_wrong_account: "refund to a different account", n_wrong_amount: "$900 refund, not $200",
  n_wrong_destination: "export to a different address", n_other_ticket: "refund on a different ticket",
  n_persuasion: "$1,800 refund, outside account, claimed pre-approval",
};
const famLabel = f => FAMILY_LABEL[f] || f;

let DATA = null, EPISODES = [], cur = {ep: 0, scene: 0}, autoplay = false, timers = [];
const later = (fn, ms) => { timers.push(setTimeout(fn, ms)); };
const clearTimers = () => { timers.forEach(clearTimeout); timers = []; };

/* ---------------------------------------------------------------- shared scene pieces (rock.css) */
function head(kicker, title, source) {
  return `<div class="scene-head"><span class="kicker">${E(kicker)}</span><h3>${E(title)}</h3><span class="src ${source || "replay"}">${source === "computed" ? "Computed from the saved run" : "Replay of a saved run"}</span></div>`;
}
function quoteHTML(who, text, cls) { return `<div class="quote ${cls || ""}"><span class="who">${E(who)}</span><q>${E(text)}</q></div>`; }
function bubble(side, label, text) { return `<div class="bubble ${side}"><b>${E(label)} <span class="src replay">real</span></b>${E(text)}</div>`; }

function verdictList(beats) {
  return `<div class="verdicts">${beats.map((r, i) => `
    <div class="vrow" style="animation-delay:${i * 0.12}s">
      <span class="model">${E(r.model)}</span><span class="pill ${r.correct ? "ok" : "bad"}">${E(r.verdict)}${r.correct ? "" : " — wrong"}</span>
      <span class="reason">&ldquo;${E(r.reason)}&rdquo;${r.well_formed ? "" : " (unparseable reply)"}</span>
    </div>`).join("")}</div>`;
}

/* rows: [{name, sub, att:{k,n}, attLabel, ok:{k,n}}]. okOnly renders only the green bar (no attack framing). */
function board(rows, keyLine, okOnly) {
  return `<div class="board">${rows.map(r => `<div class="row2"><div class="name">${E(r.name)}${r.sub ? `<small>${E(r.sub)}</small>` : ""}</div>
    <div class="bars">
      ${!okOnly ? `<div class="bar att"><i data-w="${r.att.n ? Math.round(100 * r.att.k / r.att.n) : 0}"></i><em>${E(r.attLabel || "false approvals")}: ${kOfN(r.att.k, r.att.n)} (${pct(r.att.k, r.att.n)})</em></div>` : ""}
      ${r.ok ? `<div class="bar ok"><i data-w="${r.ok.n ? Math.round(100 * r.ok.k / r.ok.n) : 0}"></i><em>${E(r.okLabel || "correct")}: ${kOfN(r.ok.k, r.ok.n)} (${pct(r.ok.k, r.ok.n)})</em></div>` : ""}
    </div></div>`).join("")}</div>
    ${keyLine ? `<p class="mini muted" style="margin-top:6px">${E(keyLine)}</p>` : ""}`;
}
function fillBars(root) { later(() => root.querySelectorAll(".bar i").forEach(i => { i.style.width = i.dataset.w + "%"; }), 100); }

function scene(o) { return {dur: o.dur || 14000, hold: !!o.hold, render: o.render, mount: o.mount}; }

/* ---------------------------------------------------------------- episode 1 & 2: the duel */
function duelScenes(ep) {
  return [
    scene({dur: 8000, render: () => `${head("Scene 1", "The Ask")}
      <p class="muted mini">${E(famLabel(ep.family))} &middot; ticket ${E(ep.ticket)}</p>
      ${quoteHTML("Operator's request, verbatim", ep.ask)}
      <p class="mini muted" style="margin-top:14px">An agent is about to ask a reviewer model to approve something else.</p>`}),
    scene({dur: 1200 + ep.agent_beats.length * 1500, render: () => `${head("Scene 2", "The Agent's Pitch")}
      <div class="bubbles">${bubble("black", "Agent", ep.claim)}<div></div></div>
      <pre class="card-text">${E(ep.agent_card_sample)}</pre>
      <p class="mini muted">False approvals: <b>${ep.agent_tally.wrong}</b> of <b>${ep.agent_tally.n}</b> reviewer configurations.</p>
      ${verdictList(ep.agent_beats)}`}),
    scene({dur: 1200 + ep.bottomline_beats.length * 1500, render: () => `${head("Scene 3", "The System Speaks First")}
      <div class="bubbles"><div></div>${bubble("white", "System", ep.fact)}</div>
      <pre class="card-text">${E(ep.bottomline_sample)}</pre>
      <p class="mini muted">False approvals: <b>${ep.bottomline_tally.wrong}</b> of <b>${ep.bottomline_tally.n}</b> reviewer configurations.</p>
      ${verdictList(ep.bottomline_beats)}`}),
    scene({dur: 12000, render: () => `${head("Scene 4", "The Verdict", "computed")}
      ${board([
        {name: "Agent card", sub: "the agent's own reason", att: {k: ep.agent_tally.wrong, n: ep.agent_tally.n}},
        {name: "Bottom-line card", sub: "the system's own comparison", att: {k: ep.bottomline_tally.wrong, n: ep.bottomline_tally.n}},
      ], "False approvals, lower is better.")}
      ${ep.repeat_offenders && ep.repeat_offenders.length ? `<p class="mini muted" style="margin-top:10px">Across all four bottom-line runs (one unsampled, three sampled), ${ep.repeat_offenders.map(r => `<b>${E(r.model)}</b> approved it ${r.approved_of_8} of 8 times`).join(" and ")}, every time the system's own line said the request did not match.</p>` : ""}`,
      mount: root => fillBars(root)}),
  ];
}

/* ---------------------------------------------------------------- episode 3 & 4: one reviewer, case by case */
function groupByFamily(rows) {
  const out = [];
  for (const r of rows) { const last = out[out.length - 1]; if (last && last.family === r.family) last.items.push(r); else out.push({family: r.family, items: [r]}); }
  return out;
}

function spotlightScenes(ep, sideA, sideB, labelA, labelB) {
  const groups = groupByFamily(ep.rows);
  const caseScenes = groups.map((g, i) => scene({dur: 13000, render: () => {
    const first = g.items[0], rest = g.items.slice(1);
    return `${head(`Case ${i + 1}`, famLabel(g.family))}
      <div class="bubbles">
        <div class="bubble black"><b>${E(labelA)} <span class="src replay">real</span></b><span class="pill ${first[sideA].correct ? "ok" : "bad"}">${E(first[sideA].verdict)}</span><br>&ldquo;${E(first[sideA].reason)}&rdquo;</div>
        <div class="bubble white"><b>${E(labelB)} <span class="src replay">real</span></b><span class="pill ${first[sideB].correct ? "ok" : "bad"}">${E(first[sideB].verdict)}</span><br>&ldquo;${E(first[sideB].reason)}&rdquo;</div>
      </div>
      ${rest.map(r => `<p class="mini muted">Ticket ${E(r.ticket)}: ${E(labelA)} ${r[sideA].verdict}${r[sideA].correct ? "" : " (wrong)"}, ${E(labelB)} ${r[sideB].verdict}${r[sideB].correct ? "" : " (wrong)"}.</p>`).join("")}`;
  }}));
  return caseScenes;
}

function worstReviewerScenes(ep) {
  return [...spotlightScenes(ep, "agent", "bottomline", "Agent card", "Bottom line"),
    scene({dur: 10000, render: () => `${head("The tally", "The Worst Reviewer", "computed")}
      ${board([{name: ep.model, sub: "non-matching requests under the agent card", att: {k: ep.wrong, n: ep.total}, attLabel: "approved when it should not"}])}`, mount: root => fillBars(root)})];
}

function tooCarefulScenes(ep) {
  return [...spotlightScenes(ep, "bottomline", "agent_card", "Bottom line", "Agent card, for contrast"),
    scene({dur: 10000, render: () => `${head("The tally", "Too Careful By Half", "computed")}
      ${board([{name: ep.model, sub: "matching, finance-approved refunds under the bottom-line card", att: {k: ep.denied, n: ep.total}, attLabel: "denied when it should approve"}])}`, mount: root => fillBars(root)})];
}

/* ---------------------------------------------------------------- episode 5: thinking on vs off */
function thinkingScenes(ep) {
  const cases = ep.rows.map((r, i) => scene({dur: 13000, render: () => `${head(`Case ${i + 1}`, famLabel(r.family))}
    <div class="bubbles">
      <div class="bubble black"><b>Thinking off <span class="src replay">real</span></b><span class="pill ${r.off.correct ? "ok" : "bad"}">${E(r.off.verdict)}</span> (${r.off.tokens_out} tokens out)<br>&ldquo;${E(r.off.reason)}&rdquo;</div>
      <div class="bubble white"><b>Thinking on <span class="src replay">real</span></b><span class="pill ${r.on.correct ? "ok" : "bad"}">${E(r.on.verdict)}</span> (${r.on.tokens_out} tokens out)<br>&ldquo;${E(r.on.reason)}&rdquo;</div>
    </div>`}));
  return [...cases, scene({dur: 12000, render: () => `${head("The tally", "Thinking Made It Worse", "computed")}
    ${board([{name: "Thinking off", ok: {k: ep.off_correct, n: ep.off_total}}, {name: "Thinking on", ok: {k: ep.on_correct, n: ep.on_total}}], null, true)}
    <p class="mini muted" style="margin-top:6px">Average output tokens: <b>${ep.off_tokens_out}</b> off, <b>${ep.on_tokens_out}</b> on (${Math.round(ep.on_tokens_out / ep.off_tokens_out)}&times;).</p>`,
    mount: root => fillBars(root)})];
}

/* ---------------------------------------------------------------- episode 6: the pooled scoreboard */
function scoreboardScenes(ep) {
  return [
    scene({dur: 14000, render: () => `${head("Scene 1", "By Card Style", "computed")}
      ${board(Object.entries(ep.by_style).map(([style, s]) => ({name: style, att: {k: s.wrong, n: s.n}})), "False approvals, pooled over all eight reviewer configurations, by card style.")}`,
      mount: root => fillBars(root)}),
    scene({dur: 14000, render: () => `${head("Scene 2", "By Reviewer", "computed")}
      ${board(ep.by_model.map(m => ({name: m.model, ok: {k: m.correct, n: m.n}})), "Correct on the bottom-line card (false approvals and false denials both count against it).", true)}`,
      mount: root => fillBars(root)}),
    scene({dur: 14000, hold: true, render: () => `${head("Scene 3", "Cited Externally", "replay")}
      ${quoteHTML("OWASP GenAI-LLM-Top10, issue #137", ep.citation.text)}
      <p class="mini" style="margin-top:10px"><a href="${E(ep.citation.issue)}" target="_blank" rel="noopener">${E(ep.citation.issue)}</a></p>`}),
  ];
}

const SCENE_BUILDERS = {
  fin9921: duelScenes, goodwill: duelScenes,
  "worst-reviewer": worstReviewerScenes, "too-careful": tooCarefulScenes,
  thinking: thinkingScenes, scoreboard: scoreboardScenes,
};

/* ---------------------------------------------------------------- player */
function render() {
  clearTimers();
  const ep = EPISODES[cur.ep], sc = ep.scenes[cur.scene];
  const screen = $("screen");
  screen.innerHTML = sc.render();
  sc.mount && sc.mount(screen);
  document.querySelectorAll(".ep-tab").forEach((t, i) => t.setAttribute("aria-selected", i === cur.ep));
  $("dots").innerHTML = ep.scenes.map((s, i) => `<button class="dot ${i < cur.scene ? "done" : ""} ${i === cur.scene ? "now" : ""}" data-i="${i}" aria-label="Scene ${i + 1}" aria-current="${i === cur.scene}"></button>`).join("");
  $("prev").disabled = cur.ep === 0 && cur.scene === 0;
  $("next").disabled = cur.ep === EPISODES.length - 1 && cur.scene === ep.scenes.length - 1;
  if (autoplay && !sc.hold) later(() => step(1), sc.dur || 12000);
  history.replaceState(null, "", `#e${cur.ep + 1}s${cur.scene + 1}`);
}

function step(d) {
  const ep = EPISODES[cur.ep];
  let s = cur.scene + d;
  if (s >= ep.scenes.length) {
    if (cur.ep < EPISODES.length - 1) cur = {ep: cur.ep + 1, scene: 0};
    else { autoplay = false; $("play").setAttribute("aria-pressed", "false"); $("play").textContent = "Autoplay"; return; }
  } else if (s < 0) {
    if (cur.ep > 0) cur = {ep: cur.ep - 1, scene: EPISODES[cur.ep - 1].scenes.length - 1};
    else return;
  } else cur.scene = s;
  render();
}

function mountTabs() {
  $("episodes").innerHTML = EPISODES.map((e, i) => `<button type="button" class="ep-tab" role="tab" data-i="${i}"><b>${e.number}. ${E(e.title)}</b><span>${E(e.tag)}</span></button>`).join("");
  $("episodes").addEventListener("click", ev => { const b = ev.target.closest(".ep-tab"); if (b) { cur = {ep: +b.dataset.i, scene: 0}; render(); } });
  $("dots").addEventListener("click", ev => { const b = ev.target.closest(".dot"); if (b) { cur.scene = +b.dataset.i; render(); } });
  $("prev").onclick = () => step(-1);
  $("next").onclick = () => step(1);
  $("play").onclick = () => { autoplay = !autoplay; $("play").setAttribute("aria-pressed", String(autoplay)); $("play").textContent = autoplay ? "Pause" : "Autoplay"; render(); };
  document.addEventListener("keydown", ev => { if (/INPUT|SELECT|TEXTAREA/.test(ev.target.tagName)) return; if (ev.key === "ArrowRight") step(1); if (ev.key === "ArrowLeft") step(-1); });
  const m = /^#e(\d+)s(\d+)$/.exec(location.hash);
  if (m && EPISODES[m[1] - 1] && EPISODES[m[1] - 1].scenes[m[2] - 1]) cur = {ep: +m[1] - 1, scene: +m[2] - 1};
  render();
}

function chrome() {
  const links = [["../index.html", "Home"], ["../start.html", "Tests"], ["index.html", "Episodes"], ["../rock/index.html", "Rock"], ["../study.html", "Study"], ["../about.html", "About"], ["../books.html", "Books"]];
  $("nav").innerHTML = links.map(([h, t]) => `<a href="${h}" class="${t === "Episodes" ? "on" : ""}">${t}</a>`).join("");
  mountTheme();
  $("foot").innerHTML = `<div class="wrap row"><p>Agent Defense Theater is a research foundation, not a product. MIT licensed. Built by Scott A. Cole.</p>
    <nav aria-label="Footer"><a href="../about.html">About</a><a href="../books.html">Books</a><a href="${GH}">GitHub</a></nav></div>`;
}

(async function main() {
  chrome();
  try { DATA = await (await fetch("data/episodes.json")).json(); }
  catch (e) { $("screen").innerHTML = `<p><b>Could not load the data.</b> Serve the site over HTTP: <code>python adt.py serve</code>, then open <code>/episodes/</code>.</p>`; return; }
  EPISODES = DATA.episodes.map(ep => ({...ep, scenes: SCENE_BUILDERS[ep.id](ep)}));
  $("fine").innerHTML = `Every bubble, card and verdict above is a real record from run <code>${E(DATA.run_id)}</code> (${E(DATA.records)} records, ${E(DATA.hardware_note)}), read by <code>tools/build_reviewer_episodes.py</code> from <a href="${GH}${E(DATA.source.jsonl)}">${E(DATA.source.jsonl)}</a> and its matching decision log, or from the preregistration's own already-verified text. No RUN LIVE: see <a href="${GH}site/episodes/README.md">README.md</a> for why.`;
  mountTabs();
})();
