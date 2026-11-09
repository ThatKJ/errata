# LinkedIn post — DRAFT (do not post until the repo URL and article URL are real)

## Post body (paste between the lines)
---
Your answer library keeps the next answer fresh.
Nobody tracks which customers were told the old one.

I built Errata to find them, with Hindsight agent memory:

- Draft answers with reflect and store based_on. Provenance comes free: it cited 32/32 true dependencies in my test set.
- Version fact IDs and invalidate old memories; never upsert evidence.
- New questions after 4 fact changes: Hindsight 8/8 correct, plain RAG 4/8.
- Hard part: deciding whether an answer is really wrong. A verdict must quote the false sentence or it goes to human review.

Synthetic data, small n. Code: https://github.com/ThatKJ/errata

#AIAgents #AgentMemory #Hindsight #LLM
---

## First comment (after the article is published)
Full write-up: [ARTICLE_URL]

## Second comment
Hindsight, the memory layer I used: https://github.com/vectorize-io/hindsight

## Checks (run `python3 content/check_content.py`)
- Under 800 characters, including spaces and hashtags.
- No links or hashtags in the first two lines.
- Hashtags only on the last line. No banned words.
- The repo link must be the real public URL. Update it if the repo name differs.
