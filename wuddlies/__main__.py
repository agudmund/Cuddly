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

import numpy as np


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m wuddlies",
                                     description="The Wuddlies naming channel.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("cook", help="cook the raw harvest into corpus.tsv")

    p_train = sub.add_parser("train", help="raise the librarian from the corpus")
    p_train.add_argument("--steps", type=int, default=24000)
    p_train.add_argument("--batch", type=int, default=384)
    p_train.add_argument("--seed", type=int, default=7)
    p_train.add_argument("--k", type=int, default=4, help="context window in characters")
    p_train.add_argument("--dim-char", type=int, default=24)
    p_train.add_argument("--hidden", type=int, default=224)
    p_train.add_argument("--patience", type=int, default=0,
                         help="stop after N evals without validation gain (0 = run to --steps)")
    p_train.add_argument("--weight-path", default=None, help="where to save the weight")
    p_train.add_argument("--curve-path", default=None, help="where to save the lab-notebook curve")

    p_sample = sub.add_parser("sample", help="pour souls from the weight")
    p_sample.add_argument("--region", default=None, help="ISO2 code, e.g. GB; omit for the world")
    p_sample.add_argument("--type", default="given", choices=("given", "surname"))
    p_sample.add_argument("--gender", default=None, choices=(None, "M", "F"))
    p_sample.add_argument("--count", type=int, default=20)
    p_sample.add_argument("--seed", type=int, default=7)
    p_sample.add_argument("--temperature", type=float, default=0.9)
    p_sample.add_argument("--weight", default=None, help="path to a .safetensors weight")

    args = parser.parse_args(argv)

    if args.cmd == "cook":
        from wuddlies.corpus import cook
        stats = cook()
        print(f"[kitchen] cooked {stats['rows']:,} rows "
              f"({stats['givens']:,} given, {stats['surnames']:,} surname) "
              f"across {stats['regions']} regions; "
              f"{stats['unique_chars']} unique characters")
        print(f"[kitchen] largest regions: "
              + ", ".join(f"{r} ({n:,})" for r, n in stats["top_regions"]))
        return 0

    if args.cmd == "train":
        from wuddlies.train import train
        train(steps=args.steps, batch=args.batch, seed=args.seed,
              k=args.k, dim_char=args.dim_char, hidden=args.hidden,
              patience=args.patience, weight_path=args.weight_path,
              curve_path=args.curve_path)
        return 0

    if args.cmd == "sample":
        from wuddlies.model import load_model
        from wuddlies.train import WEIGHT_PATH
        model = load_model(args.weight or WEIGHT_PATH)
        rng = np.random.default_rng(args.seed)
        where = args.region or "the world"
        print(f"[desk] {args.count} {args.type} names from {where}, "
              f"seed {args.seed}, temperature {args.temperature}")
        for _ in range(args.count):
            print("   " + model.sample_name(rng, region=args.region,
                                            name_type=args.type,
                                            gender=args.gender,
                                            temperature=args.temperature))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
