# YouTube upload package (final demo) — PUBLISHED PUBLIC 2026-11-10: https://youtu.be/f30yLISBpfY

**File:** `docs/demo/errata-demo.mp4`. It is 1920×1080, H.264 with AAC audio, and 3:05 long. ffprobe: `width=1920 height=1080 duration=185.03`.
**Thumbnail:** `docs/demo/thumbnail.png` (1280×720).
**Visibility:** Public. **Audience:** not made for kids. **Altered or synthetic content:** answer **Yes**, because the narration is a synthesized voice. This is disclosed on screen and in the description.

What the video is: a Playwright recording of the real app on 2026-11-10, run against the local open-source Hindsight server and Ollama. One step is live: a new change note is retained and Hindsight `recall` ranks the fact. Everything else shows saved results from the earlier verified run, and each such frame is labelled "RECORDED RUN". Narration is macOS text-to-speech; the script is in `scripts/demo_video/narration.txt`. It is not the owner's voice.

## Title
When a fact changes, which sent answers are now wrong? (Hindsight memory demo)

## Description
Errata finds security-questionnaire and RFP answers that a product-fact change made wrong. It shows the memory evidence and drafts a correction for a human to approve. Nothing is sent to customers.

All data shown is synthetic (a fictional company, Kestrel Ledger). The narration is a synthesized voice (macOS text-to-speech). The change-note recall at 0:33 is live on a laptop; the blast radius, verdicts and approval are saved results from an earlier verified run and are labelled as such on screen.

How Hindsight is used:
- reflect drafts answers and records based_on citations (provenance)
- versioned fact IDs; old memories are invalidated with a reason, never deleted
- recall maps a free-text change note to the fact it supersedes
- reflect with a response schema re-checks each answer and must quote the sentence that became false

Runs fully local: open-source Hindsight server (embedded Postgres) + Ollama qwen3.5:9b. No API key.
Measured on synthetic data (30 answers, 4 changes, 12 pre-labelled stale pairs): 0/12 silently cleared in two runs, precision of "needs correction" 0.55, recall top-1 4/4, median verification 38.5 s. A mechanism test, not an accuracy claim.

Code: https://github.com/ThatKJ/errata
Article: https://dev.to/kirtan120007/the-answers-you-already-sent-are-the-ones-hindsight-remembers-3b8e
Hindsight: https://github.com/vectorize-io/hindsight
Docs: https://hindsight.vectorize.io/

Chapters
0:00 What Errata does
0:13 Sent answers (synthetic data)
0:33 Live Hindsight retain + recall
0:59 Blast radius (recorded run)
1:22 Negative control
1:36 Evidence time machine
1:55 Editable review and audit trail
2:13 Measured results and limits
2:45 Links

## Tags
agent memory, Hindsight, LLM, Ollama, provenance, Python, RAG
