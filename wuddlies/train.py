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

Since v2 the rig also keeps a lab notebook: two percent of rows are held
out untouched, validation loss lands in data/train_curve.tsv every eval,
and a patience gate stops a lingering run at the knee of its own curve,
which is the honest, measured answer to "how long until the redundant
return paradigm". The best-seen weights are what get saved, never merely
the last ones.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from wuddlies.corpus import load_corpus
from wuddlies.model import (BOS, CHAR_BASE, EOS, GENDERS, TYPES,
                            WuddlyModel, save_model)

WEIGHT_PATH = Path(__file__).parent / "data" / "wuddly.safetensors"
CURVE_PATH = Path(__file__).parent / "data" / "train_curve.tsv"

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


def _rows_to_examples(rows, char_idx, region_idx, k, damp):
    type_idx = {t: i for i, t in enumerate(TYPES)}
    gender_idx = {g: i for i, g in enumerate(GENDERS)}
    X, reg, typ, gen, y, w = [], [], [], [], [], []
    for name, ntype, region, gender, count in rows:
        ri, ti, gi = region_idx[region], type_idx[ntype], gender_idx[gender]
        ew = (float(count) ** 0.5) * damp[ri]
        ctx = [BOS] * k
        for ch in name:
            X.append(list(ctx)); reg.append(ri); typ.append(ti); gen.append(gi)
            y.append(char_idx[ch]); w.append(ew)
            ctx = ctx[1:] + [char_idx[ch]]
        X.append(list(ctx)); reg.append(ri); typ.append(ti); gen.append(gi)
        y.append(EOS); w.append(ew)
    arrays = (np.asarray(X, np.int32), np.asarray(reg, np.int16),
              np.asarray(typ, np.int8), np.asarray(gen, np.int8),
              np.asarray(y, np.int32), np.asarray(w, np.float64))
    return arrays


def build_examples(rows, k: int, min_char_rows: int = 5, val_frac: float = 0.02,
                   split_seed: int = 1234):
    """Vocabulary, damping, and train/validation example arrays, split by ROW
    so no name leaks between the halves."""
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

    row_w = np.asarray([float(r[4]) for r in kept]) ** 0.5
    region_tot = np.zeros(len(regions))
    for (name, ntype, region, gender, count), w in zip(kept, row_w):
        region_tot[region_idx[region]] += w
    damp = 1.0 / np.sqrt(region_tot + 1e-9)

    split_rng = np.random.default_rng(split_seed)
    val_mask = split_rng.random(len(kept)) < val_frac
    train_rows = [r for r, m in zip(kept, val_mask) if not m]
    val_rows = [r for r, m in zip(kept, val_mask) if m]

    train_arrays = _rows_to_examples(train_rows, char_idx, region_idx, k, damp)
    val_arrays = _rows_to_examples(val_rows, char_idx, region_idx, k, damp)

    gender_prior = [0.0, 0.0, 0.0]
    gender_idx = {g: i for i, g in enumerate(GENDERS)}
    for (name, ntype, region, gender, count), rw in zip(kept, row_w):
        if ntype == "given":
            gender_prior[gender_idx[gender]] += rw * damp[region_idx[region]]
    region_weights = (region_tot ** 0.5).tolist()

    stats = {"rows_kept": len(kept), "rows_deferred_script": deferred,
             "rows_dropped_rare_glyphs": len(rows) - deferred - len(kept),
             "rows_train": len(train_rows), "rows_val": len(val_rows),
             "examples_train": len(train_arrays[4]),
             "examples_val": len(val_arrays[4]),
             "vocab_chars": len(chars), "regions": len(regions)}
    return train_arrays, val_arrays, chars, regions, region_weights, gender_prior, stats


def train(steps: int = 24000, batch: int = 384, seed: int = 7,
          k: int = 4, dim_char: int = 24, hidden: int = 224,
          patience: int = 0, eval_every: int = 500,
          weight_path: Path | str | None = None,
          curve_path: Path | str | None = None,
          progress=print) -> WuddlyModel:
    """Raise a librarian. With patience > 0 the run self-stops after that many
    evals without a new best validation loss, and reports its own knee."""
    weight_path = Path(weight_path or WEIGHT_PATH)
    curve_path = Path(curve_path or CURVE_PATH)
    rows = load_corpus()
    (train_arr, val_arr, chars, regions, region_weights, gender_prior, stats) = \
        build_examples(rows, k=k)
    X, reg, typ, gen, y, w = train_arr
    vX, vreg, vtyp, vgen, vy, _ = val_arr
    progress(f"[rig] corpus: {stats}")

    rng = np.random.default_rng(seed)
    model = WuddlyModel(chars, regions, region_weights, gender_prior, rng=rng,
                        k=k, dim_char=dim_char, hidden=hidden)
    progress(f"[rig] model: vocab={model.vocab} regions={len(regions)} "
             f"K={k} char={dim_char} hidden={hidden} params={model.n_params():,}")

    p = w / w.sum()
    t0 = time.perf_counter()
    running = None
    best_val, best_step, best_params, stale = float("inf"), 0, None, 0
    curve = [("step", "train_loss", "val_loss", "elapsed_s")]

    step = 0
    while step < steps:
        chunk = min(eval_every, steps - step)
        order = rng.choice(len(y), size=chunk * batch, p=p)
        for i in range(chunk):
            frac = step / max(steps, 1)
            lr = 1.5e-3 if frac < 0.6 else (7.5e-4 if frac < 0.85 else 3.75e-4)
            idx = order[i * batch:(i + 1) * batch]
            loss = model.loss_and_step(X[idx], reg[idx], typ[idx], gen[idx], y[idx], lr)
            running = loss if running is None else 0.99 * running + 0.01 * loss
            step += 1
        val = model.eval_loss(vX, vreg, vtyp, vgen, vy)
        elapsed = time.perf_counter() - t0
        curve.append((step, f"{running:.4f}", f"{val:.4f}", f"{elapsed:.0f}"))
        marker = ""
        if val < best_val - 1e-4:
            best_val, best_step, stale = val, step, 0
            best_params = {kk: t.copy() for kk, t in model.p.items()}
            marker = "  <- best"
        else:
            stale += 1
            marker = f"  (stale {stale}{'/' + str(patience) if patience else ''})"
        progress(f"[rig] step {step:6d}/{steps}  train {running:.4f}  "
                 f"val {val:.4f}  ({elapsed:.0f}s){marker}")
        if patience and stale >= patience:
            progress(f"[rig] KNEE: no validation gain for {patience} evals; "
                     f"best was step {best_step} (val {best_val:.4f}). "
                     f"The redundant-return paradigm began "
                     f"~{best_step} steps in ({best_step / 6000:.1f} kettle-units).")
            break

    if best_params is not None:
        model.p = best_params
    curve_path.write_text("\n".join("\t".join(str(c) for c in row) for row in curve)
                          + "\n", encoding="utf-8")
    save_model(model, weight_path, extra_meta={
        "trained_steps": step, "best_step": best_step,
        "best_val_loss": f"{best_val:.4f}", "seed": seed,
        **{f"corpus_{kk}": v for kk, v in stats.items()},
    })
    progress(f"[rig] saved {weight_path.name} ({weight_path.stat().st_size:,} bytes), "
             f"best-of-run weights from step {best_step}; curve -> {curve_path.name}")
    return model
