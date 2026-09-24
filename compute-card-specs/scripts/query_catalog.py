# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Card Catalog Query Tool

Filter the card catalog by vendor/model keyword and/or fields.

Usage:
    python query_catalog.py --vendor 华为
    python query_catalog.py --keyword 910 --fields model,fp16_dense_pflops,bw_tbps
    python query_catalog.py --status announced
"""

import argparse
import json
import sys
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "assets" / "card_catalog.json"


def parse_args():
    parser = argparse.ArgumentParser(description="Query card catalog")
    parser.add_argument("--vendor", default=None, help="Filter by vendor substring")
    parser.add_argument("--keyword", default=None, help="Filter by model substring")
    parser.add_argument("--status", default=None, choices=["official", "announced", "rumor"])
    parser.add_argument("--fields", default=None, help="Comma-separated fields to show (default: all)")
    return parser.parse_args()


def main():
    args = parse_args()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    cards = catalog["cards"]

    if args.vendor:
        cards = [c for c in cards if args.vendor.lower() in c.get("vendor", "").lower()]
    if args.keyword:
        cards = [c for c in cards if args.keyword.lower() in c.get("model", "").lower()
                 or args.keyword.lower() in c.get("id", "").lower()]
    if args.status:
        cards = [c for c in cards if c.get("status") == args.status]

    fields = [f.strip() for f in args.fields.split(",")] if args.fields else None
    out = []
    for c in cards:
        out.append({k: c.get(k) for k in (fields or c.keys())})
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n{len(out)} card(s) matched", file=sys.stderr)


if __name__ == "__main__":
    main()
