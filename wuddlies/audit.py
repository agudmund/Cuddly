#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/audit.py the bias microscope
-The last of the bias microscopes counted thirty thousand souls and told the truth about who was missing, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

Pours a large, seeded population from a weight and reports where the souls
actually came from: region draw shares, output script shares, gender
shares, duplication and variety, and a three-way honesty table comparing
the pour against the corpus's own footprint and against approximate real
population. The goal it audits toward, in the founder's words: fairly
representative of all humans and free of any biases other than population.

The population reference below is APPROXIMATE (rough mid-2020s millions,
for delta-flagging only, never a data source). Regions absent from it get
no population verdict rather than a wrong one. The audit reports and never
tunes: what to do about a finding is a decision, not a side effect.
"""

from __future__ import annotations

from collections import Counter

import numpy as np

# Approximate populations in millions, mid-2020s, for the corpus's larger
# regions and any region likely to surface in a pour. Reference-grade only.
APPROX_POP_M = {
    "CN": 1425, "CD": 102, "KR": 52, "UG": 48, "TW": 23, "CI": 29,
    "CM": 29, "MG": 30,
    "IN": 1440, "US": 342, "ID": 284, "PK": 245, "NG": 229, "BR": 217,
    "BD": 174, "RU": 144, "MX": 130, "ET": 129, "JP": 123, "PH": 119,
    "EG": 116, "VN": 100, "IR": 91, "TR": 87, "DE": 84, "TH": 72,
    "GB": 68, "TZ": 68, "FR": 66, "ZA": 63, "IT": 59, "KE": 56,
    "MM": 54, "CO": 52, "SD": 49, "ES": 48, "UA": 37, "AR": 46,
    "DZ": 46, "IQ": 46, "AF": 42, "PL": 37, "CA": 39, "MA": 38,
    "SA": 33, "UZ": 35, "PE": 34, "MY": 34, "AO": 36, "MZ": 33,
    "GH": 34, "YE": 34, "NP": 31, "VE": 28, "AU": 26, "NL": 18,
    "SY": 23, "ML": 23, "BF": 23, "NE": 27, "LK": 22, "KZ": 20,
    "RO": 19, "CL": 20, "EC": 18, "GT": 18, "SN": 18, "KH": 17,
    "TD": 18, "SO": 18, "ZW": 16, "GN": 14, "RW": 14, "BJ": 14,
    "TN": 12, "BE": 12, "JO": 11, "AZ": 10, "SE": 11, "HU": 10,
    "GR": 10, "PT": 10, "CZ": 11, "IL": 10, "AT": 9, "CH": 9,
    "TG": 9, "HK": 8, "LY": 7, "PY": 7, "LA": 8, "BG": 6, "RS": 7,
    "LB": 6, "NI": 7, "KG": 7, "DK": 6, "FI": 6, "SG": 6, "NO": 6,
    "SK": 5, "PS": 5, "IE": 5, "OM": 5, "CR": 5, "NZ": 5, "HR": 4,
    "GE": 4, "UY": 3, "BA": 3, "AM": 3, "AL": 3, "MD": 3, "LT": 3,
    "MK": 2, "SI": 2, "LV": 2, "EE": 1, "CY": 1, "ME": 0.6, "LU": 0.7,
    "MT": 0.5, "IS": 0.4, "AE": 10, "KW": 4, "QA": 3, "BH": 2,
}

_SCRIPTS = (
    ("Arabic", ((0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF))),
    ("Hebrew", ((0x0590, 0x05FF),)),
    ("Cyrillic", ((0x0400, 0x04FF), (0x0500, 0x052F))),
    ("Greek", ((0x0370, 0x03FF),)),
    ("Devanagari", ((0x0900, 0x097F),)),
    ("Thai", ((0x0E00, 0x0E7F),)),
    ("Georgian", ((0x10A0, 0x10FF),)),
    ("Armenian", ((0x0530, 0x058F),)),
    ("Latin", ((0x0041, 0x024F), (0x1E00, 0x1EFF),)),
)


def classify_script(name: str) -> str:
    for ch in name:
        cp = ord(ch)
        for script, blocks in _SCRIPTS:
            for lo, hi in blocks:
                if lo <= cp <= hi:
                    return script
    return "Other"


def corpus_region_shares():
    """Row share and raw-census-count share per region, from corpus.tsv."""
    from wuddlies.corpus import load_corpus
    rows = Counter()
    counts = Counter()
    for name, ntype, region, gender, count in load_corpus():
        rows[region] += 1
        counts[region] += count
    trow = sum(rows.values())
    tcnt = sum(counts.values())
    return ({r: n / trow for r, n in rows.items()},
            {r: n / tcnt for r, n in counts.items()})


def run_bias_audit(model, pours: int = 1000, per: int = 30, seed: int = 7,
                   name_type: str = "given", progress=print) -> dict:
    rng = np.random.default_rng(seed)
    n = pours * per
    region_draws = Counter()
    gender_draws = Counter()
    scripts = Counter()
    names = Counter()
    lengths = []

    for i in range(n):
        name, region, gender = model.sample_name(rng, name_type=name_type,
                                                 return_details=True)
        region_draws[region] += 1
        gender_draws[gender] += 1
        scripts[classify_script(name)] += 1
        names[name] += 1
        lengths.append(len(name))
        if (i + 1) % 5000 == 0:
            progress(f"[microscope] {i + 1:,}/{n:,} souls counted")

    row_share, count_share = corpus_region_shares()
    pop_total = sum(APPROX_POP_M.values())

    progress(f"\n[microscope] {n:,} {name_type} souls, seed {seed}")
    progress(f"[microscope] unique names: {len(names):,} "
             f"({100 * len(names) / n:.1f}%); "
             f"length mean {np.mean(lengths):.1f}, "
             f"p95 {int(np.percentile(lengths, 95))}")
    progress("[microscope] most common souls: "
             + ", ".join(f"{nm} x{c}" for nm, c in names.most_common(10)))
    progress("[microscope] gender draws: "
             + ", ".join(f"{g}: {100 * c / n:.1f}%" for g, c in gender_draws.most_common()))
    progress("[microscope] output scripts: "
             + ", ".join(f"{s}: {100 * c / n:.2f}%" for s, c in scripts.most_common()))

    progress(f"\n[microscope] top drawn regions: pour% | corpus-rows% | "
             f"corpus-census% | ~population%")
    flags = []
    for region, c in region_draws.most_common(20):
        pour = 100 * c / n
        rows_pct = 100 * row_share.get(region, 0.0)
        cnt_pct = 100 * count_share.get(region, 0.0)
        pop = APPROX_POP_M.get(region)
        pop_pct = f"{100 * pop / pop_total:5.2f}" if pop else "  n/a"
        progress(f"    {region}  {pour:5.2f} | {rows_pct:5.2f} | {cnt_pct:5.2f} | {pop_pct}")

    progress("\n[microscope] biggest of humanity vs their pour share:")
    for region in sorted(APPROX_POP_M, key=APPROX_POP_M.get, reverse=True)[:12]:
        pop_pct = 100 * APPROX_POP_M[region] / pop_total
        pour = 100 * region_draws.get(region, 0) / n
        ratio = pour / pop_pct if pop_pct else 0.0
        verdict = ("MISSING" if pour == 0 else
                   "under" if ratio < 0.5 else
                   "over" if ratio > 2.0 else "fair")
        if verdict != "fair":
            flags.append((region, verdict, pour, pop_pct))
        progress(f"    {region}  pour {pour:5.2f}%  vs pop {pop_pct:5.2f}%  "
                 f"ratio {ratio:4.2f}  {verdict}")

    return {"n": n, "unique": len(names), "region_draws": region_draws,
            "scripts": scripts, "flags": flags, "top_names": names.most_common(10)}
