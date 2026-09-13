#!/usr/bin/env python3
"""Build CoinScope's broad U.S. cent catalog.

Values are conservative collector ranges, not appraisals.  Exact key-date
overrides take precedence over series baselines.  Regenerate after reviewing
sources or changing an attribution.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "catalog" / "us_coins.json"
TODAY = "2026-09-13"

SOURCES = {
    "large": "https://www.pcgs.com/prices/detail/braided-hair-cent/663/most-active",
    "flying": "https://www.pcgs.com/prices/detail/flying-eagle-cent/664/most-active",
    "indian": "https://www.pcgs.com/prices/detail/indian-cent/44/most-active",
    "wheat": "https://www.pcgs.com/prices/detail/lincoln-cent-wheat-reverse/46/most-active",
    "modern": "https://www.pcgs.com/prices/detail/lincoln-cent-modern/47/most-active",
    "mint_end": "https://www.usmint.gov/news/press-releases/united-states-mint-hosts-historic-ceremonial-strike-for-final-production-of-the-circulating-one-cent-coin",
}

BASE = {
    "large": {"G":[28,38],"F":[38,55],"VF":[60,90],"XF":[85,140],"AU":[175,300],"MS":[400,1800]},
    "flying": {"G":[32,45],"F":[50,75],"VF":[95,150],"XF":[140,225],"AU":[325,575],"MS":[1000,5000]},
    "indian_early": {"G":[8,18],"F":[15,30],"VF":[30,65],"XF":[55,110],"AU":[110,225],"MS":[300,1500]},
    "indian_late": {"G":[2,5],"F":[4,9],"VF":[8,18],"XF":[15,35],"AU":[35,80],"MS":[100,600]},
    "wheat_early": {"G":[0.50,2],"F":[1,4],"VF":[2,7],"XF":[4,15],"AU":[10,40],"MS":[30,300]},
    "wheat_late": {"G":[0.05,0.20],"F":[0.10,0.40],"VF":[0.15,0.75],"XF":[0.25,1.50],"AU":[0.50,4],"MS":[2,40]},
    "memorial_copper": {"G":[0.01,0.05],"F":[0.01,0.08],"VF":[0.02,0.10],"XF":[0.03,0.15],"AU":[0.05,0.35],"MS":[0.50,20]},
    "memorial_zinc": {"G":[0.01,0.03],"F":[0.01,0.05],"VF":[0.01,0.08],"XF":[0.01,0.10],"AU":[0.02,0.20],"MS":[0.25,15]},
    "shield": {"G":[0.01,0.03],"F":[0.01,0.05],"VF":[0.01,0.08],"XF":[0.01,0.10],"AU":[0.02,0.20],"MS":[0.25,12]},
    "proof": {"G":[0.50,1],"F":[0.75,1.50],"VF":[1,2],"XF":[1,3],"AU":[1,5],"MS":[2,20]},
}

# Conservative broad ranges for key regular issues. These are intended to
# prevent a common coin from receiving a rare-coin value, not replace grading.
KEY_PRICES = {
    (1856, "", "Flying Eagle Cent"): {"G":[7000,9000],"F":[10000,12000],"VF":[12000,13500],"XF":[13000,15000],"AU":[18000,23000],"MS":[30000,125000]},
    (1877, "", "Indian Head Cent"): {"G":[700,1000],"F":[1000,1500],"VF":[1600,2500],"XF":[2500,4000],"AU":[4500,7500],"MS":[9000,40000]},
    (1908, "S", "Indian Head Cent"): {"G":[60,90],"F":[85,130],"VF":[125,200],"XF":[200,350],"AU":[350,650],"MS":[700,3500]},
    (1909, "S", "Indian Head Cent"): {"G":[300,450],"F":[425,650],"VF":[650,950],"XF":[900,1400],"AU":[1400,2500],"MS":[2500,12000]},
    (1909, "S", "Lincoln Cent, Wheat Reverse"): {"G":[90,150],"F":[140,225],"VF":[220,350],"XF":[325,550],"AU":[500,900],"MS":[900,6000]},
    (1914, "D", "Lincoln Cent, Wheat Reverse"): {"G":[180,260],"F":[250,400],"VF":[400,650],"XF":[650,1100],"AU":[1100,2200],"MS":[2500,20000]},
    (1922, "D", "Lincoln Cent, Wheat Reverse"): {"G":[12,25],"F":[20,40],"VF":[35,70],"XF":[65,130],"AU":[125,300],"MS":[350,2500]},
    (1931, "S", "Lincoln Cent, Wheat Reverse"): {"G":[65,90],"F":[85,120],"VF":[110,160],"XF":[150,225],"AU":[225,400],"MS":[400,2500]},
    (1943, "", "Lincoln Cent, Wheat Reverse"): {"G":[0.05,0.25],"F":[0.20,0.50],"VF":[0.30,0.90],"XF":[0.50,1],"AU":[0.70,1.50],"MS":[1,22]},
    (1943, "D", "Lincoln Cent, Wheat Reverse"): {"G":[0.10,0.35],"F":[0.25,0.65],"VF":[0.40,1],"XF":[0.75,1.50],"AU":[1,3],"MS":[2,30]},
    (1943, "S", "Lincoln Cent, Wheat Reverse"): {"G":[0.10,0.50],"F":[0.30,0.80],"VF":[0.50,1.25],"XF":[0.75,2],"AU":[1.25,4],"MS":[3,40]},
    (1951, "D", "Lincoln Cent, Wheat Reverse"): {"G":[0.05,0.15],"F":[0.10,0.30],"VF":[0.15,0.50],"XF":[0.25,0.75],"AU":[0.50,1.50],"MS":[2,20]},
    (1958, "D", "Lincoln Cent, Wheat Reverse"): {"G":[0.03,0.10],"F":[0.05,0.25],"VF":[0.10,0.40],"XF":[0.20,0.75],"AU":[0.50,1.50],"MS":[2,25]},
}

VARIETIES = {
    (1851, "", "Braided Hair Large Cent"): [("1851/81 overdate", "Inspect the final two date digits for the recognized 1851/81 overdate.", "Recognized date variety")],
    (1855, "", "Braided Hair Large Cent"): [("Knob on Ear", "Inspect Liberty's ear for the diagnostic raised knob; other 1855 date styles also exist.", "Recognized die variety")],
    (1858, "", "Flying Eagle Cent"): [("1858/7 overdate", "Inspect beneath the final 8 for remnants of a 7; strong and weak attributions exist.", "Major overdate")],
    (1864, "", "Indian Head Cent"): [("L on Ribbon", "Inspect behind the neck for designer Longacre's L; confirm pointed bust diagnostics.", "Major subtype")],
    (1869, "", "Indian Head Cent"): [("1869/9 repunched date", "Inspect the 9 for remnants of an earlier punched digit.", "Recognized repunched date")],
    (1873, "", "Indian Head Cent"): [("Doubled LIBERTY", "Inspect LIBERTY on the headband for strong separated doubling.", "Major doubled-die variety")],
    (1888, "", "Indian Head Cent"): [("1888/7 overdate", "Inspect below and left of the final 8 for remnants of a 7; authentication is essential.", "Major overdate")],
    (1909, "S", "Lincoln Cent, Wheat Reverse"): [("S VDB", "Inspect the bottom reverse for V.D.B. initials. A genuine 1909-S VDB is a major key coin and should be authenticated.", "Major key variety")],
    (1917, "", "Lincoln Cent, Wheat Reverse"): [("Doubled die obverse", "Inspect the date and IN GOD WE TRUST for clear hub doubling.", "Major doubled die")],
    (1922, "D", "Lincoln Cent, Wheat Reverse"): [("1922 No D / Weak D", "Inspect the mintmark area and reverse diagnostics. Never call a worn or filled D the No D variety without attribution.", "Major recognized variety")],
    (1936, "", "Lincoln Cent, Wheat Reverse"): [("Doubled die obverse", "Inspect the date and motto for one of the recognized doubled-die obverses.", "Recognized doubled die")],
    (1943, "", "Lincoln Cent, Wheat Reverse"): [("Bronze planchet error", "Test with a magnet and weigh it. A genuine bronze cent should not stick and is about 3.11 g; authenticate before valuing.", "Exceptional six-figure rarity")],
    (1943, "D", "Lincoln Cent, Wheat Reverse"): [("Bronze planchet error", "A genuine bronze example should not stick to a magnet and should weigh about 3.11 g.", "Exceptional rarity")],
    (1943, "S", "Lincoln Cent, Wheat Reverse"): [("1943/2-S and DDO", "Inspect the date for a 2 beneath the 3 and inspect lettering for separated doubling.", "Major recognized varieties")],
    (1944, "", "Lincoln Cent, Wheat Reverse"): [("Steel planchet error", "Test with a magnet and weigh it. A genuine steel-planchet 1944 cent is about 2.70 g; authenticate before valuing.", "Exceptional rarity")],
    (1944, "D", "Lincoln Cent, Wheat Reverse"): [("D over S mintmark", "Inspect inside and around the D for remnants of an underlying S.", "Recognized over-mintmark")],
    (1946, "S", "Lincoln Cent, Wheat Reverse"): [("S over D mintmark", "Inspect the S for remnants of an underlying D.", "Recognized over-mintmark")],
    (1951, "D", "Lincoln Cent, Wheat Reverse"): [("D over S mintmark FS-512", "Inspect the D for traces of an underlying S; professional attribution is recommended.", "Recognized over-mintmark")],
    (1955, "", "Lincoln Cent, Wheat Reverse"): [("1955 doubled die obverse", "Inspect the date and LIBERTY for strong, obvious separated doubling. Authenticate valuable candidates.", "Famous major doubled die")],
    (1958, "", "Lincoln Cent, Wheat Reverse"): [("1958 doubled die obverse", "Inspect the motto and LIBERTY for the extremely rare doubled die. It is a Philadelphia coin with no D.", "Extreme rarity")],
    (1960, "", "Lincoln Cent, Memorial Reverse"): [("Small Date", "Compare the date shape and alignment to verified Small Date diagnostics.", "Recognized date subtype")],
    (1960, "D", "Lincoln Cent, Memorial Reverse"): [("Small Date and repunched mintmarks", "Check date subtype and inspect the D for recognized repunching.", "Multiple collectible varieties")],
    (1969, "S", "Lincoln Cent, Memorial Reverse"): [("Doubled die obverse", "Inspect the date and inscriptions for strong hub doubling; ignore flat shelf-like machine doubling.", "Major doubled die")],
    (1970, "S", "Lincoln Cent, Memorial Reverse"): [("Small Date", "Inspect the high 7 and weak LIBERTY diagnostics; compare with a verified reference.", "Recognized date subtype")],
    (1971, "S", "Lincoln Cent, Memorial Reverse"): [("Doubled die obverse", "Inspect LIBERTY and IN GOD WE TRUST for strong separated hub doubling.", "Major doubled die")],
    (1972, "", "Lincoln Cent, Memorial Reverse"): [("Doubled die obverse", "Inspect IN GOD WE TRUST, LIBERTY, and the date for strong separated doubling.", "Major doubled die")],
    (1974, "", "Lincoln Cent, Memorial Reverse"): [("Aluminum experimental cent", "A silvery 1974 cent requires expert handling and legal/provenance review; do not assume plated novelty pieces are genuine.", "Extremely rare experimental issue")],
    (1982, "D", "Lincoln Cent, Memorial Reverse"): [("Small Date copper transitional error", "Determine Large/Small Date and weigh it. A genuine 1982-D Small Date copper cent is about 3.11 g, not 2.50 g.", "Extremely rare transitional error")],
    (1983, "", "Lincoln Cent, Memorial Reverse"): [
        ("Doubled die reverse", "Inspect ONE CENT and UNITED STATES OF AMERICA for strong doubling.", "Major doubled die"),
        ("Copper transitional error", "Weigh the coin. A bronze-planchet example is about 3.11 g rather than 2.50 g; authenticate candidates.", "Rare transitional error"),
    ],
    (1984, "", "Lincoln Cent, Memorial Reverse"): [("Doubled ear", "Inspect Lincoln's ear for the distinct doubled-ear diagnostic.", "Major doubled die")],
    (1988, "", "Lincoln Cent, Memorial Reverse"): [("Reverse of 1989", "Inspect the FG designer initials and Memorial details for the transitional reverse hub.", "Recognized transitional variety")],
    (1988, "D", "Lincoln Cent, Memorial Reverse"): [("Reverse of 1989", "Inspect the FG designer initials and Memorial details for the transitional reverse hub.", "Recognized transitional variety")],
    (1990, "S", "Lincoln Cent, Memorial Reverse"): [("No S proof", "A genuine proof without an S mintmark is a major rarity. Confirm proof manufacture and obtain professional authentication.", "Major proof error")],
    (1992, "", "Lincoln Cent, Memorial Reverse"): [("Close AM", "Inspect AMERICA: the A and M should nearly touch, and confirm the designer-initial position.", "Rare reverse variety")],
    (1992, "D", "Lincoln Cent, Memorial Reverse"): [("Close AM", "Inspect AMERICA for the scarce close-spaced A and M and verify secondary diagnostics.", "Rare reverse variety")],
    (1995, "", "Lincoln Cent, Memorial Reverse"): [("Doubled die obverse", "Inspect LIBERTY and IN GOD WE TRUST for separated doubling.", "Popular doubled die")],
    (1998, "", "Lincoln Cent, Memorial Reverse"): [("Wide AM", "Inspect AMERICA for clear separation between A and M and confirm the FG position.", "Proof-style reverse variety")],
    (1999, "", "Lincoln Cent, Memorial Reverse"): [("Wide AM", "Inspect AMERICA for clear A-M separation and verify secondary reverse diagnostics.", "Scarce reverse variety")],
    (2000, "", "Lincoln Cent, Memorial Reverse"): [("Wide AM", "Inspect AMERICA for a wide A-M gap and confirm the designer initials.", "Collectible reverse variety")],
    (1998, "S", "Lincoln Cent, Memorial Reverse"): [("Close AM proof", "Inspect AMERICA for the business-style close A-M spacing and verify the FG position.", "Scarce proof reverse variety")],
    (1999, "S", "Lincoln Cent, Memorial Reverse"): [("Close AM proof", "Inspect AMERICA for the business-style close A-M spacing and verify secondary diagnostics.", "Major proof reverse variety")],
    (2009, "", "Lincoln Bicentennial Cent"): [("Doubled dies", "Inspect lettering, fingers, logs, and architectural details; multiple doubled-die reverses are attributed across the four designs.", "Multiple recognized varieties")],
    (2009, "D", "Lincoln Bicentennial Cent"): [("Doubled dies", "Inspect reverse design details for hub doubling and compare with an attributed listing.", "Multiple recognized varieties")],
    (2017, "", "Lincoln Cent, Shield Reverse"): [("First Philadelphia P mintmark", "A normal 2017 Philadelphia cent carries a P. It is a one-year historic design choice, not automatically an error.", "Historic one-year issue")],
    (2023, "", "Lincoln Cent, Shield Reverse"): [("Extra V / VDBV", "Inspect the designer initials near the bust for the recognized extra-V appearance and confirm die markers.", "Popular die variety")],
}

UNIVERSAL = [
    {"name":"Off-center strike","severity":"warning","instruction":"Look for missing design with a matching blank crescent. Value depends heavily on percent off-center and whether the date remains visible.","potential":"Premium when dramatic and attributable"},
    {"name":"Clipped planchet","severity":"warning","instruction":"Look for a curved or straight missing section with Blakesley-effect weakness opposite the clip.","potential":"Collectible mint error"},
    {"name":"Broadstrike","severity":"warning","instruction":"Look for an expanded coin struck outside the retaining collar; distinguish it from post-mint damage.","potential":"Collectible mint error"},
    {"name":"Double or multiple strike","severity":"critical","instruction":"Look for a second displaced design impression. Do not confuse with machine doubling or damage.","potential":"Potentially substantial premium"},
    {"name":"Wrong planchet / off-metal","severity":"critical","instruction":"Measure weight, diameter, color, and magnetism. Valuable candidates require professional authentication.","potential":"Potentially major rarity"},
    {"name":"Die cap or brockage","severity":"critical","instruction":"Look for a mirrored incuse design or bottle-cap shape caused during striking; authenticate before valuation.","potential":"Major mint error"},
]

def record(year, mint, series, family, composition, weight, diameter=19.0, name=None):
    prices = KEY_PRICES.get((year, mint, series), BASE[family])
    checks = []
    for title, instruction, potential in VARIETIES.get((year, mint, series), []):
        checks.append({"name":title,"severity":"critical" if "error" in title.lower() or "doubled" in title.lower() else "warning","instruction":instruction,"potential":potential})
    mint_name = {"":"Philadelphia","P":"Philadelphia","D":"Denver","S":"San Francisco"}[mint]
    suffix = f"-{mint}" if mint else ""
    return {"country":"USA","denomination":"1c","year":year,"mint_mark":mint,
            "name":name or f"{year}{suffix} {series}","series":series,"mint":mint_name,
            "composition":composition,"weight_g":weight,"diameter_mm":diameter,
            "source_url":SOURCES["modern" if family in {"memorial_copper","memorial_zinc","shield","proof"} else family.split('_')[0]],
            "price_source":"CoinScope conservative range informed by PCGS Price Guide",
            "price_updated":TODAY,"prices":prices,"checks":checks}

records=[]
for y in range(1850,1858): records.append(record(y,"","Braided Hair Large Cent","large","Copper",10.89,27.5))
for y in range(1856,1859): records.append(record(y,"","Flying Eagle Cent","flying","88% copper, 12% nickel",4.67))
for y in range(1859,1908): records.append(record(y,"","Indian Head Cent","indian_early" if y<=1878 else "indian_late","Copper-nickel" if y<=1864 else "95% copper",4.67 if y<=1864 else 3.11))
for y in (1908,1909):
    records.append(record(y,"","Indian Head Cent","indian_late","95% copper",3.11))
    records.append(record(y,"S","Indian Head Cent","indian_late","95% copper",3.11))

for y in range(1909,1959):
    mints=[""]
    if y in {1909,1910,1921,1923}: mints += ["S"]
    elif y==1922: mints=["D"]
    elif 1911<=y<=1931 or 1935<=y<=1955: mints += ["D","S"]
    elif 1932<=y<=1934 or 1956<=y<=1958: mints += ["D"]
    for mint in mints:
        family="wheat_early" if y<=1933 else "wheat_late"
        comp="Zinc-coated steel" if y==1943 else "95% copper, 5% tin and zinc"
        records.append(record(y,mint,"Lincoln Cent, Wheat Reverse",family,comp,2.70 if y==1943 else 3.11))

for y in range(1959,2009):
    if y<=1964: mints=["","D"]
    elif y<=1967: mints=[""]
    elif y<=1974: mints=["","D","S"]
    elif y==2017: mints=["P","D"]
    else: mints=["","D"]
    for mint in mints:
        family="memorial_copper" if y<1982 else "memorial_zinc"
        comp="95% copper" if y<1982 else ("Copper or copper-plated zinc varieties" if y==1982 else "Copper-plated zinc")
        records.append(record(y,mint,"Lincoln Cent, Memorial Reverse",family,comp,3.11 if y<1982 else 2.50))

# San Francisco proof cents are included because they regularly enter collections
# and CoinScope may encounter them even though they were not circulation strikes.
for y in range(1975,2009):
    records.append(record(y,"S","Lincoln Cent, Memorial Reverse","proof","Copper alloy proof" if y<1982 else "Copper-plated zinc proof",3.11 if y<1982 else 2.50,
                          name=f"{y}-S Lincoln Cent Proof"))

for mint in ("","D"): records.append(record(2009,mint,"Lincoln Bicentennial Cent","memorial_zinc","Copper-plated zinc",2.50))
records.append(record(2009,"S","Lincoln Bicentennial Cent","proof","Copper alloy proof",3.11,name="2009-S Lincoln Bicentennial Cent Proof"))
for y in range(2010,2026):
    mints=["P","D"] if y==2017 else ["","D"]
    for mint in mints: records.append(record(y,mint,"Lincoln Cent, Shield Reverse","shield","Copper-plated zinc",2.50))
    records.append(record(y,"S","Lincoln Cent, Shield Reverse","proof","Copper alloy proof",3.11,name=f"{y}-S Lincoln Shield Cent Proof"))

catalog={"schema_version":2,"updated_at":TODAY,
         "scope":{"from_year":1850,"through_year":2026,"last_circulating_issue":2025,
                  "2026_status":"No circulating cent issued; production ended November 12, 2025.","source_url":SOURCES["mint_end"]},
         "universal_error_checks":UNIVERSAL,"records":records}
OUT.write_text(json.dumps(catalog,separators=(",",":"))+"\n",encoding="utf-8")
print(f"Wrote {len(records)} regular date/mint records to {OUT}")
