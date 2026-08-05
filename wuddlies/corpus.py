#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/corpus.py the corpus kitchen
-The last of the corpus kitchens washed every name the world actually uses and kept the counts that made them true, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

Cooks the harvested raw sources into one faithful corpus file. Faithful
means: every script kept as-is, casing normalised only where a source
shouts in ALL CAPS (census habits), and the real counts carried whole.
Filtering for what a given model can chew stays the MODEL's concern
(train.py); the kitchen never seasons away the world's diversity.

Since the second harvest the kitchen is a dispatcher of ADAPTERS, one per
source shape (the family pattern arriving on schedule): each adapter reads
its raw shelf and yields (name, type, region, gender, count) rows, plus a
provenance note. A missing shelf is contextual absence: reported, skipped,
never fatal. The kitchen writes two artifacts: corpus.tsv (the faithful
rows) and SOURCES.md (the provenance ledger: license, coverage, and the
bias each source is known to carry, stated rather than hidden).

Cross-source scale note, recorded honestly: census counts and
notable-person counts are not the same unit. Within a region they mix
under the trainer's count**0.5 damping, which softens the mismatch; the
ledger says so, and a finer per-source calibration is a later floor.
"""

from __future__ import annotations

import csv
import datetime as _dt
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
RAW_DIR = DATA_DIR / "raw"
CORPUS_PATH = DATA_DIR / "corpus.tsv"
SOURCES_PATH = DATA_DIR / "SOURCES.md"


def _uncap(name: str) -> str:
    """Census files shout; give SMITH back its indoor voice as Smith."""
    return name.title() if name.isupper() else name


# ── adapters ──────────────────────────────────────────────────────────────

def _read_onomaverse(name_type: str, filename: str):
    path = RAW_DIR / "onomaverse" / filename
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip()
            region = (row.get("country_code") or "").strip().upper()
            try:
                count = int(row.get("count") or 0)
            except ValueError:
                continue
            if not name or len(region) != 2 or count <= 0:
                continue
            gender = (row.get("gender") or "").strip().upper()
            if gender not in ("M", "F"):
                gender = "U"
            yield (name, name_type, region, gender, count)


def adapter_onomaverse_given():
    yield from _read_onomaverse("given", "given-name-frequency.csv")


def adapter_onomaverse_surname():
    yield from _read_onomaverse("surname", "surname-frequency.csv")


def adapter_ssa_given():
    d = RAW_DIR / "ssa"
    files = sorted(d.glob("yob*.txt"))
    if not files:
        return
    agg: Counter = Counter()
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n").split(",")
                if len(parts) != 3:
                    continue
                name, sex, count = parts
                agg[(name.strip(), sex.strip().upper())] += int(count)
    for (name, sex), count in agg.items():
        yield (name, "given", "US", "M" if sex == "M" else "F", count)


def _read_census_csv(path: Path):
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("NAME") or row.get("name") or "").strip()
            if not name or name.upper() == "ALL OTHER NAMES":
                continue
            try:
                count = int(row.get("COUNT") or row.get("count") or 0)
            except ValueError:
                continue
            if count <= 0:
                continue
            yield _uncap(name), count


def adapter_census2010_surname():
    d = RAW_DIR / "census2010"
    for path in sorted(d.glob("*.csv")) if d.exists() else []:
        for name, count in _read_census_csv(path):
            yield (name, "surname", "US", "U", count)


def adapter_census2020_surname():
    d = RAW_DIR / "census2020"
    for path in sorted(d.glob("*.csv")) if d.exists() else []:
        for name, count in _read_census_csv(path):
            yield (name, "surname", "US", "U", count)


def adapter_insee_given():
    d = RAW_DIR / "insee"
    files = sorted(d.glob("nat*.csv")) if d.exists() else []
    if not files:
        return
    agg: Counter = Counter()
    with open(files[0], "r", encoding="utf-8", errors="ignore", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            name = (row.get("preusuel") or "").strip()
            if not name or name == "_PRENOMS_RARES":
                continue
            sex = (row.get("sexe") or "").strip()
            try:
                count = int(float(row.get("nombre") or 0))
            except ValueError:
                continue
            if count <= 0:
                continue
            agg[(_uncap(name), "M" if sex == "1" else "F")] += count
    for (name, gender), count in agg.items():
        yield (name, "given", "FR", gender, count)


def adapter_wikidata():
    d = RAW_DIR / "wikidata"
    for path in sorted(d.glob("*_given.tsv")) if d.exists() else []:
        region = path.name[:2]
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) != 3:
                    continue
                name, gender, count = parts
                yield (name, "given", region, gender, int(count))
    for path in sorted(d.glob("*_family.tsv")) if d.exists() else []:
        region = path.name[:2]
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) != 3:
                    continue
                name, _gender, count = parts
                yield (name, "surname", region, "U", int(count))


# (key, adapter, license, url, bias note)
ADAPTERS = (
    ("onomaverse given", adapter_onomaverse_given, "CC-BY-4.0",
     "https://huggingface.co/datasets/onomaverse/names",
     "collection footprint over-serves the Arab world and the Mediterranean"),
    ("onomaverse surname", adapter_onomaverse_surname, "CC-BY-4.0",
     "https://huggingface.co/datasets/onomaverse/names",
     "same footprint as its given-name half"),
    ("SSA givens 1880+", adapter_ssa_given, "public domain (US gov)",
     "https://www.ssa.gov/oact/babynames/",
     "US-only by definition; names under 5 bearers suppressed at source"),
    ("US Census 2010 surnames", adapter_census2010_surname, "public domain (US gov)",
     "https://www.census.gov/topics/population/genealogy/data.html",
     "US-only; surnames under 100 bearers suppressed at source"),
    ("US Census 2020 surnames", adapter_census2020_surname, "public domain (US gov)",
     "https://www.census.gov/topics/population/genealogy/data.html",
     "US-only; present only if the 2020 shelf was reachable"),
    ("INSEE prenoms 1900+", adapter_insee_given, "Licence Ouverte (French gov)",
     "https://www.insee.fr/fr/statistiques/8595130",
     "France-only; names under 3 bearers suppressed at source"),
    ("Wikidata notable humans", adapter_wikidata, "CC0",
     "https://query.wikidata.org/",
     "fame proxy, not census: skews historical, male, and toward wiki-covered "
     "cultures; counts are notable-person counts, a different unit from census "
     "counts (mixed under sqrt damping, stated here rather than hidden)"),
)


def cook() -> dict:
    """Cook every reachable shelf into corpus.tsv + SOURCES.md. Returns stats."""
    rows: list = []
    per_source: dict[str, int] = {}
    for key, adapter, license_, url, bias in ADAPTERS:
        got = 0
        for r in adapter():
            rows.append(r)
            got += 1
        per_source[key] = got

    regions = Counter(r[2] for r in rows)
    chars = Counter()
    for r in rows:
        chars.update(r[0])
    givens = sum(1 for r in rows if r[1] == "given")

    CORPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CORPUS_PATH, "w", encoding="utf-8", newline="\n") as f:
        for name, ntype, region, gender, count in rows:
            f.write(f"{name}\t{ntype}\t{region}\t{gender}\t{count}\n")

    today = _dt.date.today().isoformat()
    lines = [
        "# The Wuddlies corpus: provenance ledger",
        "",
        f"Cooked {today} by `python -m wuddlies cook`. Aggregates and",
        "notable-public-record only; individual-level civilian data (electoral",
        "rolls, voter files, breach-derived sets) is refused regardless of",
        "technical availability. Every source's known bias is stated here",
        "rather than hidden; the bias microscope (`python -m wuddlies bias`)",
        "measures what survives into the pour.",
        "",
    ]
    for key, adapter, license_, url, bias in ADAPTERS:
        got = per_source.get(key, 0)
        status = f"{got:,} rows" if got else "shelf empty this cook (skipped)"
        lines += [f"## {key}", "",
                  f"- **Rows:** {status}", f"- **License:** {license_}",
                  f"- **Source:** {url}", f"- **Known bias:** {bias}", ""]
    SOURCES_PATH.write_text("\n".join(lines), encoding="utf-8")

    return {
        "rows": len(rows), "givens": givens, "surnames": len(rows) - givens,
        "regions": len(regions), "unique_chars": len(chars),
        "per_source": per_source,
        "top_regions": regions.most_common(8),
    }


def load_corpus() -> list[tuple[str, str, str, str, int]]:
    """Read corpus.tsv back as (name, type, region, gender, weight) tuples."""
    out = []
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 5:
                continue
            name, ntype, region, gender, weight = parts
            out.append((name, ntype, region, gender, int(weight)))
    return out
