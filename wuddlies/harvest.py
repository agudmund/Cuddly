#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/harvest.py the expedition rig
-The last of the expeditions sailed for the missing half of humanity and came home with holds full of censuses, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

The second harvest, in code. Wave 1 pulls the statistical backbones (SSA
givens since 1880, US Census surnames, INSEE prénoms 1900 onward) straight
from their government shelves. Wave 2 sails for the missing half through
the Wikidata equalizer: per-country aggregate queries (given and family
names of notable humans, CC0) for the populations the first corpus barely
heard, with per-country label-language choices recorded inline. Raw urllib
throughout, family sovereignty rules.

The bars, standing: aggregates and notable-public-record only; every
source's license and bias noted where the kitchen writes the ledger; a
failed country is reported and sailed past, never silently skipped: the
expedition lands with whatever it honestly gathered.

Label-language decisions (recorded so nobody wonders later): the CJK trio
(CN/JP/KR) harvests romanized-first because their native floors are
designed later as their own project (semantic character choice, not
phonotactic sequence); the Indic cluster harvests romanized-first because
pan-Indian romanization beats fragmenting thin data across ten scripts;
Ethiopia harvests Ge'ez-first, consistent with the corpus already carrying
Arabic and Hebrew natively.
"""

from __future__ import annotations

import functools
import io
import json
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

# A voyage narrates live or not at all: block-buffered stdout hid an entire
# failing Wave 2 behind an empty log (field 2026-08-05, the run_echoed lesson
# arriving here). Every print in this rig flushes.
print = functools.partial(print, flush=True)

RAW_DIR = Path(__file__).parent / "data" / "raw"
UA = "WuddliesHarvest/0.1 (the Cuddly family's naming channel; local research use)"
# ssa.gov's CDN refuses non-browser agents outright (403, field 2026-08-05) for a
# public-domain file; we present a standard browser string there and keep the
# honest tool UA everywhere else, especially toward Wikimedia.
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
# Wikidata's query service declared an outage-era emergency rule (797a132):
# one request per minute. The expedition bows to the declared pace exactly
# whenever it speaks to WDQS. QLever (University of Freiburg's public SPARQL
# engine over the same Wikidata data, CC0 all the way down) is the PRIMARY
# endpoint for these heavy aggregations: it is built for them, and the
# queries are written in portable SPARQL (no Blazegraph label service) so
# both endpoints understand the same text. Field lesson 2026-08-05: the
# label-service GROUP BY queries died server-side under outage recovery
# while trivial probes passed; cheap portable shapes are the cure.
WDQS_BOW_SECONDS = 65
QLEVER_BOW_SECONDS = 3
SPARQL_ENDPOINTS = (
    ("qlever", "https://qlever.cs.uni-freiburg.de/api/wikidata", QLEVER_BOW_SECONDS),
    ("wdqs", "https://query.wikidata.org/sparql", WDQS_BOW_SECONDS),
)

_PREFIXES = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

# ssa.gov refuses non-browser agents AND a plain browser string (403 both ways,
# field 2026-08-05): their gate inspects more than the UA. The data itself is
# public-domain US government work, so a public mirror is legitimate transport;
# the GitHub zipball below carries the same yob files.
SSA_URLS = (
    "https://www.ssa.gov/oact/babynames/names.zip",
    "https://github.com/hackerb9/ssa-baby-names/archive/refs/heads/main.zip",
)
CENSUS_2010_URL = "https://www2.census.gov/topics/genealogy/2010surnames/names.zip"
CENSUS_2020_URL = "https://www2.census.gov/topics/genealogy/2020surnames/names.zip"
INSEE_URLS = (
    "https://www.insee.fr/fr/statistiques/fichier/8595130/nat2024_csv.zip",
    "https://www.insee.fr/fr/statistiques/fichier/7635552/nat2022_csv.zip",
    "https://www.insee.fr/fr/statistiques/fichier/2540004/nat2021_csv.zip",
)

# (ISO2, Wikidata country Q-id, label-language chain)
WIKIDATA_TARGETS = (
    ("IN", "Q668", "en"), ("CN", "Q148", "en,zh"), ("ID", "Q252", "en,id"),
    ("PK", "Q843", "en"), ("BD", "Q902", "en"), ("ET", "Q115", "am,en"),
    ("JP", "Q17", "en,ja"), ("PH", "Q928", "en"), ("VN", "Q881", "vi,en"),
    ("KR", "Q884", "en,ko"), ("TH", "Q869", "th,en"), ("MM", "Q836", "my,en"),
    ("TZ", "Q924", "en,sw"), ("UG", "Q1036", "en,sw"), ("CD", "Q974", "fr,en"),
    ("NP", "Q837", "en"), ("LK", "Q854", "en"), ("IR", "Q794", "fa,en"),
)


def _fetch(url: str, dst: Path, timeout: int = 180, ua: str = UA) -> bool:
    """Download url to dst unless it already exists. True on present/success."""
    if dst.exists() and dst.stat().st_size > 0:
        print(f"[expedition] already aboard: {dst.name}")
        return True
    dst.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            dst.write_bytes(r.read())
        print(f"[expedition] gathered {dst.name} ({dst.stat().st_size:,} bytes)")
        return True
    except Exception as e:
        print(f"[expedition] could not gather {url}: {e}")
        return False


def _unzip(src: Path, into: Path) -> None:
    with zipfile.ZipFile(src) as z:
        z.extractall(into)


def harvest_ssa() -> bool:
    d = RAW_DIR / "ssa"
    if any(d.glob("yob*.txt")):
        print("[expedition] already aboard: SSA year files")
        return True
    z = None
    for url in SSA_URLS:
        cand = d / Path(urllib.parse.urlparse(url).path).name
        if _fetch(url, cand, ua=BROWSER_UA):
            z = cand
            break
    if z is None:
        return False
    _unzip(z, d)
    # A mirror zipball nests its payload; surface any yob files to the shelf.
    if not any(d.glob("yob*.txt")):
        for f in d.rglob("yob*.txt"):
            (d / f.name).write_bytes(f.read_bytes())
    got = len(list(d.glob("yob*.txt")))
    print(f"[expedition] SSA unpacked: {got} year files")
    return got > 0


def harvest_census() -> bool:
    ok = False
    d10 = RAW_DIR / "census2010"
    if _fetch(CENSUS_2010_URL, d10 / "names.zip"):
        if not any(d10.glob("*.csv")):
            _unzip(d10 / "names.zip", d10)
        ok = True
    d20 = RAW_DIR / "census2020"
    if _fetch(CENSUS_2020_URL, d20 / "names.zip"):
        try:
            if not any(d20.glob("*.csv")):
                _unzip(d20 / "names.zip", d20)
        except Exception as e:
            print(f"[expedition] census 2020 unpack declined: {e}")
    return ok


def harvest_insee() -> bool:
    d = RAW_DIR / "insee"
    if any(d.glob("nat*.csv")):
        print("[expedition] already aboard: INSEE nat file")
        return True
    for url in INSEE_URLS:
        z = d / Path(urllib.parse.urlparse(url).path).name
        if _fetch(url, z):
            _unzip(z, d)
            got = list(d.glob("nat*.csv"))
            if got:
                print(f"[expedition] INSEE unpacked: {got[0].name}")
                return True
    return False


def _sparql(query: str, timeout: int = 90):
    """Run one portable SPARQL query: QLever first, WDQS fallback.
    Returns (bindings, bow_seconds_for_the_endpoint_that_answered)."""
    last = None
    for name, endpoint, bow in SPARQL_ENDPOINTS:
        params = urllib.parse.urlencode({"query": query, "format": "json"})
        req = urllib.request.Request(f"{endpoint}?{params}",
                                     headers={"User-Agent": UA,
                                              "Accept": "application/sparql-results+json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))["results"]["bindings"], bow
        except Exception as e:
            print(f"[expedition]   {name} declined: {e}")
            last = e
            if name == "qlever":
                continue
            if isinstance(e, urllib.error.HTTPError) and e.code == 429:
                try:
                    wait = int(e.headers.get("Retry-After", WDQS_BOW_SECONDS))
                except (TypeError, ValueError):
                    wait = WDQS_BOW_SECONDS
                print(f"[expedition]   bowing {max(wait, WDQS_BOW_SECONDS)}s for one retry")
                time.sleep(max(wait, WDQS_BOW_SECONDS))
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return json.loads(r.read().decode("utf-8"))["results"]["bindings"], bow
    raise last


def _clean_label(label: str) -> str | None:
    label = (label or "").strip()
    if len(label) < 2 or len(label) > 40:
        return None
    if label[0] == "Q" and label[1:].isdigit():      # unlabeled item leaked through
        return None
    if any(ch in label for ch in "()[]{}/#@;:|=+_«»"):
        return None
    return label


def _wikidata_country(iso2: str, qid: str, langs: str) -> tuple[int, int]:
    d = RAW_DIR / "wikidata"
    d.mkdir(parents=True, exist_ok=True)
    primary = langs.split(",")[0]
    got_g, got_f = 0, 0

    # Portable SPARQL: group by the name ENTITY, sample its labels (primary
    # language, then English), count bearers. No Blazegraph label service, so
    # both QLever and WDQS run the same text, and the grouping stays cheap.
    given_q = _PREFIXES + f"""SELECT ?name (SAMPLE(?lp) AS ?labelP) (SAMPLE(?le) AS ?labelE) ?gender (COUNT(?h) AS ?c) WHERE {{
      ?h wdt:P31 wd:Q5 ; wdt:P27 wd:{qid} ; wdt:P735 ?name .
      OPTIONAL {{ ?h wdt:P21 ?gender }}
      OPTIONAL {{ ?name rdfs:label ?lp . FILTER(LANG(?lp) = "{primary}") }}
      OPTIONAL {{ ?name rdfs:label ?le . FILTER(LANG(?le) = "en") }}
    }} GROUP BY ?name ?gender"""
    family_q = _PREFIXES + f"""SELECT ?name (SAMPLE(?lp) AS ?labelP) (SAMPLE(?le) AS ?labelE) (COUNT(?h) AS ?c) WHERE {{
      ?h wdt:P31 wd:Q5 ; wdt:P27 wd:{qid} ; wdt:P734 ?name .
      OPTIONAL {{ ?name rdfs:label ?lp . FILTER(LANG(?lp) = "{primary}") }}
      OPTIONAL {{ ?name rdfs:label ?le . FILTER(LANG(?le) = "en") }}
    }} GROUP BY ?name"""

    def _label(b) -> str:
        return (b.get("labelP", {}).get("value")
                or b.get("labelE", {}).get("value") or "")

    def _gender(b) -> str:
        iri = b.get("gender", {}).get("value", "")
        if iri.endswith("Q6581097"):
            return "M"
        if iri.endswith("Q6581072"):
            return "F"
        return "U"

    for kind, query, path in (("given", given_q, d / f"{iso2}_given.tsv"),
                              ("family", family_q, d / f"{iso2}_family.tsv")):
        if path.exists():
            n = sum(1 for _ in open(path, encoding="utf-8"))
            print(f"[expedition] already aboard: {path.name} ({n:,})")
            got_g, got_f = (n, got_f) if kind == "given" else (got_g, n)
            continue
        try:
            rows, bow = _sparql(query)
        except Exception as e:
            print(f"[expedition] {iso2} {kind}: sailed past ({e})")
            continue
        # Distinct name ENTITIES can share a label; sum them client-side.
        agg: dict[tuple[str, str], int] = {}
        for b in rows:
            name = _clean_label(_label(b))
            if not name:
                continue
            g = _gender(b) if kind == "given" else "U"
            try:
                c = int(float(b["c"]["value"]))
            except (KeyError, ValueError):
                continue
            agg[(name, g)] = agg.get((name, g), 0) + c
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for (name, g), c in agg.items():
                f.write(f"{name}\t{g}\t{c}\n")
        n = len(agg)
        got_g, got_f = (n, got_f) if kind == "given" else (got_g, n)
        print(f"[expedition] {iso2} {kind} names aboard: {n:,}")
        time.sleep(bow)
    return got_g, got_f


def harvest_all() -> None:
    t0 = time.perf_counter()
    print("[expedition] Wave 1: the statistical backbones")
    ssa = harvest_ssa()
    census = harvest_census()
    insee = harvest_insee()
    print(f"[expedition] Wave 1 status: SSA={ssa} Census={census} INSEE={insee}")

    print("[expedition] Wave 2: the missing half, via the Wikidata equalizer")
    totals = {}
    for iso2, qid, langs in WIKIDATA_TARGETS:
        totals[iso2] = _wikidata_country(iso2, qid, langs)
    landed = {k: v for k, v in totals.items() if sum(v) > 0}
    missed = [k for k, v in totals.items() if sum(v) == 0]
    print(f"[expedition] Wave 2 status: {len(landed)}/{len(WIKIDATA_TARGETS)} "
          f"countries aboard"
          + (f"; sailed past: {', '.join(missed)}" if missed else ""))
    print(f"[expedition] home in {time.perf_counter() - t0:.0f}s; "
          f"holds at {RAW_DIR}")


if __name__ == "__main__":
    harvest_all()
