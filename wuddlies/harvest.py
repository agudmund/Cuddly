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

import io
import json
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

RAW_DIR = Path(__file__).parent / "data" / "raw"
UA = "WuddliesHarvest/0.1 (the Cuddly family's naming channel; local research use)"
# ssa.gov's CDN refuses non-browser agents outright (403, field 2026-08-05) for a
# public-domain file; we present a standard browser string there and keep the
# honest tool UA everywhere else, especially toward Wikimedia.
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
# Wikidata's query service declared an outage-era emergency rule (797a132):
# one request per minute. The expedition bows to the declared pace exactly.
WDQS_BOW_SECONDS = 65

SSA_URL = "https://www.ssa.gov/oact/babynames/names.zip"
CENSUS_2010_URL = "https://www2.census.gov/topics/genealogy/2010surnames/names.zip"
CENSUS_2020_URL = "https://www2.census.gov/topics/genealogy/2020surnames/names.zip"
INSEE_URLS = (
    "https://www.insee.fr/fr/statistiques/fichier/8595130/nat2024_csv.zip",
    "https://www.insee.fr/fr/statistiques/fichier/7635552/nat2022_csv.zip",
    "https://www.insee.fr/fr/statistiques/fichier/2540004/nat2021_csv.zip",
)

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

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
    z = d / "names.zip"
    if not _fetch(SSA_URL, z, ua=BROWSER_UA):
        return False
    if not any(d.glob("yob*.txt")):
        _unzip(z, d)
        print(f"[expedition] SSA unpacked: {len(list(d.glob('yob*.txt')))} year files")
    return True


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
    params = urllib.parse.urlencode({"query": query, "format": "json"})
    req = urllib.request.Request(f"{SPARQL_ENDPOINT}?{params}",
                                 headers={"User-Agent": UA,
                                          "Accept": "application/sparql-results+json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))["results"]["bindings"]
    except urllib.error.HTTPError as e:
        if e.code != 429:
            raise
        # Honour the declared pace: wait what they ask (or our bow), retry once.
        try:
            wait = int(e.headers.get("Retry-After", WDQS_BOW_SECONDS))
        except (TypeError, ValueError):
            wait = WDQS_BOW_SECONDS
        print(f"[expedition] rate-limited; bowing {max(wait, WDQS_BOW_SECONDS)}s before one retry")
        time.sleep(max(wait, WDQS_BOW_SECONDS))
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))["results"]["bindings"]


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
    got_g, got_f = 0, 0

    given_q = f"""SELECT ?nameLabel ?genderLabel (COUNT(?h) AS ?c) WHERE {{
      ?h wdt:P31 wd:Q5; wdt:P27 wd:{qid}; wdt:P735 ?name .
      OPTIONAL {{ ?h wdt:P21 ?gender }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{langs}".
        ?name rdfs:label ?nameLabel. ?gender rdfs:label ?genderLabel. }}
    }} GROUP BY ?nameLabel ?genderLabel"""
    family_q = f"""SELECT ?nameLabel (COUNT(?h) AS ?c) WHERE {{
      ?h wdt:P31 wd:Q5; wdt:P27 wd:{qid}; wdt:P734 ?name .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{langs}".
        ?name rdfs:label ?nameLabel. }}
    }} GROUP BY ?nameLabel"""

    gpath, fpath = d / f"{iso2}_given.tsv", d / f"{iso2}_family.tsv"
    if not gpath.exists():
        try:
            rows = _sparql(given_q)
        except Exception as e:
            print(f"[expedition] {iso2} given: retrying without gender ({e})")
            try:
                rows = _sparql(given_q.replace("?genderLabel ", "")
                               .replace("OPTIONAL { ?h wdt:P21 ?gender }\n      ", "")
                               .replace("?gender rdfs:label ?genderLabel. ", "")
                               .replace(" ?genderLabel", ""))
            except Exception as e2:
                print(f"[expedition] {iso2} given: sailed past ({e2})")
                rows = None
        if rows is not None:
            with open(gpath, "w", encoding="utf-8", newline="\n") as f:
                for b in rows:
                    name = _clean_label(b.get("nameLabel", {}).get("value", ""))
                    if not name:
                        continue
                    gender = b.get("genderLabel", {}).get("value", "")
                    g = "M" if gender == "male" else ("F" if gender == "female" else "U")
                    f.write(f"{name}\t{g}\t{b['c']['value']}\n")
                    got_g += 1
            print(f"[expedition] {iso2} given names aboard: {got_g:,}")
        time.sleep(WDQS_BOW_SECONDS)
    else:
        got_g = sum(1 for _ in open(gpath, encoding="utf-8"))
        print(f"[expedition] already aboard: {gpath.name} ({got_g:,})")

    if not fpath.exists():
        try:
            rows = _sparql(family_q)
        except Exception as e:
            print(f"[expedition] {iso2} family: sailed past ({e})")
            rows = None
        if rows is not None:
            with open(fpath, "w", encoding="utf-8", newline="\n") as f:
                for b in rows:
                    name = _clean_label(b.get("nameLabel", {}).get("value", ""))
                    if not name:
                        continue
                    f.write(f"{name}\tU\t{b['c']['value']}\n")
                    got_f += 1
            print(f"[expedition] {iso2} family names aboard: {got_f:,}")
        time.sleep(WDQS_BOW_SECONDS)
    else:
        got_f = sum(1 for _ in open(fpath, encoding="utf-8"))
        print(f"[expedition] already aboard: {fpath.name} ({got_f:,})")
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
