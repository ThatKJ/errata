"""UI helper regression: a busy button must get its original label back however it is released."""
import shutil, subprocess
from pathlib import Path
import pytest

JS = Path(__file__).parent.parent / "errata_app/static/app.js"


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_busy_restores_label_without_label_arg():
    line = next(l for l in JS.read_text().splitlines() if l.startswith("function busy("))
    check = line + """
const b = {dataset: {}, textContent: "Find the fact it changes", disabled: false};
busy(b, true, "Asking Hindsight…"); if (b.textContent !== "Asking Hindsight…" || !b.disabled) process.exit(1);
busy(b, false); if (b.textContent !== "Find the fact it changes" || b.disabled) process.exit(2);"""
    assert subprocess.run(["node", "-e", check]).returncode == 0
