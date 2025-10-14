from __future__ import annotations
import json, subprocess, sys

def test_cli_json_minimal():
    p = subprocess.run(
        [sys.executable, "-m", "poker_equity.cli", "AhKh", "QdQs", "--iters", "1000", "--seed", "7", "--json"],
        capture_output=True, text=True
    )
    assert p.returncode == 0
    data = json.loads(p.stdout or p.stderr)  # au cas où l’outil imprime sur stderr
    assert "hero" in data and "villain" in data and "meta" in data
    assert "ci95" in data["hero"] and len(data["hero"]["ci95"]) == 2
