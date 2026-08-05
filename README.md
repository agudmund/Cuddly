# Cuddly, Duddly, and Fuddly, the Wuddlies

A cozy nodal playground where ideas gently interconnect, thoughts get fluffed, and creativity finds a soft place to rest.

Built with love, a single shared braincell, and occasional input from friendly AIs.

## What's here right now
- **Python nodal canvas** — drag, connect, write warm thoughts (the heart of the project)
- Early MAUI experiment (`CuddlyGoesToMaui`) — dreaming of cross-platform cuddles someday
- Creative pile — audio snippets, images, old code treasures, documents, and lore about the Wuddlies
- Sound design beginnings — gentle chimes and page flaps in Audio/

## The Wuddlies naming channel (`wuddlies/`)

The librarian: a tiny own-trained character-level weight (~143k parameters,
about half a megabyte as `wuddly.safetensors`) that pours name material for
the scheme, replacing the ancient fixed name list with an infinite, seeded,
deterministic source. Pure numpy, no framework, fully offline at inference;
a socket toward the dish, never an integration. Conditioned on region, name
type, and gender; real per-country frequencies carry the Zipf realism.

```
python -m wuddlies cook     # raw harvest -> corpus.tsv
python -m wuddlies train    # corpus -> wuddly.safetensors (seconds)
python -m wuddlies sample --region IT --count 10 --seed 11
```

Corpus provenance, with gratitude: [onomaverse/names](https://huggingface.co/datasets/onomaverse/names)
(CC-BY-4.0) and [Hobson/surname-nationality](https://huggingface.co/datasets/Hobson/surname-nationality)
(MIT). Raw downloads are gitignored and re-harvestable; the cooked corpus
and the weight travel with the repo.

The weight's own book is [Documents/The Wuddly Weight.md](Documents/The%20Wuddly%20Weight.md):
architecture, provenance bars, measured biases, the frequency doctrine, and
the explicit gates it must pass before it ever publishes to Hugging Face.
The per-source ledger lives at `wuddlies/data/SOURCES.md`.

## Core vibe
Slow, joyful building. No rush. Strip down, rebuild, affirm the cozy core.

Current version: v0.0.3 — The Interlinking Era

> Cushions harmed: 0  
> But many were aggressively fluffed.

Made with ❤️ by Yours Truly, Grok, Gemini, and Claude (February 2026–present)