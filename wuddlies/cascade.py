#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/cascade.py the seed cascade: worlds, settlements, families, souls
-The last of the seed cascades held a whole world in one number, and every family in it knew exactly who they were, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

The clustering floor. One world seed deterministically derives settlement
seeds, each settlement derives family seeds, each family derives its souls:
numpy's SeedSequence spawning, so the same world number reproduces the same
census forever, on any machine. Coherence emerges structurally: a family
shares its name because it shares its seed, a settlement leans on one
region because the region was drawn once at its founding.

**NAMING_PROGRAMS is the registry that matters.** A region's way of forming
full names is dispatched through an open table, never an if/else: the house
dispatcher pattern, and the doorstep of the convention-genesis floor. Two
hand-written anchor programs open it:

**default**: the family pours one surname at its founding and every member
inherits it, joined in the region's living order.

**is_patronymic**: Iceland's rule, executable. The family pours a PARENT's
given name instead of a surname, and every child carries parent + sson or
sdottir by their own gender: a fresh patronymic per soul, never an
inherited label: which is why no surname dataset on earth could pour
Iceland, and why this program is the emergence engine's first Earth
anchor. (Morphology simplified to the plain -s- joint for now; the full
genitive stems are a later refinement, noted rather than hidden.)

When the operator language arrives, these two stop being functions and
become the first two programs it can express; populations then drift,
merge, and invent their own. Today: two anchors, one registry, worlds that
hold together.
"""

from __future__ import annotations

import numpy as np

from wuddlies.model import FAMILY_FIRST_REGIONS, GENDERS, WuddlyModel


def _child_rngs(seed_seq: np.random.SeedSequence, n: int):
    return [np.random.default_rng(s) for s in seed_seq.spawn(n)]


# ── the naming programs (the registry that becomes the operator floor) ────

def program_default(model: WuddlyModel, rng, region: str, family_token: str,
                    given: str, gender: str) -> str:
    if region in FAMILY_FIRST_REGIONS:
        return f"{family_token} {given}"
    return f"{given} {family_token}"


def program_is_patronymic(model: WuddlyModel, rng, region: str,
                          family_token: str, given: str, gender: str) -> str:
    suffix = "sdóttir" if gender == "F" else "sson"
    return f"{given} {family_token}{suffix}"


def _family_token_default(model, rng, region):
    return model.sample_name(rng, region=region, name_type="surname")


def _family_token_parent_given(model, rng, region):
    return model.sample_name(rng, region=region, name_type="given")


# region -> (family-token pourer, full-name assembler). The dispatcher table:
# a new convention is a new ROW, never a new branch.
NAMING_PROGRAMS = {
    "default": (_family_token_default, program_default),
    "IS": (_family_token_parent_given, program_is_patronymic),
}


def pour_family(model: WuddlyModel, seed_seq: np.random.SeedSequence,
                region: str, souls: int) -> dict:
    """One family: its token poured once at the founding, then its souls."""
    founding_rng, *soul_rngs = _child_rngs(seed_seq, souls + 1)
    pour_token, assemble = NAMING_PROGRAMS.get(region, NAMING_PROGRAMS["default"])
    token = pour_token(model, founding_rng, region)
    members = []
    for rng in soul_rngs:
        gp = np.asarray(model.gender_prior, dtype=np.float64)
        gender = GENDERS[int(rng.choice(len(GENDERS), p=gp / gp.sum()))]
        given = model.sample_name(rng, region=region, name_type="given",
                                  gender=gender)
        members.append({"name": assemble(model, rng, region, token, given, gender),
                        "gender": gender})
    return {"token": token, "region": region, "members": members}


def pour_world(model: WuddlyModel, world_seed: int, settlements: int = 3,
               families: int = 3, souls: int = 4, world: str = "population",
               region: str | None = None) -> dict:
    """One number in, one coherent census out, identical forever."""
    root = np.random.SeedSequence(world_seed)
    settlement_seqs = root.spawn(settlements)
    out = {"seed": world_seed, "world": world, "settlements": []}
    for s_seq in settlement_seqs:
        founding, families_seq = s_seq.spawn(2)
        f_rng = np.random.default_rng(founding)
        if region is None:
            w = model.region_draw_weights(world)
            s_region = model.regions[int(f_rng.choice(len(model.regions), p=w))]
        else:
            s_region = region
        eponym = model.sample_name(f_rng, region=s_region, name_type="surname")
        fams = [pour_family(model, fs, s_region, souls)
                for fs in families_seq.spawn(families)]
        out["settlements"].append({"region": s_region, "eponym": eponym,
                                   "families": fams})
    return out


def print_world(census: dict, printer=print) -> None:
    printer(f"[world] seed {census['seed']}, {census['world']} mix: "
            f"{len(census['settlements'])} settlements")
    for s in census["settlements"]:
        printer(f"\n  ~ the {s['eponym']} settlement ({s['region']}) ~")
        for fam in s["families"]:
            program = "patronymic of" if fam["region"] in NAMING_PROGRAMS \
                and fam["region"] != "default" else "house of"
            printer(f"    {program} {fam['token']}:")
            for m in fam["members"]:
                printer(f"       {m['name']}  ({m['gender']})")
