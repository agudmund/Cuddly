#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/frontier.py the weathering frontier-finder
-The last of the frontier finders asked how far a world may erode before its families stop recognising each other, and came back with a number instead of a guess, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

The instrument that answers "how weathered should the world be" with a
measurement instead of a gut feeling.

**The objective is the founder's, stated in one sentence:** the highest
variability rate that still leaves long chains mostly dominant. Everything
here is arithmetic under that criterion. The instrument never picks the
number alone: it reports the whole curve and marks the frontier at several
dominance thresholds, so the taste call (how dominant is "mostly") stays a
human one while the arithmetic stops being a guess.

**What it measures.** For each candidate wear rate it pours deep lineages
(every other mutation source switched OFF, so wear is the only variable in
the room: the Kalman rule applied to our own instrument) and then reads
the surviving population:

- **forms**: how many distinct spellings of the founding name still exist
  in the final generation. This is the variability half.
- **top2**: the share of that generation carried by the two commonest
  forms. This is the chain-dominance half, and the constraint.
- **root**: the share still carrying the founding form verbatim.
- **drift**: mean edit distance from the founding form, normalised by its
  length: a continuous coherence reading that does not need exact matches.
- **half**: top2 measured at half depth, so a dominance that is holding
  can be told apart from one that is collapsing.

Every figure is averaged across seeds AND families, because one lineage is
an anecdote. The Thingaling experiment (eleven forms at generation ten,
with Thingaling and Thingalin still dominating the streets) is the shape
this is looking for.
"""

from __future__ import annotations

import contextlib
import functools
import io
from collections import Counter

import numpy as np

from wuddlies.cascade import pour_world
from wuddlies.model import WuddlyModel

print = functools.partial(print, flush=True)

DEFAULT_RATES = (0.0, 0.02, 0.05, 0.08, 0.12, 0.18, 0.25, 0.35, 0.50)
DOMINANCE_THRESHOLDS = (0.80, 0.70, 0.60, 0.50)


def _levenshtein(a: str, b: str) -> int:
    """Plain edit distance, pure stdlib: the coherence ruler."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _collect(fam: dict) -> tuple[str, dict[int, list[str]]]:
    """The founding token, and every soul's carried token by generation."""
    root = fam["token"]
    by_gen: dict[int, list[str]] = {}

    def walk(soul):
        by_gen.setdefault(soul["gen"], []).append(soul.get("token") or root)
        for kid in soul["children"]:
            walk(kid)

    for s in fam["souls"]:
        walk(s)
    return root, by_gen


def _read_family(fam: dict, generations: int) -> dict | None:
    """One lineage's five readings, or None if it carries no inherited name."""
    root, by_gen = _collect(fam)
    leaves = by_gen.get(generations)
    if not leaves:
        return None
    counts = Counter(leaves)
    top2 = sum(c for _f, c in counts.most_common(2)) / len(leaves)
    half_gen = max(1, generations // 2)
    half = by_gen.get(half_gen, leaves)
    half_counts = Counter(half)
    return {
        "forms": len(counts),
        "top2": top2,
        "root": counts.get(root, 0) / len(leaves),
        "drift": float(np.mean([_levenshtein(t, root) / max(len(root), 1)
                                for t in leaves])),
        "half": sum(c for _f, c in half_counts.most_common(2)) / len(half),
        "souls": len(leaves),
    }


def measure_rate(model: WuddlyModel, rate: float, seeds: int, region: str,
                 generations: int, children: int, families: int,
                 temperature: float) -> dict:
    """Pour every seed at one wear rate and average the readings."""
    rows = []
    for seed in range(1, seeds + 1):
        with contextlib.redirect_stderr(io.StringIO()):
            census = pour_world(
                model, seed, settlements=1, families=families,
                souls=children + 1, world="archive", region=region,
                # Everything but wear is switched off: one variable in the room.
                drift_rate=0.0, gen_drift_rate=0.0, promotions_on=False,
                generations=generations, children_max=children,
                temperature=temperature, wear_rate=rate, max_souls=500000)
        for fam in census["settlements"][0]["families"]:
            reading = _read_family(fam, generations)
            if reading:
                rows.append(reading)
    if not rows:
        return {"rate": rate, "lineages": 0}
    out = {"rate": rate, "lineages": len(rows)}
    for key in ("forms", "top2", "root", "drift", "half", "souls"):
        out[key] = float(np.mean([r[key] for r in rows]))
    return out


def find_frontier(model: WuddlyModel, rates=DEFAULT_RATES, seeds: int = 5,
                  region: str = "GH", generations: int = 10,
                  children: int = 2, families: int = 3,
                  temperature: float = 0.9, progress=print) -> list[dict]:
    """Sweep the rates, report the curve, and mark the frontier at each
    dominance threshold. Returns the rows so a caller can do its own maths."""
    progress(f"[frontier] sweeping {len(rates)} wear rates x {seeds} seeds "
             f"x {families} lineages, {generations} generations deep in {region}")
    results = []
    for rate in rates:
        row = measure_rate(model, rate, seeds, region, generations, children,
                           families, temperature)
        results.append(row)
        if row["lineages"]:
            progress(f"[frontier]   wear {rate:4.2f}  forms {row['forms']:5.1f}  "
                     f"top2 {row['top2']:.3f}  root {row['root']:.3f}  "
                     f"drift {row['drift']:.3f}  half {row['half']:.3f}  "
                     f"({row['souls']:.0f} souls/lineage)")

    progress("")
    progress("[frontier] the frontier, by how dominant you want the long chains:")
    picks = {}
    for threshold in DOMINANCE_THRESHOLDS:
        ok = [r for r in results if r.get("lineages") and r["top2"] >= threshold]
        if not ok:
            progress(f"[frontier]   top-2 >= {threshold:.0%}  ->  no rate qualifies")
            continue
        best = max(ok, key=lambda r: r["rate"])
        picks[threshold] = best
        progress(f"[frontier]   top-2 >= {threshold:.0%}  ->  wear {best['rate']:.2f}"
                 f"   ({best['forms']:.1f} surviving forms, "
                 f"drift {best['drift']:.2f}, root {best['root']:.0%})")
    progress("")
    progress("[frontier] the curve is the answer; the threshold is the taste call.")
    return results
