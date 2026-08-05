#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/gguf_export.py the interchange door
-The last of the export doors packed the whole librarian into one universal envelope, stamped for any machine that may ever ask, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

Exports a wuddly weight into GGUF: not to be RUN by llama.cpp (its compute
graphs speak transformer; our culture-socketed MLP is its own species) but
as the INTERCHANGE CONTAINER: one standardized, richly-typed binary that
GGUF readers in C, C++, C#, and Rust already parse, so every future port
(the Unity twin, an arbitrary DLL) reads one well-specified envelope
instead of our hand-rolled safetensors. Tensors travel under their own
names; the vocabulary, regions, origins, priors, richness, and even the
approximate-population table ride as properly typed metadata arrays
instead of JSON strings. Architecture is declared as "wuddly" so no
loader mistakes it for a chat model.

The safetensors stays the training-native working format; the GGUF is the
travel format, and the someday ggml-C port (the true run-anywhere rail,
already Vulkan-blessed on this machine) will read this same envelope.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from wuddlies.model import APPROX_POP_M, GENDERS, TYPES, WuddlyModel, load_model

GGUF_PATH = Path(__file__).parent / "data" / "wuddly.gguf"


def export_gguf(weight_path: str | Path, out_path: str | Path | None = None,
                progress=print) -> Path:
    import gguf

    model: WuddlyModel = load_model(weight_path)
    out_path = Path(out_path) if out_path else GGUF_PATH

    w = gguf.GGUFWriter(str(out_path), arch="wuddly")
    w.add_string("general.name", "The Wuddly Weight (the librarian)")
    w.add_string("general.license", "see Cuddly/Documents/The Wuddly Weight.md")
    w.add_string("wuddly.format", "wuddly-gguf-v1")
    w.add_uint32("wuddly.context_chars", model.k)
    w.add_uint32("wuddly.dim.char", model.dim_char)
    w.add_uint32("wuddly.dim.region", model.dim_region)
    w.add_uint32("wuddly.dim.type", model.dim_type)
    w.add_uint32("wuddly.dim.gender", model.dim_gender)
    w.add_uint32("wuddly.dim.origin", model.dim_origin)
    w.add_uint32("wuddly.hidden", model.hidden)
    w.add_array("wuddly.chars", model.chars)
    w.add_array("wuddly.types", list(TYPES))
    w.add_array("wuddly.genders", list(GENDERS))
    w.add_array("wuddly.regions", model.regions)
    w.add_array("wuddly.origins", model.origins)
    w.add_array("wuddly.region_weights",
                [float(x) for x in model.region_weights])
    w.add_array("wuddly.region_richness",
                [int(x) for x in model.region_richness])
    w.add_array("wuddly.gender_prior", [float(x) for x in model.gender_prior])
    pop_regions = list(APPROX_POP_M.keys())
    w.add_array("wuddly.population.regions", pop_regions)
    w.add_array("wuddly.population.millions",
                [float(APPROX_POP_M[r]) for r in pop_regions])

    for name, tensor in model.p.items():
        w.add_tensor(name, np.ascontiguousarray(tensor, dtype=np.float32))

    w.write_header_to_file()
    w.write_kv_data_to_file()
    w.write_tensors_to_file()
    w.close()
    progress(f"[envelope] wrote {out_path.name} "
             f"({out_path.stat().st_size:,} bytes, "
             f"{len(model.p)} tensors, arch=wuddly)")
    return out_path


def _field(reader, key):
    """One metadata field's value, tolerant across gguf-py vintages."""
    f = reader.fields.get(key)
    if f is None:
        return None
    if hasattr(f, "contents"):
        return f.contents()
    # Older vintages: decode parts by type manually (arrays of str/num).
    vals = [f.parts[i] for i in f.data]
    out = []
    for v in vals:
        out.append(bytes(v).decode("utf-8") if v.dtype == np.uint8
                   else v.item() if v.size == 1 else v.tolist())
    return out if len(out) != 1 else out[0]


def load_gguf(gguf_path: str | Path) -> WuddlyModel:
    """Reconstruct the living librarian from the envelope ALONE: the exact
    operation every port performs, exercised here in the home language."""
    import gguf

    reader = gguf.GGUFReader(str(gguf_path))
    model = WuddlyModel(
        chars=list(_field(reader, "wuddly.chars")),
        regions=list(_field(reader, "wuddly.regions")),
        region_weights=[float(x) for x in _field(reader, "wuddly.region_weights")],
        region_richness=[int(x) for x in _field(reader, "wuddly.region_richness")],
        gender_prior=[float(x) for x in _field(reader, "wuddly.gender_prior")],
        origins=list(_field(reader, "wuddly.origins")),
        k=int(_field(reader, "wuddly.context_chars")),
        dim_char=int(_field(reader, "wuddly.dim.char")),
        dim_region=int(_field(reader, "wuddly.dim.region")),
        dim_type=int(_field(reader, "wuddly.dim.type")),
        dim_gender=int(_field(reader, "wuddly.dim.gender")),
        dim_origin=int(_field(reader, "wuddly.dim.origin")),
        hidden=int(_field(reader, "wuddly.hidden")),
    )
    for t in reader.tensors:
        model.p[t.name] = np.asarray(t.data, dtype=np.float32).reshape(
            model.p[t.name].shape).copy()
    return model


def verify_gguf(gguf_path: str | Path, weight_path: str | Path,
                progress=print) -> bool:
    """Round-trip proof: read the envelope back and compare every tensor
    byte-for-byte against the living model. A port that parses this file
    holds exactly the librarian."""
    import gguf

    model = load_model(weight_path)
    reader = gguf.GGUFReader(str(gguf_path))
    got = {t.name: t for t in reader.tensors}
    for name, tensor in model.p.items():
        if name not in got:
            progress(f"[envelope] MISSING tensor {name}")
            return False
        back = np.asarray(got[name].data).reshape(tensor.shape)
        if not np.array_equal(back.astype(np.float32),
                              tensor.astype(np.float32)):
            progress(f"[envelope] MISMATCH in {name}")
            return False
    progress(f"[envelope] verified: {len(model.p)} tensors round-trip "
             f"byte-true; {len(reader.fields)} metadata fields aboard")
    return True
