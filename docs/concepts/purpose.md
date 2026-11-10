# Purpose and principles

## The problem panAtlas exists to solve

Multi-modal models are hard to evaluate, and a single general score is the wrong instrument. What "good" means
changes with the **domain** (a dermatology read is nothing like an ECG forecast) and, inside a domain, with the
**context**: geography, culture, population, environment, care setting and equipment. A model that reads skin
lesions well on one skin type can fail on another; a triage model tuned on one country's intensive-care data can
misfire in a field clinic elsewhere. One leaderboard number hides exactly that variance. The plan's conclusion is
that evaluation has to be **structured by domain and stratified by context**, and that this cannot be done without
first **mapping the domain** (`PLAN.md` §1).

panAtlas is that map. It is a provenance-first knowledge graph that links the parts of an evaluation to each other:

- **concepts** of every field, grounded in that field's own vocabularies (MeSH for medicine, Wikidata and others across fields) and arranged as a curriculum, from foundations
  up through specialties and subspecialties;
- **datasets**, the corpora that models are trained on and the sets they are tested on, each registered once with a
  global identifier and an audit manifest;
- **models**, with what they were trained on (their curriculum) and what they were evaluated on;
- **benchmarks**, with what they measure, how to read their metric, and every score the atlas holds for them;
- the **documents** behind all of it (about 93 million training, evaluation and reference documents on the
  2026-09-24 count), each placed by concept.

**panAtlas covers every domain, not one field.** Medicine holds the most data today: most of the registered
datasets, the MeSH grounding and the specialty curriculum are medical, because that is where the work started. The
graph, the identifiers, the dataset managers and the federation are domain-agnostic, and other domains are built the
same way medicine was: ground the field's concepts in its own vocabularies, register its datasets, models and
benchmarks, and attach them to the same graph. Parts of the metadata layer (competency frameworks, the education
ladder, stratification standards) are medicine-shaped today, and each new domain gets its own parallels
(`PLAN.md` §2).

The atlas is meant to evaluate **humans and AI** against the same points: an expert taking a quiz on a concept and
a model graded through a controlled interface. That assessment surface is designed and not deployed (see
[What panAtlas is not](#what-panatlas-is-not)). What runs today is the evaluation of models.

## Who it is for

| Reader | What they use |
|---|---|
| Researchers choosing or comparing models | The explorer at panatlas.net, the [public API](../system/public-api.md), and the [Astral agent](../system/astral.md) |
| Engineers extending the atlas | The [build pipeline](../system/build-pipeline.md), the registries, the [repository map](../reference/repository-map.md) |
| Sites that hold data | The Cresco federation: a dataset joins where it sits ([Distributed](../distributed/index.md)) |
| Curators | The markdown fact-graph and its verification rules ([Architecture](architecture.md)) |
| Other agents and language-model clients | `tools.json` from the public API, and the SPARQL store through Astral |

## Principles

### Provenance first: sources are evidence, not authority

Every factual statement carries a provenance tag that says where it was seen. The markdown fact-graph enforces a
tag on every factual bullet (`atlas/CLAUDE.md`, rule 5), in one of a fixed set of forms (`src:<slug>@<ver>`,
`conv:YYYY-MM-DD`, `web:<url>`, `wikidata:Q<id>`, or a link to a `document-` page).

Citing a source does not make a claim true. Wikipedia, a clinical guideline, an ontology: each is a **registered
source**, recorded as a `source-` page with publisher, version strategy and licence, and the plan says plainly that
"registration is not endorsement" (`PLAN.md` §5). A claim becomes `verified` only through a human curator's
sign-off (`verified_by`). Seeding never verifies anything.

The same rule runs through the generated layers. Contamination labels that were never measured are downgraded to
`UNCHECKED` rather than shown as clean (`web/hygiene_enrich.py`); a model's curriculum entry records the SLURM jobs,
configuration and codebase of each training stage (`web/pipeline/model_curriculum.json`); a dataset is identified
by a URN and audited by a manifest hash ([Manifests](../metadata/manifests.md)).

### Describe once, evaluate many times

The project names this as its evaluation policy: describe once, evaluate many (DOEM) times.

!!! note "Definition not yet written down"
    The name and its framing are on record; a formal definition is not. The statements below describe how the
    current code behaves, which is the closest thing to a definition today. They are not a policy text.

In the code, a thing is described once and then reused by every evaluation that touches it:

- a dataset is registered once in `web/datasets.json` (schema `panatlas.datasets/1`), keyed by URN, and every graph
  node, manager report and public API record refers to that entry ([Dataset registry](../metadata/dataset-registry.md));
- a benchmark is a node with its metric, what it measures and how to read it, and every model's score attaches to
  that node ([Benchmarks](../metadata/benchmarks.md));
- every measured score, for every model type, sits in one index (`data/evals_index.json`, built by
  `web/build_evals_index.py`) that the site, the API and its clients all read ([Evaluation records](../metadata/evaluation-records.md)).

### Blanks are tracked as rigorously as facts

An unknown is recorded as an unknown, in the same field that would hold the value, so that it can be counted,
compared and closed. Examples from the code and records:

- `curriculum_disclosed: false` on external models: "we do not know what this model was trained on" becomes a
  recorded, comparable property (`web/build_curriculum.py`, [Models and curriculum](../metadata/models-and-curriculum.md)).
- The training-provenance gap register (`docs/curriculum-gap-register.md`) lists every blank that stops a full
  account of how a model was built, with a severity and a named recovery lead for each.
- Coverage is stamped honestly: record-level topic joins report the share of documents they cover (55.89 % for one
  pretraining corpus, 43.35 % for another, 2026-08-08) and list uncovered sources instead of blending them in
  (`web/build_record_level.py`).
- Registered-but-unscored models are listed with the reason they were not run (`listed_not_run` in the public API),
  and every evaluation response states what the atlas covers, "so a missed search cannot read as missing data"
  (`docs/public-api.md`).

### Measure, date, and say which it is

Counts shown on the site and in these docs are read from the deployed data or the source, not estimated. Every
statement of status says whether a thing is designed, built, or measured, and a measured number carries its date.
Claims are kept as narrow as the evidence: the exact-match contamination check, for example, is reported as "no
verbatim-document matches" and not as freedom from near-duplicate leakage (`docs/panatlas-system-and-interface.md`
§D.3).

### Wikipedia seeds; it is never the verified layer

Wikipedia is used three ways, none of them as an authority:

1. **Seed.** `atlas/tools/seed_wikipedia.py` writes a concept page pinned to an article revision (`oldid`), at
   `status: draft`, with a CC BY-SA attribution block and a needs-verification callout.
2. **Overlay.** MeSH is canonical over Wikipedia. A concept in MeSH has MeSH as its source of record; Wikipedia is at
   most a human-readable overlay, and is the identity only for genuinely non-MeSH nodes (`GRAPH_STANDARDS.md`).
3. **Coverage measure.** The Wikipedia world-view layer (run 20260901) links every document to one primary article
   with an evidence class, which lets the atlas say how much of the known world its documents cover and where it
   holds no evidence at all ([Web site](../system/web-site.md#world-map), [Astral](../system/astral.md)).

### Experts curate

People, not pipelines, decide what is verified. Curators sign in with their ORCID iD. The role model is
viewer, domain editor, reviewer and super curator, with capabilities `pa_read`, `pa_suggest`, `pa_edit`,
`pa_verify` and `pa_admin` (`web/wp-plugin/panatlas-explorer/panatlas-explorer.php`). Today a proposal is recorded
for a curator to act on and never auto-publishes; the target design moves verification to a reviewed and merged
pull request ([Architecture](architecture.md#the-architecture-pivot)).

### Structure travels; data stays

A dataset joins the atlas where it sits, under its owner's control. Only structure (identifiers, counts, edges,
hashes) crosses the federation; documents, pixels, embeddings and anything carrying protected health information
never do. See [Distributed](../distributed/index.md).

### Exact or not at all

A mirror or a store counts only when it is proven to recreate its source exactly. Each NSF Open Knowledge Network
mirror is proven against its upstream, and each SPARQL store must round-trip every graph exactly before it is
switched live ([Knowledge store](../system/knowledge-store.md)).

### Licence is a per-document attribute

The atlas ingests what it needs and records the licence of each document at ingest; the licence is consulted when
documents are shared or put into a training set (`web/acquisition/arxiv/arxiv_doc_index.py`,
`web/licence/`). Restricted and credentialed datasets are catalogued, never served
([Acquisition and licence](../metadata/acquisition-and-licence.md)).

## What panAtlas is not

| It is not | Why |
|---|---|
| A single leaderboard | Each benchmark keeps its own metric, and values are compared only within one benchmark (`docs/public-api.md`, rules). Rankings across benchmarks are mean positions, stated as such. |
| A data host | Datasets are link-only. The public API lists every record and serves no data. Restricted data is metadata only. |
| An authority by citation | A registered source is evidence. Verification is a curator's act. |
| A Wikipedia mirror | Wikipedia seeds drafts and measures coverage; MeSH is canonical. |
| An open wiki | Viewing the explorer is gated to an allowlist today, and edits go through proposals (see [Web site](../system/web-site.md#sign-in-and-the-access-gate)). |
| The assessment platform, yet | "Test yourself" quizzes, per-person mastery, gates, disputes and adaptive testing are designed in `PLAN.md` and not deployed (`docs/panatlas-system-and-interface.md`, Part A). |
| A finished federation | The substrate supports federation and the mesh runs; no external site contributes yet ([Distributed](../distributed/index.md)). |

!!! note "Scope statements from the plan"
    "Most extensive reference for multi-modal evaluation" is the long-term aim, not a current claim. The plan
    describes the defensible novelty at small scale as **structural**: a provenance-grounded, graph-structured,
    context-stratified evaluation atlas in which the reference corpus and the evaluation scaffold are the same
    network (`PLAN.md` §2).
