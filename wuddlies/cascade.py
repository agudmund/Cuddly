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

import sys
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

def pour_token(model: WuddlyModel, rng, region: str, program: dict,
               temperature: float = 0.9) -> str:
    return model.sample_name(rng, region=region, name_type=program["token_source"],
                             temperature=temperature)


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


def _mint_particles(model: WuddlyModel, rng, region: str) -> dict:
    """A culture inventing patronymics grows its particles from its OWN
    soil: the tails of names its region actually pours. Invention, never
    Iceland-import (importing is what confluences do, with the herd)."""
    tails = []
    for _ in range(6):
        name = model.sample_name(rng, region=region, name_type="given",
                                 temperature=1.0)
        tail = name[-3:].lower() if len(name) >= 4 else name.lower()
        if tail and tail not in tails:
            tails.append(tail)
    m = tails[0] if tails else "son"
    f = next((t for t in tails[1:] if t != m), m + "a")
    return {"M": m, "F": f, "U": m}


def maybe_drift(program: dict, rng, drift_rate: float,
                stamp: str, model: WuddlyModel | None = None,
                region: str | None = None) -> tuple[dict, list[str]]:
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
            if model is not None and region is not None:
                minted = _mint_particles(model, rng, region)
                prog["child_suffix"] = minted
                log.append(f"{stamp}: this settlement went patronymic and "
                           f"minted its own particles from local soil: "
                           f"-{minted['M']} (M), -{minted['F']} (F)")
            else:
                prog["child_suffix"] = dict(prog.get("child_suffix")
                                            or {"M": "sson", "F": "sdóttir", "U": "sson"})
                log.append(f"{stamp}: this settlement went patronymic "
                           "(a parent's name now carries)")
            prog["token_inherits"] = False
            prog["id"] = "went_patronymic"
        else:
            prog["token_source"] = "surname"
            prog["child_suffix"] = None
            prog["token_inherits"] = True
            prog["id"] = "settled_surnames"
            log.append(f"{stamp}: patronymics froze into standing surnames")
    return prog, log


# ── merge crossover: the herds meet ───────────────────────────────────────

def crossover(prog_a: dict, prog_b: dict, root_a: str, root_b: str,
              rng) -> tuple[dict, list[str]]:
    """Two herds found one settlement; their programs recombine field-wise.
    A custom (like patronymic particles) can arrive WITH its herd: import,
    honestly logged, as distinct from drift's local invention."""
    log = []
    src_a = bool(rng.integers(2))
    src_parent, src_root = (prog_a, root_a) if src_a else (prog_b, root_b)
    ord_a = bool(rng.integers(2))
    ord_parent, ord_root = (prog_a, root_a) if ord_a else (prog_b, root_b)
    prog = {
        "id": f"confluence({root_a}x{root_b})",
        "token_source": src_parent["token_source"],
        "token_inherits": src_parent["token_inherits"],
        "order": ord_parent["order"],
        "child_suffix": None,
    }
    log.append(f"confluence: the token walks {src_root}'s way "
               f"({prog['token_source']}); name order follows {ord_root} "
               f"({prog['order']})")
    sa, sb = prog_a.get("child_suffix"), prog_b.get("child_suffix")
    if sa and sb:
        prog["child_suffix"] = {g: (sa if bool(rng.integers(2)) else sb)[g]
                                for g in ("M", "F", "U")}
        log.append("confluence: the particles blended from both herds")
    elif (sa or sb) and prog["token_source"] == "given":
        carrier = root_a if sa else root_b
        prog["child_suffix"] = dict(sa or sb)
        log.append(f"confluence: the particles arrived with the {carrier} herd")
    return prog, log


# ── the promotion watcher: accidents become traditions ────────────────────

INITIAL_RUN_SHARE = 0.5     # half a generation sharing a first letter
INITIAL_RUN_MIN = 4         # ...among at least this many souls


def watch_for_promotions(gen: int, level: list, program: dict,
                         families: list) -> tuple[dict, list[str]]:
    """Inspect a completed generation's ACTUAL names for regularities worth
    crystallizing. Deterministic observation, never a dice roll: the Smith
    route in miniature. Returns the (possibly promoted) program for the
    NEXT generation, plus log lines; family echo laws land on the family."""
    log = []
    prog = program

    # The initial-letter run: an accident of the elders becomes law.
    if not program.get("initial") and len(level) >= INITIAL_RUN_MIN:
        firsts = {}
        for soul, _fam in level:
            c = soul["given"][:1].upper()
            firsts[c] = firsts.get(c, 0) + 1
        letter, count = max(firsts.items(), key=lambda kv: kv[1])
        if count / len(level) >= INITIAL_RUN_SHARE:
            prog = dict(program)
            prog["initial"] = letter
            prog["id"] = prog["id"] + f"+initial({letter})"
            log.append(f"generation {gen} promotion: {count} of {len(level)} "
                       f"souls happened to share the letter {letter}; the "
                       f"accident is now tradition, and the young must carry it")

    # The echo: a child bearing their parent's own name founds a custom.
    for soul, fam in level:
        parent_given = soul.get("parent_given")
        if (parent_given and soul["given"] == parent_given
                and "echo" not in fam["laws"]):
            fam["laws"]["echo"] = soul["given"]
            log.append(f"generation {gen} promotion: in the {fam['token']} "
                       f"family a child received their parent's own name; "
                       f"the name {soul['given']} now carries")
    return prog, log


# ── generational time, breadth-first so the watcher can see ───────────────

def _pour_given(model, rng, region, gender, program, echo: str | None,
                temperature: float = 0.9) -> str:
    if echo:
        return echo
    initial = program.get("initial")
    for _ in range(12):
        given = model.sample_name(rng, region=region, name_type="given",
                                  gender=gender, temperature=temperature)
        if not initial or given[:1].upper() == initial:
            return given
    return given


def pour_history(model: WuddlyModel, families_seq: np.random.SeedSequence,
                 fam_roots: list[str], programs: list[dict],
                 generations: int, children_max: int,
                 drift_log: list, promotions_on: bool,
                 temperature: float = 0.9) -> list[dict]:
    """Pour a settlement's whole history one generation at a time, letting
    the watcher inspect each completed generation before the next is born."""
    n_fam = len(fam_roots)
    fam_seqs = families_seq.spawn(n_fam)
    fams = []
    level = []   # (soul, family) pairs of the generation being poured
    for froot, fseq in zip(fam_roots, fam_seqs):
        founding, kids = fseq.spawn(2)
        f_rng = np.random.default_rng(founding)
        token = pour_token(model, f_rng, froot, programs[0], temperature)
        fam = {"token": token, "region": froot, "souls": [], "laws": {},
               "_kid_seq": kids}
        fams.append(fam)

    frontier = [(None, fam, fam["_kid_seq"]) for fam in fams]
    for gen in range(1, generations + 1):
        program = programs[min(gen, len(programs) - 1)]
        level = []
        next_frontier = []
        for parent, fam, kid_seq in frontier:
            own_rng = np.random.default_rng(kid_seq.spawn(1)[0])
            n_kids = int(own_rng.integers(1, children_max + 1))
            for ks in kid_seq.spawn(n_kids):
                s_rng = np.random.default_rng(ks)
                gp = np.asarray(model.gender_prior, dtype=np.float64)
                gender = GENDERS[int(s_rng.choice(len(GENDERS), p=gp / gp.sum()))]
                echo = fam["laws"].get("echo")
                given = _pour_given(model, s_rng, fam["region"], gender,
                                    program, echo, temperature)
                token = (fam["token"] if program["token_inherits"]
                         else (parent["given"] if parent else fam["token"]))
                soul = {"given": given, "gender": gender, "gen": gen,
                        "parent_given": parent["given"] if parent else None,
                        "name": assemble(program, token, given, gender),
                        "children": []}
                (parent["children"] if parent else fam["souls"]).append(soul)
                level.append((soul, fam))
                next_frontier.append((soul, fam, ks.spawn(1)[0]))
        if promotions_on and gen < generations:
            promoted, plog = watch_for_promotions(gen, level,
                                                  programs[min(gen + 1,
                                                               len(programs) - 1)],
                                                  fams)
            # A promoted law flows down ALL the remaining years, not just the
            # next one, or the watcher re-crystallizes its own tradition.
            if promoted.get("initial"):
                for j in range(gen + 1, len(programs)):
                    if not programs[j].get("initial"):
                        pj = dict(programs[j])
                        pj["initial"] = promoted["initial"]
                        pj["id"] += f"+initial({promoted['initial']})"
                        programs[j] = pj
            drift_log.extend(plog)
        print(f"[world] generation {gen} poured: {len(level)} souls",
              file=sys.stderr, flush=True)
        frontier = next_frontier
    for fam in fams:
        fam.pop("_kid_seq", None)
    return fams


def pour_world(model: WuddlyModel, world_seed: int, settlements: int = 3,
               families: int = 3, souls: int = 4, world: str = "population",
               region: str | None = None, drift_rate: float = DRIFT_RATE,
               generations: int = 1, children_max: int | None = None,
               gen_drift_rate: float = GEN_DRIFT_RATE,
               confluences: int = 0,
               roots: tuple[str, str] | None = None,
               promotions_on: bool = True,
               temperature: float = 0.9,
               max_souls: int = 25000) -> dict:
    """One number in, one coherent history out, drift log included.
    `souls` caps children-per-parent when children_max is not given. The
    last `confluences` settlements are founded by TWO herds meeting: their
    programs recombine, and each family carries its own root region."""
    children_max = children_max or max(1, souls - 1)
    # Honest growth arithmetic BEFORE pouring: generations are exponential,
    # and a silent hour of grinding is not a world, it is a mistake with no
    # narrator (field lesson, a 20-generation x3-children request, 2026-08-05).
    mean_kids = (1 + children_max) / 2
    expected = settlements * families * sum(mean_kids ** g
                                            for g in range(1, generations + 1))
    if expected > max_souls:
        raise SystemExit(
            f"[world] this world would pour ~{int(expected):,} souls "
            f"({settlements} settlements x {families} families x up-to-"
            f"{children_max} children over {generations} generations); "
            f"the cap is {max_souls:,}.\n"
            f"[world] for a deep DYNASTY pour a lineal saga: --children 1 "
            f"(one heir per generation = "
            f"{settlements * families * generations} souls).\n"
            f"[world] or raise the cap deliberately with --max-souls.")
    root = np.random.SeedSequence(world_seed)
    out = {"seed": world_seed, "world": world, "generations": generations,
           "settlements": []}
    for idx, s_seq in enumerate(root.spawn(settlements)):
        founding, drift_seq, families_seq = s_seq.spawn(3)
        f_rng = np.random.default_rng(founding)
        d_rng = np.random.default_rng(drift_seq)
        is_confluence = idx >= settlements - confluences

        def draw_region():
            if region is not None:
                return region
            w = model.region_draw_weights(world)
            return model.regions[int(f_rng.choice(len(model.regions), p=w))]

        if is_confluence:
            root_a, root_b = roots if roots else (draw_region(), draw_region())
            eponym = (model.sample_name(f_rng, region=root_a, name_type="surname")
                      + "-"
                      + model.sample_name(f_rng, region=root_b, name_type="surname"))
            program, drift_log = crossover(base_program_for(root_a),
                                           base_program_for(root_b),
                                           root_a, root_b, d_rng)
            mint_soil = root_a
            s_roots = (root_a, root_b)
        else:
            s_region = draw_region()
            eponym = model.sample_name(f_rng, region=s_region, name_type="surname")
            program, drift_log = maybe_drift(base_program_for(s_region), d_rng,
                                             drift_rate, "founding drift",
                                             model=model, region=s_region)
            mint_soil = s_region
            s_roots = None

        programs = [program]
        for g in range(1, generations + 1):
            nxt, glog = maybe_drift(programs[-1], d_rng, gen_drift_rate,
                                    f"generation {g} drift",
                                    model=model, region=mint_soil)
            programs.append(nxt)
            drift_log.extend(glog)

        fam_roots = ([root_a if d_rng.random() < 0.5 else root_b
                      for _ in range(families)] if is_confluence
                     else [mint_soil] * families)
        fams = pour_history(model, families_seq, fam_roots, programs,
                            generations, children_max, drift_log,
                            promotions_on, temperature)
        out["settlements"].append({"region": mint_soil, "roots": s_roots,
                                   "eponym": eponym, "programs": programs,
                                   "drift": drift_log, "families": fams})
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
        if s.get("roots"):
            a, b = s["roots"]
            printer(f"\n  ~ the {s['eponym']} confluence ({a} × {b}) ~")
        else:
            printer(f"\n  ~ the {s['eponym']} settlement ({s['region']}) ~")
        for line in s["drift"]:
            printer(f"    * {line}")
        for fam in s["families"]:
            label = ("line of" if not s["programs"][0]["token_inherits"]
                     else "house of")
            tag = f" ({fam['region']})" if s.get("roots") else ""
            law = fam.get("laws", {}).get("echo")
            law_tag = f"  [the name {law} carries]" if law else ""
            printer(f"    {label} {fam['token']}{tag}:{law_tag}")
            for i, soul in enumerate(fam["souls"]):
                _print_soul(soul, "    ", i == len(fam["souls"]) - 1, printer)
