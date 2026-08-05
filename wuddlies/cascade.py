#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/cascade.py the seed cascade: worlds, settlements, families, souls
-The last of the seed cascades held a whole world in one number, and every family in it knew exactly who they were, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

The clustering floor, now speaking the OPERATOR LANGUAGE. One world seed
deterministically derives settlement seeds, families, souls (SeedSequence
spawning: the same number reproduces the same census forever, within a
version). Coherence emerges structurally: a family shares its name because
it shares its seed.

**A naming convention is a PROGRAM, and a program is DATA.** Version one of
the operator language is a small declarative dict executed by one
interpreter: `token_source` (what a family pours at its founding: a
surname to inherit, or a parent's given name), `order` (given-first or
family-first), `child_suffix` (per-gender particles appended to the token:
the patronymic operator), `token_inherits` (whether the token is a
standing family label or minted per generation: the marker the future
generational floor reads). The two Earth anchors are now sentences in this
language rather than functions: plain inheritance, and Iceland's
patronymic law. New conventions are new DICTS, never new branches.

**Founding drift is the first emergence brick.** At each settlement's
founding there is a small seeded chance its inherited program mutates: a
suffix weathers (a diacritic lost, a doubled letter worn smooth), the
name order flips, or the token source itself turns patronymic: and every
mutation lands in the census's drift log, so "what on earth did those
ones do" always has a true answer with a generation stamp. Drift is
deterministic per world seed, rare by default, and dialable to zero.

The registry REGION_PROGRAMS maps regions to their base programs (the
dispatcher shape: rows, never branches); everywhere unlisted speaks the
default program in its region's living name order. When drift, merge, and
the promotion watcher are all standing, these bases become merely the
opening state of histories that write themselves.
"""

from __future__ import annotations

import unicodedata

import numpy as np

from wuddlies.model import FAMILY_FIRST_REGIONS, GENDERS, WuddlyModel

DRIFT_RATE = 0.12   # per-settlement founding; 0 pours perfectly still worlds


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

# region -> base program. A new convention is a new ROW, never a new branch.
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


# ── founding drift: the first emergence brick ─────────────────────────────

def _weather_suffix(suffix: str, rng) -> str:
    """One small phonetic weathering of a particle."""
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


def maybe_drift(program: dict, rng, drift_rate: float) -> tuple[dict, list[str]]:
    """A settlement founding may mutate its inherited program. Returns the
    (possibly new) program and the drift-log lines that explain it."""
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
            log.append(f"founding drift: the {g} particle weathered "
                       f"{old} -> {new}")
    elif kind == "order":
        prog["order"] = ("family_first" if prog["order"] == "given_first"
                         else "given_first")
        prog["id"] = prog["id"] + "+flipped"
        log.append(f"founding drift: name order flipped to {prog['order']}")
    else:
        if prog["token_source"] == "surname":
            prog["token_source"] = "given"
            prog["child_suffix"] = dict(prog.get("child_suffix")
                                        or {"M": "sson", "F": "sdóttir", "U": "sson"})
            prog["token_inherits"] = False
            prog["id"] = "went_patronymic"
            log.append("founding drift: this settlement went patronymic "
                       "(a parent's name now carries)")
        else:
            prog["token_source"] = "surname"
            prog["child_suffix"] = None
            prog["token_inherits"] = True
            prog["id"] = "settled_surnames"
            log.append("founding drift: patronymics froze into standing surnames")
    return prog, log


# ── the cascade ───────────────────────────────────────────────────────────

def pour_family(model: WuddlyModel, seed_seq: np.random.SeedSequence,
                region: str, program: dict, souls: int) -> dict:
    founding_rng, *soul_rngs = [np.random.default_rng(s)
                                for s in seed_seq.spawn(souls + 1)]
    token = pour_token(model, founding_rng, region, program)
    members = []
    for rng in soul_rngs:
        gp = np.asarray(model.gender_prior, dtype=np.float64)
        gender = GENDERS[int(rng.choice(len(GENDERS), p=gp / gp.sum()))]
        given = model.sample_name(rng, region=region, name_type="given",
                                  gender=gender)
        members.append({"name": assemble(program, token, given, gender),
                        "gender": gender})
    return {"token": token, "region": region, "members": members}


def pour_world(model: WuddlyModel, world_seed: int, settlements: int = 3,
               families: int = 3, souls: int = 4, world: str = "population",
               region: str | None = None,
               drift_rate: float = DRIFT_RATE) -> dict:
    """One number in, one coherent census out, drift log included."""
    root = np.random.SeedSequence(world_seed)
    out = {"seed": world_seed, "world": world, "settlements": []}
    for s_seq in root.spawn(settlements):
        founding, drift_seq, families_seq = s_seq.spawn(3)
        f_rng = np.random.default_rng(founding)
        if region is None:
            w = model.region_draw_weights(world)
            s_region = model.regions[int(f_rng.choice(len(model.regions), p=w))]
        else:
            s_region = region
        eponym = model.sample_name(f_rng, region=s_region, name_type="surname")
        program, drift_log = maybe_drift(base_program_for(s_region),
                                         np.random.default_rng(drift_seq),
                                         drift_rate)
        fams = [pour_family(model, fs, s_region, program, souls)
                for fs in families_seq.spawn(families)]
        out["settlements"].append({"region": s_region, "eponym": eponym,
                                   "program": program, "drift": drift_log,
                                   "families": fams})
    return out


def print_world(census: dict, printer=print) -> None:
    printer(f"[world] seed {census['seed']}, {census['world']} mix: "
            f"{len(census['settlements'])} settlements")
    for s in census["settlements"]:
        printer(f"\n  ~ the {s['eponym']} settlement ({s['region']}) ~")
        for line in s["drift"]:
            printer(f"    * {line}")
        label = ("patronymic of" if s["program"].get("child_suffix")
                 else "house of")
        for fam in s["families"]:
            printer(f"    {label} {fam['token']}:")
            for m in fam["members"]:
                printer(f"       {m['name']}  ({m['gender']})")
