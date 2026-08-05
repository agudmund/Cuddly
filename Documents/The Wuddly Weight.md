# The Wuddly Weight

**This is the model card for `wuddly.safetensors`, the librarian: a tiny own-trained character-level name model, documented from the living context of its birth (2026-08-05) rather than reconstructed later.** It lives here in the repo while the weight proves itself in field usage; if and when it earns publication to Hugging Face, this document matures into its public card. The standing gate, in the founder's words: nothing gets published that is incomplete or not field tested.

## What it is

**A conditioned character-level model that generates human given names and surnames, small enough to embed in anything.** Pure numpy at train and inference time, no framework anywhere. The current canonical weight is about 1.4 MB (roughly 400 thousand parameters at laboratory dimensions); its first-day sibling was 581 KB at 143 thousand parameters. For scale, the family's reference for "a small model" is a 25 MB TTS voice; the librarian is an order of magnitude under that with room to grow.

**It exists to replace a relic.** Its ancestors are `names.py` and `NameGen.cs`, a frozen bank of one hundred names and a print loop that quote-wrapped them for pasting into C#. The weight replaces the finite list with an infinite, seeded, deterministic source: the same seed always pours the same souls, so a name can be a pure function of an NPC's identity with nothing stored anywhere.

**It is a component toward a larger private scheme.** The weight serves as the naming channel of a world-generation system whose core algorithm deliberately lives off-disk and off-network. The interface honors that boundary by design: the sampler accepts an opaque seed and (in a future head) a vector of meaning-free condition floats. The weight never learns what the numbers mean; meaning is assigned at wiring time, elsewhere.

## Architecture

**A fixed-window MLP over characters, conditioned on region, name type, and gender.** The last K characters (K carried per-model in metadata; 4 for the first weights, 6 for the laboratory line) meet embeddings for region (ISO2), type (given or surname), and gender (M, F, U) in a concatenated input, pass through two tanh hidden layers, and produce a softmax over the character vocabulary. Training is hand-rolled Adam over cross-entropy, minutes on an ordinary CPU.

**The file is fully self-contained.** The safetensors container is written and read by a minimal implementation of the format: an 8-byte little-endian header length, a JSON header mapping tensor names to dtype, shape, and data offsets, then raw float32 bytes. The character vocabulary, region list, sampler priors, and per-model dimensions travel inside the file's own metadata as JSON strings, so loading requires nothing but numpy and the format itself. The forward pass is simple enough to hand-port to C# or any other host as a dependency-free loop, which is a design goal, not an accident.

**Determinism is doctrine.** Sampling takes a seeded generator; identical seed and arguments reproduce identical names forever, across machines. The intended use is hierarchical: a world seed derives region seeds, which derive settlement seeds, which derive family seeds, so coherence emerges structurally while every draw stays reproducible.

## Training data and its ethics

**Every source is aggregate or notable-public-record; no individual-level civilian data, ever.** The standing bars, set jointly and enforced at the license door: no electoral rolls, no voter files, no civil-registry or social-registry records, no breach-derived or scrape-derived personal datasets regardless of technical availability, and no bulk extraction against a platform's terms. Several famous large name datasets fail these bars and are refused by name in the provenance ledger. The good sources enforce gentleness themselves: the census-grade files suppress rare names at the source (SSA below five bearers, INSEE below three), which means the most identifying rows never existed in the material.

**The sources, as of this writing** (the authoritative list with per-source bias notes is `wuddlies/data/SOURCES.md`):

- **onomaverse/names** (CC-BY-4.0): per-country given and surname frequencies, 106 countries, the founding corpus.

- **US Census surnames** (public domain): every surname with 100 or more bearers in the 2010 census.

- **INSEE prénoms** (Licence Ouverte): every given name born in France 1900 onward, with counts.

- **SSA givens since 1880** (public domain): the American century of first names, aboard via public-domain mirror transport (141 year files, 111 thousand aggregated name rows).

- **Wikidata notable humans** (CC0): per-country aggregate queries over given and family names of notable people, the cross-script equalizer for populations under-served by machine-readable statistics; aboard for 18 countries (59 thousand rows) through the QLever engine with the official service as fallback, honest about being a fame proxy rather than a census.

- **IBGE Nomes no Brasil** (Brazilian government open data): 130 thousand first names covering 200 million people from the 2010 census; queued.

**The known biases are measured, not guessed.** The repo carries a bias microscope (`python -m wuddlies bias`) that pours thirty thousand souls under a fixed seed and reports region draw shares against corpus footprint and approximate real population, script shares, gender shares, and duplication. At the time of writing it reports the founding corpus's collection footprint plainly: the Arab world and Mediterranean over-served, and roughly half of humanity (India, China, Indonesia, Pakistan, Ethiopia, Japan) drastically under-poured, with India at a pour-to-population ratio of 0.08. It also caught, live, the predicted e-government bias: when Western statistical backbones landed while the equalizer was storm-delayed, the US flipped from fair (0.73) to over-poured (2.52). Repair is data-first: the equalizer sails for the missing half before any population weighting is trusted. Nobody left out includes nobody left out of the accounting.

**One deliberate deferral, stated with its reason.** CJK naming (Chinese, Japanese kanji, Korean hangul) is semantic character choice rather than phonotactic sequence, and deserves machinery that respects that; those scripts are harvested but deferred from the current weight's training rather than given a bad seat. Romanized forms participate today; the native-script floor is its own future project.

## The frequency doctrine

**Teach the weight the truth; put the dial on the desk.** The model trains on damped real frequencies (count to the power 0.5, with per-region damping so small countries keep a voice, and a gem guard ceiling so census mega-names cannot drown the rare tail's gradient). It therefore knows that Mohamed and Maria are common, which is what makes a poured census read human (Zipf realism: a village has three of someone and one of someone else). Diversity is then a sampling-time dial, not a training-time amputation: temperature flattens the learned distribution reversibly, surfacing the rare tail on request without ever unlearning the truth. Capping at training time would have destroyed the realism mode permanently; damping trains humility instead of ignorance.

## Measured behavior

**From the standing yardstick (30,000 souls, seed 7), at the time of writing:** uniqueness between 51 and 64 percent depending on the weight generation; mean name length 5.6 to 5.8 with a 95th percentile of 9; the most common pours are the world's actual most common names in plausible proportion (Mohamed at roughly 0.7 percent of the world pour). Training knees are measured, not assumed: the patience gate found redundancy beginning at 14,000 steps on the founding corpus at laboratory dimensions, and validation loss is tracked against a held-out two percent of rows split by row so nothing leaks.

**Known rough seams, honestly:** Arabic-script output trails the romanized rows in quality; gender labels skew (M 45, F 33, U 22 at the third audit, improving as Wikidata's labels arrive) as a corpus labeling artifact with a repair path through the gender-inference table; counts from censuses and counts of notable people are different units mixed under damping, stated in the ledger pending finer calibration.

**The three-audit trend, recorded as it happened (all at 30,000 souls, seed 7):** the founding corpus poured India at a 0.09 pour-to-population ratio; the storm-partial second corpus (Western backbones landed, equalizer delayed) pushed the US from fair 0.73 to over-poured 2.52, catching the predicted e-government bias live; the third corpus (466 thousand rows, 131 regions, equalizer aboard for all 18 targets) healed Japan outright to fair band (0.59) on romanized material and multiplied the variety of every missing-half region, while pour shares moved little because notable-person counts and census counts are different units. Conclusion, per the sequencing rule: the data has now earned the population-weighting mode; pour-share repair is a weights question from here, not a data question, except where a native-script floor is the designed answer (China foremost).

**The fifth schooling (same day still) turned the reviews into weights.** The kitchen grew two enrichments from the harvest's own shelves (62,868 name-level origin tags carried through; 11,662 U-gendered rows repaired at 0.8 confidence, the ambiguous kept honest), and the rig's example-weight composition became five deliberate stages: Zipf base, per-family and per-region gem ceilings, region damping, a normalised family factor over the tagged rows, then gender and richness boosts. The brain gained the origin conditioning axis (`--origin Sanskrit --region IN` pours Vijay, Rajesh, Roshna) and a doubled type embedding. Measured results: given-pour uniqueness rose from 60.7 to 71.6 percent, unknown-gender draws collapsed from 21.6 to 9.3 percent, population-preset fairness held for every giant at an improved KL of 0.0020, and lane-bleed acquired its baseline instrument (3.98 percent of surname pours are corpus given-only names). Two honest findings joined the punch list: the origin column is a 3,261-tag micro-taxonomy wanting normalization, and a pinned origin needs a co-occurrence region prior so its flavor survives away from home.

**The fourth floor closed the arc the same day.** With the gem guard capping census mega-names at the weight distribution's own top permille (2,331 rows clipped; the training knee stretched from 8,500 to 18,500 steps as the rare tail kept its gradient voice) and the world-mix presets shipped (`archive`, `population`, `equal`, each measured against its own declared target), the population preset put **every one of the twelve largest populations in the fair band**: India 0.79, China 0.78, the US corrected from 2.83 to 1.20, Indonesia 1.24, Pakistan 1.28, Ethiopia 1.17, Japan 1.31: at KL 0.0025 against target and 98.5 percent region coverage, with pour uniqueness rising. The founding fairness goal, representative of all humans with no bias but population, became a measured property of a command-line flag. China's remaining gap is pour *quality* rather than quantity, and its designed answer stays the native-script floor.

## Use

**From anywhere, via the family fleet:** the `wuddly` verb (a `_util/bin` front door) runs the desk from any directory: bare `wuddly` prints the complete register of verbs and arguments, and `wuddly completions --install` wires PowerShell tab-completion (verbs, flags, world modes, all regions baked from the live weight, marquee origins).

**From the desk (run from the repo root):**

    python -m wuddlies sample --region IT --count 10 --seed 11
    python -m wuddlies sample --type surname --region US --count 10
    python -m wuddlies sample --world population --count 20
    python -m wuddlies sample --type fullname --world population --count 20
    python -m wuddlies bias --world population

The `fullname` type pours whole souls: region drawn once, given and surname
born there together, joined in the region's living name order (family-first
across the CJK sphere, Vietnam, and Hungary; given-first elsewhere). The
convention-genesis floor will one day make that ordering emergent; today it
is a small honest table.

**From code:** `from wuddlies import load_model`, then `model.sample_name(rng, region="FR", name_type="given")` with a `numpy.random.default_rng(seed)`. The `condition` parameter is the reserved socket and currently refuses non-None values honestly.

## Acknowledgments

**More than one mind fed this weight's design, and the ledger says so gladly.** The external-source expedition map grew from a scouting exchange with Gemini: asked whether Gemma's pretrained models carried extractable name data inside them (they do not, in any wholesale form), "the dear gem", as the founder calls it, offered up the wider world's registries instead. Those leads were then triaged through this document's bars: some became sources or redirects (the IBGE treasure traces directly to that exchange), others were declined at the door with their reasons recorded in the ledger; the triage judgment is this house's, the generosity of the map was Gemini's. The stratified-sampling and cultural-anchor ideas from the same channel shaped the gem guard and the origin-axis roadmap. **Grok contributed the fairness-engineering pass** (relayed 2026-08-05): the distributional evaluation metrics adopted into the microscope's roadmap (KL divergence against a declared target, top-N coverage, per-family entropy to catch a region collapsing onto its five most popular names), the language-family grouping axis that fused with the cultural-origin idea into one conditioning roadmap, stratified batch sampling as a rig option, and the within-family-only constraint on the future variant floor. Its fair-versus-realistic framing resolved into this card's pour-mode preset menu (equal-family, soft-population clamped, archive-honest) rather than a training-time choice, because conditioning decouples per-region truth from cross-region mix. Several of its recommendations (explicit condition tokens, simplicity as a fairness property, a methodology-and-limitations document) were independently convergent with what was already built, which is its own kind of review. **A second Grok pass** (relayed the same day, moments before its chat window gave out) reviewed the rig's actual code and specified the fifth floor's training-balance layer: language-family damping above region damping, per-family gem ceilings, a mild gender boost for givens, a richness regularizer, effective-mass-per-family reporting, and in-training fairness metrics so early stopping finds the joint knee of loss and fairness; it also endorsed the script deferral and the row-level hold-out as-is. One design note carried forward with it: region-to-family lookup mislabels melting-pot nations (its own US example spans every family on earth), so the family layer's substrate is name-level language tags rather than a region table. The repo's founding credit line (built by Yours Truly with Grok, Gemini, and Claude) continues to be earned by all of its names.

## The path to publication

**The weight publishes to Hugging Face only when it has earned it.** The family pulls freely from that commons and intends to give back, and precisely because of that, nothing ships incomplete. The gates, explicit so future readers know when the day has come:

- **Field-proven:** used in real projects over real time, with the seams that only usage finds already found.

- **The missing half repaired:** the biggest-of-humanity table showing no major population under a fair-band ratio for reasons of our corpus (deliberate deferrals like the CJK floor documented instead).

- **Documentation complete:** this card matured, the ledger current, the attribution honored (CC-BY sources credited in the published card), and a weight license chosen deliberately on that day rather than defaulted.

Until then, this document is the weight's honest mirror: what it is, what it ate, what it still owes, and why it was built with this much care. It carries the names of real humanity, gathered the way we would want our own names gathered, For Enjoying.
