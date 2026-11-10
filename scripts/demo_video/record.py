"""Record the real Errata app (port 8766, copy of the demo DB) at 1920x1080. Logs scene start times for narration."""
import json, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

D = Path(__file__).parent
DUR = {l.split()[0]: float(l.split()[1]) for l in open(D / "durations.txt")}
APP = "http://127.0.0.1:8766/"
NOTE = "Heads up from legal: as of Nov 4 we onboarded Snowflake (US) as a new subprocessor for product usage analytics; it receives customer account metadata."
OVERLAY = """([cap, badge, live]) => {
  let o = document.getElementById('__cap');
  if (!o) {
    o = document.createElement('div'); o.id='__cap';
    Object.assign(o.style,{position:'fixed',left:'50%',bottom:'28px',transform:'translateX(-50%)',maxWidth:'1500px',padding:'14px 26px',
      background:'rgba(12,14,20,.88)',color:'#fff',font:'600 26px/1.35 -apple-system,Helvetica,Arial,sans-serif',borderRadius:'10px',zIndex:2147483647,textAlign:'center'});
    document.body.appendChild(o);
    const t = document.createElement('div'); t.id='__tag';
    Object.assign(t.style,{position:'fixed',right:'18px',top:'70px',padding:'6px 12px',background:'rgba(12,14,20,.85)',color:'#fff',
      font:'500 16px -apple-system,Helvetica,Arial,sans-serif',borderRadius:'6px',zIndex:2147483647});
    t.textContent='Narration: synthesized voice (macOS text-to-speech). Data: synthetic.'; document.body.appendChild(t);
    const b = document.createElement('div'); b.id='__badge';
    Object.assign(b.style,{position:'fixed',left:'18px',top:'70px',padding:'6px 12px',color:'#fff',font:'700 17px -apple-system,Helvetica,Arial,sans-serif',borderRadius:'6px',zIndex:2147483647});
    document.body.appendChild(b);
  }
  const host = document.querySelector('dialog[open]') || document.body;
  for (const id of ['__cap','__tag','__badge']) { const e = document.getElementById(id); if (e.parentNode !== host) host.appendChild(e); }
  o.textContent = cap; o.style.display = cap ? 'block' : 'none';
  const b = document.getElementById('__badge'); b.textContent = badge || ''; b.style.display = badge ? 'block':'none';
  b.style.background = live ? '#b42318' : '#344054';
}"""

def card(title, lines, foot=""):
    li = "".join(f"<li>{l}</li>" for l in lines)
    return f"""<html><body style="margin:0;width:1920px;height:1080px;background:#0f1218;color:#f2f4f7;font-family:-apple-system,Helvetica,Arial,sans-serif;display:flex;flex-direction:column;justify-content:center;padding:0 150px;box-sizing:border-box">
<h1 style="font-size:64px;margin:0 0 30px">{title}</h1><ul style="font-size:34px;line-height:1.5;margin:0;padding-left:36px">{li}</ul>
<p style="font-size:24px;color:#98a2b3;margin-top:40px">{foot}</p></body></html>"""

log, T0 = [], None
def scene(page, key, cap, badge="", live=False):
    page.evaluate(OVERLAY, [cap, badge, live])
    log.append({"key": key, "t": time.monotonic() - T0}); print(key, round(log[-1]["t"], 1), flush=True)
def hold(key, extra=0.8):
    end = log[[l["key"] for l in log].index(key)]["t"] + DUR[key] + extra
    while time.monotonic() - T0 < end: time.sleep(0.1)
def smooth(page, sel, dy, steps=12, pause=0.12):
    for _ in range(steps):
        page.evaluate("([s,d]) => { const e = s ? document.querySelector(s) : document.scrollingElement; e.scrollBy(0,d); }", [sel, dy]); time.sleep(pause)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, record_video_dir=str(D / "raw"), record_video_size={"width": 1920, "height": 1080}, bypass_csp=True)
    page = ctx.new_page(); T0 = time.monotonic()
    page.set_content(card("Errata", ["A product fact changed.", "Which customer answers you <b>already sent</b> are now wrong?",
        "Errata finds them with Hindsight agent memory, shows the evidence, and drafts a correction for a human."],
        "Fictional company and customers. Runs fully local: open-source Hindsight + Ollama qwen3.5:9b."))
    scene(page, "s1", "When a fact changes, find the answers already sent that are now wrong."); hold("s1")

    page.goto(APP); page.wait_for_selector("#workspace:not([hidden])")
    page.click("#tabbtn-answers"); page.locator("#answers").scroll_into_view_if_needed()
    page.evaluate("() => { const r=[...document.querySelectorAll('#answers tbody tr')].find(t=>t.textContent.includes('Q02')); r.style.outline='4px solid #f79009'; r.scrollIntoView({block:'center'}); }")
    scene(page, "s2", "30 sent answers drafted by Hindsight reflect. Each stores the facts it cited (based_on).", "SYNTHETIC DATA"); hold("s2")

    page.evaluate("() => window.scrollTo(0,0)")
    page.fill("#note", NOTE); page.fill("#eff", "2026-11-04")
    scene(page, "s3", "LIVE: the note is retained in local Hindsight, then recall ranks the fact it supersedes (real time, no cuts).", "LIVE", True)
    page.click("#proposeBtn")
    page.wait_for_selector("text=Which fact does this change?", timeout=300000)
    hold("s3", 0)
    scene(page, "s3b", "Hindsight recall ranked F03 (subprocessors) first. Not applied in this recording.", "LIVE", True); hold("s3b")

    page.click("button.change[data-sel='C1']"); page.wait_for_selector("text=Recorded run")
    scene(page, "s4", "SAVED RESULTS from an earlier verified run: change C1, Mumbai region. Fact F01 v1 invalidated, v2 valid.", "RECORDED RUN")
    time.sleep(7); smooth(page, None, 40, 10); hold("s4")

    page.fill("#q", "Midwest"); time.sleep(0.5)
    scene(page, "s5", "Negative control Q03 (US credit union): routed to human review, not cleared and not flagged wrong.", "RECORDED RUN"); hold("s5")
    page.fill("#q", ""); page.evaluate("() => window.scrollTo(0,0)")

    page.click("[data-ev='Q02']"); page.wait_for_selector("#review .timeline", timeout=60000)
    scene(page, "s6", "Evidence time machine: fact v1, answer as sent, old memory invalidated (read live from Hindsight), v2, verdict, decision.", "LIVE MEMORY READ", True)
    time.sleep(3); smooth(page, "#review .dlg-body", 70, 30, 0.35); hold("s6")
    page.evaluate("() => document.getElementById('review').close()"); page.evaluate(OVERLAY, ["", "", False])

    page.click("[data-ev='Q01']"); page.wait_for_selector("#draft", timeout=60000)
    page.evaluate("() => document.querySelector('#draft').scrollIntoView({block:'center'})")
    scene(page, "s7", "The drafted correction is editable and the reviewer is recorded. Not approved in this recording.", "REVIEW")
    page.click("#draft"); page.keyboard.press("Meta+ArrowDown"); page.keyboard.press("End"); page.keyboard.type(" [Edited by reviewer before approval.]", delay=35)
    page.fill("#reviewer", "Demo reviewer (video)"); time.sleep(4); page.evaluate("() => document.getElementById('review').close()"); page.evaluate(OVERLAY, ["", "", False])
    page.click("#tabbtn-log"); page.locator("#log").scroll_into_view_if_needed()
    page.evaluate("() => { const r=[...document.querySelectorAll('#log li')].find(l=>l.textContent.includes('decide')); if(r){r.style.outline='4px solid #f79009'; r.scrollIntoView({block:'center'});} }")
    page.evaluate(OVERLAY, ["Audit trail: Q02 correction approved earlier, not sent.", "RECORDED RUN", False]); hold("s7")

    page.set_content(card("Measured locally (synthetic, small n)", [
        "Stale answers silently cleared: <b>0 / 12</b>, in two runs",
        "Precision of <i>needs correction</i>: <b>0.55</b> (4 of 5 false alarms quoted a really stale sentence)",
        "Change note to right fact (Hindsight recall top-1): <b>4 / 4</b>",
        "Verification: median <b>38.5 s</b> per answer, laptop, qwen3.5:9b",
        "Stack: Python stdlib server, SQLite audit, hindsight-client 1.2.0, local Hindsight + Ollama"],
        "Source: docs/LOCAL_VALIDATION_REPORT.md and results/local/eval_local.json (run 2). One dataset, one model: a mechanism test, not an accuracy claim."))
    scene(page, "s8", ""); hold("s8")
    page.set_content(card("Errata", ["Code, data, raw logs: <b>github.com/ThatKJ/errata</b>",
        "Write-up: <b>dev.to/kirtan120007</b>", "Hindsight: <b>github.com/vectorize-io/hindsight</b>"], "Narration: synthesized voice. All data synthetic. Errata never contacts customers."))
    scene(page, "s9", ""); hold("s9", 2.0)
    vpath = page.video.path(); ctx.close(); b.close()
json.dump({"video": str(vpath), "scenes": log}, open(D / "timeline.json", "w"), indent=1)
print("done", vpath)
