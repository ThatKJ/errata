// Errata UI (vanilla). All server/LLM text goes through esc() before rendering.
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
let S = null, current = null;

async function api(path, body) {
  const r = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {});
  const j = await r.json().catch(() => ({ error: `HTTP ${r.status}` }));
  if (!r.ok) throw new Error(j.error || `HTTP ${r.status}`);
  return j;
}
function banner(msg) { const b = $("#banner"); b.hidden = !msg; b.textContent = msg ? `Error: ${msg}` : ""; }
function busy(btn, on, label) { btn.disabled = on; if (label) { btn.dataset.l ??= btn.textContent; btn.textContent = on ? label : btn.dataset.l; } }

async function load() {
  try { S = await api("/api/state"); render(); banner(""); }
  catch (e) { banner(`cannot reach the Errata server (${e.message})`); }
}

function render() {
  $("#status").innerHTML = S.configured
    ? `<span class="dot"></span>Hindsight Cloud · bank <code>${esc(S.bank)}</code>`
    : `<span class="dot off"></span>Hindsight not configured`;
  if (!S.configured) { banner("HINDSIGHT_API_KEY is not set on the server. Add it to .env and restart. (No data is faked.)"); }
  const seeded = !!S.seeded_at;
  $("#setup").hidden = seeded || !S.configured;
  $("#workspace").hidden = !seeded;
  const sp = S.seed;
  $("#seedProgress").hidden = !sp.running && !sp.error;
  $("#seedBar").style.width = `${Math.round((100 * sp.done) / (sp.total || 1))}%`;
  $("#seedText").textContent = sp.error ? `Failed: ${sp.error}` : `Drafting answer ${sp.done}/${sp.total} with Hindsight reflect…`;
  $("#seedBtn").disabled = sp.running;
  if (sp.running) setTimeout(load, 1500);
  if (!seeded) return;

  const lastImpact = {};
  for (const c of S.changes) for (const i of c.impacts) if (!(i.qid in lastImpact)) lastImpact[i.qid] = i;
  $("#answers tbody").innerHTML = S.answers.map((a) => {
    const cited = a.cited_facts.map((f) => `<span class="chip cite" title="cited by Hindsight reflect (based_on)">${esc(f)}</span>`).join("");
    const idx = a.index_deps.filter((f) => !a.cited_facts.includes(f)).map((f) => `<span class="chip idx" title="app dependency index">${esc(f)}</span>`).join("");
    const st = a.status.startsWith("correction") ? `<span class="pill fixed">v${a.version} · ${esc(a.status)}</span>`
      : a.status.startsWith("draft_failed") ? `<span class="pill needs_review">draft failed</span>` : `<span class="pill sent">sent ${esc(a.sent_at)}</span>`;
    return `<tr><td>${esc(a.qid)}</td><td>${esc(a.deal)}</td><td>${esc(a.question)}</td><td class="ans">${esc(a.text) || "<em>none</em>"}</td><td>${cited}${idx}</td><td>${st}</td></tr>`;
  }).join("");

  $("#facts").innerHTML = S.facts.map((f) => `<li><span class="v">${esc(f.fid)} · v${f.version}</span> ${esc(f.text)}${
    f.history.map((h) => `<div class="old">v${h.version}: ${esc(h.text)} <span class="v">(until ${esc(h.valid_to)}, ${esc(h.superseded_by_change)})</span></div>`).join("")}</li>`).join("");

  $("#log").innerHTML = S.events.map((e) => `<li>${esc(e.at.replace("T", " ").slice(0, 16))} — <strong>${esc(e.kind)}</strong> ${esc(e.detail)}</li>`).join("");

  const proposed = S.changes.find((c) => c.status === "proposed");
  $("#proposal").innerHTML = proposed ? proposalHtml(proposed) : "";
  if (proposed) $("#applyBtn").onclick = () => apply(proposed.id);

  const applied = S.changes.find((c) => c.status === "applied");
  $("#impacts").innerHTML = applied ? impactsHtml(applied) : `<p class="empty">Post a change to see which sent answers it touches.</p>`;
  document.querySelectorAll("[data-review]").forEach((b) => (b.onclick = () => openReview(applied, b.dataset.review)));
}

function proposalHtml(c) {
  const opts = Object.values(S.facts).map((f) => `<option value="${esc(f.fid)}" ${f.fid === c.suggested_fact ? "selected" : ""}>${esc(f.fid)} — ${esc(f.text.slice(0, 80))}</option>`).join("");
  return `<div class="proposal"><p><strong>Hindsight recall</strong> ranked the facts this note most likely changes: ${c.ranked_facts.slice(0, 4).map((f) => `<code>${esc(f)}</code>`).join(" › ") || "<em>no match</em>"}
    <span class="hint">(rank order only, not a probability · ${esc(c.recall_ms)} ms)</span></p>
    <label for="factSel">Fact being superseded — confirm or correct</label><select id="factSel">${opts}</select>
    <div class="row end"><button class="primary" id="applyBtn">Supersede fact &amp; check sent answers</button></div></div>`;
}

function impactsHtml(c) {
  const by = (v) => c.impacts.filter((i) => i.verdict === v);
  const others = S.answers.length - c.impacts.length;
  const row = (i) => `<div class="imp"><span class="pill ${esc(i.verdict)}">${esc(i.verdict.replace("_", " "))}</span>
    <div><strong>${esc(i.qid)}</strong> · ${esc(S.answers.find((a) => a.qid === i.qid)?.deal)}<div class="why">${esc(i.reason)}</div>
    <div class="why">found via ${i.sources.map((s) => `<code>${esc(s)}</code>`).join(" + ")}</div></div>
    ${i.decision ? `<span class="pill ${i.decision === "approve" ? "fixed" : "sent"}">${esc(i.decision)}d · ${esc(i.reviewer)}</span>`
      : i.verdict !== "unaffected" ? `<button class="ghost" data-review="${esc(i.qid)}">Review</button>` : "<span></span>"}</div>`;
  return `<p class="hint">Change <code>${esc(c.id)}</code> superseded <code>${esc(c.applied_fact)}</code>: “${esc(c.note.slice(0, 140))}”</p>
    <div class="group">Needs correction (${by("affected").length})</div>${by("affected").map(row).join("") || '<p class="empty">none</p>'}
    <div class="group">Needs human review (${by("needs_review").length})</div>${by("needs_review").map(row).join("") || '<p class="empty">none</p>'}
    <div class="group">Checked — still accurate (${by("unaffected").length})</div>${by("unaffected").map(row).join("") || '<p class="empty">none</p>'}
    <p class="hint">${others} other sent answers are not linked to ${esc(c.applied_fact)} by citation or index, so they were not re-checked.</p>`;
}

function openReview(c, qid) {
  current = { c, qid };
  const i = c.impacts.find((x) => x.qid === qid), a = S.answers.find((x) => x.qid === qid);
  const f = S.facts.find((x) => x.fid === c.applied_fact), prev = f.history[f.history.length - 1];
  $("#revBody").innerHTML = `<p><strong>${esc(qid)}</strong> · ${esc(a.deal)} asked: “${esc(a.question)}”</p>
    <div class="cmp"><div class="box"><h3>Sent ${esc(a.sent_at)} (v${a.version})</h3>${esc(a.text)}</div>
    <div class="box"><h3>Drafted correction — edit before approving</h3><textarea id="draft" rows="5">${esc(i.draft)}</textarea></div></div>
    <div class="evidence"><strong>Memory evidence</strong>
      <ul><li>Fact <code>${esc(f.fid)}</code> v${prev?.version}: <span class="old">${esc(prev?.text)}</span> — invalidated in Hindsight, valid until ${esc(prev?.valid_to)}</li>
      <li>Fact <code>${esc(f.fid)}</code> v${f.version} (current): ${esc(f.text)}</li>
      <li>This answer was linked to ${esc(f.fid)} via ${i.sources.map((s) => `<code>${esc(s)}</code>`).join(" + ")}</li>
      ${i.evidence.map((m) => `<li>reflect <code>based_on</code>: <code>${esc(m.document_id || m.type)}</code> — ${esc(m.text)}</li>`).join("") || "<li>reflect returned no based_on memories for this verdict</li>"}</ul>
      <div class="why">Verdict reason: ${esc(i.reason)}</div></div>`;
  $("#review").showModal();
}

async function decide(decision) {
  const reviewer = $("#reviewer").value.trim();
  if (!reviewer) { $("#reviewer").focus(); return; }
  const btn = decision === "approve" ? $("#approveBtn") : $("#rejectBtn");
  busy(btn, true, "Saving…");
  try {
    await api(`/api/changes/${current.c.id}/impacts/${current.qid}/decision`, { decision, reviewer, text: $("#draft").value });
    $("#review").close(); await load();
  } catch (e) { banner(e.message); } finally { busy(btn, false); }
}

async function apply(cid) {
  const btn = $("#applyBtn"); busy(btn, true, "Checking sent answers with Hindsight…");
  try { await api(`/api/changes/${cid}/apply`, { fact_id: $("#factSel").value }); await load(); }
  catch (e) { banner(e.message); busy(btn, false); }
}

$("#seedBtn").onclick = async () => { try { await api("/api/seed", {}); load(); } catch (e) { banner(e.message); } };
$("#proposeBtn").onclick = async () => {
  const btn = $("#proposeBtn"); busy(btn, true, "Asking Hindsight…");
  try { await api("/api/changes", { note: $("#note").value, effective: $("#eff").value }); $("#note").value = ""; await load(); }
  catch (e) { banner(e.message); } finally { busy(btn, false); }
};
$("#approveBtn").onclick = () => decide("approve");
$("#rejectBtn").onclick = () => decide("reject");
$("#cancelBtn").onclick = () => $("#review").close();
$("#eff").value = new Date().toISOString().slice(0, 10);
load();
