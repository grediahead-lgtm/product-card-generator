import argparse
import csv
import json
import sys

from .generate import run


def _cell(v):
    s = str(v)
    return "'" + s if s.startswith(("=", "+", "-", "@")) else s


def main(argv=None):
    ap = argparse.ArgumentParser(prog="card_gen", description="Build product titles and descriptions from a CSV of attributes.")
    ap.add_argument("products", help="CSV with one product per row (any columns you use in the templates)")
    ap.add_argument("--config", required=True, help="JSON with templates, limits and required attributes")
    ap.add_argument("--out", default="cards.csv")
    args = ap.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    with open(args.products, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out, info = run(rows, cfg)
    fields = ["sku"] + [p + l for l in cfg["languages"] for p in ("title_", "desc_")] + ["issues"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in out:
            w.writerow({k: _cell(r.get(k, "")) for k in fields})
    print(json.dumps(info))
    return 0


if __name__ == "__main__":
    sys.exit(main())
