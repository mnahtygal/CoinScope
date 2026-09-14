#!/usr/bin/env python3
import json
from pathlib import Path

catalog = json.loads((Path(__file__).parents[1] / "catalog" / "us_coins.json").read_text())
records = catalog["records"]
keys = [(r["year"], r["mint_mark"], r["series"]) for r in records]

assert catalog["scope"]["from_year"] == 1850
assert catalog["scope"]["through_year"] == 2026
assert catalog["scope"]["last_circulating_issue"] == 2025
assert len(records) == 391
assert len(keys) == len(set(keys))
assert min(r["year"] for r in records) == 1850
assert max(r["year"] for r in records) == 2025
assert not any(r["year"] == 2026 for r in records)

for record in records:
    assert record["country"] == "USA" and record["denomination"] == "1c"
    assert record["mint_mark"] in {"", "P", "D", "S"}
    assert set(record["prices"]) == {"G", "F", "VF", "XF", "AU", "MS"}
    for low, high in record["prices"].values():
        assert 0 <= low <= high

lookup = {(r["year"], r["mint_mark"], r["series"]): r for r in records}
assert (1857, "", "Braided Hair Large Cent") in lookup
assert (1857, "", "Flying Eagle Cent") in lookup
assert (1909, "S", "Indian Head Cent") in lookup
assert (1909, "S", "Lincoln Cent, Wheat Reverse") in lookup
assert (1943, "", "Lincoln Cent, Wheat Reverse") in lookup
assert (2017, "P", "Lincoln Cent, Shield Reverse") in lookup
assert (2025, "D", "Lincoln Cent, Shield Reverse") in lookup
assert len(catalog["universal_error_checks"]) >= 6

print(f"PASS: {len(records)} cent issues and {sum(len(r['checks']) for r in records)} date-specific checks")
