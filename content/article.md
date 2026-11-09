# The answers you already sent are the ones Hindsight remembers

<!-- DRAFT. Every number below comes from real runs logged in docs/MEMORY_PROOF.md and results/spike/.
     TODO before publishing: (1) replace the [PENDING] grounded-verifier numbers after the credit top-up re-run;
     (2) add the screenshots listed in content/ARTICLE_PUBLISHING_CHECKLIST.md; (3) run the word/term checks. -->

In October, a security-questionnaire answer told an Indian microfinance customer: *"Kestrel Ledger cannot host data within India, as all customer data is exclusively stored and processed in the AWS us-east-1 region in N. Virginia, USA."* That was true when it went out. On November 3 we launched a Mumbai region. The answer was still sitting in that customer's security review, now wrong, and nobody on our side knew which customers had been told the old version.

The company is fictional. Every customer, fact and answer in this post is synthetic data I generated. The sentence above is a real output, though. Hindsight's `reflect` wrote it from the fact sheet I gave it, and the problem it illustrates is the one I wanted to work on: **once a fact changes, which answers you already sent are now wrong?**

## The problem nobody's tool looks at

If you answer security questionnaires and RFPs, you live inside an answer library. Loopio, Responsive and friends are good at keeping the *next* answer current: they have review cycles, owners and freshness scores. In the public docs, changelogs and reviews I could reach (Loopio's help centre blocked me), I couldn't find a feature that goes backwards. None of them takes a changed fact and lists every customer who already received an answer built on the old version.

That gap needs three things:

1. **Provenance at send time.** Which facts did each answer actually rely on?
2. **Facts that change without being overwritten.** The old version has to stay inspectable, and it must stop influencing new answers.
3. **A judgement per answer.** "Is our data stored in the US?" is *still true* for a US credit union after an India region launches. Depending on a changed fact is not the same as being wrong.

I built **Errata** to test whether an agent memory layer could carry those three jobs. I used [Hindsight](https://github.com/vectorize-io/hindsight), Vectorize's open-source agent memory, through Hindsight Cloud. The idea isn't new in general. A project called Unsay did retroactive correction for medication safety on CockroachDB. What I wanted to know was whether Hindsight's `retain`/`recall`/`reflect` primitives make it cheap to build for B2B commitments.

## How it hangs together

Errata is small: a standard-library Python HTTP server, a SQLite audit store, and the official `hindsight-client`. The browser never sees the API key.

```
UI → server.py → core.py ──► Hindsight Cloud: retain · recall · reflect(based_on) · invalidate
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

Is it accurate? I generated 30 answers over a 20-fact sheet and compared the cited facts with the facts each question actually depends on. I fixed that ground truth before running anything.

- **Recall: 1.00** (32 of 32 true dependencies cited).
- **Precision: 0.78.** `based_on` over-cites, mostly through consolidated *observations* that mention neighbouring facts. Q01's answer about hosting also cited the backups fact, because the answer itself mentioned backups.

For a "who might be affected?" sweep, over-citing is the right failure direction.

## Superseding a fact without destroying the evidence

My first instinct was to re-retain the fact under the same `document_id`. Hindsight treats that as an upsert: it deletes the old document's memories and writes new ones. The memory IDs that earlier `based_on` citations pointed to would then stop resolving, and my audit trail would quietly break.

So every fact version gets its own document ID (`fact:F01:v1` → `fact:F01:v2`). The old memories are invalidated with a reason rather than deleted (`core.py`, line 223):

```python
old_doc, new_doc = f["doc_id"], next_doc_id(f["doc_id"])
listed = self.hs.list_memories(self.bank, document_id=old_doc, limit=100)
for m in (listed or {}).get("items") or []:
    self.hs.invalidate(self.bank, m["id"], f"superseded by change {cid} effective {ch['effective']}: {ch['note'][:200]}")
```

`invalidate` is a `PATCH /memories/{id}` with `state: "invalidated"`. The memory is excluded from recall but kept, with its reason, for audit. The high-level Python client doesn't wrap that endpoint, so it's the one raw HTTP call in the codebase.

Which fact a free-text note supersedes comes from `recall` over the fact memories. A human confirms the top suggestion before anything changes. In my runs, recall's top hit was the right fact for **4 of 4** change notes.

Does the old version stop leaking into new answers? I asked 8 fresh questions after all four changes. Hindsight `reflect` got **8 of 8** right, including when I let it search the bank that still holds the 30 old (now wrong) sent answers. Plain BM25 retrieval over the same raw documents, with the same local model writing the answer, got **4 of 8**, plus one answer that stated both the old and the new value. A stateless model got **2 of 8**.

## Where I was wrong

I expected Hindsight to win at *finding* the affected answers. On this dataset it doesn't, at least not alone. A dumb keyword index over question text found all 12 affected answers with fewer false candidates (4 vs 7). That's partly because I wrote the keyword list knowing my own fact sheet, which a real team with 500 facts can't do as easily. Errata uses the union of both, and the measured lesson is that candidates were never the hard part.

The hard part is the **verdict**. When I ran Errata's verifier (`reflect` with a `response_schema`) on the data-residency change, it found all three truly affected answers. It also flagged four that weren't wrong, including my deliberate trap: the US credit union whose "your data stays in the US" answer is still true. Worse, in an earlier run the same trap had come back correctly *unaffected*. The verdict isn't deterministic.

So I made the verifier earn its "affected" (`core.py`, line 78):

```python
def grounded(verdict, sent_text):
    """'affected' only counts if the verifier quoted a sentence that is really in the sent answer."""
    quote = (verdict.get("false_sentence") or "").strip()
    if verdict.get("status") == "affected" and not (quote and norm(quote) in norm(sent_text)):
        return "needs_review", "verifier said affected but did not quote a sentence that was actually sent: " + (verdict.get("reason") or ""), ""
    return verdict["status"], verdict.get("reason", ""), quote if verdict.get("status") == "affected" else ""
```

The schema now requires the exact sentence from the sent answer that became false. If the model can't point at one that really exists, the item drops to *needs review* instead of *needs correction*. [PENDING: live re-measurement of the grounded verifier on the same 20 candidates.]

One accidental test came free. Midway through a run my Cloud credits ran out, and every verification call started failing with HTTP 402. All ten failures surfaced as *needs review*, never as "unaffected". I'd unit-tested exactly that; it held under a real outage.

## Lessons I'd reuse

1. **Capture provenance when you generate, not later.** `reflect`'s `based_on` gave me a dependency record at zero labelling cost, with perfect recall on my set. Store it next to the output.
2. **Version your document IDs; never upsert evidence.** Invalidate superseded memories with a reason. Your citations stay resolvable and your history stays honest.
3. **Measure the boring baseline first.** My keyword index embarrassed my assumptions about candidate retrieval, and that told me where the real work was.
4. **Make the model quote its evidence.** A verdict that must point at a sentence that actually exists is cheap to check in code.
5. **Fail toward a human.** Every error path in Errata ends in *needs review*, and approval is the only way anything changes.

Everything above ran on synthetic data: 20 facts, 30 answers and 4 changes. That's a smoke test of a mechanism, not an accuracy claim. The code, the dataset with its ground truth, and the raw run logs are in the repo: [GITHUB_REPO_URL]. Hindsight itself is at [github.com/vectorize-io/hindsight](https://github.com/vectorize-io/hindsight), with docs at [hindsight.vectorize.io](https://hindsight.vectorize.io/). Vectorize's explainer on [what agent memory is](https://vectorize.io/what-is-agent-memory) is a good primer on why "retain, recall, reflect" is a different shape from RAG.
