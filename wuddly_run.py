#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddly_run.py the friend kit: one file, one envelope, whole worlds
-The last of the travel kits fit a civilization in one pocket and asked for nothing but numpy on arrival, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

The standalone runner for a wuddly GGUF envelope. No repo, no package,
no framework: just this file, the .gguf beside it, and:

    pip install numpy gguf

    python wuddly_run.py wuddly6.gguf
    python wuddly_run.py wuddly6.gguf --region IT --count 10
    python wuddly_run.py wuddly6.gguf --type surname --world population
    python wuddly_run.py wuddly6.gguf --type full --parent Amara --culture "-1,1,0,0,0,0,0,0"
    python wuddly_run.py wuddly6.gguf --list regions

Same seed, same souls, forever, on any machine.

THE ENVELOPE CONTRACT (so this file doubles as the format's reference):
a GGUF with general.architecture == "wuddly" carrying float32 tensors
Ec (char embeddings; token 0 is the pre-name pad, 1 is end-of-name, real
characters begin at index 2), Er/Et/Eg/Eo (region/type/gender/origin
embeddings), Wc (8-float culture projection), Wp (parent-name pooling
projection), and the MLP W1/b1/W2/b2/W3/b3. Metadata arrays carry the
character vocabulary, regions, origins, sampler priors, per-region data
richness, and an approximate population table. The forward pass: last K
character embeddings, concatenated with the condition embeddings, the
projected culture floats, and the mean-pooled parent-name embedding,
through two tanh layers to logits over the vocabulary.
"""

import argparse
import re
import sys

import numpy as np

BOS, EOS, CHAR_BASE = 0, 1, 2
TYPES = ("given", "surname", "full")
GENDERS = ("U", "M", "F")
DIM_CULTURE = 8
RICHNESS_FLOOR = 50
POP_CLAMP = 0.12
POP_ABSENT = 0.002


def _field(reader, key):
    f = reader.fields.get(key)
    if f is None:
        return None
    if hasattr(f, "contents"):
        return f.contents()
    vals = [f.parts[i] for i in f.data]
    out = [bytes(v).decode("utf-8") if v.dtype == np.uint8
           else v.item() if v.size == 1 else v.tolist() for v in vals]
    return out if len(out) != 1 else out[0]


class Wuddly:
    def __init__(self, gguf_path: str):
        import gguf
        r = gguf.GGUFReader(gguf_path)
        self.chars = list(_field(r, "wuddly.chars"))
        self.regions = list(_field(r, "wuddly.regions"))
        self.origins = list(_field(r, "wuddly.origins"))
        self.region_weights = np.asarray(_field(r, "wuddly.region_weights"),
                                         dtype=np.float64)
        self.richness = np.asarray(_field(r, "wuddly.region_richness"),
                                   dtype=np.float64)
        self.gender_prior = np.asarray(_field(r, "wuddly.gender_prior"),
                                       dtype=np.float64)
        self.k = int(_field(r, "wuddly.context_chars"))
        self.dim_char = int(_field(r, "wuddly.dim.char"))
        pop_r = list(_field(r, "wuddly.population.regions"))
        pop_m = list(_field(r, "wuddly.population.millions"))
        self.population = dict(zip(pop_r, [float(x) for x in pop_m]))
        self.char_to_idx = {c: CHAR_BASE + i for i, c in enumerate(self.chars)}
        self.p = {}
        for t in r.tensors:
            arr = np.asarray(t.data, dtype=np.float32)
            shape = tuple(int(d) for d in t.shape)
            self.p[t.name] = arr.reshape(shape) if arr.shape != shape else arr
        # Orientation self-check: W1's columns must equal b1's width (GGUF
        # and numpy disagree on dimension order in some reader vintages).
        if self.p["W1"].shape[1] != self.p["b1"].size:
            for name in ("W1", "W2", "W3", "Wc", "Wp", "Ec", "Er", "Et",
                          "Eg", "Eo"):
                if self.p[name].ndim == 2:
                    self.p[name] = self.p[name].reshape(
                        self.p[name].shape[::-1])

    # ── the forward pass, whole ───────────────────────────────────────────
    def _forward(self, ctx, reg_i, typ_i, gen_i, ori_i, cul, pool):
        x = np.concatenate([
            self.p["Ec"][ctx].reshape(1, self.k * self.dim_char),
            self.p["Er"][[reg_i]], self.p["Et"][[typ_i]],
            self.p["Eg"][[gen_i]], self.p["Eo"][[ori_i]],
            cul @ self.p["Wc"], pool @ self.p["Wp"],
        ], axis=1)
        h1 = np.tanh(x @ self.p["W1"] + self.p["b1"])
        h2 = np.tanh(h1 @ self.p["W2"] + self.p["b2"])
        return h2 @ self.p["W3"] + self.p["b3"]

    def world_weights(self, world: str) -> np.ndarray:
        voice = np.minimum(1.0, self.richness / RICHNESS_FLOOR)
        if world == "archive":
            w = self.region_weights.copy()
        elif world == "equal":
            w = voice.copy()
        else:
            pop = np.asarray([self.population.get(r, 0.0)
                              for r in self.regions])
            share = np.where(pop > 0, pop / max(pop.sum(), 1e-9), POP_ABSENT)
            w = np.minimum(share, POP_CLAMP) * voice
        return w / max(w.sum(), 1e-9)

    def sample(self, rng, region=None, name_type="given", gender=None,
               world="archive", origin=None, culture=None, parent=None,
               temperature=0.9, max_len=32):
        if region is None:
            w = self.world_weights(world)
            reg_i = int(rng.choice(len(self.regions), p=w))
        else:
            reg_i = self.regions.index(region)
        typ_i = TYPES.index(name_type)
        if typ_i >= self.p["Et"].shape[0]:
            raise SystemExit("this envelope predates full-name dreaming")
        if gender is None and name_type == "given":
            gp = self.gender_prior / max(self.gender_prior.sum(), 1e-9)
            gen_i = int(rng.choice(len(GENDERS), p=gp))
        else:
            gen_i = GENDERS.index(gender) if gender else 0
        ori_i = self.origins.index(origin) if origin else 0
        cul = (np.asarray(culture, np.float32).reshape(1, DIM_CULTURE)
               if culture is not None else np.zeros((1, DIM_CULTURE), np.float32))
        if parent:
            ids = [self.char_to_idx[c] for c in parent[:20]
                   if c in self.char_to_idx]
            pool = (self.p["Ec"][ids].mean(axis=0, keepdims=True)
                    if ids else np.zeros((1, self.dim_char), np.float32))
        else:
            pool = np.zeros((1, self.dim_char), np.float32)

        ctx = [BOS] * self.k
        out = []
        vocab = CHAR_BASE + len(self.chars)
        for _ in range(max_len):
            z = self._forward(np.asarray([ctx]), reg_i, typ_i, gen_i, ori_i,
                              cul, pool)[0].astype(np.float64)
            z /= max(temperature, 1e-4)
            z[BOS] = -np.inf
            if len(out) < 2:
                z[EOS] = -np.inf
            z -= z.max()
            prob = np.exp(z)
            prob /= prob.sum()
            nxt = int(rng.choice(vocab, p=prob))
            if nxt == EOS:
                break
            out.append(self.chars[nxt - CHAR_BASE])
            ctx = ctx[1:] + [nxt]
        return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="wuddly_run.py",
        description="Pour names from a wuddly GGUF envelope. Same seed, "
                    "same souls, forever.")
    ap.add_argument("model", help="path to the .gguf envelope")
    ap.add_argument("--type", default="given", choices=TYPES)
    ap.add_argument("--region", default=None, help="ISO2 code, e.g. IT")
    ap.add_argument("--gender", default=None, choices=(None, "M", "F"))
    ap.add_argument("--world", default="archive",
                    choices=("archive", "population", "equal"))
    ap.add_argument("--origin", default=None,
                    help="name family, e.g. Sanskrit, Arabic")
    ap.add_argument("--culture", default=None,
                    help='eight floats, e.g. "-1,1,0,0,0,0,0,0"')
    ap.add_argument("--parent", default=None,
                    help="condition the dream on this name (full-type envelopes)")
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--temperature", type=float, default=0.9)
    ap.add_argument("--list", default=None, choices=(None, "regions", "origins"),
                    help="print what the envelope knows, then exit")
    args = ap.parse_args()

    m = Wuddly(args.model)
    if args.list == "regions":
        print(" ".join(m.regions))
        return 0
    if args.list == "origins":
        print(" | ".join(o for o in m.origins if o))
        return 0

    culture = None
    if args.culture:
        culture = [float(x) for x in re.split(r"[,\s]+", args.culture) if x]
    rng = np.random.default_rng(args.seed)
    where = args.region or f"the world ({args.world})"
    print(f"[wuddly] {args.count} {args.type} names from {where}, "
          f"seed {args.seed}")
    for _ in range(args.count):
        print("   " + m.sample(rng, region=args.region, name_type=args.type,
                               gender=args.gender, world=args.world,
                               origin=args.origin, culture=culture,
                               parent=args.parent,
                               temperature=args.temperature))
    return 0


if __name__ == "__main__":
    sys.exit(main())
