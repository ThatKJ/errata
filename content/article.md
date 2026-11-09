# The answers you already sent are the ones Hindsight remembers

<!-- DRAFT. Numbers come from real runs: docs/LOCAL_VALIDATION_REPORT.md (local) and docs/MEMORY_PROOF.md (earlier Cloud spike).
     TODO before publishing: (1) replace [GITHUB_REPO_URL] once the repo is public; (2) add screenshots from
     content/ARTICLE_PUBLISHING_CHECKLIST.md; (3) run content/check_content.py. -->

In October, a security-questionnaire answer told an Indian microfinance customer: *"Kestrel Ledger cannot host data within India, as all customer data is exclusively stored and processed in the AWS us-east-1 region in N. Virginia, USA."* That was true when it went out. On November 3 we launched a Mumbai region. The answer was still sitting in that customer's security review, now wrong, and nobody on our side knew which customers had been told the old version.

The company is fictional. Every customer, fact and answer here is synthetic data. The sentence above is a real `reflect` output, though, and it shows the question I wanted to answer: **once a fact changes, which answers you already sent are now wrong?**

## The problem nobody's tool looks at

If you answer security questionnaires and RFPs, you live inside an answer library. Loopio, Responsive and friends keep the *next* answer current. In the public docs and reviews I could reach, I found nothing that goes backwards, taking a changed fact and listing every customer who already received the old version.

That gap needs three things:

1. **Provenance at send time.** Which facts did each answer actually rely on?
2. **Facts that change without being overwritten.** The old version has to stay inspectable, and it must stop influencing new answers.
3. **A judgement per answer.** "Is our data stored in the US?" is *still true* for a US credit union after an India region launches. Depending on a changed fact is not the same as being wrong.

I built **Errata** to test whether an agent memory layer could carry those three jobs. I used [Hindsight](https://github.com/vectorize-io/hindsight), Vectorize's open-source agent memory. I started on Hindsight Cloud and finished on the open-source server running on my laptop, with embedded Postgres and `qwen3.5:9b` through Ollama. No API key, no Docker. The idea isn't new: a project called Unsay did retroactive correction for medication safety on CockroachDB. What I wanted to know was whether Hindsight's `retain`/`recall`/`reflect` primitives make it cheap to build for B2B commitments.

## How it hangs together

Errata is small: a standard-library Python HTTP server, a SQLite audit store, and the official `hindsight-client`.

```
UI → server.py → core.py ──► local Hindsight: retain · recall · reflect(based_on) · invalidate
                     │                 └─► embedded Postgres + Ollama (qwen3.5:9b)
                     └──────► SQLite: fact versions, answer versions, impacts, approvals
```

The flow has three steps for the user:

- **Post a change.** It's just the Slack message, pasted as text.
- **See affected sent answers.** Each is grouped as *needs correction*, *needs review* or *still accurate*.
- **Review and approve a drafted correction.**

Approval writes the decision back into memory. Nothing is ever sent to a customer.

## Provenance came for free (mostly)

When Errata drafts an answer, it calls `reflect` restricted to fact memories with `include_facts=True`. The response's `based_on.memories` tells me which memories the answer used. I tag every fact memory `fact:Fxx`, so mapping citations back to facts is a few lines (`errata_app/core.py`, line 53):

```python
def facts_from_based_on(based_on):
    """Fact ids a reflect answer cited, from memory tags (fact:Fxx) or versioned document ids (fact:Fxx:vN)."""
    out = []
    for m in (as_dict(based_on) or {}).get("memories") or []:
        ids = [t.split(":", 1)[1] for t in (m.get("tags") or []) if t.startswith("fact:")]
        if not ids and re.match(r"fact:F\d+:v\d+$", m.get("document_id") or ""):
            ids = [m["document_id"].split(":")[1]]
        out += [i for i in ids if i not in out]
    return out
```

That list is stored with the answer. It is the dependency record I never had to hand-label.

Is it accurate? On Hindsight Cloud I generated 30 answers over a 20-fact sheet and compared the cited facts with the facts each question actually depends on, using ground truth fixed before running anything.

- **Recall: 1.00** (32 of 32 true dependencies cited).
- **Precision: 0.78.** `based_on` over-cites, mostly through consolidated *observations* that mention neighbouring facts. Q01's answer about hosting also cited the backups fact, because the answer itself mentioned backups.

For a "who might be affected?" sweep, over-citing is the right failure direction.

## Superseding a fact without destroying the evidence

My first instinct was to re-retain the fact under the same `document_id`. Hindsight treats that as an upsert: it deletes the old document's memories and writes new ones. The memory IDs that earlier `based_on` citations pointed to would then stop resolving, and my audit trail would quietly break.

So every fact version gets its own document ID (`fact:F01:v1` → `fact:F01:v2`). The new version is retained *first*, then the old memories are invalidated with a reason rather than deleted (`core.py`, line 233):

```python
self.hs.retain(self.bank, new_text, document_id=new_doc, tags=["kind:fact", f"fact:{fid}"], ...)
listed = self.hs.list_memories(self.bank, document_id=old_doc, limit=100)
items = (listed or {}).get("items") or []
for m in items:
    self.hs.invalidate(self.bank, m["id"], f"superseded by change {cid} effective {ch['effective']}: {ch['note'][:200]}")
```

`invalidate` is a `PATCH /memories/{id}` with `state: "invalidated"`. The memory is excluded from recall but kept, with its reason, for audit.

Which fact a free-text note supersedes comes from `recall` over the fact memories. A human confirms the top suggestion before anything changes. Recall's top hit was the right fact for **4 of 4** change notes, on Cloud and again locally.

Does the old version stop leaking into new answers? In the Cloud run I asked 8 fresh questions after all four changes. Hindsight `reflect` got **8 of 8** right, including when I let it search the bank that still holds the 30 old (now wrong) sent answers. Plain BM25 over the same raw documents, with the same answer model, got **4 of 8**. A stateless model got **2 of 8**.

## Where I was wrong

I expected Hindsight to win at *finding* the affected answers. On this dataset it doesn't, at least not alone. A dumb keyword index over question text found all 12 affected answers with fewer false candidates (4 vs 7). That's partly because I wrote the keyword list knowing my own fact sheet, which a real team with 500 facts can't do as easily. Errata uses the union; candidates were never the hard part.

The hard part is the **verdict**. On the data-residency change, Errata's verifier (`reflect` with a `response_schema`) found all three truly affected answers, but also flagged four that weren't wrong, including my deliberate trap: a US credit union whose "your data stays in the US" answer is still true. In an earlier run that trap came back correctly *unaffected*. The verdict isn't deterministic.

So I made the verifier earn its "affected" (`core.py`):

```python
def grounded(verdict, sent_text):
    """'affected' only counts if the verifier quoted a sentence that is really in the sent answer."""
    quote = (verdict.get("false_sentence") or "").strip()
    if verdict.get("status") == "affected" and not (len(norm(quote).split()) >= 2 and norm(quote) in norm(sent_text)):
        return "needs_review", (f"verifier said affected but its quote was not found in the sent answer (quote: {json.dumps(quote[:200])}): "
                                + (verdict.get("reason") or "")), ""
    return verdict["status"], verdict.get("reason", ""), quote if verdict.get("status") == "affected" else ""
```

The schema now requires the exact sentence from the sent answer that became false. If the model can't point at one that really exists, the item drops to *needs review* instead of *needs correction*.

Then I re-ran everything locally: all 30 answers and all 4 changes through the real app pipeline, against 12 affected answers I had labelled in advance. The honest numbers:

- **False clears: 0 of 12.** Every truly affected answer reached a human. 6 were marked *needs correction* and 6 *needs review*, the latter because the model's quote didn't match the sent text verbatim.
- **Precision of "needs correction": 0.50.** The six "false positives" surprised me: each quotes a sent sentence that really is stale. The local model's chatty answers restated neighbouring facts, like "No other third parties process customer data, including any analytics vendors." inside a billing answer. My labels assumed answers stay on topic. That assumption was wrong, not the verifier.

A verification costs about 38 seconds on a laptop, which is fine for a batch job that runs once per change.

## Lessons I'd reuse

1. **Capture provenance when you generate.** `based_on` gave me a dependency record at zero labelling cost.
2. **Version document IDs; never upsert evidence.** Invalidate superseded memories with a reason.
3. **Measure the boring baseline first.** My keyword index embarrassed my assumptions about candidate retrieval.
4. **Make the model quote its evidence.** A verdict that must point at a sentence that actually exists is cheap to check in code.
5. **Short answers are easier to audit.** Every extra sentence you send is another claim that can go stale.
6. **Fail toward a human.** Every error path ends in *needs review*; only approval changes anything.

Everything above ran on synthetic data: 20 facts, 30 answers and 4 changes, with one local model. That's a mechanism test, not an accuracy claim. Code, dataset, ground truth and raw logs: [GITHUB_REPO_URL]. Hindsight itself is at [github.com/vectorize-io/hindsight](https://github.com/vectorize-io/hindsight), with docs at [hindsight.vectorize.io](https://hindsight.vectorize.io/). Vectorize's [agent memory explainer](https://vectorize.io/what-is-agent-memory) is a good primer.
