"""Errata HTTP server (stdlib only). The Hindsight API key stays server-side; the browser never sees it.
Run: uv run python -m errata_app.server   (reads .env; serves http://127.0.0.1:8765)
"""
import json, os, re, threading, traceback, urllib.request
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from . import core
from .seed_data import FACTS, QUESTIONS

ROOT = Path(__file__).resolve().parent
ENV = {**{k: v for k, v in (l.strip().split("=", 1) for l in open(ROOT.parent / ".env") if "=" in l and not l.startswith("#"))}
       } if (ROOT.parent / ".env").exists() else {}
CFG = {k: os.environ.get(k) or ENV.get(k, "") for k in ("HINDSIGHT_API_KEY", "HINDSIGHT_BASE_URL", "ERRATA_BANK", "ERRATA_DB")}
store = core.Store(CFG["ERRATA_DB"] or str(ROOT.parent / "errata.db"))
BANK = CFG["ERRATA_BANK"] or store.meta("bank") or store.meta("bank", "errata-demo-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"))
store.meta("bank", BANK)
HS_URL = CFG["HINDSIGHT_BASE_URL"] or "http://127.0.0.1:8888"  # local open-source Hindsight; key only needed for Cloud
HS = core.LiveHindsight(HS_URL, CFG["HINDSIGHT_API_KEY"] or None)
APP = core.Errata(HS, store, BANK, FACTS, QUESTIONS)
SEED = {"running": False, "done": 0, "total": len(QUESTIONS), "error": None}
BUSY = threading.Lock()  # one mutating Hindsight workflow at a time (demo-scale app)


def hindsight_up():
    try:
        return urllib.request.urlopen(HS_URL + "/health", timeout=2).status == 200
    except Exception:
        return False


def state():
    return {"configured": hindsight_up(), "hindsight": "local" if HS_URL.startswith(("http://127.0.0.1", "http://localhost")) else "remote", "bank": BANK, "seeded_at": store.meta("seeded_at"), "seed": SEED,
            "facts": store.facts(), "answers": store.answers(),
            "changes": [{**c, "impacts": store.impacts(c["id"])} for c in reversed(store.changes())],
            "events": store.events(30)}


def run_seed():
    try:
        APP.seed(progress=lambda d, t: SEED.update(done=d, total=t))
    except Exception as e:
        SEED["error"] = core.describe_error(e)
        traceback.print_exc()
    finally:
        SEED["running"] = False
        BUSY.release()


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'")
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n < 0 or n > 20000:
            raise ValueError("bad request size")
        b = json.loads(self.rfile.read(n) or b"{}")
        if not isinstance(b, dict):
            raise ValueError("JSON object expected")
        return b

    def log_message(self, fmt, *a):  # keep request bodies out of logs
        print(f"{self.command} {self.path.split('?')[0]} -> {a[1] if len(a) > 1 else ''}")

    def do_GET(self):
        p = self.path.split("?")[0]
        if (self.headers.get("Host") or "").split(":")[0] not in ("127.0.0.1", "localhost"):  # DNS-rebinding guard
            return self._send(403, {"error": "localhost only"})
        if p == "/api/state":
            return self._send(200, state())
        if p == "/favicon.ico":
            self.send_response(204); self.end_headers(); return
        f = {"/": "index.html", "/app.js": "app.js", "/app.css": "app.css"}.get(p)
        if not f:
            return self._send(404, {"error": "not found"})
        ctype = {"html": "text/html; charset=utf-8", "js": "text/javascript", "css": "text/css"}[f.rsplit(".", 1)[1]]
        self._send(200, (ROOT / "static" / f).read_bytes(), ctype)

    def do_POST(self):
        p = self.path.split("?")[0]
        # CSRF / DNS-rebinding guard: only JSON requests addressed to this local server
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in ("127.0.0.1", "localhost") or not (self.headers.get("Content-Type") or "").startswith("application/json"):
            return self._send(403, {"error": "requests must be application/json to localhost"})
        try:
            b = self._body()
            if p == "/api/seed":
                if not BUSY.acquire(blocking=False):
                    return self._send(409, {"error": "another operation is running"})
                if store.meta("seeded_at"):
                    BUSY.release()
                    return self._send(409, {"error": "already seeded"})
                SEED.update(running=True, done=0, error=None)
                threading.Thread(target=run_seed, daemon=True).start()
                return self._send(202, {"ok": True})
            if not BUSY.acquire(blocking=False):
                return self._send(409, {"error": "another operation is running"})
            try:
                if p == "/api/changes":
                    eff = b.get("effective") or datetime.now(timezone.utc).date().isoformat()
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", eff):
                        raise ValueError("effective must be YYYY-MM-DD")
                    return self._send(200, APP.propose_change(b.get("note", ""), eff))
                m = re.fullmatch(r"/api/changes/(C\d+)/apply", p)
                if m:
                    if b.get("fact_id") not in FACTS:
                        raise ValueError("unknown fact_id")
                    return self._send(200, {"impacts": APP.apply_change(m.group(1), b["fact_id"])})
                m = re.fullmatch(r"/api/changes/(C\d+)/impacts/(Q\d+)/decision", p)
                if m:
                    reviewer = (b.get("reviewer") or "").strip()[:80]
                    if not reviewer:
                        raise ValueError("reviewer name required")
                    text = b.get("text")
                    if text is not None and not isinstance(text, str):
                        raise ValueError("text must be a string")
                    return self._send(200, APP.decide(m.group(1), m.group(2), b.get("decision"), reviewer, None if text is None else text[:2000]))
                return self._send(404, {"error": "not found"})
            finally:
                BUSY.release()
        except (ValueError, json.JSONDecodeError) as e:
            self._send(400, {"error": str(e)})
        except core.Conflict as e:
            self._send(409, {"error": str(e)})
        except Exception as e:  # upstream (Hindsight) or unexpected: honest error, no fake success
            traceback.print_exc()
            self._send(502, {"error": f"Hindsight request failed — {core.describe_error(e)}"})


def main():
    port = int(os.environ.get("PORT", "8765"))
    print(f"Errata on http://127.0.0.1:{port}  bank={BANK}  hindsight={HS_URL}")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()


if __name__ == "__main__":
    main()
