// Errata UI (vanilla, no build step). Every server/model string passes through esc() before it touches the DOM.
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
let S = null, sel = null, filter = "all", query = "", tab = "answers", cur = null;

const LABEL = { affected: "Needs correction", needs_review: "Needs review", unaffected: "Still accurate", pending: "Checking", queued: "Queued",
  approved: "Approved, not sent", rejected: "Rejected, original stands" };
const SOURCE = { hindsight_citation: "Hindsight citation", dependency_index: "keyword index", draft_failed: "no draft on file" };
const ORDER = { affected: 0, needs_review: 1, pending: 2, queued: 2, unaffected: 3 };

async function api(path, body) {
  const r = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {});
  const j = await r.json().catch(() => ({ error: `HTTP ${r.status}` }));
  if (!r.ok) throw new Error(j.error || `HTTP ${r.status}`);
  return j;
}
function banner(msg) { const b = $("#banner"); b.hidden = !msg; b.textContent = msg || ""; }
function busy(btn, on, label) { if (!btn) return; btn.disabled = on; if (label) { btn.dataset.l ??= btn.textContent; btn.textContent = on ? label : btn.dataset.l; } }
const DT = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "UTC" });
const D = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
function fmt(iso) { if (!iso) return ""; const d = new Date(iso.length === 10 ? iso + "T00:00:00Z" : iso); return isNaN(d) ? iso : iso.length === 10 ? D.format(d) : DT.format(d) + " UTC"; }
const statusOf = (i) => i.decision === "approve" ? "approved" : i.decision === "reject" ? "rejected" : i.verdict;
const sources = (ss) => ss.map((s) => SOURCE[s] || s).join(" and ");
const answer = (qid) => S.answers.find((a) => a.qid === qid) || {};
const fact = (fid) => S.facts.find((f) => f.fid === fid);
function markQuote(text, quote) {  // highlight only when the exact sentence is really in the text (server-verified in evidence; best-effort here)
  if (!quote) return esc(text);
  const i = text.toLowerCase().indexOf(quote.toLowerCase().replace(/^["“*]+|["”*.]+$/g, ""));
  if (i < 0) return esc(text);
  const n = quote.replace(/^["“*]+|["”*.]+$/g, "").length;
  return esc(text.slice(0, i)) + "<mark>" + esc(text.slice(i, i + n)) + "</mark>" + esc(text.slice(i + n));
}

async function load() {
  try { S = await api("/api/state"); render(); banner(""); }
  catch (e) { banner(`Cannot reach the Errata server (${e.message}). Start it with: uv run python -m errata_app.server`); }
}

function render() {
  $("#status").innerHTML = S.configured
    ? `<span class="dot"></span>Hindsight ${esc(S.hindsight)}, bank <code>${esc(S.bank)}</code>`
    : `<span class="dot off"></span>Hindsight unreachable`;
  if (!S.configured) banner("Hindsight is not reachable. Run scripts/hindsight-local.sh start and make sure Ollama is running. Saved records below are still shown; nothing is faked.");
  const seeded = !!S.seeded_at;
  $("#setup").hidden = seeded || !S.configured;
  $("#workspace").hidden = !seeded;
  const sp = S.seed;
  $("#seedProgress").hidden = !sp.running && !sp.error;
  $("#seedBar").style.width = `${Math.round((100 * sp.done) / (sp.total || 1))}%`;
  $("#seedBarWrap").setAttribute("aria-valuenow", sp.done);
  $("#seedText").textContent = sp.error ? `Failed: ${sp.error}` : `Drafting answer ${sp.done} of ${sp.total} with Hindsight reflect`;
  $("#seedBtn").disabled = sp.running;
  const running = S.changes.some((c) => c.running);
  if (sp.running || running) setTimeout(load, 2000);
  if (!seeded) return;
  if (!S.changes.some((c) => c.id === sel)) {
    const pick = S.changes.find((c) => c.running) || S.changes.find((c) => c.status === "applying") || S.changes.find((c) => c.status === "proposed") || S.changes.find((c) => c.status === "applied") || S.changes[0];
    sel = pick ? pick.id : null;
  }
  renderRail(); renderFocus(); renderRecords();
}

function renderRail() {
  $("#changeList").innerHTML = S.changes.map((c) => {
    const p = c.progress, n = c.impacts.length;
    const meta = c.status === "proposed" ? "Awaiting your confirmation of the fact"
      : c.status === "failed" ? "Failed before any fact changed"
      : c.running ? `Checking ${p.verified} of ${p.candidates} sent answers`
      : c.status === "applying" ? `Interrupted: ${p.verified} of ${p.candidates} checked`
      : `${esc(c.applied_fact)} superseded. ${n} answers checked, ${c.impacts.filter((i) => i.verdict === "affected").length} need correction`;
    return `<li><button class="change" data-sel="${esc(c.id)}" aria-current="${c.id === sel}"><span class="id">${esc(c.id)}, effective ${esc(fmt(c.effective))}</span><span class="t">${esc(c.note.slice(0, 90))}${c.note.length > 90 ? "…" : ""}</span><span class="m">${meta}</span></button></li>`;
  }).join("") || `<li class="quiet">No change posted yet.</li>`;
  document.querySelectorAll("[data-sel]").forEach((b) => (b.onclick = () => { sel = b.dataset.sel; filter = "all"; render(); }));
}

function renderFocus() {
  const c = S.changes.find((x) => x.id === sel);
  const active = document.activeElement && document.activeElement.id === "q";
  $("#focus").innerHTML = !c ? `<div class="card empty"><h2>Nothing has changed yet</h2><p>Post a change on the left. Hindsight recall will suggest which fact it supersedes, and you confirm before anything moves.</p></div>`
    : c.status === "proposed" ? proposalHtml(c) : c.status === "failed" ? failedHtml(c) : radiusHtml(c);
  document.querySelectorAll("[data-w]").forEach((el) => (el.style.width = `${el.dataset.w}%`));  // CSP forbids inline style attributes
  if (active) { const q = $("#q"); if (q) { q.focus(); q.setSelectionRange(q.value.length, q.value.length); } }
  const ab = $("#applyBtn"); if (ab) ab.onclick = () => apply(c.id);
  const rb = $("#resumeBtn"); if (rb) rb.onclick = () => resume(c.id);
  document.querySelectorAll("[data-ev]").forEach((b) => (b.onclick = () => openEvidence(c.id, b.dataset.ev)));
  document.querySelectorAll("[data-filter]").forEach((b) => (b.onclick = () => { filter = b.dataset.filter; renderFocus(); }));
  const q = $("#q"); if (q) q.oninput = () => { query = q.value; renderFocus(); };
}

function proposalHtml(c) {
  const opts = S.facts.map((f) => `<option value="${esc(f.fid)}" ${f.fid === c.suggested_fact ? "selected" : ""}>${esc(f.fid)}: ${esc(f.text.slice(0, 90))}</option>`).join("");
  const ranked = c.ranked_facts.slice(0, 4).map((f) => `<code>${esc(f)}</code>`).join(", ");
  return `<div class="card"><div class="head-row"><h1>Which fact does this change?</h1><span class="stamp">Hindsight recall answered in ${esc(c.recall_ms)} ms</span></div>
    <p class="said">${esc(c.note)}</p>
    <p>Recall ranked the facts this note most likely supersedes: ${ranked || "<em>no match</em>"}. <span class="quiet">Rank order, not a probability. You decide.</span></p>
    <label for="factSel">Fact being superseded</label><select id="factSel">${opts}</select>
    <p class="quiet">Confirming retains the new version in Hindsight, invalidates the old one with a reason, and then checks every sent answer linked to the fact, one local model call each.</p>
    <div class="decide"><button class="primary" id="applyBtn">Supersede fact and check sent answers</button></div></div>`;
}
function failedHtml(c) {
  return `<div class="card"><h1>${esc(c.id)} could not be applied</h1><p class="said">${esc(c.note)}</p><p class="note red">Hindsight rejected the supersede step, so no fact version changed and no answer was checked. The audit trail has the error. Post the change again once Hindsight is reachable.</p></div>`;
}

function radiusHtml(c) {
  const f = fact(c.applied_fact), old = f.history.find((h) => h.superseded_by_change === c.id) || f.history[f.history.length - 1];
  const p = c.progress || { candidates: c.impacts.length, verified: c.impacts.length, pending: [] };
  const n = (v) => c.impacts.filter((i) => i.verdict === v).length;
  const approved = c.impacts.filter((i) => i.decision === "approve").length, rejected = c.impacts.filter((i) => i.decision === "reject").length;
  const total = p.candidates || 1;
  const seg = (k, v) => `<span class="seg-${k}" data-w="${(100 * v) / total}" title="${esc(LABEL[k])}: ${v}"></span>`;
  const stamp = c.running ? `<span class="stamp live">Checking live now</span>`
    : c.status === "applying" ? `<span class="stamp">Interrupted before all answers were checked</span>`
    : `<span class="stamp">Recorded run, verified ${esc(fmt(c.verified_at))}</span>`;
  const job = c.running ? `<div class="jobline" role="status"><div class="bar"><span data-w="${(100 * p.verified) / total}"></span></div>
      <span>Checking ${esc(p.pending[0] || "")} (${p.verified + 1} of ${p.candidates}). One local model call per answer, usually 40 s to 3 min.</span></div>`
    : c.status === "applying" ? `<div class="jobline"><span>${p.verified} of ${p.candidates} checked. ${c.job_error ? "Last error: " + esc(c.job_error) + ". " : ""}Resuming only checks the ${p.pending.length} remaining.</span><button class="ghost small" id="resumeBtn">Resume checking</button></div>` : "";
  const items = c.impacts.map((i) => ({ ...i, st: statusOf(i) }));
  for (const q of p.pending) items.push({ qid: q, verdict: c.running && q === p.pending[0] ? "pending" : "queued", st: c.running && q === p.pending[0] ? "pending" : "queued", sources: [], reason: "", decision: null });
  items.sort((a, b) => (ORDER[a.verdict] ?? 9) - (ORDER[b.verdict] ?? 9) || (a.decision ? 1 : 0) - (b.decision ? 1 : 0) || a.qid.localeCompare(b.qid));
  const counts = { all: items.length, affected: n("affected"), needs_review: n("needs_review"), unaffected: n("unaffected"), decided: approved + rejected };
  const shown = items.filter((i) => filter === "all" || (filter === "decided" ? !!i.decision : i.verdict === filter))
    .filter((i) => { if (!query) return true; const a = answer(i.qid), s = `${i.qid} ${a.deal} ${a.question} ${a.text} ${i.reason}`.toLowerCase(); return s.includes(query.toLowerCase()); });
  const chip = (k, label) => `<button class="pill-btn" data-filter="${k}" aria-pressed="${filter === k}">${label} ${counts[k]}</button>`;
  const others = S.answers.length - p.candidates;
  return `<div class="card">
    <div class="head-row"><h1>${esc(c.note)}</h1>${stamp}</div>
    <p class="quiet sub">Change ${esc(c.id)}, effective ${esc(fmt(c.effective))}. Fact ${esc(f.fid)} moved from version ${old ? old.version : "?"} to version ${f.version}.</p>
    <div class="factshift">
      <div class="v"><span class="k">Before, ${esc(old?.doc_id)}, invalidated in Hindsight${old?.invalidated_memories != null ? ` (${old.invalidated_memories} memor${old.invalidated_memories === 1 ? "y" : "ies"})` : ""}</span><span class="old">${esc(old?.text)}</span></div>
      <div class="v new"><span class="k">Now, ${esc(f.doc_id)}, valid</span>${esc(f.text)}</div>
    </div>
    <div class="radius" aria-label="Sent answers linked to this fact, by verdict">
      <div class="bar-seg">${seg("affected", n("affected"))}${seg("needs_review", n("needs_review"))}${seg("unaffected", n("unaffected"))}${seg("pending", p.pending.length)}</div>
      <ul class="tally">
        <li><b>${p.candidates}</b><span>sent answers linked to ${esc(f.fid)}</span></li>
        <li><span class="sw seg-affected"></span><b>${n("affected")}</b><span>need correction</span></li>
        <li><span class="sw seg-needs_review"></span><b>${n("needs_review")}</b><span>need your review</span></li>
        <li><span class="sw seg-unaffected"></span><b>${n("unaffected")}</b><span>still accurate</span></li>
        ${p.pending.length ? `<li><span class="sw seg-pending"></span><b>${p.pending.length}</b><span>not yet checked</span></li>` : ""}
        ${approved + rejected ? `<li><b>${approved}</b><span>approved, not sent${rejected ? `, ${rejected} rejected` : ""}</span></li>` : ""}
      </ul>
      ${job}
    </div>
    <div class="toolbar"><div class="filters">${chip("all", "All")}${chip("affected", LABEL.affected)}${chip("needs_review", LABEL.needs_review)}${chip("unaffected", LABEL.unaffected)}${chip("decided", "Decided")}</div>
      <input id="q" type="search" placeholder="Filter by customer, answer or text" aria-label="Filter answers" value="${esc(query)}"></div>
    <div class="rows">${shown.map(rowHtml).join("") || `<p class="empty">No answers match this filter.</p>`}</div>
    <p class="others">${others} other sent answers are not linked to ${esc(f.fid)} by Hindsight citation or keyword index, so they were not re-checked.</p>
  </div>`;
}

function rowHtml(i) {
  const a = answer(i.qid), st = i.st;
  const body = i.verdict === "pending" ? `<div class="why">Hindsight reflect is judging this answer against the current fact.</div>`
    : i.verdict === "queued" ? `<div class="why">Waiting its turn.</div>`
    : i.quoted ? `<div class="quote">Sentence now false: <mark>${esc(i.quoted)}</mark></div><div class="why">${esc(i.reason)}</div>`
    : `<div class="why">${esc(i.reason)}</div>`;
  const meta = i.sources.length ? `<div class="meta">Linked to the fact via ${esc(sources(i.sources))}${i.decision ? `. ${esc(LABEL[st])} by ${esc(i.reviewer)}, ${esc(fmt(i.decided_at))}` : ""}</div>` : "";
  const act = i.sources.length ? `<button class="${i.verdict === "affected" && !i.decision ? "primary" : "ghost"} small" data-ev="${esc(i.qid)}">${i.decision || i.verdict === "unaffected" ? "Open evidence" : "Review evidence"}</button>` : "";
  return `<article class="row"><div><span class="status ${esc(st)}">${esc(LABEL[st] || st)}</span></div>
    <div><div class="who"><small>${esc(i.qid)}</small>${esc(a.deal)}</div><div class="q">${esc(a.question)}</div>${body}${meta}</div>
    <div class="act">${act}</div></article>`;
}

function renderRecords() {
  const last = {};
  for (const c of S.changes) for (const i of c.impacts) if (!(i.qid in last)) last[i.qid] = i;
  $("#answers tbody").innerHTML = S.answers.map((a) => {
    const cited = a.cited_facts.map((f) => `<span class="chip cite" title="cited by Hindsight reflect (based_on)">${esc(f)}</span>`).join("");
    const idx = a.index_deps.filter((f) => !a.cited_facts.includes(f)).map((f) => `<span class="chip idx" title="keyword index">${esc(f)}</span>`).join("");
    const st = a.status.startsWith("correction") ? `<span class="status approved">v${a.version}, approved, not sent</span>`
      : a.status.startsWith("draft_failed") ? `<span class="status needs_review">Draft failed</span>` : `<span class="status">Sent ${esc(fmt(a.sent_at))}</span>`;
    const t = a.text || "";
    return `<tr><td><code>${esc(a.qid)}</code></td><td>${esc(a.deal)}</td><td>${esc(a.question)}</td><td class="ans">${esc(t.slice(0, 240))}${t.length > 240 ? `<span class="more" title="${esc(t)}">… (${t.length} chars)</span>` : t ? "" : "<em>no draft</em>"}</td><td>${cited}${idx}</td><td>${st}</td></tr>`;
  }).join("");
  $("#facts").innerHTML = S.facts.map((f) => `<li><span class="v">${esc(f.fid)} v${f.version}</span>${esc(f.text)}${
    f.history.map((h) => `<span class="old">v${h.version}: ${esc(h.text)} (valid until ${esc(fmt(h.valid_to))}, superseded by ${esc(h.superseded_by_change)})</span>`).join("")}</li>`).join("");
  $("#log").innerHTML = S.events.map((e) => `<li><span class="at">${esc(fmt(e.at))}</span><strong>${esc(e.kind)}</strong><span class="d">${esc(e.detail)}</span></li>`).join("");
}

// ---- evidence time machine ----------------------------------------------------------------
async function openEvidence(cid, qid) {
  cur = { cid, qid };
  const dlg = $("#review");
  $("#revBody").innerHTML = `<p class="quiet">Loading evidence…</p>`;
  if (!dlg.open) dlg.showModal();
  try { renderEvidence(await api(`/api/changes/${cid}/impacts/${qid}/evidence`)); }
  catch (e) { $("#revBody").innerHTML = `<p class="note red">Could not load evidence: ${esc(e.message)}</p>`; }
}

function memHtml(mems, live, noun) {
  if (mems === null || mems === undefined) return live ? "" : `<div class="mem">Hindsight unreachable, so the live memory state is not shown. <span class="stored-tag">stored evidence only</span></div>`;
  if (!mems.length) return `<div class="mem">No ${esc(noun)} memories found in Hindsight. <span class="live-tag">live</span></div>`;
  return `<div class="mem">${mems.length} ${esc(noun)} memor${mems.length === 1 ? "y" : "ies"} in Hindsight <span class="live-tag">live</span>${mems.slice(0, 3).map((m) => `<div><b>${esc(m.state)}</b> <code>${esc((m.id || "").slice(0, 8))}</code> ${esc(m.text.slice(0, 140))}${m.invalidation_reason ? `<div>Reason: ${esc(m.invalidation_reason)}</div><div>Invalidated ${esc(fmt(m.invalidated_at))}</div>` : ""}</div>`).join("")}</div>`;
}

function renderEvidence(ev) {
  const imp = S.changes.find((c) => c.id === ev.change_id).impacts.find((i) => i.qid === ev.qid);
  const st = statusOf(imp);
  $("#revTitle").textContent = `${ev.qid}: ${ev.deal}`;
  const tl = ev.timeline.map((s) => {
    if (s.kind === "fact_retained") return `<li class="tl"><div class="when">${esc(fmt(s.at))}</div><div class="what"><h3>Fact ${esc(ev.fact_id)} version ${s.version} retained</h3><div class="doc">${esc(s.doc_id)}</div><p class="text old">${esc(s.text)}</p></div></li>`;
    if (s.kind === "answer_sent") return `<li class="tl"><div class="when">${esc(fmt(s.at))}</div><div class="what"><h3>Answer sent to ${esc(ev.deal)}</h3><div class="doc">${esc(s.doc_id)}</div><p class="text">${ev.quote_found ? markQuote(s.text, ev.quoted) : esc(s.text)}</p>${ev.quote_found ? `<p class="note ok">The highlighted sentence is the verifier's quote, verified in code as verbatim text of this answer.</p>` : ""}${memHtml(s.memories, ev.live, "sent-answer")}</div></li>`;
    if (s.kind === "change_effective") return `<li class="tl change"><div class="when">${esc(fmt(s.at))}</div><div class="what"><h3>Change ${esc(s.change_id)} takes effect</h3><p class="text">${esc(s.note)}</p>
        <p><strong>Old version ${esc(s.old_doc_id)} invalidated.</strong></p>${memHtml(s.invalidated, ev.live, "invalidated")}${s.still_valid && s.still_valid.length ? `<p class="note red">${s.still_valid.length} memories of the old version are still valid in Hindsight. Verdicts for this change were routed to review.</p>` : ""}
        <p><strong>New version ${esc(s.new_doc_id)} retained.</strong></p><p class="text">${esc(s.new_text)}</p>${memHtml(s.new_version, ev.live, "valid")}</div></li>`;
    if (s.kind === "verified") return `<li class="tl verified"><div class="when">${esc(fmt(s.at))}</div><div class="what"><h3>Verdict: ${esc(LABEL[s.verdict] || s.verdict)}${s.recorded ? `<span class="stored-tag">recorded run</span>` : ""}</h3>
        <p>${esc(s.reason)}</p>
        <p class="quiet">This answer was linked to ${esc(ev.fact_id)} via ${esc(sources(ev.provenance))}. The verdict came from Hindsight reflect with a response schema, judged against the current fact only${s.verify_ms ? `, in ${(s.verify_ms / 1000).toFixed(0)} s` : ""}.</p>
        ${s.verdict === "needs_review" ? `<p class="note">Routed to you instead of being cleared or corrected automatically.</p>` : ""}
        ${s.based_on && s.based_on.length ? `<div class="mem">Memories reflect based this verdict on <span class="stored-tag">stored at verification</span>${s.based_on.map((m) => `<div><code>${esc(m.document_id || m.type)}</code> ${esc(m.text)}</div>`).join("")}</div>` : `<div class="mem">reflect returned no based_on memories for this verdict.</div>`}</div></li>`;
    if (s.kind === "decided") return `<li class="tl decided"><div class="when">${esc(fmt(s.at))}</div><div class="what"><h3>${s.decision === "approve" ? "Correction approved, not sent" : "Rejected, original stands"}</h3><p>By ${esc(s.reviewer)}. Retained in Hindsight as <code>${esc(s.retained_as)}</code>.</p>${memHtml(s.memories, ev.live, "decision")}</div></li>`;
    return "";
  }).join("");
  const sent = ev.timeline.find((s) => s.kind === "answer_sent"), dec = ev.timeline.find((s) => s.kind === "decided");
  const right = dec ? (dec.decision === "approve" ? `<div class="pane"><h3>Approved correction, version ${esc(dec.retained_as.split(":v")[1])}, not sent</h3><p class="final">${esc(dec.final_text)}</p></div>` : `<div class="pane"><h3>Decision</h3><p>Rejected by ${esc(dec.reviewer)}. The original answer stands.</p></div>`)
    : imp.verdict === "unaffected" ? `<div class="pane"><h3>Judged still accurate</h3><p class="quiet">Nothing to correct. If you disagree, the verdict reason on the left is the place to start.</p></div>`
    : `<div class="pane"><h3>Drafted correction, edit before approving</h3><textarea id="draft" aria-label="Drafted correction">${esc(imp.draft)}</textarea>
        <label for="reviewer">Your name, recorded with the decision</label><input id="reviewer" autocomplete="name" required maxlength="80">
        <div class="decide"><p class="quiet">Approving records version ${esc(sent.version + 1)} of this answer and retains your decision in Hindsight. Nothing is sent to the customer.</p>
        <button type="button" class="ghost danger" id="rejectBtn">Reject, keep original</button><button type="button" class="primary" id="approveBtn">Approve correction</button></div></div>`;
  $("#revBody").innerHTML = `<div class="ev-head"><div class="q">Asked: “${esc(ev.question)}”</div></div>
    <div class="ev-grid"><ol class="timeline">${tl}</ol>
    <div class="compare"><div class="pane"><h3>Sent ${esc(fmt(sent.at))}, version ${sent.version}</h3><p class="sent">${ev.quote_found ? markQuote(sent.text, ev.quoted) : esc(sent.text)}</p></div>${right}</div></div>`;
  const ab = $("#approveBtn"), rb = $("#rejectBtn");
  if (ab) ab.onclick = () => decide("approve"); if (rb) rb.onclick = () => decide("reject");
}

async function decide(decision) {
  const reviewer = $("#reviewer").value.trim();
  if (!reviewer) { $("#reviewer").focus(); return; }
  const btn = decision === "approve" ? $("#approveBtn") : $("#rejectBtn");
  busy(btn, true, "Saving…");
  try {
    await api(`/api/changes/${cur.cid}/impacts/${cur.qid}/decision`, { decision, reviewer, text: $("#draft").value });
    await load(); await openEvidence(cur.cid, cur.qid);
  } catch (e) { banner(e.message); busy(btn, false); }
}

async function apply(cid) {
  const btn = $("#applyBtn"); busy(btn, true, "Superseding the fact in Hindsight…");
  try { await api(`/api/changes/${cid}/apply`, { fact_id: $("#factSel").value }); await load(); }
  catch (e) { banner(e.message); busy(btn, false); }
}
async function resume(cid) {
  const btn = $("#resumeBtn"); busy(btn, true, "Resuming…");
  try { await api(`/api/changes/${cid}/resume`, {}); await load(); }
  catch (e) { banner(e.message); busy(btn, false); }
}

$("#seedBtn").onclick = async () => { try { await api("/api/seed", {}); load(); } catch (e) { banner(e.message); } };
$("#postForm").onsubmit = async (ev) => {
  ev.preventDefault();
  const btn = $("#proposeBtn"); busy(btn, true, "Asking Hindsight…");
  try { const c = await api("/api/changes", { note: $("#note").value, effective: $("#eff").value }); $("#note").value = ""; sel = c.id; await load(); }
  catch (e) { banner(e.message); } finally { busy(btn, false); }
};
$("#cancelBtn").onclick = () => $("#review").close();
document.querySelectorAll("[data-tab]").forEach((b) => (b.onclick = () => {
  tab = b.dataset.tab;
  document.querySelectorAll("[data-tab]").forEach((x) => x.setAttribute("aria-selected", x.dataset.tab === tab));
  document.querySelectorAll("[role=tabpanel]").forEach((p) => (p.hidden = p.id !== `tab-${tab}`));
}));
$("#eff").value = new Date().toISOString().slice(0, 10);
load();
