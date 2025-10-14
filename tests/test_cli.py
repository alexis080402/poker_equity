from __future__ import annotations
import subprocess, sys

def test_cli_help_runs():
    p = subprocess.run([sys.executable, "-m", "poker_equity.cli", "--help"])
    assert p.returncode == 0
