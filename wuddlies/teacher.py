#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/teacher.py the self-distillation tutor for the sixth era
-The last of the teachers poured a thousand invented cultures into lessons, then stepped aside so the weight could dream them whole, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

The sixth era's founding move: neuralization by self-distillation. The
symbolic engine built in the fifth era becomes the TEACHER: it invents
thousands of synthetic cultures (name order, patronymic particles minted
from random regional soil, inheritance habits), assigns each a point in
the eight-float culture space, and pours labeled lessons: given these
conditions and this culture's location, THIS is the whole assembled name.
The student weight then learns to dream the assembly itself: order,
suffixes, agreement: as geometry rather than code.

The culture space is structured loosely by generative factors (order on
one axis, patronymic-ness on another, particle texture on two more) with
noise throughout and the last dimensions left deliberately fallow: enough
smoothness that interpolation means something, enough freedom that the
weight organizes the rest itself. Midpoints between cultures are hybrids
nobody designed: the founder's doctrine, "a space where the weight is
given room to grow."

Wear is NOT taught and NOT logged on the neural path, by the founder's
ruling (2026-08-05): temperature does the weathering, organically,
receipt-free. The chronicle spec keeps its receipts for the worlds one
studies; this path grows free for the worlds one releases.

Output: data/lessons.tsv with columns
    culture(8 comma floats) TAB region TAB parent TAB gender TAB target
where parent is empty for founding pours and target is the FULL assembled
name the student must learn to emit whole.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from wuddlies.cascade import _mint_particles
from wuddlies.model import GENDERS, WuddlyModel

LESSONS_PATH = Path(__file__).parent / "data" / "lessons.tsv"

CULTURE_DIMS = 8


def _invent_culture(model: WuddlyModel, rng) -> tuple[dict, np.ndarray]:
    """One synthetic culture and its point in the eight-float space."""
    region = model.regions[int(rng.integers(len(model.regions)))]
    order_ff = bool(rng.integers(2))
    patro = bool(rng.integers(2))
    particles = None
    if patro:
        soil = model.regions[int(rng.integers(len(model.regions)))]
        particles = _mint_particles(model, rng, soil)
    culture = {"region": region, "order_ff": order_ff, "particles": particles}

    vec = rng.normal(0.0, 0.12, CULTURE_DIMS)
    vec[0] += 1.0 if order_ff else -1.0
    vec[1] += 1.0 if patro else -1.0
    if particles:
        vec[2] += (sum(map(ord, particles["M"])) % 97) / 97 - 0.5
        vec[3] += (sum(map(ord, particles["F"])) % 97) / 97 - 0.5
    # dims 4..7 stay noise: fallow ground, the weight's to organize.
    return culture, vec.astype(np.float32)


def _lesson(model: WuddlyModel, rng, culture: dict) -> tuple[str, str, str]:
    """One lesson: (parent, gender, target full name) in this culture."""
    region = culture["region"]
    gp = np.asarray(model.gender_prior, dtype=np.float64)
    gender = GENDERS[int(rng.choice(len(GENDERS), p=gp / gp.sum()))]
    given = model.sample_name(rng, region=region, name_type="given",
                              gender=gender)
    if culture["particles"]:
        parent = model.sample_name(rng, region=region, name_type="given")
        suffix = culture["particles"]["F" if gender == "F"
                                      else "M" if gender == "M" else "U"]
        family = parent + suffix
    else:
        parent = ""
        family = model.sample_name(rng, region=region, name_type="surname")
    target = (f"{family} {given}" if culture["order_ff"]
              else f"{given} {family}")
    return parent, gender, target


def teach(model: WuddlyModel, cultures: int = 2000, lessons_per: int = 30,
          seed: int = 6, progress=print) -> dict:
    """Pour the curriculum. The teacher works; the receipts are its own."""
    rng = np.random.default_rng(seed)
    LESSONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    patro_n = 0
    with open(LESSONS_PATH, "w", encoding="utf-8", newline="\n") as f:
        for c in range(cultures):
            culture, vec = _invent_culture(model, rng)
            patro_n += 1 if culture["particles"] else 0
            vs = ",".join(f"{x:.4f}" for x in vec)
            for _ in range(lessons_per):
                parent, gender, target = _lesson(model, rng, culture)
                f.write(f"{vs}\t{culture['region']}\t{parent}\t{gender}\t{target}\n")
                n += 1
            if (c + 1) % 400 == 0:
                progress(f"[teacher] {c + 1:,}/{cultures:,} cultures taught "
                         f"({n:,} lessons)")
    stats = {"cultures": cultures, "lessons": n,
             "patronymic_cultures": patro_n,
             "path": str(LESSONS_PATH)}
    progress(f"[teacher] curriculum complete: {n:,} lessons across "
             f"{cultures:,} cultures ({patro_n:,} patronymic); "
             f"-> {LESSONS_PATH.name}")
    return stats


def load_lessons() -> list[tuple[np.ndarray, str, str, str, str]]:
    """Read lessons back: (culture_vec, region, parent, gender, target)."""
    out = []
    with open(LESSONS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 5:
                continue
            vec = np.asarray([float(x) for x in parts[0].split(",")],
                             dtype=np.float32)
            out.append((vec, parts[1], parts[2], parts[3], parts[4]))
    return out
