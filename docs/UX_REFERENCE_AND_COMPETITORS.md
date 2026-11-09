# UX references and competitor comparison

_Bounded scout, 2026-11-10 (IST). Public pages only; nothing behind a login was inspected; no code, assets or layouts were copied. Status labels: **CONFIRMED** (read on the page), **INFERRED** (from snippets or third parties), **UNVERIFIED** (could not be read)._ The full first-pass table with 15 products and repos is in [`../results/spike/competitor-check.md`](../results/spike/competitor-check.md) (2026-11-09); this file records what was re-checked and what Errata took from it.

## 1. Competitors: do they re-check answers already sent?

| Product | Persona and core flow | What was read (access 2026-11-10) | Overlap with Errata | Sweep of *sent* answers after a fact change? | UX patterns worth learning from | Effort to copy for them |
|---|---|---|---|---|---|---|
| **Conveyor (ConveyorAI)** | Security/GRC team answering questionnaires in portals, Slack, Trust Center | `docs.conveyor.com/docs/introducing-conveyorai`, `…/troubleshooting-inaccurate-answers`, `…/configuring-answer-sources` (all fetched). CONFIRMED: "learns from your edits so answers get better over time"; corrected answers "saved … as Past Answers for future questionnaires"; fixing a source applies "for all new answers right away"; a **History tab** compares "the original ConveyorAI answer with the final output" with "green updates and red deletions" | Past-answer memory, per-answer edit history, source toggles | **NOT FOUND.** Every statement is about *new* answers and *future* questionnaires | Per-answer history diff with coloured additions/deletions; explicit source toggles | Low. They already store past answers with cited sources; a backward join is a feature away |
| **Inventive AI** | RFP/security teams; drafts cited answers from approved content | `inventive.ai` (fetched). CONFIRMED: "every answer it drafts links back to the source document"; "AI detects conflicting, outdated, and stale answers"; "Never Submit an RFP With Outdated Company Information" | Citations per answer, stale detection in the library | **NOT FOUND.** Stale detection is framed at drafting and content-maintenance time ("before it ships again" on their IT/security page, 2026-11-09) | Citation list per answer with document name, page and section | Low to medium |
| **Loopio** | Proposal and RFP teams with a curated library | `loopio.com/blog/loopio-content-library/` (fetched): CONFIRMED Freshness Score 0–100, Content Review Cycles, "audit-ready update histories", Library Reporting. `support.loopio.com/…/360023922353` returned **403**: usage *count* per entry is INFERRED from search snippets | Review cycles, freshness, entry history | **NOT FOUND.** Usage is exposed as a count; no documented "projects that used entry X" lookup | Freshness as a first-class, visible score; owners and review deadlines | Medium (needs per-project usage links) |
| **Responsive (RFPIO)** | Same persona, large libraries | Help center not readable anonymously. INFERRED from vendor blog and reviews: "Used Count", Advanced Search for content "not used in the last year", 90-day review cycles | Used-count, review cycles | **UNVERIFIED / NOT FOUND** | "Answer Library Used / Edited" indicators on project answers | Unknown |
| **Unsay** (prior winner, medication safety) | Pharmacist; FDA recall retroactively corrects reassurances already given | GitHub README and schema (2026-11-09) | **The same mechanism**: versioned facts, per-answer read-set, retroactive sweep, drafted correction, outbox | **YES**, in another domain | Decision → fact-version provenance; corrections queued, never auto-sent | n/a, idea precedent, credited in README and article |

**Conclusion (unchanged from the first pass):** no product checked documents a sweep of answers *already sent to a named customer* when a fact changes. The data to do it exists in Conveyor and Inventive, so this is a missing workflow, not a moat. Errata does not claim to be first; it credits Unsay for the mechanism and claims the application to sent B2B commitments with memory-derived provenance.

## 2. Interaction patterns adopted (two, as budgeted) and deferred

1. **Per-answer history as a timeline with before/after** (Conveyor's History tab, GitLab/Harness split diff). Implemented as the **evidence time machine**: fact v1 → answer sent → change effective (old version invalidated, new version retained, both read live from Hindsight) → verdict → decision, beside a sent-vs-corrected pane. The false sentence is highlighted only when the server verified it is verbatim in the sent text.
2. **Freshness as a visible, per-change tally** (Loopio's score, risk-queue dashboards). Implemented as the **blast radius strip**: one bar per change, segmented by verdict, with counts that never sum across changes and a separate "not yet checked" segment while a job runs.

Deferred to roadmap: library import from Loopio/Responsive exports, per-customer region context, owners and review deadlines per fact, customer-facing disclosure drafts.

## 3. Visual references and the design decisions

Pinterest itself was not browsed (no scraping). Search surfaced these accessible references instead; each was looked at for a principle, not copied:

| Reference (accessed 2026-11-10) | Principle taken | Deliberately not copied |
|---|---|---|
| Dribbble "Activity Log" collection, https://dribbble.com/nof9010/collections/6685830-Activity-Log | Dated vertical timeline with a thin rule; the event, not decoration, carries the colour | Card-per-event layouts, avatars, illustrative icons |
| Netguru fintech "Audit trail" shot (Dribbble, via search) | Drawer/side-panel for the selected change; monospace only for identifiers | Dark glass panels, gradients |
| SaaSUI "Activity Feed & Audit Log UI patterns" https://www.saasui.design/blog/saas-activity-feed-audit-log-ux-patterns | Group by day, filters above a dense list, side panel for detail | Infinite feed with reactions |
| GitLab side-by-side diff issue https://gitlab.com/gitlab-org/gitlab/-/issues/231339 and Harness diff viewer component https://harness-design.netlify.app/components/markdown-display/diff-viewer | Split before/after panes; highlight the changed span inline | Code-review chrome, line numbers |
| Onshape audit dashboards (information architecture) https://cad.onshape.com/help/Content/Plans/audit_reports.htm | Overview → per-document trail → detail | Enterprise admin table styling |

**Chosen aesthetic:** calm, evidence-first. Paper `#f5f5f2` page, white surfaces, graphite ink `#1b1f24`, one action colour (teal `#0e6b6b`), status colours only for status (red correction, amber review, green accurate, teal approved) and always paired with words. One sans family (system stack, Inter if installed) for the interface and one serif stack (Charter / Iowan / Georgia) reserved for **verbatim customer-facing text**, so "what we told them" reads as a document, not as UI chrome. 8 px spacing scale, 6/10/14 px radii by hierarchy, a single soft elevation on the focus card, 160 ms transitions, reduced-motion respected. Avoided on purpose: all-caps eyebrow labels, middle-dot meta strings, arrows in buttons, identical cards for everything, gradient "AI dashboard" washes.

**What the screen must answer in five seconds** and where: *What changed?* the headline is the announcement, with the old fact struck through beside the new one. *Which promises may be wrong?* the blast radius bar and the rows, ordered by severity, each quoting the sentence now false. *What is the evidence?* the row's provenance line and the time machine. *What next?* one button per row, primary only where a correction awaits review.

## 4. Honest limits of this scout
- Loopio's and Responsive's help centers could not be read anonymously; "not found" there rests on snippets and reviews.
- Marketing pages describe capabilities, not absence. "Not found in the pages read" is not proof a feature does not exist.
- No logged-in product UI was inspected, so competitor UX patterns come from public docs and screenshots.
