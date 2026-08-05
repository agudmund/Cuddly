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
DIM_TYPE = 16       # widened at the fifth schooling against type lane-bleed
DIM_GENDER = 8
DIM_ORIGIN = 12     # the name-level family axis (Arabic, Sanskrit, Germanic...)
HIDDEN = 224

TYPES = ("given", "surname", "full")   # "full" arrived with the sixth era
GENDERS = ("U", "M", "F")

# The sixth era's two senses: the culture socket (eight meaning-free floats,
# the dish's condition input finally alive) and parent-name pooling (the
# parent's characters averaged into one vector, so patronymic assembly can
# be DREAMT rather than coded).
DIM_CULTURE = 8
CULT_PROJ = 16
PAR_PROJ = 16

# ── the world-mix presets (the fourth floor) ──────────────────────────────
# Fair versus realistic is a FLAG, never a training choice: the weight
# learns each region's internal distribution truthfully, and these presets
# only decide the cross-region mix at pour time.
#   archive     the corpus as it honestly is (damped source mass)
#   population  soft-proportional to real population, clamped so no giant
#               dominates, scaled by data richness so thin regions are
#               never hammered into repetition
#   equal       every sufficiently-fed region gets an equal voice (the v1
#               stand-in for Grok's equal-language-family target, which
#               arrives with the family-axis floor)
WORLD_MODES = ("archive", "population", "equal")

# Regions whose real-world convention writes the family name first. A small
# honest set (the convention-genesis floor will one day make this emergent);
# everywhere else pours given-first.
FAMILY_FIRST_REGIONS = frozenset({"CN", "JP", "KR", "TW", "HK", "VN", "HU",
                                  "MN", "KH"})
RICHNESS_FLOOR = 50      # unique names a region needs for a full voice
POP_CLAMP = 0.12         # no region may exceed this share in population mode
POP_ABSENT = 0.002       # nominal share for regions missing from the table

# Approximate populations in millions, mid-2020s. REFERENCE-GRADE ONLY: it
# steers a pour preset and flags audit deltas, never poses as a data source.
# Baked into the weight's metadata so the file stays self-contained.
APPROX_POP_M = {
    "CN": 1425, "IN": 1440, "US": 342, "ID": 284, "PK": 245, "NG": 229,
    "BR": 217, "BD": 174, "RU": 144, "MX": 130, "ET": 129, "JP": 123,
    "PH": 119, "EG": 116, "VN": 100, "CD": 102, "IR": 91, "TR": 87,
    "DE": 84, "TH": 72, "GB": 68, "TZ": 68, "FR": 66, "ZA": 63, "IT": 59,
    "KE": 56, "MM": 54, "KR": 52, "CO": 52, "SD": 49, "UG": 48, "ES": 48,
    "AR": 46, "DZ": 46, "IQ": 46, "AF": 42, "CA": 39, "MA": 38, "PL": 37,
    "UA": 37, "AO": 36, "UZ": 35, "MY": 34, "PE": 34, "GH": 34, "YE": 34,
    "SA": 33, "MZ": 33, "NP": 31, "MG": 30, "CI": 29, "CM": 29, "VE": 28,
    "NE": 27, "AU": 26, "TW": 23, "ML": 23, "BF": 23, "SY": 23, "LK": 22,
    "KZ": 20, "CL": 20, "RO": 19, "EC": 18, "GT": 18, "SN": 18, "NL": 18,
    "TD": 18, "SO": 18, "KH": 17, "ZW": 16, "GN": 14, "RW": 14, "BJ": 14,
    "TN": 12, "BE": 12, "JO": 11, "CU": 11, "HT": 12, "BO": 12, "DO": 11,
    "SS": 11, "AZ": 10, "SE": 11, "HU": 10, "GR": 10, "PT": 10, "CZ": 11,
    "IL": 10, "AE": 10, "TJ": 10, "PG": 10, "AT": 9, "CH": 9, "TG": 9,
    "HN": 10, "HK": 8, "LA": 8, "LY": 7, "PY": 7, "KG": 7, "NI": 7,
    "RS": 7, "TM": 7, "BG": 6, "LB": 6, "DK": 6, "FI": 6, "SG": 6,
    "NO": 6, "SK": 5, "PS": 5, "IE": 5, "OM": 5, "CR": 5, "NZ": 5,
    "KW": 4, "HR": 4, "GE": 4, "UY": 3, "BA": 3, "AM": 3, "AL": 3,
    "MD": 3, "LT": 3, "QA": 3, "MK": 2, "SI": 2, "LV": 2, "BH": 2,
    "EE": 1, "CY": 1, "ME": 0.6, "LU": 0.7, "MT": 0.5, "IS": 0.4,
}


class WuddlyModel:
    """The librarian's brain: parameters plus forward / backward / sample."""

    def __init__(self, chars: list[str], regions: list[str],
                 region_weights: list[float] | None = None,
                 gender_prior: list[float] | None = None,
                 rng: np.random.Generator | None = None,
                 k: int = K, dim_char: int = DIM_CHAR,
                 dim_region: int = DIM_REGION, dim_type: int = DIM_TYPE,
                 dim_gender: int = DIM_GENDER, hidden: int = HIDDEN,
                 region_richness: list[int] | None = None,
                 origins: list[str] | None = None,
                 dim_origin: int = DIM_ORIGIN):
        self.chars = list(chars)                      # index CHAR_BASE + i
        self.regions = list(regions)
        self.origins = list(origins or [""])          # index 0 = untagged
        self.region_weights = list(region_weights or [1.0] * len(regions))
        self.gender_prior = list(gender_prior or [0.0, 0.5, 0.5])
        self.region_richness = list(region_richness or [0] * len(regions))
        self.char_to_idx = {c: CHAR_BASE + i for i, c in enumerate(self.chars)}
        self.vocab = CHAR_BASE + len(self.chars)
        self.k, self.dim_char, self.dim_region = k, dim_char, dim_region
        self.dim_type, self.dim_gender, self.hidden = dim_type, dim_gender, hidden
        self.dim_origin = dim_origin
        rng = rng or np.random.default_rng(0)

        v, r = self.vocab, len(self.regions)
        d_in = (k * dim_char + dim_region + dim_type + dim_gender + dim_origin
                + CULT_PROJ + PAR_PROJ)

        def init(*shape):
            return (rng.standard_normal(shape) * 0.08).astype(np.float32)

        self.p = {
            "Ec": init(v, dim_char),
            "Er": init(r, dim_region),
            "Et": init(len(TYPES), dim_type),
            "Eg": init(len(GENDERS), dim_gender),
            "Eo": init(len(self.origins), dim_origin),
            "Wc": init(DIM_CULTURE, CULT_PROJ),
            "Wp": init(dim_char, PAR_PROJ),
            "W1": init(d_in, hidden), "b1": np.zeros(hidden, np.float32),
            "W2": init(hidden, hidden), "b2": np.zeros(hidden, np.float32),
            "W3": init(hidden, v), "b3": np.zeros(v, np.float32),
        }
        self._adam = {kk: (np.zeros_like(w), np.zeros_like(w)) for kk, w in self.p.items()}
        self._adam_t = 0

    def n_params(self) -> int:
        return sum(int(np.prod(t.shape)) for t in self.p.values())

    # ── forward ───────────────────────────────────────────────────────────

    def _parent_pool(self, pidx, plen):
        """Mean of the parent name's char embeddings; zeros when no parent."""
        emb = self.p["Ec"][pidx]                       # (B, P, dc)
        mask = (pidx > 0)[..., None]                   # pad index 0 masked out
        summed = (emb * mask).sum(axis=1)
        return summed / np.maximum(plen, 1)[:, None]

    def _input_vec(self, ctx, reg, typ, gen, ori, cul=None, pidx=None,
                   plen=None):
        b = ctx.shape[0]
        if cul is None:
            cul = np.zeros((b, DIM_CULTURE), np.float32)
        if pidx is None:
            pool = np.zeros((b, self.dim_char), np.float32)
        else:
            pool = self._parent_pool(pidx, plen)
        return np.concatenate([
            self.p["Ec"][ctx].reshape(b, self.k * self.dim_char),
            self.p["Er"][reg], self.p["Et"][typ], self.p["Eg"][gen],
            self.p["Eo"][ori],
            cul @ self.p["Wc"], pool @ self.p["Wp"],
        ], axis=1)

    def forward(self, ctx, reg, typ, gen, ori, cul=None, pidx=None, plen=None):
        x = self._input_vec(ctx, reg, typ, gen, ori, cul, pidx, plen)
        h1 = np.tanh(x @ self.p["W1"] + self.p["b1"])
        h2 = np.tanh(h1 @ self.p["W2"] + self.p["b2"])
        logits = h2 @ self.p["W3"] + self.p["b3"]
        return logits, (x, h1, h2)

    def eval_loss(self, ctx, reg, typ, gen, ori, target, batch: int = 4096,
                  cul=None, pidx=None, plen=None) -> float:
        """Mean cross-entropy over a fixed example set, no learning."""
        total, n = 0.0, ctx.shape[0]
        for s in range(0, n, batch):
            e = min(s + batch, n)
            logits, _ = self.forward(
                ctx[s:e], reg[s:e], typ[s:e], gen[s:e], ori[s:e],
                None if cul is None else cul[s:e],
                None if pidx is None else pidx[s:e],
                None if plen is None else plen[s:e])
            logits -= logits.max(axis=1, keepdims=True)
            ex = np.exp(logits)
            probs = ex / ex.sum(axis=1, keepdims=True)
            total += float(-np.log(probs[np.arange(e - s), target[s:e]] + 1e-9).sum())
        return total / n

    # ── training ──────────────────────────────────────────────────────────

    def loss_and_step(self, ctx, reg, typ, gen, ori, target, lr: float,
                      cul=None, pidx=None, plen=None) -> float:
        """One cross-entropy training step with hand-rolled Adam. Returns loss."""
        b = ctx.shape[0]
        if cul is None:
            cul = np.zeros((b, DIM_CULTURE), np.float32)
        pool = (self._parent_pool(pidx, plen) if pidx is not None
                else np.zeros((b, self.dim_char), np.float32))
        logits, (x, h1, h2) = self.forward(ctx, reg, typ, gen, ori, cul,
                                           pidx, plen)
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
        off += self.dim_gender
        g["Eo"] = np.zeros_like(self.p["Eo"])
        np.add.at(g["Eo"], ori, dx[:, off:off + self.dim_origin])
        off += self.dim_origin
        dx_c = dx[:, off:off + CULT_PROJ]
        g["Wc"] = cul.T.astype(np.float32) @ dx_c
        off += CULT_PROJ
        dx_p = dx[:, off:off + PAR_PROJ]
        g["Wp"] = pool.T.astype(np.float32) @ dx_p
        if pidx is not None:
            dpool = (dx_p @ self.p["Wp"].T) / np.maximum(plen, 1)[:, None]
            mask = (pidx > 0)[..., None]
            np.add.at(g["Ec"], pidx, dpool[:, None, :] * mask)

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

    def region_draw_weights(self, world: str = "archive") -> np.ndarray:
        """The cross-region mix for a world preset, normalised to sum 1."""
        if world not in WORLD_MODES:
            raise ValueError(f"unknown world mode '{world}' (choose from {WORLD_MODES})")
        rich = np.asarray(self.region_richness, dtype=np.float64)
        voice = np.minimum(1.0, rich / RICHNESS_FLOOR)     # thin regions speak softly
        if world == "archive":
            w = np.asarray(self.region_weights, dtype=np.float64)
        elif world == "equal":
            w = voice.copy()
        else:  # population
            pop = np.asarray([APPROX_POP_M.get(r, 0.0) for r in self.regions])
            share = np.where(pop > 0, pop / max(pop.sum(), 1e-9), POP_ABSENT)
            w = np.minimum(share, POP_CLAMP) * voice
        total = w.sum()
        if total <= 0:
            w = np.ones(len(self.regions), dtype=np.float64)
            total = w.sum()
        return w / total

    def sample_name(self, rng: np.random.Generator, region: str | None = None,
                    name_type: str = "given", gender: str | None = None,
                    temperature: float = 0.9, max_len: int = 24,
                    condition=None, return_details: bool = False,
                    world: str = "archive", origin: str | None = None,
                    culture=None, parent: str | None = None):
        """Draw one name. Deterministic for a given rng state and arguments.
        With return_details, returns (name, region, gender) so an audit can
        see which region and gender each draw actually used. The `world`
        preset decides the cross-region mix when no region is pinned; the
        `origin` axis (Arabic, Sanskrit, Germanic, ...) is opt-in and rides
        alongside region rather than replacing it. Since the sixth era the
        socket is ALIVE: `culture` (eight floats; `condition` accepted as
        its older name) locates the pour in the learned culture space, and
        `parent` conditions patronymic dreaming on an actual name."""
        culture = condition if condition is not None else culture
        if name_type == "full" and self.p["Et"].shape[0] < len(TYPES):
            raise ValueError("this weight predates the sixth era and cannot "
                             "pour full names neurally; re-school it")
        cul = None
        if culture is not None:
            cul = np.asarray(culture, dtype=np.float32).reshape(1, DIM_CULTURE)
        pidx = plen = None
        if parent:
            ids = [self.char_to_idx[c] for c in parent[:20]
                   if c in self.char_to_idx]
            if ids:
                pidx = np.zeros((1, 20), np.int32)
                pidx[0, :len(ids)] = ids
                plen = np.asarray([len(ids)])
        if region is None:
            w = self.region_draw_weights(world)
            reg_i = int(rng.choice(len(self.regions), p=w))
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
        ori_i = self.origins.index(origin) if origin else 0

        ctx = [BOS] * self.k
        out = []
        for _ in range(max_len):
            logits, _ = self.forward(np.asarray([ctx], np.int32),
                                     np.asarray([reg_i]), np.asarray([typ_i]),
                                     np.asarray([gen_i]), np.asarray([ori_i]),
                                     cul, pidx, plen)
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
        name = "".join(out)
        if return_details:
            return name, self.regions[reg_i], GENDERS[gen_i]
        return name

    def sample_fullname(self, rng: np.random.Generator, region: str | None = None,
                        gender: str | None = None, temperature: float = 0.9,
                        world: str = "archive", origin: str | None = None,
                        return_details: bool = False):
        """Pour one whole soul: region drawn once, given and surname both born
        there, joined in the region's real name order (family-first where that
        is the living convention). Deterministic like everything else."""
        if region is None:
            w = self.region_draw_weights(world)
            region = self.regions[int(rng.choice(len(self.regions), p=w))]
        given, _, g = self.sample_name(rng, region=region, name_type="given",
                                       gender=gender, temperature=temperature,
                                       origin=origin, return_details=True)
        surname = self.sample_name(rng, region=region, name_type="surname",
                                   temperature=temperature, origin=origin)
        full = (f"{surname} {given}" if region in FAMILY_FIRST_REGIONS
                else f"{given} {surname}")
        if return_details:
            return full, region, g
        return full


# ── minimal safetensors ───────────────────────────────────────────────────

def save_model(model: WuddlyModel, path: str | Path, extra_meta: dict | None = None) -> Path:
    """Write the model as a self-contained .safetensors file."""
    path = Path(path)
    meta = {
        "format": "wuddly-v1",
        "chars": json.dumps(model.chars, ensure_ascii=False),
        "regions": json.dumps(model.regions),
        "region_weights": json.dumps(model.region_weights),
        "region_richness": json.dumps(model.region_richness),
        "gender_prior": json.dumps(model.gender_prior),
        "origins": json.dumps(model.origins, ensure_ascii=False),
        "dims": json.dumps({"K": model.k, "char": model.dim_char,
                            "region": model.dim_region, "type": model.dim_type,
                            "gender": model.dim_gender, "hidden": model.hidden,
                            "origin": model.dim_origin}),
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
        region_richness=json.loads(meta.get("region_richness", "[]")) or None,
        gender_prior=json.loads(meta["gender_prior"]),
        origins=json.loads(meta.get("origins", '[""]')),
        k=int(dims.get("K", K)), dim_char=int(dims.get("char", DIM_CHAR)),
        dim_region=int(dims.get("region", DIM_REGION)),
        dim_type=int(dims.get("type", DIM_TYPE)),
        dim_gender=int(dims.get("gender", DIM_GENDER)),
        dim_origin=int(dims.get("origin", DIM_ORIGIN)),
        hidden=int(dims.get("hidden", HIDDEN)),
    )
    for name, info in header.items():
        start, end = info["data_offsets"]
        arr = np.frombuffer(data[start:end], dtype=np.float32).reshape(info["shape"])
        model.p[name] = arr.copy()
    return model
