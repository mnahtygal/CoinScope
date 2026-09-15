#!/usr/bin/env python3
"""Export a portable CoinScope collection snapshot without changing the database."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "coinscope.db"
DEFAULT_OUT = ROOT / "data" / "exports"
FACE_VALUES = {"1c": 0.01, "5c": 0.05, "10c": 0.10, "25c": 0.25, "50c": 0.50, "1 Dollar": 1.00, "Silver Dollar": 1.00}


def money(value: float) -> str:
    return f"${value:,.2f}"


def analysis_for(row: dict) -> dict:
    try:
        return json.loads(row.get("analysis_json") or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Export CoinScope collection CSV + readable summary")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="CoinScope SQLite database")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Export directory")
    args = parser.parse_args()

    if not args.db.is_file():
        parser.error(f"database not found: {args.db}")

    args.out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    csv_path = args.out / f"coinscope-collection-{stamp}.csv"
    summary_path = args.out / f"coinscope-summary-{stamp}.md"

    connection = sqlite3.connect(args.db)
    connection.row_factory = sqlite3.Row
    rows = [dict(row) for row in connection.execute("SELECT * FROM scans WHERE status='saved' ORDER BY id")]
    connection.close()

    export_rows = []
    denomination_counts = Counter()
    grade_counts = Counter()
    storage_counts = Counter()
    low_total = high_total = 0.0

    for row in rows:
        analysis = analysis_for(row)
        matched = bool(analysis.get("matched"))
        low = float(analysis.get("value_low", FACE_VALUES.get(row.get("denomination"), 0.0))) if matched else FACE_VALUES.get(row.get("denomination"), 0.0)
        high = float(analysis.get("value_high", low)) if matched else low
        low_total += low
        high_total += high
        denomination_counts[row.get("denomination") or "Unidentified"] += 1
        grade_counts[row.get("grade") or "Unknown"] += 1
        storage_counts[row.get("storage_status") or "unassigned"] += 1
        export_rows.append({
            "id": row.get("id"),
            "created_at": row.get("created_at"),
            "country": row.get("country"),
            "denomination": row.get("denomination"),
            "year": row.get("year"),
            "mint_mark": row.get("mint_mark"),
            "series": row.get("coin_series"),
            "variant": row.get("coin_variant"),
            "grade": row.get("grade"),
            "grade_confidence": row.get("grade_confidence"),
            "storage_status": row.get("storage_status"),
            "tube_number": row.get("tube_number"),
            "tube_position": row.get("tube_position"),
            "hold_reason": row.get("hold_reason"),
            "value_low": f"{low:.2f}",
            "value_high": f"{high:.2f}",
            "collector_priced": "yes" if matched else "no",
            "notes": row.get("notes"),
            "obverse": row.get("obverse"),
            "reverse": row.get("reverse"),
        })

    fields = list(export_rows[0]) if export_rows else [
        "id", "created_at", "country", "denomination", "year", "mint_mark", "series", "variant",
        "grade", "grade_confidence", "storage_status", "tube_number", "tube_position", "hold_reason",
        "value_low", "value_high", "collector_priced", "notes", "obverse", "reverse"
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(export_rows)

    lines = [
        "# CoinScope Collection Snapshot",
        "",
        f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %I:%M %p %Z')}",
        f"Saved coins: **{len(rows)}**",
        f"Estimated collection range: **{money(low_total)}–{money(high_total)}**",
        f"Tubed: **{storage_counts['tube']}**  |  Held aside: **{storage_counts['hold']}**  |  Unassigned: **{storage_counts['unassigned']}**",
        "",
        "## By denomination",
        "",
    ]
    lines.extend(f"- {name}: {count}" for name, count in sorted(denomination_counts.items()))
    lines.extend(["", "## By grade", ""])
    lines.extend(f"- {name}: {count}" for name, count in sorted(grade_counts.items()))
    held = [r for r in export_rows if r["storage_status"] == "hold"]
    lines.extend(["", "## Hold tray", ""])
    if held:
        for row in sorted(held, key=lambda r: float(r["value_high"]), reverse=True):
            mint = f"-{row['mint_mark']}" if row["mint_mark"] else ""
            lines.append(f"- #{row['id']} — {row['year']}{mint} {row['denomination']} {row['grade']} — up to {money(float(row['value_high']))}: {row['hold_reason'] or 'collector inspection'}")
    else:
        lines.append("- Nothing currently held aside.")
    lines.extend(["", "## Files", "", f"- CSV: `{csv_path.name}`", f"- Summary: `{summary_path.name}`", ""])
    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Exported {len(rows)} saved coins")
    print(f"CSV:     {csv_path}")
    print(f"Summary: {summary_path}")
    print(f"Value:   {money(low_total)}–{money(high_total)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
