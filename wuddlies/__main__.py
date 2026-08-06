#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/__main__.py the name desk CLI
-The last of the name desks took requests at the counter, a seed and a region for a soul made to order, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

The counter service over the librarian: cook the corpus, raise the weight,
and pour souls. Run from the Cuddly repo root:

    python -m wuddlies cook
    python -m wuddlies train [--steps N] [--batch N] [--seed N]
    python -m wuddlies sample [--region GB] [--type given|surname]
                              [--gender M|F] [--count 20] [--seed 7]
                              [--temperature 0.9]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

# The marquee origin families for tab-completion (any of the full 3,261
# corpus tags still works typed in full; these are the clean big names).
MARQUEE_ORIGINS = (
    "Arabic", "Hebrew", "Latin", "Greek", "Spanish", "Germanic", "English",
    "Sanskrit", "Italian", "French", "Chinese", "Japanese", "Korean",
    "Persian", "Turkish", "Russian", "Portuguese", "Vietnamese", "Thai",
    "Hindi", "Swahili", "Yoruba", "Hausa", "Irish",
)

REGISTER = """\
wuddly - the Wuddlies naming desk (runs from anywhere; home: the Cuddly repo)

VERBS
  harvest      run the expedition: pull every raw source aboard (idempotent)
  cook         cook the raw harvest into corpus.tsv + the SOURCES.md ledger
  train        raise the librarian from the corpus
                 --steps N (60000)  --batch N (384)  --seed N (7)
                 --k N (6)  --dim-char N (32)  --hidden N (384)
                 --patience N (12; 0 runs to --steps)
                 --weight-path PATH  --curve-path PATH
  sample       pour souls from the weight
                 --region XX        ISO2, e.g. IT, IN, BR (omit for the world)
                 --type T           given | surname | fullname (given)
                                    fullname = one soul: region drawn once,
                                    real name order (family-first in CN/JP/KR/
                                    VN/HU and kin)
                 --gender G         M | F                      (weight priors)
                 --world W          archive | population | equal   (archive)
                 --origin O         name family, e.g. Sanskrit, Arabic
                 --count N (20)  --seed N (7)  --temperature T (0.9)
                 --weight PATH      a specific .safetensors
  world        pour a whole coherent world from one seed: settlements found
               themselves, families share names, Iceland runs its patronymic
               program (the seed cascade + the NAMING_PROGRAMS registry)
                 --seed N (7)  --settlements N (3)  --families N (3)
                 --souls N (4)  --world W (population)  --region XX (pin)
                 --drift-rate F (0.12)   founding drift; 0 pours still worlds
                 --generations N (1)     the years flow: lineages descend,
                                         patronymics mint from each parent
                 --children N (souls-1)  max children per parent
                 --gen-drift F (0.06)    drift between generations; stamped
                 --confluence N (0)      the herds meet: last N settlements
                                         founded by TWO roots, programs
                                         recombined, families per-root
                 --roots A,B             pin every confluence's pair
                 --promotions on|off     the watcher: accidents become law
                                         (initial-letter runs, the echo)
                 --temperature T (0.9)   calm cultures promote more traditions
                 --max-souls N (25000)   the growth guard: generations are
                                         exponential; --children 1 pours
                                         lineal DYNASTIES (20 gens = 20 souls)
                 --name X                pin the first family's founding name
                                         verbatim and watch it evolve
                 --wear F (0.08)         per-child surname weathering: cousins
                                         come to spell their ancestor apart
  bias         run the 30,000-soul microscope over a pour
                 --pours N (1000)  --per N (30)  --seed N (7)
                 --type T  --world W  --weight PATH
  frontier     find how weathered a world may be before its chains break
                 --rates "0,0.05,0.1"  --seeds N (5)  --region XX (GH)
                 --generations N (10)  --children N (2)  --families N (3)
                 (reports the whole curve; the threshold stays your call)
  gguf         pack a weight into the GGUF interchange envelope
                 --weight PATH (canonical)  --out PATH
                 (container, not chat-model: arch=wuddly; verified byte-true)
  completions  print the PowerShell tab-completion script
                 --install          write it beside the fleet and wire the profile

EXAMPLES
  wuddly sample --world population --count 15
  wuddly sample --origin Sanskrit --region IN --count 12 --seed 7
  wuddly sample --type surname --world equal --temperature 1.25
  wuddly bias --world population
  wuddly train

Same seed, same souls, forever. Docs: Cuddly/Documents/The Wuddly Weight.md
"""


def _completions_script() -> str:
    """Build the PowerShell completer, region list baked from the live weight."""
    regions: list[str] = []
    try:
        from wuddlies.model import load_model
        from wuddlies.train import WEIGHT_PATH
        regions = load_model(WEIGHT_PATH).regions
    except Exception as e:
        # Degrade gracefully (a completer without region names still
        # completes verbs and flags) but SAY SO: a silent swallow here
        # would ship a quietly poorer artifact and read as success, which
        # is the family's most expensive shape of bug.
        print(f"[desk] no regions baked in: {type(e).__name__} - {e}",
              file=sys.stderr)
    verbs = {
        "harvest": "pull every raw source aboard",
        "cook": "raw harvest -> corpus.tsv + ledger",
        "train": "raise the librarian",
        "sample": "pour souls from the weight",
        "world": "pour a whole coherent world from one seed",
        "bias": "run the 30k-soul microscope",
        "frontier": "find the weathering frontier",
        "gguf": "pack a weight into the GGUF envelope",
        "completions": "print or install this completer",
    }
    flags_world = ["--seed", "--settlements", "--families", "--souls",
                   "--world", "--region", "--drift-rate", "--generations",
                   "--children", "--gen-drift", "--confluence", "--roots",
                   "--promotions", "--temperature", "--max-souls", "--name",
                   "--wear", "--weight"]
    flags = {
        "train": ["--steps", "--batch", "--seed", "--k", "--dim-char",
                   "--hidden", "--patience", "--weight-path", "--curve-path"],
        "sample": ["--region", "--type", "--gender", "--count", "--seed",
                    "--temperature", "--weight", "--world", "--origin"],
        "bias": ["--pours", "--per", "--seed", "--type", "--weight", "--world"],
        "world": flags_world,
        "frontier": ["--rates", "--seeds", "--region", "--generations",
                      "--children", "--families", "--temperature", "--weight"],
        "gguf": ["--weight", "--out"],
        "completions": ["--install"],
    }
    def ps_list(items):
        return ",".join("'" + i.replace("'", "''") + "'" for i in items)
    verb_lines = ";".join(f"'{v}'='{d}'" for v, d in verbs.items())
    flag_lines = ";".join(f"'{v}'=@({ps_list(f)})" for v, f in flags.items())
    return f"""# -Intricate - bin/wuddly.completions.ps1 generated tab-completions for the naming desk
# -The last of the completion tables finished every word you began, For Enjoying
# -Built using a single shared braincell by Yours Truly and various Intelligences
#
# GENERATED file: regenerate with `wuddly completions --install` (regions are
# baked from the live weight at emit time).
Register-ArgumentCompleter -Native -CommandName wuddly -ScriptBlock {{
    param($wordToComplete, $commandAst, $cursorPosition)
    $verbs = @{{{verb_lines}}}
    $flags = @{{{flag_lines}}}
    $enums = @{{'--world'=@('archive','population','equal');
               '--type'=@('given','surname','fullname'); '--gender'=@('M','F')}}
    $regions = @({ps_list(regions)})
    $origins = @({ps_list(MARQUEE_ORIGINS)})
    $tokens = $commandAst.ToString() -split '\\s+' | Where-Object {{ $_ }}
    $prev = if ($tokens.Count -gt 1) {{ $tokens[-1 - [int][bool]$wordToComplete] }} else {{ '' }}
    $verb = ($tokens | Select-Object -Skip 1 | Where-Object {{ $_ -notlike '-*' }} | Select-Object -First 1)
    $out = if ($enums.ContainsKey($prev)) {{ $enums[$prev] }}
        elseif ($prev -eq '--region') {{ $regions }}
        elseif ($prev -eq '--origin') {{ $origins }}
        elseif ($verb -and $flags.ContainsKey($verb)) {{ $flags[$verb] }}
        else {{ $verbs.Keys }}
    $out | Where-Object {{ $_ -like "$wordToComplete*" }} | Sort-Object | ForEach-Object {{
        $tip = if ($verbs.ContainsKey($_)) {{ $verbs[$_] }} else {{ $_ }}
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $tip)
    }}
}}
"""


def _install_completions() -> None:
    script = _completions_script()
    bin_dir = Path(__file__).resolve().parents[2] / "_util" / "bin"
    target = bin_dir / "wuddly.completions.ps1"
    target.write_text(script, encoding="utf-8", newline="\n")
    print(f"[desk] completer written: {target}")
    profile = Path.home() / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    marker = "wuddly completions --install"
    line = f". \"{target}\"  # managed by `{marker}`"
    existing = profile.read_text(encoding="utf-8") if profile.exists() else ""
    if marker in existing:
        print(f"[desk] profile already wired: {profile}")
    else:
        profile.parent.mkdir(parents=True, exist_ok=True)
        with open(profile, "a", encoding="utf-8") as f:
            f.write(f"\n# Wuddlies completions\n{line}\n")
        print(f"[desk] profile wired: {profile} (new shells complete inline)")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="wuddly",
                                     description="The Wuddlies naming channel.")
    sub = parser.add_subparsers(dest="cmd", required=False)

    sub.add_parser("harvest", help="run the expedition: pull every raw source aboard")
    sub.add_parser("cook", help="cook the raw harvest into corpus.tsv")
    p_teach = sub.add_parser("teach", help="pour the sixth era's curriculum of invented cultures")
    p_teach.add_argument("--cultures", type=int, default=5000)
    p_teach.add_argument("--chains", type=int, default=5,
                         help="lineages poured per culture")
    p_teach.add_argument("--chain-len", type=int, default=5,
                         help="generations walked per lineage")
    p_teach.add_argument("--seed", type=int, default=7)
    p_teach.add_argument("--weight", default=None)
    p_front = sub.add_parser("frontier", help="find how weathered a world may be before its chains break")
    p_front.add_argument("--rates", default=None,
                         help='wear rates to sweep, e.g. "0,0.05,0.1,0.2"')
    p_front.add_argument("--seeds", type=int, default=5)
    p_front.add_argument("--region", default="GH")
    p_front.add_argument("--generations", type=int, default=10)
    p_front.add_argument("--children", type=int, default=2)
    p_front.add_argument("--families", type=int, default=3)
    p_front.add_argument("--temperature", type=float, default=0.9)
    p_front.add_argument("--weight", default=None)

    p_watch = sub.add_parser("longwatch", help="run one world for hundreds of generations")
    p_watch.add_argument("--generations", type=int, default=500)
    p_watch.add_argument("--population", type=int, default=80)
    p_watch.add_argument("--wear", type=float, default=0.08)
    p_watch.add_argument("--seed", type=int, default=1)
    p_watch.add_argument("--region", default="GH")
    p_watch.add_argument("--name", default=None, help="pin the founding name")
    p_watch.add_argument("--weight", default=None)

    p_gguf = sub.add_parser("gguf", help="pack a weight into the GGUF interchange envelope")
    p_gguf.add_argument("--weight", default=None, help="source .safetensors (default: canonical)")
    p_gguf.add_argument("--out", default=None, help="destination .gguf")
    p_comp = sub.add_parser("completions", help="print the PowerShell tab-completion script")
    p_comp.add_argument("--install", action="store_true",
                        help="write it beside the fleet and wire the profile")

    p_train = sub.add_parser("train", help="raise the librarian from the corpus")
    p_train.add_argument("--steps", type=int, default=60000)
    p_train.add_argument("--batch", type=int, default=384)
    p_train.add_argument("--seed", type=int, default=7)
    p_train.add_argument("--k", type=int, default=6, help="context window in characters")
    p_train.add_argument("--dim-char", type=int, default=32)
    p_train.add_argument("--hidden", type=int, default=384)
    p_train.add_argument("--patience", type=int, default=12,
                         help="stop after N evals without validation gain (0 = run to --steps)")
    p_train.add_argument("--weight-path", default=None, help="where to save the weight")
    p_train.add_argument("--curve-path", default=None, help="where to save the lab-notebook curve")
    p_train.add_argument("--lessons", action="store_true",
                         help="mix in the sixth era's culture curriculum (run teach first)")
    p_train.add_argument("--lesson-mix", type=float, default=0.35)

    p_world = sub.add_parser("world", help="pour a whole coherent world from one seed")
    p_world.add_argument("--seed", type=int, default=7)
    p_world.add_argument("--settlements", type=int, default=3)
    p_world.add_argument("--families", type=int, default=3)
    p_world.add_argument("--souls", type=int, default=4)
    p_world.add_argument("--world", default="population",
                         choices=("archive", "population", "equal"))
    p_world.add_argument("--region", default=None, help="pin every settlement to one region")
    p_world.add_argument("--drift-rate", type=float, default=None,
                         help="per-settlement founding drift chance (default 0.12; 0 = still)")
    p_world.add_argument("--generations", type=int, default=1,
                         help="how many generations flow beneath each founding (1)")
    p_world.add_argument("--children", type=int, default=None,
                         help="max children per parent (default: --souls minus one)")
    p_world.add_argument("--gen-drift", type=float, default=None,
                         help="per-generation drift chance (default 0.06; 0 = still years)")
    p_world.add_argument("--confluence", type=int, default=0,
                         help="found the last N settlements by two herds meeting")
    p_world.add_argument("--roots", default=None,
                         help="pin every confluence's pair, e.g. IN,CN")
    p_world.add_argument("--promotions", default="on", choices=("on", "off"),
                         help="the watcher that crystallizes accidents into law")
    p_world.add_argument("--temperature", type=float, default=0.9,
                         help="pour heat: calm cultures (0.65) promote more traditions")
    p_world.add_argument("--max-souls", type=int, default=25000,
                         help="warn above this projected size (0 = pour in silence)")
    p_world.add_argument("--name", default=None,
                         help="pin the first family's founding name verbatim, e.g. Thingaling")
    p_world.add_argument("--wear", type=float, default=None,
                         help="per-child surname weathering chance (default 0.08; 0 = names never wear)")
    p_world.add_argument("--weight", default=None)

    p_bias = sub.add_parser("bias", help="run the bias microscope over a large pour")
    p_bias.add_argument("--pours", type=int, default=1000)
    p_bias.add_argument("--per", type=int, default=30)
    p_bias.add_argument("--seed", type=int, default=7)
    p_bias.add_argument("--type", default="given", choices=("given", "surname"))
    p_bias.add_argument("--weight", default=None)
    p_bias.add_argument("--world", default="archive",
                        choices=("archive", "population", "equal"),
                        help="which world-mix preset to audit")

    p_sample = sub.add_parser("sample", help="pour souls from the weight")
    p_sample.add_argument("--region", default=None, help="ISO2 code, e.g. GB; omit for the world")
    p_sample.add_argument("--type", default="given",
                          choices=("given", "surname", "fullname", "full"))
    p_sample.add_argument("--gender", default=None, choices=(None, "M", "F"))
    p_sample.add_argument("--count", type=int, default=20)
    p_sample.add_argument("--seed", type=int, default=7)
    p_sample.add_argument("--temperature", type=float, default=0.9)
    p_sample.add_argument("--weight", default=None, help="path to a .safetensors weight")
    p_sample.add_argument("--world", default="archive",
                          choices=("archive", "population", "equal"),
                          help="cross-region mix when no --region is pinned")
    p_sample.add_argument("--origin", default=None,
                          help="name-level family axis, e.g. Sanskrit, Arabic, Germanic")
    p_sample.add_argument("--culture", default=None,
                          help="eight floats locating the pour in culture space, e.g. \"1,-1,0,0,0,0,0,0\"")
    p_sample.add_argument("--parent", default=None,
                          help="condition the dream on this parent's name (sixth-era weights)")

    args = parser.parse_args(argv)

    if not args.cmd:
        print(REGISTER)
        return 0

    if args.cmd == "frontier":
        import re as _re
        from wuddlies.frontier import DEFAULT_RATES, find_frontier
        from wuddlies.model import load_model
        from wuddlies.train import WEIGHT_PATH
        model = load_model(args.weight or WEIGHT_PATH)
        rates = (tuple(float(x) for x in _re.split(r"[,\s]+", args.rates) if x)
                 if args.rates else DEFAULT_RATES)
        find_frontier(model, rates=rates, seeds=args.seeds, region=args.region,
                      generations=args.generations, children=args.children,
                      families=args.families, temperature=args.temperature)
        return 0

    if args.cmd == "longwatch":
        from wuddlies.deeptime import watch
        from wuddlies.model import load_model
        from wuddlies.train import WEIGHT_PATH
        model = load_model(args.weight or WEIGHT_PATH)
        watch(model, generations=args.generations, population=args.population,
              wear_rate=args.wear, seed=args.seed, region=args.region,
              root=args.name)
        return 0

    if args.cmd == "gguf":
        from wuddlies.gguf_export import export_gguf, verify_gguf
        from wuddlies.train import WEIGHT_PATH
        src = args.weight or WEIGHT_PATH
        out = export_gguf(src, args.out)
        ok = verify_gguf(out, src)
        return 0 if ok else 1

    if args.cmd == "completions":
        if args.install:
            _install_completions()
        else:
            print(_completions_script())
        return 0

    if args.cmd == "harvest":
        from wuddlies.harvest import harvest_all
        harvest_all()
        return 0

    if args.cmd == "cook":
        from wuddlies.corpus import cook
        stats = cook()
        print(f"[kitchen] cooked {stats['rows']:,} rows "
              f"({stats['givens']:,} given, {stats['surnames']:,} surname) "
              f"across {stats['regions']} regions; "
              f"{stats['unique_chars']} unique characters")
        for src, n in stats["per_source"].items():
            print(f"[kitchen]   {src}: {n:,} rows")
        print(f"[kitchen] origin-tagged: {stats['origin_tagged']:,} rows across "
              f"{stats['distinct_origins']} origins; gender repaired: "
              f"{stats['gender_repaired']:,} rows")
        print(f"[kitchen] largest regions: "
              + ", ".join(f"{r} ({n:,})" for r, n in stats["top_regions"]))
        return 0

    if args.cmd == "teach":
        from wuddlies.model import load_model
        from wuddlies.teacher import teach
        from wuddlies.train import WEIGHT_PATH
        model = load_model(args.weight or WEIGHT_PATH)
        teach(model, cultures=args.cultures, chains=args.chains,
              chain_len=args.chain_len, seed=args.seed)
        return 0

    if args.cmd == "train":
        from wuddlies.train import train
        train(steps=args.steps, batch=args.batch, seed=args.seed,
              k=args.k, dim_char=args.dim_char, hidden=args.hidden,
              patience=args.patience, weight_path=args.weight_path,
              curve_path=args.curve_path, lessons=args.lessons,
              lesson_mix=args.lesson_mix)
        return 0

    if args.cmd == "world":
        from wuddlies.cascade import (DRIFT_RATE, GEN_DRIFT_RATE,
                                      TOKEN_WEAR_RATE, pour_world, print_world)
        from wuddlies.model import load_model
        from wuddlies.train import WEIGHT_PATH
        model = load_model(args.weight or WEIGHT_PATH)
        rate = DRIFT_RATE if args.drift_rate is None else args.drift_rate
        gen_rate = GEN_DRIFT_RATE if args.gen_drift is None else args.gen_drift
        # PowerShell reads A,B as its own array syntax and may deliver "A B";
        # accept comma or whitespace with equal grace (the tolerant-parse rule).
        roots = None
        if args.roots:
            import re
            parts = [p for p in re.split(r"[,\s]+", args.roots.upper()) if p]
            if len(parts) != 2:
                print(f"[desk] --roots wants exactly two regions, got: {parts}")
                return 2
            roots = (parts[0], parts[1])
        wear = TOKEN_WEAR_RATE if args.wear is None else args.wear
        census = pour_world(model, args.seed, settlements=args.settlements,
                            families=args.families, souls=args.souls,
                            world=args.world, region=args.region,
                            drift_rate=rate, generations=args.generations,
                            children_max=args.children,
                            gen_drift_rate=gen_rate,
                            confluences=args.confluence, roots=roots,
                            promotions_on=(args.promotions == "on"),
                            temperature=args.temperature,
                            max_souls=args.max_souls,
                            root_name=args.name, wear_rate=wear)
        print_world(census)
        return 0

    if args.cmd == "bias":
        from wuddlies.audit import run_bias_audit
        from wuddlies.model import load_model
        from wuddlies.train import WEIGHT_PATH
        model = load_model(args.weight or WEIGHT_PATH)
        run_bias_audit(model, pours=args.pours, per=args.per, seed=args.seed,
                       name_type=args.type, world=args.world)
        return 0

    if args.cmd == "sample":
        from wuddlies.model import load_model
        from wuddlies.train import WEIGHT_PATH
        model = load_model(args.weight or WEIGHT_PATH)
        rng = np.random.default_rng(args.seed)
        culture = None
        if args.culture:
            import re as _re
            culture = [float(x) for x in _re.split(r"[,\s]+", args.culture) if x]
        where = args.region or f"the world ({args.world})"
        label = "full names" if args.type == "fullname" else f"{args.type} names"
        print(f"[desk] {args.count} {label} from {where}, "
              f"seed {args.seed}, temperature {args.temperature}")
        for _ in range(args.count):
            if args.type == "fullname":
                print("   " + model.sample_fullname(rng, region=args.region,
                                                    gender=args.gender,
                                                    temperature=args.temperature,
                                                    world=args.world,
                                                    origin=args.origin))
            else:
                print("   " + model.sample_name(rng, region=args.region,
                                                name_type=args.type,
                                                gender=args.gender,
                                                temperature=args.temperature,
                                                world=args.world,
                                                origin=args.origin,
                                                culture=culture,
                                                parent=args.parent,
                                                max_len=32 if args.type == "full"
                                                else 24))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
