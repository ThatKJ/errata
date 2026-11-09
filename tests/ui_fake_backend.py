"""UI end-to-end harness with a FAKE Hindsight backend (no Cloud calls). Proves the browser flow and persistence only.
NOT evidence of Hindsight behaviour; screenshots from this mode must never be published as real.
Run: ERRATA_DB=/tmp/x.db PORT=8790 uv run python tests/ui_fake_backend.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["HINDSIGHT_API_KEY"] = ""          # force server to start unconfigured, then inject the fake
from tests.test_core import FakeHindsight
from errata_app import core, server
from errata_app.seed_data import FACTS, QUESTIONS

fake = FakeHindsight(verdicts={"Bharat": {"status": "affected", "false_sentence": "Seeded answer.", "reason": "FAKE verdict: India region now exists",
                                          "corrected_answer": "FAKE draft: data can stay in Mumbai (ap-south-1)."}})
server.APP = core.Errata(fake, server.store, server.BANK, FACTS, QUESTIONS)
server.main()
