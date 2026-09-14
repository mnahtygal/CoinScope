#!/usr/bin/env python3
import json
from pathlib import Path

catalog=json.loads((Path(__file__).parents[1]/"catalog"/"us_noncent.json").read_text())
rules=catalog["rules"]
assert set(r["denomination"] for r in rules)=={"5c","10c","25c","50c","1 Dollar"}
assert len(rules)==40
assert len(catalog["alerts"])>=30
assert sum(1 for a in catalog["alerts"] if a.get("prices"))>=5
assert any(r["series"]=="Buffalo Nickel" for r in rules)
assert any(r["series"]=="Mercury Dime" for r in rules)
assert any(r["series"]=="Washington State Quarter" for r in rules)
assert any(r["series"]=="Kennedy Half Dollar, Clad" for r in rules)
assert any(r["series"]=="Morgan Dollar" for r in rules)
assert any(r["series"]=="Peace Dollar" for r in rules)
for r in rules:
    assert 1850 <= r["year_start"] <= 2026 and 1850 <= r["year_end"] <= 2026
    assert r["year_start"] <= r["year_end"]
    assert set(r["prices"])=={"G","F","VF","XF","AU","MS"}
    for low,high in r["prices"].values(): assert 0 <= low <= high
print(f"PASS: {len(rules)} non-cent series rules and {len(catalog['alerts'])} major alerts")
