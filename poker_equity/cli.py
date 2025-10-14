from __future__ import annotations
import argparse, json
from . import __version__
from .equity import equity_hu, equity_vs_range

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pkeq",
        description=("Calcul d'equity Texas Hold'em HU — main vs main ou main vs range (Monte Carlo)."),
    )
    p.add_argument("hero", nargs="?", help="Main Héro, ex: AhKh")
    p.add_argument("villain", nargs="?", help="Main Vilain (si pas de --villain-range)")
    p.add_argument("--villain-range", dest="villain_range", default=None,
                   help="Range Vilain, ex: 'TT+,AQs+,KQo,A5s-A2s'")
    p.add_argument("--board", dest="board", default=None, help="Board partiel, ex: AsKs2c")
    p.add_argument("--iters", dest="iters", type=int, default=200_000, help="Itérations Monte Carlo")
    p.add_argument("--seed", dest="seed", type=int, default=None, help="Graine RNG")
    p.add_argument("--json", dest="as_json", action="store_true", help="Sortie JSON")
    p.add_argument("-V", "--version", action="version", version=f"pkeq {__version__}")
    return p

def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.hero:
        parser.print_help(); return 0

    if args.villain_range:
        res = equity_vs_range(args.hero, args.villain_range, board=args.board, iters=args.iters, seed=args.seed)
    else:
        if not args.villain:
            parser.error("Spécifie soit `villain` (main), soit `--villain-range` (range).")
        res = equity_hu(args.hero, args.villain, board=args.board, iters=args.iters, seed=args.seed)

    if args.as_json:
        print(json.dumps(res, indent=2))
    else:
        m = res["meta"]; h = res["hero"]; v = res["villain"]
        if "villain_range" in m:
            print(f"HERO={m['hero']}  RANGE=\"{m['villain_range']}\"  BOARD={m['board'] or '(preflop)'}  "
                  f"N={h['n']}  SEED={m['seed']}  RANGE_SIZE={m['range_size_available']}/{m['range_size']}")
        else:
            print(f"HERO={m['hero']}  VILLAIN={m['villain']}  BOARD={m['board'] or '(preflop)'}  N={h['n']}  SEED={m['seed']}")
        print(f"→ HERO equity = {h['equity']:.3%}  (±{h['stdev']:.2%})  IC95=[{h['ci95'][0]:.3%}, {h['ci95'][1]:.3%}]")
        print(f"→ VILLAIN     = {v['equity']:.3%}  (±{v['stdev']:.2%})  IC95=[{v['ci95'][0]:.3%}, {v['ci95'][1]:.3%}]")
    return 0
