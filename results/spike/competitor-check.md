# Competitor check: backward correction of already-sent answers

Date: 2026-11-09. Research only. All fetched content was treated as untrusted data.

**Definitions**
- **Forward hygiene** keeps the answer library current so that *future* answers are right. It covers review cycles, expiry and freshness, owners, conflict and stale flags, and auto-updating library entries.
- **Backward correction** starts from a changed fact. It finds every answer *already sent* to a named customer or deal that relied on the old fact, then flags it or drafts a correction.

**Access limits**
- support.loopio.com returned HTTP 403 to WebFetch, so Loopio evidence comes from search-indexed snippets of its help articles.
- The Responsive help center (support.devrev.ai/responsivedemo) rendered no article body.
- No logged-in product UIs were inspected.

## Table

| Product | Forward hygiene features (evidence) | Backward correction of sent answers? | Evidence URL + short quote | Notes |
|---|---|---|---|---|
| **Loopio** | VERIFIED (help-center snippets). Freshness Score: "Reviewing a Library Entry or using it in a Project increases the score." Review Cycles at the entry, category and library level with up to 10 reviewers. Entry Owners. Entry History audit trail. "Reviews from Projects" suggests library changes once a project entry is marked Complete. | **NOT FOUND** | https://support.loopio.com/hc/en-us/articles/360020519494-What-is-a-Freshness-Score ; https://support.loopio.com/hc/en-us/articles/360023922353-Getting-Started-Library ("shows you the number of times an Entry has been used"); https://support.loopio.com/hc/en-us/articles/4417065553171-Loopio-Dictionary ; https://support.loopio.com/hc/en-us/articles/4409006385555-Can-I-Assign-Library-Entry-Owners ; https://support.loopio.com/hc/en-us/articles/360020475693-What-are-Reviews-from-Projects | Usage is exposed as a **count**. No per-entry "used in projects" list was found. The only documented "used in" lookup is attachment → library entries. Data flows project → library (forward), never library → submitted projects. Articles were 403 to direct fetch, so this rests on snippets. |
| **Responsive (ex-RFPIO)** | UNVERIFIED or partial: "Used Count" in LookUp ("When you copy from the document, Responsive includes it in the Used Count"), Audit Answers duplicate alerts, Bulk Update, Duplicate Report, review cycles (reviews say they cannot notify ahead of the due date). | **NOT FOUND** | https://support.devrev.ai/responsivedemo/article/ART-3031-getting-started-with-responsive-lookup (search snippet); G2/TrustRadius reviews | The official help center was not readable. One Capterra reviewer says completed projects cannot be searched for Q&A pairs that are not already in the library. |
| **Conveyor** | VERIFIED (changelog). AI Librarian conflict highlighting (Oct 2025). Stale KB detection via MCP (Apr 2026). Verify KB answers via API (May 2026). Bulk edit when "one little change can break big chunks of your knowledge" (May 2026). SharePoint sync (Aug 2026). | **NOT FOUND**, with the closest building blocks of any product checked | https://conveyor.com/changelog. The questions API (May 12, 2026) returns answers with "cited sources". Trust Center subscriber notifications cover only *subprocessor changes* and *announcements* (Jul 2026). https://docs.conveyor.com/docs/past-answers | The answer-to-source citations per questionnaire plus a customer notification channel would let a customer *build* a sweep through the API, but none is shipped. Conditional-question regeneration applies only within an open questionnaire. |
| **Inventive AI** | VERIFIED (marketing page): "A certificate expiry or policy revision flags every answer that depends on it **before it ships again**". Flagged answers are routed to their owner. | **NOT FOUND**. The flag is explicitly forward ("before it ships again"). | https://www.inventive.ai/solution/it-and-security-teams. Also: "Every submitted answer records its source, approver, and date" | The same page records submitted-answer provenance, which is the data a backward sweep needs, but it does not claim a sweep. This is the closest *claim*. Only the marketing page was inspected. |
| **SafeBase (Drata) / Vanta** | UNVERIFIED: KB built from past questionnaires. Vanta says the KB updates "as policies evolve" (sponsored press release). Trust Center subscriber updates. | **NOT FOUND** | https://safebase.io/blog/ai-questionnaire-assistance ; https://www.vanta.com/resources/new-capabilities-automate-inbound-questionnaires-and-demonstrate-trust | Trust Centers push the *current* posture to subscribers. They do not track or correct individual answers already sent. |
| **Arphie** | UNVERIFIED (own G2 listing): "AI agents proactively identify outdated answers" when underlying documents change. | **NOT FOUND** | https://www.g2.com/products/arphie/discuss | Library hygiene only. |
| **AutoRFP.ai** | UNVERIFIED (third party): stale or conflicting answers are highlighted for review. | **NOT FOUND** | https://autorfp.ai/blog/autorfp-vs-1up-ai | Library hygiene only. |
| **1up** | UNVERIFIED (competitor blogs): approved answers override outdated ones; manual quarterly review is recommended. | **NOT FOUND** | https://autorfp.ai/blog/autorfp-vs-1up-ai ; https://www.inventive.ai/blog-posts/arphie-vs-1up | Library hygiene only. |
| **Procurize** (found incidentally) | Concept and how-to blog: a change-detection "Impact Matrix" maps policy clause → questionnaire ID → evidence and "automatically updates the corresponding questionnaire fields across your entire portfolio". | **UNVERIFIED** (closest conceptual match) | https://blog.procurize.ai/ai-powered-change-detection-for-auto-updating-security-quest | It is a build guide, not a shipped feature. Notifications go only to internal Slack/Teams. It does not say whether *submitted* questionnaires are covered, and nothing reaches customers. |
| **UpGuard** (incidental) | Beta "questionnaire changes view" compares two versions of a questionnaire. | NOT FOUND | https://www.upguard.com/releases/questionnaire-changes-view.md | This is buyer-side diffing, not vendor-side correction. |
| **nickbitzis/rfp-copilot** | VERIFIED (code). `retrieval.py` has `SUPERSEDE_GAP_DAYS = 180`, and "A newer policy doc that disagrees with an answer supersedes it", so stale sources are dropped *at retrieval time*. CI fails if outdated-source usage exceeds 2%. Write-back stores `provenance={"questionnaire", "job_id", "item_id", "based_on": citations}`. | **NOT FOUND** | https://github.com/nickbitzis/rfp-copilot (README, src/rfpcopilot/retrieval.py, review.py) | Jobs and items are stored with their citations in SQLite, so a backward join is possible, but no code walks past jobs when a fact changes. This is purely forward. |
| **atconeyisland/rfp-memory-agent** | VERIFIED (code). `STALE_DAYS = 21` flags computed in code. `correct()` tombstones the old item (`old.superseded_by = it.id`) so the "same question now answers with the new fact". | **NOT FOUND** | https://github.com/atconeyisland/rfp-memory-agent (rfp_agent/memory.py, tools.py) | The correction only affects the *next* answer ("visible change on re-ask"). Nothing revisits drafts already given to Acme and others. |
| **hasnain1522/RFPulse** | Records win/loss outcomes into Hindsight memory for future RFPs. | **NOT FOUND** | https://github.com/hasnain1522/RFPulse (README, backend/app/routes/api.py) | Outcome learning only. A grep for stale, supersede and correct found nothing relevant. |
| **manimounika-gubbala/MEMORA** | Pre-mortem over past bids and verified win/loss conflict detection. | **NOT FOUND** | https://github.com/manimounika-gubbala/MEMORA (README, backend/agent.py, memory.py) | Strategy memory, not fact correction. |
| **JonathanSolvesProblems/unsay** | n/a | **VERIFIED yes, but in the medication-safety domain** | https://github.com/JonathanSolvesProblems/unsay. README: "when the FDA recalls that drug… Unsay finds every person it already reassured, works out which of those answers are now wrong, and corrects them." `unsay/sweep.py`: "Retroactive invalidation: going back and repairing answers that have gone wrong." | See the section below. |

## Unsay mechanism (verified from README, `sql/002_schema.sql`, `unsay/sweep.py`)

- **Schema.** It has five parts:
  - a bitemporal `fact` table, with `valid_from`/`valid_to` and `asserted_at`/`retracted_at`
  - `decision`, which records each answer given to a named `patient`
  - `decision_read`, which records the exact `fact_version` each answer consumed, with a `load_bearing` flag
  - `sweep`, plus a `correction` table with `UNIQUE (sweep_id, decision_id)`
  - an `outbox` for exactly-once notification, written in the same transaction as the correction
- **The sweep.** It is one join, `decision → decision_read (load_bearing) → fact WHERE retracted_at IS NOT NULL AND status='standing'`. Each affected answer is then re-decided against current memory. If the verdict moves, a correction is drafted and a notification is queued for a named person.
- **Domain.** Pharmacy and FDA recalls (openFDA), with recalls scoped by lot. It was built on CockroachDB and AWS Bedrock and took 2nd place at the CockroachDB × AWS hackathon.
- **How much Errata borrows.** Errata reuses the core mechanism: versioned facts, a per-answer read-set of fact versions with load-bearing marks, a sweep join, re-decision, and draft-correction plus an outbox. Mapping fact→product claim, decision→sent RFP answer, and patient→customer/deal is a **domain port**. The answer-tracing mechanism itself is not new relative to Unsay.

## Novelty verdict

**Backward sweep of already-sent answers in the RFP / security-questionnaire domain: WEAK novelty.**

- **Product side.** None of the products or repos inspected *ships* a documented backward sweep of already-submitted answers per customer or deal. Every verified feature is forward hygiene, such as Inventive's "flags every answer that depends on it **before it ships again**" and Loopio's usage *count* and review cycles. Several products already hold the needed data:
  - Conveyor exposes per-question "cited sources" through its API and runs Trust Center subscriber notifications.
  - Inventive says it records each submitted answer's source.
  - rfp-copilot stores per-job citations.
  - Procurize publishes a concept with a policy→questionnaire "Impact Matrix".

  So the gap is a missing *workflow*, not missing *data*. An incumbent could close it quickly.
- **Mechanism side.** Unsay already demonstrates the exact pattern publicly in another domain: versioned facts, the answer→fact-version read-set, a retroactive sweep, and a drafted correction with notification.

**Precise residual differentiation (what Errata can honestly claim)**
1. It is the first application, among products checked, of the retroactive sweep to *sent B2B commitments* (RFP and security-questionnaire answers), keyed per customer and deal. Incumbents stop at "fix the library before the next send".
2. Its unit of correction is a sent answer that may carry contractual weight. That brings disclosure logic Unsay lacks: whether this customer must be told, and what was represented on which date. Bitemporal "when did we know" separates an honest error from a negligent one.
3. RFP-specific load-bearing detection. A paraphrased or blended answer must be traced to the product claims it rests on, whereas Unsay links recalls by explicit lot and product.

Errata should not claim the trace-and-repair mechanism itself is novel; credit Unsay. Not found in the docs inspected is not proof of absence.

### Sources inspected
- **Loopio:** help-center articles 360020519494, 360023922353, 4417065553171, 4409006385555, 360020475693, 360055300673, 360051561813 (via search snippets; direct fetch returned 403).
- **Responsive:** support.devrev.ai ART-3031 and ART-2857 (empty render), plus G2, Capterra and TrustRadius reviews.
- **Conveyor:** conveyor.com/changelog (full fetch) and docs.conveyor.com past-answers (snippet).
- **Others:**
  - inventive.ai/solution/it-and-security-teams (full fetch)
  - blog.procurize.ai change-detection post (full fetch)
  - SafeBase and Vanta blog and press pages (snippets)
  - Arphie, AutoRFP and 1up comparison pages (snippets)
- **GitHub repos:** for the four RFP repos and Unsay, I read the README and the GitHub tree, and grepped the core source files.
