#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/model.py the librarian: tiny conditioned char model + safetensors I/O
-The last of the librarians learnt every alphabet it was handed and held the whole craft in a few hundred kilobytes, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

A conditioned character-level MLP in pure numpy: no torch, no runtime
framework, nothing between the weight and the machine. Context window of K
characters plus region / type / gender embeddings, two tanh hidden layers,
softmax over the character vocabulary. Small enough to train in minutes
and to hand-port to C# later as a dependency-free forward pass.

Dimensions are per-model, carried in the weight file's own metadata, so a
half-megabyte v1 and a bigger laboratory sibling load through the same
door. The module constants below are only the defaults a new brain is
born with.

The weight travels as wuddly.safetensors, written and read by the minimal
safetensors implementation at the bottom (8-byte little-endian header
length, JSON header, raw tensor bytes): fully self-contained, needing
nothing but this file and numpy.

The sampler is deterministic by seed. The `condition` parameter is the
SOCKET for the dish: a vector of meaning-free floats reserved for wiring
by the schema's keeper; current weights carry no float-condition head yet
and honestly refuse rather than silently ignoring it.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

BOS = 0   # also the padding context before a name starts; never sampled
EOS = 1
CHAR_BASE = 2

K = 4               # default context window, in characters
DIM_CHAR = 24
DIM_REGION = 16
DIM_TYPE = 8
DIM_GENDER = 8
HIDDEN = 224

TYPES = ("given", "surname")
GENDERS = ("U", "M", "F")


class WuddlyModel:
    """The librarian's brain: parameters plus forward / backward / sample."""

    def __init__(self, chars: list[str], regions: list[str],
                 region_weights: list[float] | None = None,
                 gender_prior: list[float] | None = None,
                 rng: np.random.Generator | None = None,
                 k: int = K, dim_char: int = DIM_CHAR,
                 dim_region: int = DIM_REGION, dim_type: int = DIM_TYPE,
                 dim_gender: int = DIM_GENDER, hidden: int = HIDDEN):
        self.chars = list(chars)                      # index CHAR_BASE + i
        self.regions = list(regions)
        self.region_weights = list(region_weights or [1.0] * len(regions))
        self.gender_prior = list(gender_prior or [0.0, 0.5, 0.5])
        self.char_to_idx = {c: CHAR_BASE + i for i, c in enumerate(self.chars)}
        self.vocab = CHAR_BASE + len(self.chars)
        self.k, self.dim_char, self.dim_region = k, dim_char, dim_region
        self.dim_type, self.dim_gender, self.hidden = dim_type, dim_gender, hidden
        rng = rng or np.random.default_rng(0)

        v, r = self.vocab, len(self.regions)
        d_in = k * dim_char + dim_region + dim_type + dim_gender

        def init(*shape):
            return (rng.standard_normal(shape) * 0.08).astype(np.float32)

        self.p = {
            "Ec": init(v, dim_char),
            "Er": init(r, dim_region),
            "Et": init(len(TYPES), dim_type),
            "Eg": init(len(GENDERS), dim_gender),
            "W1": init(d_in, hidden), "b1": np.zeros(hidden, np.float32),
            "W2": init(hidden, hidden), "b2": np.zeros(hidden, np.float32),
            "W3": init(hidden, v), "b3": np.zeros(v, np.float32),
        }
        self._adam = {kk: (np.zeros_like(w), np.zeros_like(w)) for kk, w in self.p.items()}
        self._adam_t = 0

    def n_params(self) -> int:
        return sum(int(np.prod(t.shape)) for t in self.p.values())

    # ── forward ───────────────────────────────────────────────────────────

    def _input_vec(self, ctx, reg, typ, gen):
        b = ctx.shape[0]
        return np.concatenate([
            self.p["Ec"][ctx].reshape(b, self.k * self.dim_char),
            self.p["Er"][reg], self.p["Et"][typ], self.p["Eg"][gen],
        ], axis=1)

    def forward(self, ctx, reg, typ, gen):
        x = self._input_vec(ctx, reg, typ, gen)
        h1 = np.tanh(x @ self.p["W1"] + self.p["b1"])
        h2 = np.tanh(h1 @ self.p["W2"] + self.p["b2"])
        logits = h2 @ self.p["W3"] + self.p["b3"]
        return logits, (x, h1, h2)

    def eval_loss(self, ctx, reg, typ, gen, target, batch: int = 4096) -> float:
        """Mean cross-entropy over a fixed example set, no learning."""
        total, n = 0.0, ctx.shape[0]
        for s in range(0, n, batch):
            e = min(s + batch, n)
            logits, _ = self.forward(ctx[s:e], reg[s:e], typ[s:e], gen[s:e])
            logits -= logits.max(axis=1, keepdims=True)
            ex = np.exp(logits)
            probs = ex / ex.sum(axis=1, keepdims=True)
            total += float(-np.log(probs[np.arange(e - s), target[s:e]] + 1e-9).sum())
        return total / n

    # ── training ──────────────────────────────────────────────────────────

    def loss_and_step(self, ctx, reg, typ, gen, target, lr: float) -> float:
        """One cross-entropy training step with hand-rolled Adam. Returns loss."""
        b = ctx.shape[0]
        logits, (x, h1, h2) = self.forward(ctx, reg, typ, gen)
        logits -= logits.max(axis=1, keepdims=True)
        ex = np.exp(logits)
        probs = ex / ex.sum(axis=1, keepdims=True)
        loss = float(-np.log(probs[np.arange(b), target] + 1e-9).mean())

        dlogits = probs
        dlogits[np.arange(b), target] -= 1.0
        dlogits /= b

        g = {}
        g["W3"] = h2.T @ dlogits
        g["b3"] = dlogits.sum(axis=0)
        dh2 = dlogits @ self.p["W3"].T
        dz2 = dh2 * (1.0 - h2 * h2)
        g["W2"] = h1.T @ dz2
        g["b2"] = dz2.sum(axis=0)
        dh1 = dz2 @ self.p["W2"].T
        dz1 = dh1 * (1.0 - h1 * h1)
        g["W1"] = x.T @ dz1
        g["b1"] = dz1.sum(axis=0)
        dx = dz1 @ self.p["W1"].T

        kdc = self.k * self.dim_char
        dEc_flat = dx[:, :kdc].reshape(b, self.k, self.dim_char)
        g["Ec"] = np.zeros_like(self.p["Ec"])
        np.add.at(g["Ec"], ctx, dEc_flat)
        off = kdc
        g["Er"] = np.zeros_like(self.p["Er"])
        np.add.at(g["Er"], reg, dx[:, off:off + self.dim_region])
        off += self.dim_region
        g["Et"] = np.zeros_like(self.p["Et"])
        np.add.at(g["Et"], typ, dx[:, off:off + self.dim_type])
        off += self.dim_type
        g["Eg"] = np.zeros_like(self.p["Eg"])
        np.add.at(g["Eg"], gen, dx[:, off:off + self.dim_gender])

        self._adam_t += 1
        b1c = 1.0 - 0.9 ** self._adam_t
        b2c = 1.0 - 0.999 ** self._adam_t
        for kk, grad in g.items():
            m, v = self._adam[kk]
            m *= 0.9
            m += 0.1 * grad
            v *= 0.999
            v += 0.001 * grad * grad
            self.p[kk] -= (lr * (m / b1c) / (np.sqrt(v / b2c) + 1e-8)).astype(np.float32)
        return loss

    # ── sampling ──────────────────────────────────────────────────────────

    def sample_name(self, rng: np.random.Generator, region: str | None = None,
                    name_type: str = "given", gender: str | None = None,
                    temperature: float = 0.9, max_len: int = 24,
                    condition=None) -> str:
        """Draw one name. Deterministic for a given rng state and arguments."""
        if condition is not None:
            raise ValueError("current weights carry no float-condition head yet; "
                             "the socket is reserved for wiring in the dish")
        if region is None:
            w = np.asarray(self.region_weights, dtype=np.float64)
            reg_i = int(rng.choice(len(self.regions), p=w / w.sum()))
        else:
            reg_i = self.regions.index(region)
        typ_i = TYPES.index(name_type)
        if gender is None:
            if name_type == "given":
                gp = np.asarray(self.gender_prior, dtype=np.float64)
                gen_i = int(rng.choice(len(GENDERS), p=gp / gp.sum()))
            else:
                gen_i = 0
        else:
            gen_i = GENDERS.index(gender)

        ctx = [BOS] * self.k
        out = []
        for _ in range(max_len):
            logits, _ = self.forward(np.asarray([ctx], np.int32),
                                     np.asarray([reg_i]), np.asarray([typ_i]),
                                     np.asarray([gen_i]))
            z = logits[0].astype(np.float64) / max(temperature, 1e-4)
            z[BOS] = -np.inf
            if len(out) < 2:
                z[EOS] = -np.inf          # no soul gets a one-letter name
            z -= z.max()
            p = np.exp(z)
            p /= p.sum()
            nxt = int(rng.choice(self.vocab, p=p))
            if nxt == EOS:
                break
            out.append(self.chars[nxt - CHAR_BASE])
            ctx = ctx[1:] + [nxt]
        return "".join(out)


# ── minimal safetensors ───────────────────────────────────────────────────

def save_model(model: WuddlyModel, path: str | Path, extra_meta: dict | None = None) -> Path:
    """Write the model as a self-contained .safetensors file."""
    path = Path(path)
    meta = {
        "format": "wuddly-v1",
        "chars": json.dumps(model.chars, ensure_ascii=False),
        "regions": json.dumps(model.regions),
        "region_weights": json.dumps(model.region_weights),
        "gender_prior": json.dumps(model.gender_prior),
        "dims": json.dumps({"K": model.k, "char": model.dim_char,
                            "region": model.dim_region, "type": model.dim_type,
                            "gender": model.dim_gender, "hidden": model.hidden}),
    }
    for k, v in (extra_meta or {}).items():
        meta[k] = str(v)

    header: dict = {"__metadata__": meta}
    offset = 0
    blobs = []
    for name, tensor in model.p.items():
        t = np.ascontiguousarray(tensor, dtype=np.float32)
        blobs.append(t.tobytes())
        header[name] = {"dtype": "F32", "shape": list(t.shape),
                        "data_offsets": [offset, offset + len(blobs[-1])]}
        offset += len(blobs[-1])
    hjson = json.dumps(header, ensure_ascii=False).encode("utf-8")
    with open(path, "wb") as f:
        f.write(len(hjson).to_bytes(8, "little"))
        f.write(hjson)
        for b in blobs:
            f.write(b)
    return path


def load_model(path: str | Path) -> WuddlyModel:
    """Read a wuddly .safetensors file back into a live model."""
    raw = Path(path).read_bytes()
    hlen = int.from_bytes(raw[:8], "little")
    header = json.loads(raw[8:8 + hlen].decode("utf-8"))
    meta = header.pop("__metadata__")
    data = raw[8 + hlen:]
    dims = json.loads(meta.get("dims", "{}"))

    model = WuddlyModel(
        chars=json.loads(meta["chars"]),
        regions=json.loads(meta["regions"]),
        region_weights=json.loads(meta["region_weights"]),
        gender_prior=json.loads(meta["gender_prior"]),
        k=int(dims.get("K", K)), dim_char=int(dims.get("char", DIM_CHAR)),
        dim_region=int(dims.get("region", DIM_REGION)),
        dim_type=int(dims.get("type", DIM_TYPE)),
        dim_gender=int(dims.get("gender", DIM_GENDER)),
        hidden=int(dims.get("hidden", HIDDEN)),
    )
    for name, info in header.items():
        start, end = info["data_offsets"]
        arr = np.frombuffer(data[start:end], dtype=np.float32).reshape(info["shape"])
        model.p[name] = arr.copy()
    return model
