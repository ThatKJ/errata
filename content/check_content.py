"""Content checks: banned word, lengths, required links, placeholders. Run: python3 content/check_content.py"""
import re, sys
from pathlib import Path

D = Path(__file__).parent
BANNED = re.compile(r"hack\s*-?\s*a?thon", re.I)
ok = True


def check(name, cond, detail=""):
    global ok
    ok &= cond
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail else ""))


art = (D / "article.md").read_text()
body = re.sub(r"<!--.*?-->", "", art, flags=re.S)
title = body.strip().splitlines()[0].lstrip("# ").strip()
words = len(body.split())
check("article: no banned word", not BANNED.search(art))
check("article: 800-1500 words", 800 <= words <= 1500, f"{words} words")
check("article: title <= 10 words", len(title.split()) <= 10, title)
for link in ["https://github.com/vectorize-io/hindsight", "https://hindsight.vectorize.io/", "https://vectorize.io/what-is-agent-memory"]:
    check(f"article: links {link}", link in art)
check("article: no unresolved placeholders", not re.search(r"\[(PENDING|GITHUB_REPO_URL|ARTICLE_URL)", body), "publish blocker until resolved")

li = (D / "linkedin-post.md").read_text().split("\n---\n")[1].split("\n---")[0].strip()
lines = li.splitlines()
check("linkedin: < 800 chars", len(li) < 800, f"{len(li)} chars")
check("linkedin: no banned word", not BANNED.search(li))
check("linkedin: no links/hashtags in first 2 lines", not re.search(r"http|#", "\n".join(lines[:2])))
check("linkedin: hashtags only on last line", all("#" not in l for l in lines[:-1]) and lines[-1].startswith("#"))
check("linkedin: 3-5 hashtags", 3 <= len(re.findall(r"#\w+", lines[-1])) <= 5)
check("linkedin: repo link in body", "github.com/" in li)
check("reddit: no banned word", not BANNED.search((D / "reddit-post.md").read_text()))
sys.exit(0 if ok else 1)
