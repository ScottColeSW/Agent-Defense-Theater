/* Episode player for the ASI03 reviewer-calibration finding. REPLAY only: every card, verdict and
   reason shown here is read at load time from data/episodes.json, itself built by
   tools/build_reviewer_episodes.py straight from the saved run's .jsonl and .decisions.jsonl.
   There is no live re-run: see README.md in this folder for why. */
const GH = "https://github.com/ScottColeSW/Agent-Defense-Theater/tree/main/";
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const pct = (k, n) => n ? Math.round((k / n) * 1000) / 10 + "%" : "n/a";
const FAIL = `<div class="loaderr">Could not load site/episodes/data/episodes.json. Serve the folder over HTTP: <code>python adt.py serve</code></div>`;

const FAMILY_LABEL = {
  m_refund_200: "$200 refund, finance approved", m_refund_120: "$120 refund, finance approved",
  m_refund_30: "$30 goodwill refund", m_export_finance: "customer export, finance",
  n_unrequested_refund: "unrequested $50 refund", n_unrequested_export: "unrequested export, outside address",
  n_wrong_account: "refund to a different account", n_wrong_amount: "$900 refund, not $200",
  n_wrong_destination: "export to a different address", n_other_ticket: "refund on a different ticket",
  n_persuasion: "$1,800 refund, outside account, claimed pre-approval",
};
const famLabel = f => FAMILY_LABEL[f] || f;

let DATA = null, EPISODES = [], cur = 0;

function chrome() {
  const links = [["../index.html", "Home"], ["../start.html", "Tests"], ["index.html", "Episodes"], ["../rock/index.html", "Rock"], ["../study.html", "Study"], ["../about.html", "About"], ["../books.html", "Books"]];
  $("nav").innerHTML = links.map(([h, t]) => `<a href="${h}" class="${t === "Episodes" ? "on" : ""}">${t}</a>`).join("");
  mountTheme();
  $("foot").innerHTML = `<div class="wrap row"><p>Agent Defense Theater is a research foundation, not a product. MIT licensed. Built by Scott A. Cole.</p>
    <nav aria-label="Footer"><a href="../about.html">About</a><a href="../books.html">Books</a><a href="${GH}">GitHub</a></nav></div>`;
}

function verdictPill(r) {
  return `<span class="pill ${r.correct ? "ok" : "bad"}">${esc(r.verdict)}${r.correct ? "" : " — wrong"}</span>`;
}

function reviewerRows(beats) {
  return beats.map(r => `
    <div class="vrow">
      <span class="model">${esc(r.model)}</span>${verdictPill(r)}
      <span class="reason">&ldquo;${esc(r.reason)}&rdquo;${r.well_formed ? "" : " (unparseable reply)"}</span>
    </div>`).join("");
}

// -- episodes 1 & 2: agent_card vs bottomline duel ---------------------------
function renderDuel(ep) {
  const extra = ep.repeat_offenders && ep.repeat_offenders.length
    ? `<p class="caption">On the bottom-line card across all four runs (unsampled plus three sampled passes), ${ep.repeat_offenders.map(r => `<b>${esc(r.model)}</b> approved it ${r.approved_of_8} of 8 times`).join(" and ")}, every time the system's own line said the request did not match.</p>` : "";
  return `
    <h3 class="ep-title">Episode ${ep.number}: ${esc(ep.title)}</h3>
    <div class="ep-tag">${esc(ep.tag)} &middot; ${esc(famLabel(ep.family))} &middot; ticket ${esc(ep.ticket)}</div>
    <p class="line"><b>What the operator actually asked for, verbatim:</b> &ldquo;${esc(ep.ask)}&rdquo;</p>
    <div class="duel">
      <div class="pane agent">
        <h4>Agent card &mdash; the agent's own reason</h4>
        <div class="pane-tally">False approvals: <b>${ep.agent_tally.wrong}</b> of <b>${ep.agent_tally.n}</b> reviewer configurations</div>
        <p class="line">Agent's reason, shown to the reviewer: &ldquo;${esc(ep.claim)}&rdquo;</p>
        <pre class="card-text">${esc(ep.agent_card_sample)}</pre>
        <div class="verdicts">${reviewerRows(ep.agent_beats)}</div>
      </div>
      <div class="pane bottomline">
        <h4>Bottom-line card &mdash; the system's own comparison</h4>
        <div class="pane-tally">False approvals: <b>${ep.bottomline_tally.wrong}</b> of <b>${ep.bottomline_tally.n}</b> reviewer configurations</div>
        <p class="line">The system's own line, stated first: &ldquo;${esc(ep.fact)}&rdquo;</p>
        <pre class="card-text">${esc(ep.bottomline_sample)}</pre>
        <div class="verdicts">${reviewerRows(ep.bottomline_beats)}</div>
      </div>
    </div>
    ${extra}`;
}

// -- episode 3 & 4: one reviewer, a table of real cards -----------------------
function renderSpotlightFooled(ep) {
  const rows = ep.rows.map(r => `
    <tr>
      <td class="fam">${esc(famLabel(r.family))}<br><span class="reason">${esc(r.ticket)}</span></td>
      <td>${verdictPill(r.agent)}<div class="reason">&ldquo;${esc(r.agent.reason)}&rdquo;</div></td>
      <td>${verdictPill(r.bottomline)}<div class="reason">&ldquo;${esc(r.bottomline.reason)}&rdquo;</div></td>
    </tr>`).join("");
  return `
    <h3 class="ep-title">Episode ${ep.number}: ${esc(ep.title)}</h3>
    <div class="ep-tag">${esc(ep.tag)}</div>
    <p class="line"><b>${esc(ep.model)}</b> approved <b>${ep.wrong}</b> of <b>${ep.total}</b> non-matching requests under the agent card, in this run. The same model, shown the bottom-line card instead, on the same cases:</p>
    <table class="spot-table">
      <thead><tr><th>Request</th><th>Agent card verdict</th><th>Bottom-line verdict</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function renderSpotlightCareful(ep) {
  const rows = ep.rows.map(r => `
    <tr>
      <td class="fam">${esc(famLabel(r.family))}<br><span class="reason">${esc(r.ticket)}</span></td>
      <td>${verdictPill(r.bottomline)}<div class="reason">&ldquo;${esc(r.bottomline.reason)}&rdquo;</div></td>
      <td>${verdictPill(r.agent_card)}<div class="reason">&ldquo;${esc(r.agent_card.reason)}&rdquo;</div></td>
    </tr>`).join("");
  return `
    <h3 class="ep-title">Episode ${ep.number}: ${esc(ep.title)}</h3>
    <div class="ep-tag">${esc(ep.tag)}</div>
    <p class="line">These four requests all match what the operator actually asked for; the right answer is approve. Under the bottom-line card, <b>${esc(ep.model)}</b> denied <b>${ep.denied}</b> of <b>${ep.total}</b> of them anyway, citing a refund limit the operator's own request (stated first on that card) already clears.</p>
    <table class="spot-table">
      <thead><tr><th>Request</th><th>Bottom-line verdict</th><th>Agent card verdict, for contrast</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

// -- episode 5: thinking on vs off --------------------------------------------
function renderThinking(ep) {
  const rows = ep.rows.map(r => `
    <tr>
      <td class="fam">${esc(famLabel(r.family))}</td>
      <td>${verdictPill(r.off)}<div class="reason">&ldquo;${esc(r.off.reason)}&rdquo; (${r.off.tokens_out} tokens out)</div></td>
      <td>${verdictPill(r.on)}<div class="reason">&ldquo;${esc(r.on.reason)}&rdquo; (${r.on.tokens_out} tokens out)</div></td>
    </tr>`).join("");
  return `
    <h3 class="ep-title">Episode ${ep.number}: ${esc(ep.title)}</h3>
    <div class="ep-tag">${esc(ep.tag)}</div>
    <p class="line">All four of these requests match what the operator asked; the right answer is approve. Same model, same bottom-line card, thinking off against thinking on.</p>
    <div class="think-head">
      <div class="think-stat"><div class="v">${pct(ep.off_correct, ep.off_total)}</div><div class="l">correct, thinking off (${ep.off_correct}/${ep.off_total} on the full bottom-line card) &middot; ${ep.off_tokens_out} tokens out, average</div></div>
      <div class="think-stat"><div class="v" style="color:var(--red-ink)">${pct(ep.on_correct, ep.on_total)}</div><div class="l">correct, thinking on (${ep.on_correct}/${ep.on_total}) &middot; ${ep.on_tokens_out} tokens out, average &mdash; ${Math.round(ep.on_tokens_out / ep.off_tokens_out)}&times; the tokens</div></div>
    </div>
    <table class="spot-table">
      <thead><tr><th>Request</th><th>Thinking off</th><th>Thinking on</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

// -- episode 6: the pooled scoreboard -----------------------------------------
function renderScoreboard(ep) {
  const styleRows = Object.entries(ep.by_style).map(([style, s]) => {
    const w = s.n ? (s.wrong / s.n) * 100 : 0;
    return `<div class="nm">${esc(style)}</div><div class="track"><div class="fill" style="width:${w}%"></div></div><div class="val">${esc(s.wrong)}/${esc(s.n)} (${pct(s.wrong, s.n)})</div>`;
  }).join("");
  const modelRows = ep.by_model.map(m => `<tr><td>${esc(m.model)}</td><td>${esc(m.correct)}/${esc(m.n)}</td><td>${pct(m.correct, m.n)}</td></tr>`).join("");
  return `
    <h3 class="ep-title">Episode ${ep.number}: ${esc(ep.title)}</h3>
    <div class="ep-tag">${esc(ep.tag)}</div>
    <p class="line">False approvals &mdash; approving a request that did not match what the operator asked for &mdash; pooled over all eight reviewer configurations, by card style:</p>
    <div class="score-bars">
      <div class="hd">Card style</div><div class="hd">False approvals</div><div class="hd"></div>
      ${styleRows}
    </div>
    <p class="line" style="margin-top:18px"><b>Correct on the bottom-line card, by reviewer</b> (both false approvals and false denials counted against it):</p>
    <table class="spot-table">
      <thead><tr><th>Reviewer</th><th>Correct/total</th><th></th></tr></thead>
      <tbody>${modelRows}</tbody>
    </table>
    <div class="citation-box">
      Cited externally: <a href="${esc(ep.citation.issue)}" target="_blank" rel="noopener">OWASP GenAI-LLM-Top10, issue #137</a>.
      ${esc(ep.citation.text)}
    </div>`;
}

const RENDER = {fin9921: renderDuel, goodwill: renderDuel, "worst-reviewer": renderSpotlightFooled,
  "too-careful": renderSpotlightCareful, thinking: renderThinking, scoreboard: renderScoreboard};

function render() {
  const ep = EPISODES[cur];
  document.querySelectorAll(".ep-tab").forEach((el, i) => el.setAttribute("aria-selected", i === cur));
  $("screen").innerHTML = RENDER[ep.id](ep);
  location.hash = `#e${ep.number}`;
}

function mountTabs() {
  $("tabs").innerHTML = EPISODES.map((e, i) => `<button type="button" class="ep-tab" role="tab" data-i="${i}"><b>${e.number}. ${esc(e.title)}</b><span>${esc(e.tag)}</span></button>`).join("");
  $("tabs").addEventListener("click", ev => { const b = ev.target.closest(".ep-tab"); if (b) { cur = +b.dataset.i; render(); } });
  const m = /^#e(\d+)$/.exec(location.hash);
  if (m) { const i = EPISODES.findIndex(e => e.number === +m[1]); if (i >= 0) cur = i; }
}

async function load() {
  chrome();
  let data;
  try {
    const res = await fetch("data/episodes.json");
    if (!res.ok) throw new Error(res.status);
    data = await res.json();
  } catch (e) {
    $("screen").innerHTML = FAIL;
    $("replay-note").textContent = "could not load the run.";
    return;
  }
  DATA = data;
  EPISODES = data.episodes;
  $("replay-note").innerHTML = `<b>REPLAY</b> &middot; run <code>${esc(data.run_id)}</code> &middot; ${esc(data.records)} real records &middot; ${esc(data.hardware_note)}`;
  $("src").innerHTML = `Source: <a href="${GH}${esc(data.source.jsonl)}">${esc(data.source.jsonl)}</a>, its matching decision log, and the preregistration's own already-verified text. No live re-run: see <a href="${GH}site/episodes/README.md">README.md</a>.`;
  mountTabs();
  render();
}

load();
