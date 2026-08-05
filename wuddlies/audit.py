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

Since the fourth floor the microscope examines any world preset (archive,
population, equal) and carries the distributional metrics from Grok's
fairness pass: KL divergence between the pour and its own declared target,
region coverage, and a per-region collapse check (draws, unique share, and
top-name share) that catches a region pouring only its five most popular
names. The population reference lives in model.py beside the presets it
steers, reference-grade only. The audit reports and never tunes: what to
do about a finding is a decision, not a side effect.
"""

from __future__ import annotations

from collections import Counter

import numpy as np

from wuddlies.model import APPROX_POP_M

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
                   name_type: str = "given", world: str = "archive",
                   progress=print) -> dict:
    rng = np.random.default_rng(seed)
    n = pours * per
    region_draws = Counter()
    region_names: dict[str, Counter] = {}
    gender_draws = Counter()
    scripts = Counter()
    names = Counter()
    lengths = []

    for i in range(n):
        name, region, gender = model.sample_name(rng, name_type=name_type,
                                                 world=world,
                                                 return_details=True)
        region_draws[region] += 1
        region_names.setdefault(region, Counter())[name] += 1
        gender_draws[gender] += 1
        scripts[classify_script(name)] += 1
        names[name] += 1
        lengths.append(len(name))
        if (i + 1) % 5000 == 0:
            progress(f"[microscope] {i + 1:,}/{n:,} souls counted")

    row_share, count_share = corpus_region_shares()
    pop_total = sum(APPROX_POP_M.values())

    progress(f"\n[microscope] {n:,} {name_type} souls, seed {seed}, world={world}")
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

    # ── the distributional metrics (the Grok pass) ────────────────────────
    target = model.region_draw_weights(world)
    pour_vec = np.asarray([region_draws.get(r, 0) for r in model.regions],
                          dtype=np.float64)
    pour_p = (pour_vec + 1e-9) / (pour_vec.sum() + 1e-9 * len(model.regions))
    targ_p = (np.asarray(target) + 1e-9)
    targ_p = targ_p / targ_p.sum()
    kl = float(np.sum(pour_p * np.log(pour_p / targ_p)))
    coverage = 100 * sum(1 for r in model.regions if region_draws.get(r, 0)) \
        / max(len(model.regions), 1)
    progress(f"[microscope] KL(pour || {world}-target): {kl:.4f} nats "
             f"(0 = the pour matches its declared mix)")
    progress(f"[microscope] region coverage: {coverage:.1f}% of "
             f"{len(model.regions)} regions appear in the pour")

    progress(f"[microscope] collapse check, top drawn regions "
             f"(draws | unique% | top-name share):")
    for region, c in region_draws.most_common(12):
        rc = region_names[region]
        uniq = 100 * len(rc) / c
        top_share = 100 * rc.most_common(1)[0][1] / c
        marker = "  <- collapsing" if (c >= 100 and (uniq < 25 or top_share > 15)) else ""
        progress(f"    {region}  {c:5d} | {uniq:5.1f}% | {top_share:4.1f}%{marker}")

    progress(f"\n[microscope] top drawn regions: pour% | corpus-rows% | "
             f"corpus-census% | ~population%")
    for region, c in region_draws.most_common(20):
        pour = 100 * c / n
        rows_pct = 100 * row_share.get(region, 0.0)
        cnt_pct = 100 * count_share.get(region, 0.0)
        pop = APPROX_POP_M.get(region)
        pop_pct = f"{100 * pop / pop_total:5.2f}" if pop else "  n/a"
        progress(f"    {region}  {pour:5.2f} | {rows_pct:5.2f} | {cnt_pct:5.2f} | {pop_pct}")

    progress("\n[microscope] biggest of humanity vs their pour share:")
    flags = []
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
            "scripts": scripts, "flags": flags, "kl": kl,
            "coverage": coverage, "top_names": names.most_common(10)}
