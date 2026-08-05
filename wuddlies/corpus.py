#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/corpus.py the corpus kitchen
-The last of the corpus kitchens washed every name the world actually uses and kept the counts that made them true, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

Cooks the harvested raw datasets into one faithful corpus file. Faithful
means: every script kept as-is (Latin, Hebrew, Arabic, hangul, all of it),
casing and diacritics untouched, and the real per-country counts carried
whole. Filtering for what a given model can chew is the MODEL's concern
(train.py); the kitchen never seasons away the world's diversity.

Sources cooked in v1: onomaverse given-name-frequency + surname-frequency
(per-country counts, gender on givens). The popular-names ranking, the
gender-inference table, the transliteration atlas, and the equivalence
graph stay raw for the later floors (validation, variant adoption). The
Hobson nationality-labeled surnames wait for an enrichment pass, since
their regions are nationality words rather than ISO codes.

Output: wuddlies/data/corpus.tsv with columns
    name <TAB> type(given|surname) <TAB> region(ISO2) <TAB> gender(M|F|U) <TAB> weight(count)
one row per (name, country) pairing, exactly as the census saw it.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
RAW_DIR = DATA_DIR / "raw"
CORPUS_PATH = DATA_DIR / "corpus.tsv"


def _cook_frequency_csv(path: Path, name_type: str, rows_out: list) -> int:
    """Stream one onomaverse frequency CSV into corpus rows. Returns row count."""
    kept = 0
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
                gender = "U"        # unknown, multi, or surname
            rows_out.append((name, name_type, region, gender, count))
            kept += 1
    return kept


def cook() -> dict:
    """Cook the raw harvest into corpus.tsv. Returns a stats dict."""
    rows: list = []
    givens = _cook_frequency_csv(RAW_DIR / "onomaverse" / "given-name-frequency.csv",
                                 "given", rows)
    surnames = _cook_frequency_csv(RAW_DIR / "onomaverse" / "surname-frequency.csv",
                                   "surname", rows)

    regions = Counter(r[2] for r in rows)
    chars = Counter()
    for r in rows:
        chars.update(r[0])

    CORPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CORPUS_PATH, "w", encoding="utf-8", newline="\n") as f:
        for name, ntype, region, gender, count in rows:
            f.write(f"{name}\t{ntype}\t{region}\t{gender}\t{count}\n")

    return {
        "rows": len(rows),
        "givens": givens,
        "surnames": surnames,
        "regions": len(regions),
        "unique_chars": len(chars),
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
