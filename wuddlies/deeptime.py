#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/deeptime.py the long watch over hundreds of generations
-The last of the long watches let a thousand generations pass in a heartbeat, and wrote down every time the world quietly changed its mind, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

The instrument for the founder's deep-time question: do chunks of a
distribution stay solid for long stretches and then spawn into something
completely different? The only way to know is literal iteration, so this
iterates, accelerated, and writes down what it sees.

**Why the demography changes and the dynamics do not.** Unbounded
branching cannot reach a hundred generations: that is the exponential wall
the growth guard exists to stop. So the long watch holds the population at
a carrying capacity instead: each generation, N souls each pick a parent
from the generation before and inherit their name, with the SAME
`_wear_token` operator the cascade uses, at the same per-child chance.
This is the standard population model for exactly this question, and the
mutation process is identical to the live one; only the demography is
bounded. Given names are not poured because they have no bearing on how a
carried name erodes, which keeps a thousand generations instant rather
than merely possible.

**What the watch records**, every generation:

- **forms**: how many distinct spellings are alive at once.
- **top**: the share held by the commonest form (dominance).
- **root**: whether the founding form is still anywhere in the world.
- **entropy**: Shannon diversity of the form distribution, in bits.
- **turnovers**: every time the commonest form CHANGES, with the length of
  the reign that just ended. This is the founder's question stated as a
  number: a long reign followed by a turnover IS a chunk staying solid and
  then spawning into something else.

Fixation (one form holding the whole world) is reported rather than
prevented: it is the monoculture attractor, and under the Almar Doctrine
it is a destination the world is allowed to reach, never a failure to
correct.
"""

from __future__ import annotations

import functools
import math
from collections import Counter

import numpy as np

from wuddlies.cascade import _wear_token
from wuddlies.model import WuddlyModel

print = functools.partial(print, flush=True)


def watch(model: WuddlyModel | None, generations: int = 500,
          population: int = 80, wear_rate: float = 0.08, seed: int = 1,
          region: str = "GH", root: str | None = None,
          checkpoints: int = 6, reign_floor: float = 0.25,
          progress=print) -> dict:
    """Run one world for `generations` generations at a fixed population.

    A form only counts as REIGNING while it holds at least `reign_floor` of
    the population. Below that the world is in interregnum, with no name
    anyone would call dominant. Without that floor the measure counts
    photo finishes as revolutions: when the top two forms are near-tied,
    which one leads flips by chance every other generation, and 130 such
    flips look like turmoil while describing a world that never moved.
    """
    rng = np.random.default_rng(seed)
    if root is None:
        root = (model.sample_name(rng, region=region, name_type="surname")
                if model is not None else "Thingaling")
    pop = [root] * population

    history = []
    turnovers = []          # (generation, outgoing form, reign length)
    reigning, reign_start = None, 0
    interregnum = 0
    fixed_at = None
    diversified = False

    # The unbiased ledger: several kinds of achievement recorded side by
    # side, never collapsed into one score. A single definition of "a long
    # reign" quietly decides which worlds count as interesting, which is the
    # Almar Doctrine's failure mode moved up a level: not correcting a
    # branch, but declining to see it. Dominance and persistence and
    # solitude are different things a name can do, and a world is described
    # by which of them it did rather than ranked by any one.
    first_seen: dict[str, int] = {}
    last_seen: dict[str, int] = {}
    present_gens: Counter = Counter()
    peak_share: dict[str, float] = {}
    revivals: Counter = Counter()
    singleton_run: dict[str, int] = {}
    longest_singleton: dict[str, int] = {}
    alive_prev: set = set()

    # Continuity: a thread is unbroken while no ancestor of this soul has
    # mutated. Each soul remembers the generation its line last changed, so
    # the longest unbroken thread is the purest reading of "never changed":
    # a property of one path through the tree rather than of the crowd.
    unbroken_since = [0] * population
    longest_thread = 0

    # Descent between FORMS, not souls: when one spelling wears into
    # another, that edge is recorded once. It buys the two achievements a
    # population count cannot see, fecundity (how many spellings a form
    # gave rise to) and influence (how much of the final world descends
    # through it).
    derived_from: dict[str, str] = {}
    spawned: Counter = Counter()
    check_every = max(1, generations // max(checkpoints, 1))
    snapshots = []

    for gen in range(1, generations + 1):
        parents = rng.integers(0, population, population)
        nxt, nxt_since = [], []
        for p in parents:
            token = pop[p]
            since = unbroken_since[p]
            if wear_rate > 0 and rng.random() < wear_rate:
                worn = _wear_token(token, rng)
                if worn != token:
                    if worn not in derived_from:
                        derived_from[worn] = token
                        spawned[token] += 1
                    token, since = worn, gen
            nxt.append(token)
            nxt_since.append(since)
            longest_thread = max(longest_thread, gen - since)
        pop, unbroken_since = nxt, nxt_since

        counts = Counter(pop)
        top_form, top_n = counts.most_common(1)[0]
        total = len(pop)
        probs = np.asarray([c / total for c in counts.values()])
        entropy = float(-(probs * np.log2(probs)).sum())
        history.append({"gen": gen, "forms": len(counts),
                        "top": top_n / total, "top_form": top_form,
                        "root": counts.get(root, 0) / total,
                        "entropy": entropy})

        for form, c in counts.items():
            if form not in first_seen:
                first_seen[form] = gen
            elif form not in alive_prev:
                revivals[form] += 1
            last_seen[form] = gen
            present_gens[form] += 1
            peak_share[form] = max(peak_share.get(form, 0.0), c / total)
            if c == 1:
                singleton_run[form] = singleton_run.get(form, 0) + 1
                longest_singleton[form] = max(longest_singleton.get(form, 0),
                                              singleton_run[form])
            else:
                singleton_run[form] = 0
        alive_prev = set(counts)

        holder = top_form if (top_n / total) >= reign_floor else None
        if holder != reigning:
            if reigning is not None:
                turnovers.append((gen, reigning, gen - reign_start))
            reigning, reign_start = holder, gen
        if holder is None:
            interregnum += 1
        # Fixation means RETURNING to one form after diversity existed; the
        # founding generation trivially holds one form and is not news.
        if len(counts) > 1:
            diversified = True
        elif fixed_at is None and diversified:
            fixed_at = gen
        if gen % check_every == 0 or gen == generations:
            snapshots.append((gen, counts.most_common(4), len(counts)))

    reigns = [t[2] for t in turnovers]
    if reigning is not None:
        reigns.append(generations - reign_start)
    if not reigns:
        reigns = [0]
    out = {
        "root": root, "wear_rate": wear_rate, "population": population,
        "generations": generations, "history": history,
        "turnovers": turnovers, "fixed_at": fixed_at,
        "reign_floor": reign_floor,
        "interregnum": interregnum / max(generations, 1),
        "longest_reign": max(reigns), "mean_reign": float(np.mean(reigns)),
        "final_forms": history[-1]["forms"],
        "mean_forms": float(np.mean([h["forms"] for h in history])),
        "peak_forms": max(h["forms"] for h in history),
        "final_top": history[-1]["top"],
        "snapshots": snapshots,
        # the profile: several achievements, none ranked above another
        "endured": present_gens.most_common(3),
        "root_lasted": present_gens.get(root, 0),
        "root_last_seen": last_seen.get(root, 0),
        "solitary": sorted(longest_singleton.items(), key=lambda kv: -kv[1])[:3],
        "revived": sum(revivals.values()),
        "revived_top": revivals.most_common(3),
        "ever_lived": len(first_seen),
        "longest_thread": longest_thread,
        "fecund": spawned.most_common(3),
        "influence": _influence(pop, derived_from),
    }
    _report(out, progress)
    return out


"""
--- the achievement question -------------------------------------------

An achievement, in a world whose only primitives are forms, bearers,
time and descent, is **a pattern that persists against the process that
dissolves patterns**. Everything here is eroding; anything that lasts had
to resist. The types are therefore not arbitrary, they are the modes of
persistence those four primitives allow, and the list closes when the
primitives run out:

    dominance    persisting in NUMBER      held a quarter of the world
    endurance    persisting in TIME        present, at any share, for ages
    continuity   persisting UNBROKEN       a line that never once changed
    solitude     persisting ALONE          the only bearer, for generations
    fidelity     persisting as ORIGIN      the founding name still here
    fecundity    persisting THROUGH KIN    the spellings it gave rise to
    influence    persisting as ANCESTOR    the road the present travelled
    recurrence   persisting by RETURNING   died, and was re-derived

Eight, and the taxonomy is closed only in the sense that these are the
ones today's primitives support. Add geography and "spread" appears; add
prestige and "imitation" appears. New primitives, new ways to last.

`achievements()` then answers the weathering question a second way. Each
rate is scored on every axis, every axis is normalised across the rates,
and the rate's richness is the GEOMETRIC mean of its scores: a measure
that rewards a world where many kinds of achievement are possible at once
and collapses if any becomes impossible. It never asks which achievement
is best, only where the most of them can happen together.
"""


def achievements(model, rates=(0.005, 0.01, 0.02, 0.035, 0.05, 0.08, 0.12),
                 seeds: int = 5, generations: int = 600, population: int = 80,
                 region: str = "GH", root: str | None = None,
                 progress=print) -> list[dict]:
    """Score every wear rate on all eight axes and report where they cluster."""
    axes = ("dominance", "endurance", "continuity", "solitude",
            "fidelity", "fecundity", "influence", "recurrence")
    rows = []
    progress(f"[achieve] scoring {len(rates)} rates x {seeds} worlds x "
             f"{generations} generations on {len(axes)} axes of persistence")
    for rate in rates:
        acc = {a: [] for a in axes}
        for seed in range(1, seeds + 1):
            w = watch(model, generations=generations, population=population,
                      wear_rate=rate, seed=seed, region=region, root=root,
                      progress=lambda *_a, **_k: None)
            g = max(generations, 1)
            acc["dominance"].append(w["longest_reign"] / g)
            acc["endurance"].append(max([n for _f, n in w["endured"]] or [0]) / g)
            acc["continuity"].append(w["longest_thread"] / g)
            acc["solitude"].append(max([n for _f, n in w["solitary"]] or [0]) / g)
            acc["fidelity"].append(w["root_lasted"] / g)
            acc["fecundity"].append(max([n for _f, n in w["fecund"]] or [0]))
            acc["influence"].append(max([s for _f, s in w["influence"]] or [0]))
            acc["recurrence"].append(w["revived"] / g)
        rows.append({"rate": rate,
                     **{a: float(np.mean(v)) for a, v in acc.items()}})

    # Normalise each axis across the rates, then take the geometric mean.
    for a in axes:
        hi = max(r[a] for r in rows) or 1.0
        for r in rows:
            r[a + "_n"] = r[a] / hi
    for r in rows:
        vals = [max(r[a + "_n"], 1e-6) for a in axes]
        r["richness"] = float(np.exp(np.mean(np.log(vals))))

    progress("[achieve] rate    " + "  ".join(f"{a[:4]}" for a in axes)
             + "   richness")
    for r in rows:
        progress(f"[achieve] {r['rate']:<7.4g}"
                 + "  ".join(f"{r[a + '_n']:.2f}" for a in axes)
                 + f"     {r['richness']:.3f}")
    best = max(rows, key=lambda r: r["richness"])
    progress("")
    progress(f"[achieve] the most kinds of achievement coexist at wear "
             f"{best['rate']:.4g} (richness {best['richness']:.3f})")
    sat = [a for a in axes if sum(1 for r in rows if r[a + "_n"] > 0.98) > 2]
    if sat:
        progress(f"[achieve] note, these axes saturate across most of the "
                 f"range and so discriminate weakly here: {', '.join(sat)}")
    weak = [a for a in axes if best[a + "_n"] < 0.4]
    if weak:
        progress(f"[achieve] even there these stay thin: {', '.join(weak)}")
    progress("[achieve] no axis is ranked above another; richness only asks "
             "how many can happen at once.")
    return rows


def _influence(final_pop: list[str], derived_from: dict[str, str]) -> list:
    """How much of the world alive at the end descends through each form.
    A form can be long dead and still be the road most of the present
    travelled down: influence is an achievement no census can see."""
    through: Counter = Counter()
    for form in set(final_pop):
        seen, node = set(), form
        while node is not None and node not in seen:
            seen.add(node)
            node = derived_from.get(node)
        for ancestor in seen:
            if ancestor != form:
                through[ancestor] += final_pop.count(form)
    total = max(len(final_pop), 1)
    return [(f, n / total) for f, n in through.most_common(3)]


def _report(w: dict, progress) -> None:
    progress(f"[longwatch] '{w['root']}' through {w['generations']} generations, "
             f"population {w['population']}, wear {w['wear_rate']}")
    progress(f"[longwatch] forms alive: mean {w['mean_forms']:.1f}, "
             f"peak {w['peak_forms']}, final {w['final_forms']}; "
             f"final dominance {w['final_top']:.0%}")
    progress(f"[longwatch] reigns (a form holding >= {w['reign_floor']:.0%}): "
             f"{len(w['turnovers'])} ended; longest {w['longest_reign']} "
             f"generations, mean {w['mean_reign']:.0f}; "
             f"{w['interregnum']:.0%} of history had no dominant name at all")
    if w["fixed_at"]:
        progress(f"[longwatch] the world FIXED on a single form at generation "
                 f"{w['fixed_at']} (the monoculture attractor, reported not corrected)")
    else:
        progress("[longwatch] never fixed: the world still holds more than one form")

    if w["turnovers"]:
        progress("[longwatch] the reigns, in order (a long one then a turnover is "
                 "a chunk staying solid then spawning into something else):")
        for gen, form, length in w["turnovers"][:12]:
            progress(f"[longwatch]   gen {gen:5d}  '{form}' ended a reign of "
                     f"{length} generations")
        if len(w["turnovers"]) > 12:
            progress(f"[longwatch]   ... and {len(w['turnovers']) - 12} more")

    progress(f"[longwatch] the profile, several kinds of achievement, none "
             f"ranked above another ({w['ever_lived']} forms ever lived):")
    progress("[longwatch]   endured (most generations present, at any share): "
             + ", ".join(f"'{f}' {n}g" for f, n in w["endured"]))
    progress(f"[longwatch]   the founding name '{w['root']}' was present for "
             f"{w['root_lasted']} generations, last seen at "
             f"{w['root_last_seen']}")
    if w["solitary"] and w["solitary"][0][1] > 1:
        progress("[longwatch]   stayed solitary (longest run as the only "
                 "bearer): " + ", ".join(f"'{f}' {n}g" for f, n in w["solitary"]))
    progress(f"[longwatch]   revivals (a form died and was re-derived "
             f"later): {w['revived']}"
             + (("; " + ", ".join(f"'{f}' x{n}" for f, n in w["revived_top"]))
                if w["revived_top"] else ""))
    progress(f"[longwatch]   longest unbroken thread (a line that never "
             f"changed, however few carried it): {w['longest_thread']} "
             f"generations")
    if w["fecund"]:
        progress("[longwatch]   most fecund (spellings it gave rise to): "
                 + ", ".join(f"'{f}' {n}" for f, n in w["fecund"]))
    if w["influence"]:
        progress("[longwatch]   most influential (share of the final world "
                 "descending through it): "
                 + ", ".join(f"'{f}' {s:.0%}" for f, s in w["influence"]))

    progress("[longwatch] snapshots of the world:")
    for gen, common, forms in w["snapshots"]:
        top = ", ".join(f"{f} x{c}" for f, c in common)
        progress(f"[longwatch]   gen {gen:5d}  ({forms} forms)  {top}")
