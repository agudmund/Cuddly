#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/train.py the training rig
-The last of the training rigs taught a newborn weight the world's names before the kettle finished boiling, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

Builds training examples from the cooked corpus and raises the librarian.
The v1 weight studies the alphabetic scripts; rows written in CJK, kana,
or hangul are counted and deferred to their own future floor rather than
given a bad seat at this one (those naming systems are semantic character
choice, not phonotactic sequence, and deserve machinery that respects
that). Nothing is dropped silently: the rig reports exactly what it kept
and what it deferred.

Example weighting carries the Zipf realism with a gentle hand: each row
weighs count**0.5 (so common names stay common without drowning the rare),
and regions are damped by the square root of their total weight (so small
countries keep a real voice next to giants).
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from wuddlies.corpus import load_corpus
from wuddlies.model import (BOS, CHAR_BASE, EOS, GENDERS, K, TYPES,
                            WuddlyModel, save_model)

WEIGHT_PATH = Path(__file__).parent / "data" / "wuddly.safetensors"

# Codepoint blocks deferred from the v1 weight (see module docstring).
_DEFERRED_BLOCKS = (
    (0x1100, 0x11FF), (0x2E80, 0x9FFF), (0x3130, 0x318F),
    (0x31F0, 0x31FF), (0xAC00, 0xD7AF), (0xF900, 0xFAFF),
    (0x20000, 0x3FFFF),
)


def script_ok(name: str) -> bool:
    for ch in name:
        cp = ord(ch)
        for lo, hi in _DEFERRED_BLOCKS:
            if lo <= cp <= hi:
                return False
    return True


def build_examples(rows, min_char_rows: int = 5):
    """Turn corpus rows into (X, reg, typ, gen, y, p) training arrays."""
    kept = [r for r in rows if script_ok(r[0])]
    deferred = len(rows) - len(kept)

    presence: dict[str, int] = {}
    for name, *_ in kept:
        for ch in set(name):
            presence[ch] = presence.get(ch, 0) + 1
    rare = {c for c, n in presence.items() if n < min_char_rows}
    if rare:
        kept = [r for r in kept if not (set(r[0]) & rare)]

    chars = sorted({c for r in kept for c in r[0]})
    regions = sorted({r[2] for r in kept})
    char_idx = {c: CHAR_BASE + i for i, c in enumerate(chars)}
    region_idx = {r: i for i, r in enumerate(regions)}
    type_idx = {t: i for i, t in enumerate(TYPES)}
    gender_idx = {g: i for i, g in enumerate(GENDERS)}

    row_w = np.asarray([float(r[4]) for r in kept]) ** 0.5
    region_tot = np.zeros(len(regions))
    for (name, ntype, region, gender, count), w in zip(kept, row_w):
        region_tot[region_idx[region]] += w
    damp = 1.0 / np.sqrt(region_tot + 1e-9)

    X, reg, typ, gen, y, w = [], [], [], [], [], []
    for (name, ntype, region, gender, count), rw in zip(kept, row_w):
        ri, ti, gi = region_idx[region], type_idx[ntype], gender_idx[gender]
        ew = rw * damp[ri]
        ctx = [BOS] * K
        for ch in name:
            X.append(list(ctx)); reg.append(ri); typ.append(ti); gen.append(gi)
            y.append(char_idx[ch]); w.append(ew)
            ctx = ctx[1:] + [char_idx[ch]]
        X.append(list(ctx)); reg.append(ri); typ.append(ti); gen.append(gi)
        y.append(EOS); w.append(ew)

    p = np.asarray(w, dtype=np.float64)
    p /= p.sum()

    # Sampler priors, damped the same way the training data is.
    gender_prior = [0.0, 0.0, 0.0]
    for (name, ntype, region, gender, count), rw in zip(kept, row_w):
        if ntype == "given":
            gender_prior[gender_idx[gender]] += rw * damp[region_idx[region]]
    region_weights = (region_tot ** 0.5).tolist()

    stats = {"rows_kept": len(kept), "rows_deferred_script": deferred,
             "rows_dropped_rare_glyphs": len(rows) - deferred - len(kept),
             "examples": len(y), "vocab_chars": len(chars), "regions": len(regions)}
    arrays = (np.asarray(X, np.int32), np.asarray(reg, np.int16),
              np.asarray(typ, np.int8), np.asarray(gen, np.int8),
              np.asarray(y, np.int32), p)
    return arrays, chars, regions, region_weights, gender_prior, stats


def train(steps: int = 6000, batch: int = 384, seed: int = 7,
          progress=print) -> WuddlyModel:
    rows = load_corpus()
    (X, reg, typ, gen, y, p), chars, regions, region_weights, gender_prior, stats = \
        build_examples(rows)
    progress(f"[rig] corpus: {stats}")

    rng = np.random.default_rng(seed)
    model = WuddlyModel(chars, regions, region_weights, gender_prior, rng=rng)
    progress(f"[rig] model: vocab={model.vocab} regions={len(regions)} "
             f"params={sum(int(np.prod(t.shape)) for t in model.p.values()):,}")

    order = rng.choice(len(y), size=steps * batch, p=p)
    t0 = time.perf_counter()
    running = None
    for step in range(steps):
        lr = 1.5e-3 if step < steps * 0.6 else (7.5e-4 if step < steps * 0.85 else 3.75e-4)
        idx = order[step * batch:(step + 1) * batch]
        loss = model.loss_and_step(X[idx], reg[idx], typ[idx], gen[idx], y[idx], lr)
        running = loss if running is None else 0.99 * running + 0.01 * loss
        if (step + 1) % 500 == 0 or step == 0:
            progress(f"[rig] step {step + 1:5d}/{steps}  loss {running:.4f}  "
                     f"({time.perf_counter() - t0:.0f}s)")

    save_model(model, WEIGHT_PATH, extra_meta={
        "trained_steps": steps, "trained_examples_seen": steps * batch,
        "seed": seed, **{f"corpus_{k}": v for k, v in stats.items()},
    })
    progress(f"[rig] saved {WEIGHT_PATH.name} "
             f"({WEIGHT_PATH.stat().st_size:,} bytes) after "
             f"{time.perf_counter() - t0:.0f}s")
    return model
