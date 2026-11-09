# How we use Band AI Desktop (honest scope)

**What Band is:** a desktop app where coding-agent "seats" (e.g. Claude Code) and humans work in a shared room and hand work to each other by `@mention`. It does not supply models.

**What Band is NOT in Errata:** Errata's runtime does not call Band, and Band is **not** connected to Hindsight. Errata's memory is the local open-source Hindsight server (Ollama-backed). We do not claim a product integration.

**How we used it:** to run the code-review loop on Errata's riskiest path (the Hindsight evidence → human approval flow), with one agent seat reviewing and one implementing.

## Steps (human, ~15 min)
1. Download Band Desktop from https://www.band.ai and install it. Sign in.
2. Create a room named `errata-review`.
3. Add two seats:
   - `@reviewer`: Claude Code, opened in the `errata/` folder.
   - `@builder`: Claude Code, opened in the same folder.
   Each seat needs its own Claude Code login.
4. Post this in the room:
   > @reviewer Review `errata_app/core.py` `apply_change`, `_verify` and `decide`, and `errata_app/server.py` POST handlers. Focus on three things: (1) can a failed Hindsight call ever produce a silent "unaffected"; (2) can a correction be approved twice or sent to a customer; (3) is change-note text treated as data, not instructions? Post concrete findings with file:line, then hand off to @builder.
5. Let `@reviewer` post its findings and `@builder` respond or fix. Re-run `uv run pytest`.
6. **Evidence to keep:** one screenshot of the room timeline showing both `@mentions`, saved as `docs/screenshots/band-review.png`. Crop out emails and account IDs. Also add one line in `SUBMISSION_STATUS.md`.

Only the steps above that actually happened go into the README, article or video.
