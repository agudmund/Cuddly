# The Wuddlies corpus: provenance ledger

Cooked 2026-08-05 by `python -m wuddlies cook`. Aggregates and
notable-public-record only; individual-level civilian data (electoral
rolls, voter files, breach-derived sets) is refused regardless of
technical availability. Every source's known bias is stated here
rather than hidden; the bias microscope (`python -m wuddlies bias`)
measures what survives into the pour.

## onomaverse given

- **Rows:** 53,868 rows
- **License:** CC-BY-4.0
- **Source:** https://huggingface.co/datasets/onomaverse/names
- **Known bias:** collection footprint over-serves the Arab world and the Mediterranean

## onomaverse surname

- **Rows:** 41,248 rows
- **License:** CC-BY-4.0
- **Source:** https://huggingface.co/datasets/onomaverse/names
- **Known bias:** same footprint as its given-name half

## SSA givens 1880+

- **Rows:** shelf empty this cook (skipped)
- **License:** public domain (US gov)
- **Source:** https://www.ssa.gov/oact/babynames/
- **Known bias:** US-only by definition; names under 5 bearers suppressed at source

## US Census 2010 surnames

- **Rows:** 162,253 rows
- **License:** public domain (US gov)
- **Source:** https://www.census.gov/topics/population/genealogy/data.html
- **Known bias:** US-only; surnames under 100 bearers suppressed at source

## US Census 2020 surnames

- **Rows:** shelf empty this cook (skipped)
- **License:** public domain (US gov)
- **Source:** https://www.census.gov/topics/population/genealogy/data.html
- **Known bias:** US-only; present only if the 2020 shelf was reachable

## INSEE prenoms 1900+

- **Rows:** 38,477 rows
- **License:** Licence Ouverte (French gov)
- **Source:** https://www.insee.fr/fr/statistiques/8595130
- **Known bias:** France-only; names under 3 bearers suppressed at source

## Wikidata notable humans

- **Rows:** shelf empty this cook (skipped)
- **License:** CC0
- **Source:** https://query.wikidata.org/
- **Known bias:** fame proxy, not census: skews historical, male, and toward wiki-covered cultures; counts are notable-person counts, a different unit from census counts (mixed under sqrt damping, stated here rather than hidden)
