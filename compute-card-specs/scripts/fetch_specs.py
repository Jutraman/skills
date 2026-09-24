# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Compute Card Specs Fetcher

Generate a comparison table (Markdown/CSV/JSON) from the card catalog.
Optionally emit a Web-calibration checklist for cards lacking official sources.

Usage:
    python fetch_specs.py --cards all --format md --output specs_table.md
    python fetch_specs.py --cards ascend-910b nvidia-h100-sxm --format csv
    python fetch_specs.py --cards all --format md --output specs_table.md --calibrate
"""

import argparse
import csv
import io
import json
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
CATALOG = ASSETS / "card_catalog.json"

COLUMNS = [
    ("vendor", "厂商"),
    ("model", "型号"),
    ("status", "状态"),
    ("fp16_dense_pflops", "FP16稠密(PFLOPS)"),
    ("fp16_sparse_pflops", "FP16稀疏(PFLOPS)"),
    ("fp8_pflops", "FP8(PFLOPS)"),
    ("fp4_pflops", "FP4(PFLOPS)"),
    ("int8_tops", "INT8(TOPS)"),
    ("memory_gb", "显存(GB)"),
    ("memory_type", "显存类型"),
    ("bw_tbps", "带宽(TB/s)"),
    ("interconnect", "卡间互联"),
    ("tdp_w", "功耗(W)"),
    ("process_nm", "制程(nm)"),
]

STATUS_LABEL = {"official": "已发布", "announced": "已发布未上市", "rumor": "爆料未证实"}


def parse_args():
    parser = argparse.ArgumentParser(description="Generate compute card specs table")
    parser.add_argument(
        "--cards",
        nargs="+",
        default=["all"],
        help="Card ids or 'all' (default: all)",
    )
    parser.add_argument(
        "--format", choices=["md", "csv", "json"], default="md", help="Output format"
    )
    parser.add_argument("--output", default=None, help="Output file (default: stdout)")
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Append a web-calibration checklist for cards without official sources",
    )
    return parser.parse_args()


def load_catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def select_cards(catalog: dict, ids: list[str]) -> list[dict]:
    cards = catalog["cards"]
    if "all" in ids:
        return cards
    by_id = {c["id"]: c for c in cards}
    missing = [i for i in ids if i not in by_id]
    if missing:
        print(f"[WARN] unknown card ids ignored: {missing}", file=sys.stderr)
    return [by_id[i] for i in ids if i in by_id]


def fmt(value, sparse=False):
    if value is None:
        return "—"
    text = str(value)
    return f"{text}*" if sparse else text


def render_markdown(cards: list[dict], catalog: dict) -> str:
    lines = []
    lines.append("# 国内外已发布算力卡规格对比表")
    lines.append("")
    lines.append(f"> 数据截止：{catalog['meta'].get('updated', '见目录')} · 状态口径：已发布/已发布未上市/爆料未证实 · `*`=稀疏算力 · `—`=官方未公开")
    lines.append("")
    header = "| " + " | ".join(label for _, label in COLUMNS) + " |"
    sep = "|" + "|".join("---" for _ in COLUMNS) + "|"
    lines.append(header)
    lines.append(sep)
    for c in cards:
        row = []
        for key, _ in COLUMNS:
            if key == "status":
                row.append(STATUS_LABEL.get(c.get(key), c.get(key) or "—"))
            elif key == "fp16_sparse_pflops":
                row.append(fmt(c.get(key), sparse=True))
            else:
                row.append(fmt(c.get(key)))
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("## 数据来源")
    lines.append("")
    for c in cards:
        lines.append(f"- **{c['vendor']} {c['model']}**：{'；'.join(c.get('sources', []))}")
    return "\n".join(lines) + "\n"


def render_csv(cards: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([label for _, label in COLUMNS])
    for c in cards:
        writer.writerow([c.get(key, "—") for key, _ in COLUMNS])
    return buf.getvalue()


def render_json(cards: list[dict]) -> str:
    return json.dumps(cards, ensure_ascii=False, indent=2)


def calibration_checklist(cards: list[dict]) -> str:
    lines = ["", "## Web 校准清单（无官方一手来源的卡片）", ""]
    pending = [
        c for c in cards
        if any("建议 Web 校准" in s or "公开报道" in s for s in c.get("sources", []))
    ]
    if not pending:
        lines.append("全部卡片已有官方来源，无需校准。")
        return "\n".join(lines) + "\n"
    for c in pending:
        lines.append(f"- [ ] {c['vendor']} {c['model']}：检索官方 datasheet，逐字段核对算力/显存/带宽/互联/功耗")
    lines.append("")
    lines.append("> 检索建议：`<型号> datasheet 官方` / 厂商官网产品页 / 发布会胶片；注意稠密vs稀疏、单向vs双向口径")
    return "\n".join(lines) + "\n"


def main():
    args = parse_args()
    catalog = load_catalog()
    cards = select_cards(catalog, args.cards)
    if not cards:
        print("No cards selected.", file=sys.stderr)
        sys.exit(1)

    if args.format == "md":
        content = render_markdown(cards, catalog)
    elif args.format == "csv":
        content = render_csv(cards)
    else:
        content = render_json(cards)

    if args.calibrate and args.format == "md":
        content += calibration_checklist(cards)

    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
        print(f"Saved: {args.output} ({len(cards)} cards)")
    else:
        print(content)


if __name__ == "__main__":
    main()
