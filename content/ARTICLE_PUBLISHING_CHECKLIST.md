# Article publishing checklist (every member publishes their OWN article)

1. `python3 content/check_content.py` → all article checks PASS. The placeholder check passes only after the [PENDING] number and the repo URL are filled in.
2. Add screenshots. Each must be a real capture from the running app, with alt text:
   - `docs/screenshots/overnight-01-blast-radius.png`. Alt: "One fact change and the 12 sent answers linked to it, grouped by verdict, synthetic data".
   - `docs/screenshots/overnight-02-evidence-time-machine.png`. Alt: "Evidence timeline for one answer: fact version, sent text with the false sentence highlighted, drafted correction".
   - `docs/screenshots/overnight-03-invalidated-memory.png`. Alt: "The old fact memory shown as invalidated in Hindsight with its reason and timestamp".
   All three are real captures of the local app on the real demo bank (2026-11-10). Nothing in them is personal.
3. Platform: Dev.to or Hashnode recommended (developer audience, Markdown native). Medium or LinkedIn Articles are also allowed. Paste the Markdown and check the rendered headers, code blocks and links. Fix any broken formatting.
4. Remove the HTML comment at the top. Tags: `ai`, `llm`, `python`, `agents`.
5. Publish **publicly**. Open the URL in a logged-out private window.
6. Record the URL in `SUBMISSION_STATUS.md`. Then post the LinkedIn first comment and the Reddit link post.

Per-member note: the guide wants one article and one LinkedIn post per member, each in their own words and about what *they* did. Don't publish this draft under several names. See `content/members/` once the names are confirmed.
