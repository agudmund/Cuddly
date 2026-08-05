#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/cascade.py the seed cascade: worlds, settlements, families, souls
-The last of the seed cascades held a whole world in one number, and every family in it knew exactly who they were, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

The clustering floor, speaking the OPERATOR LANGUAGE, now with GENERATIONAL
TIME. One world seed deterministically derives settlements, lineages, and
every soul in every generation (SeedSequence spawning: the same number
reproduces the same history forever, within a version).

**A naming convention is a PROGRAM, and a program is DATA:** token_source
(a standing surname, or a parent's given name), order, per-gender
child_suffix particles, token_inherits. One interpreter executes them all;
the Earth anchors (plain inheritance, Iceland's patronymic law) are
sentences in the language, and new conventions are new dicts.

**Generations make the law LIVE.** In a surname world the house token
flows down verbatim. In a patronymic world each child's name is minted
from their own parent's actual given name: Gitta's son Ewan fathers Runa
Ewansdóttir, and nothing anywhere stored that: the rule executed down the
years from one seed. This is the two-NPCs-spawn-more-NPCs use case
standing up: descent needs a convention, and now the convention runs.

**Drift flows down the years too.** Founding drift may mutate a
settlement's inherited program at birth, and a smaller per-generation
chance mutates it mid-history: the particle weathers in generation two,
the patronymics freeze in generation three, and every mutation lands in
the census's drift log with its generation stamp, so the elders' names
keep the old spelling while the young carry the new: watchable, logged,
reproducible. Both rates are dialable to zero for perfectly still worlds.

REGION_PROGRAMS maps regions to base programs (rows, never branches).
Ahead: merge crossover when settlements meet, the promotion watcher, and
programs serialized per population: the save-format of invented cultures.
"""

from __future__ import annotations

import unicodedata

import numpy as np

from wuddlies.model import FAMILY_FIRST_REGIONS, GENDERS, WuddlyModel

DRIFT_RATE = 0.12       # at each settlement's founding
GEN_DRIFT_RATE = 0.06   # between each generation, per settlement


# ── the operator language, v1: programs are data ──────────────────────────

def program_default(region: str) -> dict:
    return {
        "id": "inherited_surname",
        "token_source": "surname",
        "order": "family_first" if region in FAMILY_FIRST_REGIONS else "given_first",
        "child_suffix": None,
        "token_inherits": True,
    }


IS_PATRONYMIC = {
    "id": "is_patronymic",
    "token_source": "given",
    "order": "given_first",
    # Simplified -s- joint; the full genitive stems are a later refinement.
    "child_suffix": {"M": "sson", "F": "sdóttir", "U": "sson"},
    "token_inherits": False,
}

REGION_PROGRAMS = {
    "IS": IS_PATRONYMIC,
}


def base_program_for(region: str) -> dict:
    prog = REGION_PROGRAMS.get(region)
    return dict(prog) if prog else program_default(region)


# ── the interpreter ───────────────────────────────────────────────────────

def pour_token(model: WuddlyModel, rng, region: str, program: dict) -> str:
    return model.sample_name(rng, region=region, name_type=program["token_source"])


def assemble(program: dict, token: str, given: str, gender: str) -> str:
    suffixes = program.get("child_suffix")
    worn = token + suffixes.get(gender, "") if suffixes else token
    if program["order"] == "family_first":
        return f"{worn} {given}"
    return f"{given} {worn}"


# ── drift: mutations at foundings and down the years ──────────────────────

def _weather_suffix(suffix: str, rng) -> str:
    ops = []
    plain = unicodedata.normalize("NFD", suffix)
    plain = "".join(c for c in plain if not unicodedata.combining(c))
    if plain != suffix:
        ops.append(plain)                                   # diacritic lost
    for i in range(len(suffix) - 1):
        if suffix[i] == suffix[i + 1]:
            ops.append(suffix[:i] + suffix[i + 1:])         # doubled worn smooth
    vowels = "aeiouy"
    vi = [i for i, c in enumerate(suffix) if c in vowels]
    if vi:
        i = vi[int(rng.integers(len(vi)))]
        swap = vowels[int(rng.integers(len(vowels)))]
        ops.append(suffix[:i] + swap + suffix[i + 1:])      # vowel shift
    return ops[int(rng.integers(len(ops)))] if ops else suffix


def maybe_drift(program: dict, rng, drift_rate: float,
                stamp: str) -> tuple[dict, list[str]]:
    """One roll of the drift die. Returns the (possibly new) program and the
    log lines, each carrying its stamp (founding, or a generation mark)."""
    if drift_rate <= 0 or rng.random() >= drift_rate:
        return program, []
    prog = dict(program)
    log = []
    kinds = ["suffix"] * 3 + ["order"] + ["source"]
    kind = kinds[int(rng.integers(len(kinds)))]
    if kind == "suffix" and prog.get("child_suffix"):
        suffixes = dict(prog["child_suffix"])
        g = ("M", "F", "U")[int(rng.integers(3))]
        old = suffixes.get(g, "")
        new = _weather_suffix(old, rng)
        if new != old:
            suffixes[g] = new
            prog["child_suffix"] = suffixes
            prog["id"] = prog["id"] + "+worn"
            log.append(f"{stamp}: the {g} particle weathered {old} -> {new}")
    elif kind == "order":
        prog["order"] = ("family_first" if prog["order"] == "given_first"
                         else "given_first")
        prog["id"] = prog["id"] + "+flipped"
        log.append(f"{stamp}: name order flipped to {prog['order']}")
    else:
        if prog["token_source"] == "surname":
            prog["token_source"] = "given"
            prog["child_suffix"] = dict(prog.get("child_suffix")
                                        or {"M": "sson", "F": "sdóttir", "U": "sson"})
            prog["token_inherits"] = False
            prog["id"] = "went_patronymic"
            log.append(f"{stamp}: this settlement went patronymic "
                       "(a parent's name now carries)")
        else:
            prog["token_source"] = "surname"
            prog["child_suffix"] = None
            prog["token_inherits"] = True
            prog["id"] = "settled_surnames"
            log.append(f"{stamp}: patronymics froze into standing surnames")
    return prog, log


# ── generational time ─────────────────────────────────────────────────────

def pour_soul(model: WuddlyModel, seed_seq: np.random.SeedSequence,
              region: str, programs: list[dict], gen: int,
              parent_token: str, generations: int, children_max: int) -> dict:
    """One soul and, recursively, their descendants. The token handed to a
    child is the house name (inherited) or THIS soul's given (patronymic)."""
    own_seq, kids_seq = seed_seq.spawn(2)
    rng = np.random.default_rng(own_seq)
    program = programs[min(gen, len(programs) - 1)]
    gp = np.asarray(model.gender_prior, dtype=np.float64)
    gender = GENDERS[int(rng.choice(len(GENDERS), p=gp / gp.sum()))]
    given = model.sample_name(rng, region=region, name_type="given",
                              gender=gender)
    soul = {"given": given, "gender": gender, "gen": gen,
            "name": assemble(program, parent_token, given, gender),
            "children": []}
    if gen < generations:
        n_kids = int(rng.integers(1, children_max + 1))
        next_program = programs[min(gen + 1, len(programs) - 1)]
        child_token = (parent_token if next_program["token_inherits"]
                       else given)
        soul["children"] = [
            pour_soul(model, ks, region, programs, gen + 1, child_token,
                      generations, children_max)
            for ks in kids_seq.spawn(n_kids)
        ]
    return soul


def pour_lineage(model: WuddlyModel, seed_seq: np.random.SeedSequence,
                 region: str, programs: list[dict], generations: int,
                 children_max: int) -> dict:
    founding_rng, souls_seq = [np.random.default_rng(s) if i == 0 else s
                               for i, s in enumerate(seed_seq.spawn(2))]
    token = pour_token(model, founding_rng, region, programs[0])
    n_first = int(founding_rng.integers(1, children_max + 1))
    firstborn = [pour_soul(model, ss, region, programs, 1, token,
                           generations, children_max)
                 for ss in souls_seq.spawn(n_first)]
    return {"token": token, "region": region, "souls": firstborn}


def pour_world(model: WuddlyModel, world_seed: int, settlements: int = 3,
               families: int = 3, souls: int = 4, world: str = "population",
               region: str | None = None, drift_rate: float = DRIFT_RATE,
               generations: int = 1, children_max: int | None = None,
               gen_drift_rate: float = GEN_DRIFT_RATE) -> dict:
    """One number in, one coherent history out, drift log included.
    `souls` caps children-per-parent when children_max is not given."""
    children_max = children_max or max(1, souls - 1)
    root = np.random.SeedSequence(world_seed)
    out = {"seed": world_seed, "world": world, "generations": generations,
           "settlements": []}
    for s_seq in root.spawn(settlements):
        founding, drift_seq, families_seq = s_seq.spawn(3)
        f_rng = np.random.default_rng(founding)
        if region is None:
            w = model.region_draw_weights(world)
            s_region = model.regions[int(f_rng.choice(len(model.regions), p=w))]
        else:
            s_region = region
        eponym = model.sample_name(f_rng, region=s_region, name_type="surname")

        d_rng = np.random.default_rng(drift_seq)
        program, drift_log = maybe_drift(base_program_for(s_region), d_rng,
                                         drift_rate, "founding drift")
        programs = [program]
        for g in range(1, generations + 1):
            nxt, glog = maybe_drift(programs[-1], d_rng, gen_drift_rate,
                                    f"generation {g} drift")
            programs.append(nxt)
            drift_log.extend(glog)

        fams = [pour_lineage(model, fs, s_region, programs, generations,
                             children_max)
                for fs in families_seq.spawn(families)]
        out["settlements"].append({"region": s_region, "eponym": eponym,
                                   "programs": programs, "drift": drift_log,
                                   "families": fams})
    return out


def _print_soul(soul: dict, prefix: str, last: bool, printer) -> None:
    branch = "└ " if last else "├ "
    printer(f"{prefix}{branch}{soul['name']}  ({soul['gender']})")
    ext = "   " if last else "│  "
    kids = soul["children"]
    for i, kid in enumerate(kids):
        _print_soul(kid, prefix + ext, i == len(kids) - 1, printer)


def print_world(census: dict, printer=print) -> None:
    printer(f"[world] seed {census['seed']}, {census['world']} mix, "
            f"{census['generations']} generation(s): "
            f"{len(census['settlements'])} settlements")
    for s in census["settlements"]:
        printer(f"\n  ~ the {s['eponym']} settlement ({s['region']}) ~")
        for line in s["drift"]:
            printer(f"    * {line}")
        for fam in s["families"]:
            label = ("line of" if not s["programs"][0]["token_inherits"]
                     else "house of")
            printer(f"    {label} {fam['token']}:")
            for i, soul in enumerate(fam["souls"]):
                _print_soul(soul, "    ", i == len(fam["souls"]) - 1, printer)
