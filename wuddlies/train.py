#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/train.py the training rig
-The last of the training rigs taught a newborn weight the world's names before the kettle finished boiling, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

Builds training examples from the cooked corpus and raises the librarian.
The weight studies the alphabetic scripts; rows in CJK, kana, or hangul
are counted and deferred to their own future floor rather than given a
bad seat (those naming systems are semantic character choice, not
phonotactic sequence). Nothing is dropped silently.

The example-weight composition, in order, as of the fifth schooling:

**Base:** count**0.5, the Zipf-gentling damp.

**Per-group gem ceilings:** origin-tagged rows are capped at their own
language family's top permille, untagged rows at their region's (regions
under 200 rows borrow the global ceiling), so no family's mega-names set
the bar for anyone else's rare tail.

**Region damping:** 1/sqrt of region mass, small countries keep a voice.

**Family factor:** origin-tagged rows are rebalanced across language
families (1/sqrt of family mass, normalised to mean one over tagged rows)
so no linguistic sphere dominates through many countries; untagged rows
ride on region damping alone, honestly.

**Gender boost:** given rows get a mild inverse-prior lift (exponent 0.4)
so underrepresented genders keep gradient voice; the kitchen's
inference-table repair does the data-side half of the same job.

**Richness allocation:** a mild 1 + 0.15*log1p(unique names) per region,
because a region holding eight thousand forms needs more study time than
one holding fifty.

The rig keeps its lab notebook: two percent of rows held out by row,
validation each 500 steps into data/train_curve.tsv, a patience gate that
stops a lingering run at its own knee, and best-seen weights saved rather
than merely last ones.
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

# Codepoint blocks deferred from the current weights (see module docstring).
_DEFERRED_BLOCKS = (
    (0x1100, 0x11FF), (0x2E80, 0x9FFF), (0x3130, 0x318F),
    (0x31F0, 0x31FF), (0xAC00, 0xD7AF), (0xF900, 0xFAFF),
    (0x20000, 0x3FFFF),
)

GROUP_CEILING_PERMILLE = 99.5
REGION_CEILING_MIN_ROWS = 200
GENDER_BOOST_EXP = 0.4
RICHNESS_BOOST = 0.15


def script_ok(name: str) -> bool:
    for ch in name:
        cp = ord(ch)
        for lo, hi in _DEFERRED_BLOCKS:
            if lo <= cp <= hi:
                return False
    return True


def _rows_to_examples(rows, weights, char_idx, region_idx, origin_idx, k):
    type_idx = {t: i for i, t in enumerate(TYPES)}
    gender_idx = {g: i for i, g in enumerate(GENDERS)}
    X, reg, typ, gen, ori, y, w = [], [], [], [], [], [], []
    for (name, ntype, region, gender, count, origin), ew in zip(rows, weights):
        ri = region_idx[region]
        ti, gi = type_idx[ntype], gender_idx[gender]
        oi = origin_idx.get(origin, 0)
        ctx = [BOS] * k
        for ch in name:
            X.append(list(ctx)); reg.append(ri); typ.append(ti); gen.append(gi)
            ori.append(oi); y.append(char_idx[ch]); w.append(ew)
            ctx = ctx[1:] + [char_idx[ch]]
        X.append(list(ctx)); reg.append(ri); typ.append(ti); gen.append(gi)
        ori.append(oi); y.append(EOS); w.append(ew)
    return (np.asarray(X, np.int32), np.asarray(reg, np.int16),
            np.asarray(typ, np.int8), np.asarray(gen, np.int8),
            np.asarray(ori, np.int16), np.asarray(y, np.int32),
            np.asarray(w, np.float64))


def build_examples(rows, k: int, min_char_rows: int = 5, val_frac: float = 0.02,
                   split_seed: int = 1234):
    """Vocabularies, the five-stage weight composition, and train/validation
    example arrays split by ROW so no name leaks between the halves."""
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
    origins = [""] + sorted({r[5] for r in kept if r[5]})
    char_idx = {c: CHAR_BASE + i for i, c in enumerate(chars)}
    region_idx = {r: i for i, r in enumerate(regions)}
    origin_idx = {o: i for i, o in enumerate(origins)}

    reg_of = np.asarray([region_idx[r[2]] for r in kept])
    ori_of = np.asarray([origin_idx.get(r[5], 0) for r in kept])
    gen_of = np.asarray([GENDERS.index(r[3]) for r in kept])
    is_given = np.asarray([r[1] == "given" for r in kept])

    # Stage 1: the Zipf-gentling base.
    row_w = np.asarray([float(r[4]) for r in kept]) ** 0.5

    # Stage 2: per-group gem ceilings (family for tagged, region for untagged,
    # global fallback for thin regions).
    global_ceiling = float(np.percentile(row_w, GROUP_CEILING_PERMILLE))
    ceiling = np.full(len(kept), global_ceiling)
    for oi in range(1, len(origins)):
        mask = ori_of == oi
        if mask.sum() >= 20:
            ceiling[mask] = np.percentile(row_w[mask], GROUP_CEILING_PERMILLE)
    untagged = ori_of == 0
    for ri in range(len(regions)):
        mask = untagged & (reg_of == ri)
        if mask.sum() >= REGION_CEILING_MIN_ROWS:
            ceiling[mask] = np.percentile(row_w[mask], GROUP_CEILING_PERMILLE)
    gem_clipped = int((row_w > ceiling).sum())
    row_w = np.minimum(row_w, ceiling)

    # Stage 3: region damping.
    region_tot = np.bincount(reg_of, weights=row_w, minlength=len(regions))
    region_damp = 1.0 / np.sqrt(region_tot + 1e-9)
    w = row_w * region_damp[reg_of]

    # Stage 4: the family factor, tagged rows only, normalised to mean one.
    family_tot = np.bincount(ori_of, weights=w, minlength=len(origins))
    family_damp = 1.0 / np.sqrt(family_tot + 1e-9)
    tagged = ~untagged
    if tagged.any():
        mean_fd = float((w[tagged] * family_damp[ori_of[tagged]]).sum()
                        / max(w[tagged].sum(), 1e-9))
        factor = family_damp / max(mean_fd, 1e-9)
        w[tagged] *= factor[ori_of[tagged]]

    # Stage 5: gender boost on givens, then richness allocation.
    gender_mass = np.bincount(gen_of[is_given], weights=w[is_given],
                              minlength=len(GENDERS))
    gender_share = gender_mass / max(gender_mass.sum(), 1e-9)
    g_boost = 1.0 / (gender_share + 0.05) ** GENDER_BOOST_EXP
    g_boost /= max(float((w[is_given] * g_boost[gen_of[is_given]]).sum()
                         / max(w[is_given].sum(), 1e-9)), 1e-9)
    w[is_given] *= g_boost[gen_of[is_given]]

    rich_sets: dict[str, set] = {}
    for name, ntype, region, gender, count, origin in kept:
        rich_sets.setdefault(region, set()).add(name)
    region_richness = [len(rich_sets.get(r, ())) for r in regions]
    w *= 1.0 + RICHNESS_BOOST * np.log1p(np.asarray(region_richness)[reg_of])

    split_rng = np.random.default_rng(split_seed)
    val_mask = split_rng.random(len(kept)) < val_frac
    train_rows = [r for r, m in zip(kept, val_mask) if not m]
    val_rows = [r for r, m in zip(kept, val_mask) if m]
    train_arrays = _rows_to_examples(train_rows, w[~val_mask], char_idx,
                                     region_idx, origin_idx, k)
    val_arrays = _rows_to_examples(val_rows, w[val_mask], char_idx,
                                   region_idx, origin_idx, k)

    gender_prior = gender_mass.tolist()
    region_weights = (region_tot ** 0.5).tolist()

    fam_mass = np.bincount(ori_of, weights=w, minlength=len(origins))
    fam_share = fam_mass / max(fam_mass.sum(), 1e-9)
    top_fams = sorted(((origins[i] or "(untagged)", round(100 * s, 1))
                       for i, s in enumerate(fam_share)),
                      key=lambda t: -t[1])[:8]

    stats = {"rows_kept": len(kept), "rows_deferred_script": deferred,
             "rows_dropped_rare_glyphs": len(rows) - deferred - len(kept),
             "rows_train": len(train_rows), "rows_val": len(val_rows),
             "examples_train": len(train_arrays[5]),
             "examples_val": len(val_arrays[5]),
             "vocab_chars": len(chars), "regions": len(regions),
             "origins": len(origins), "gem_clipped_rows": gem_clipped,
             "effective_mass_top": top_fams}
    return (train_arrays, val_arrays, chars, regions, origins, region_weights,
            region_richness, gender_prior, stats)


def train(steps: int = 60000, batch: int = 384, seed: int = 7,
          k: int = 6, dim_char: int = 32, hidden: int = 384,
          patience: int = 12, eval_every: int = 500,
          weight_path: Path | str | None = None,
          curve_path: Path | str | None = None,
          progress=print) -> WuddlyModel:
    """Raise a librarian. With patience > 0 the run self-stops after that many
    evals without a new best validation loss, and reports its own knee."""
    weight_path = Path(weight_path or WEIGHT_PATH)
    curve_path = Path(curve_path or CURVE_PATH)
    rows = load_corpus()
    (train_arr, val_arr, chars, regions, origins, region_weights,
     region_richness, gender_prior, stats) = build_examples(rows, k=k)
    X, reg, typ, gen, ori, y, w = train_arr
    vX, vreg, vtyp, vgen, vori, vy, _ = val_arr
    progress(f"[rig] corpus: {stats}")

    rng = np.random.default_rng(seed)
    model = WuddlyModel(chars, regions, region_weights, gender_prior, rng=rng,
                        k=k, dim_char=dim_char, hidden=hidden,
                        region_richness=region_richness, origins=origins)
    progress(f"[rig] model: vocab={model.vocab} regions={len(regions)} "
             f"origins={len(origins)} K={k} char={dim_char} hidden={hidden} "
             f"params={model.n_params():,}")

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
            loss = model.loss_and_step(X[idx], reg[idx], typ[idx], gen[idx],
                                       ori[idx], y[idx], lr)
            running = loss if running is None else 0.99 * running + 0.01 * loss
            step += 1
        val = model.eval_loss(vX, vreg, vtyp, vgen, vori, vy)
        elapsed = time.perf_counter() - t0
        curve.append((step, f"{running:.4f}", f"{val:.4f}", f"{elapsed:.0f}"))
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
