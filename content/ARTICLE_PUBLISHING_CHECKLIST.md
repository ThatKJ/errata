# Article publishing checklist (every member publishes their OWN article)

1. `python3 content/check_content.py` → all article checks PASS. The placeholder check passes only after the [PENDING] number and the repo URL are filled in.
2. Add screenshots. Each must be a real capture from the running app, with alt text:
   - `docs/screenshots/01-workspace-seeded-real.png`. Alt: "Errata's sent-answers table with the facts each answer cited, synthetic data".
   - The impacts panel after the Mumbai change (capture from the local run).
   - The review dialog showing the Memory evidence (same).
3. Platform: Dev.to or Hashnode recommended (developer audience, Markdown native). Medium or LinkedIn Articles are also allowed. Paste the Markdown and check the rendered headers, code blocks and links. Fix any broken formatting.
4. Remove the HTML comment at the top. Tags: `ai`, `llm`, `python`, `agents`.
5. Publish **publicly**. Open the URL in a logged-out private window.
6. Record the URL in `SUBMISSION_STATUS.md`. Then post the LinkedIn first comment and the Reddit link post.

Per-member note: the guide wants one article and one LinkedIn post per member, each in their own words and about what *they* did. Don't publish this draft under several names. See `content/members/` once the names are confirmed.
