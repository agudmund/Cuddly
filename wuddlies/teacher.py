#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/teacher.py the self-distillation tutor for the sixth era onward
-The last of the teachers poured a thousand invented cultures into lessons, then stepped aside so the weight could dream them whole, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

Neuralization by self-distillation: the symbolic engine becomes the
TEACHER, inventing cultures and pouring labelled lessons so the student
weight can learn to dream assembly as geometry rather than execute it as
code.

**Since the seventh era the lessons are LINEAGES, not single souls.** A
culture is walked down a chain of generations, and each lesson is one
handing-over: the name a parent carried, and the whole name their child
ends up with. That is the only shape in which inheritance and erosion are
visible at all, because both are relations between two generations rather
than properties of one name.

**And the whole erosion band is taught, not one rate.** Each culture draws
its own weathering level across the band the frontier-finder measured
(roughly one to twelve percent, where one percent gives reigns lasting
over a hundred generations and twelve percent gives a world with no
dominant name at all), and that level rides in the culture vector. The
weight therefore learns weathering as a continuous axis it can be asked
for, instead of a constant somebody had to guess. The founder's ruling
stands underneath it: erosion is temperature-born and receiptless on this
path, taught rather than instructed.

The culture space stays loosely structured (order, patronymic-ness,
particle texture, erosion) with noise throughout and the last dimensions
deliberately fallow, so midpoints between cultures are hybrids nobody
designed and the weight organises the rest itself.

Output: data/lessons.tsv with columns
    culture(8 comma floats) TAB region TAB handed TAB gender TAB target
where `handed` is the name being passed down (a family name in inheriting
cultures, a parent's given name in patronymic ones) and `target` is the
full name the child ends up with, worn or not.
"""

from __future__ import annotations

import functools
from pathlib import Path

import numpy as np

from wuddlies.cascade import _mint_particles, _wear_token
from wuddlies.model import GENDERS, WuddlyModel

print = functools.partial(print, flush=True)

LESSONS_PATH = Path(__file__).parent / "data" / "lessons.tsv"

CULTURE_DIMS = 8
# The band the frontier-finder measured, taught end to end.
EROSION_BAND = (0.005, 0.13)


def _invent_culture(model: WuddlyModel, rng) -> tuple[dict, np.ndarray]:
    """One synthetic culture and its point in the eight-float space."""
    region = model.regions[int(rng.integers(len(model.regions)))]
    order_ff = bool(rng.integers(2))
    patro = bool(rng.integers(2))
    erosion = float(rng.uniform(*EROSION_BAND))
    particles = None
    if patro:
        soil = model.regions[int(rng.integers(len(model.regions)))]
        particles = _mint_particles(model, rng, soil)
    culture = {"region": region, "order_ff": order_ff,
               "particles": particles, "erosion": erosion}

    vec = rng.normal(0.0, 0.12, CULTURE_DIMS)
    vec[0] += 1.0 if order_ff else -1.0
    vec[1] += 1.0 if patro else -1.0
    if particles:
        vec[2] += (sum(map(ord, particles["M"])) % 97) / 97 - 0.5
        vec[3] += (sum(map(ord, particles["F"])) % 97) / 97 - 0.5
    # The erosion axis, centred and scaled to sit in the same range as the
    # structural dimensions, so a walk along it means as much as a walk
    # along any other.
    lo, hi = EROSION_BAND
    vec[4] += 2.0 * (erosion - lo) / (hi - lo) - 1.0
    # dims 5..7 stay noise: fallow ground, the weight's to organise.
    return culture, vec.astype(np.float32)


def _assemble(culture: dict, given: str, family: str) -> str:
    return f"{family} {given}" if culture["order_ff"] else f"{given} {family}"


def _lineage(model: WuddlyModel, rng, culture: dict, chain: int):
    """Walk one lineage, yielding (handed, gender, target) per generation.

    In an inheriting culture the handed name is the family's, and it may
    weather on its way to the child: that pairing is the copy-with-mutation
    signal the whole seventh era exists to teach. In a patronymic culture
    the handed name is the parent's own given name, which is regenerated
    every generation and so has nothing to erode.
    """
    region = culture["region"]
    gp = np.asarray(model.gender_prior, dtype=np.float64)
    gp = gp / max(gp.sum(), 1e-9)

    if culture["particles"]:
        handed = model.sample_name(rng, region=region, name_type="given")
        for _ in range(chain):
            gender = GENDERS[int(rng.choice(len(GENDERS), p=gp))]
            given = model.sample_name(rng, region=region, name_type="given",
                                      gender=gender)
            suffix = culture["particles"].get(gender, culture["particles"]["M"])
            yield handed, gender, _assemble(culture, given, handed + suffix)
            handed = given
    else:
        token = model.sample_name(rng, region=region, name_type="surname")
        for _ in range(chain):
            gender = GENDERS[int(rng.choice(len(GENDERS), p=gp))]
            given = model.sample_name(rng, region=region, name_type="given",
                                      gender=gender)
            handed = token
            if rng.random() < culture["erosion"]:
                token = _wear_token(token, rng)
            yield handed, gender, _assemble(culture, given, token)


def teach(model: WuddlyModel, cultures: int = 5000, chains: int = 5,
          chain_len: int = 5, seed: int = 7, progress=print,
          lessons_per: int | None = None) -> dict:
    """Pour the curriculum. `lessons_per` is honoured for older callers by
    splitting it into chains of `chain_len`."""
    if lessons_per:
        chains = max(1, lessons_per // chain_len)
    rng = np.random.default_rng(seed)
    LESSONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    patro_n = 0
    worn = 0
    with open(LESSONS_PATH, "w", encoding="utf-8", newline="\n") as f:
        for c in range(cultures):
            culture, vec = _invent_culture(model, rng)
            patro_n += 1 if culture["particles"] else 0
            vs = ",".join(f"{x:.4f}" for x in vec)
            for _ in range(chains):
                prev_family = None
                for handed, gender, target in _lineage(model, rng, culture,
                                                       chain_len):
                    f.write(f"{vs}\t{culture['region']}\t{handed}\t"
                            f"{gender}\t{target}\n")
                    n += 1
                    if handed not in target:
                        worn += 1
            if (c + 1) % 500 == 0:
                progress(f"[teacher] {c + 1:,}/{cultures:,} cultures taught "
                         f"({n:,} lessons)")
    stats = {"cultures": cultures, "lessons": n,
             "patronymic_cultures": patro_n,
             "handings_that_changed_the_name": worn,
             "path": str(LESSONS_PATH)}
    progress(f"[teacher] curriculum complete: {n:,} lessons across "
             f"{cultures:,} cultures ({patro_n:,} patronymic); "
             f"{worn:,} handings changed the name in transit "
             f"({100 * worn / max(n, 1):.1f}%); -> {LESSONS_PATH.name}")
    return stats


def load_lessons() -> list[tuple[np.ndarray, str, str, str, str]]:
    """Read lessons back: (culture_vec, region, handed, gender, target)."""
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
