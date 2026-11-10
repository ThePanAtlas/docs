# Benchmarks

A benchmark in panAtlas is described once, by a registry entry, an ontology classification, a
taxonomy placement, a suite-fit verdict and a mapping from its items to concepts. Results attach to
it separately (see [Evaluation records](evaluation-records.md)). This page documents every field of
that description. Counts were computed with `python3` from the files at repo HEAD `57505c6` on
2026-11-10.

## Where benchmark metadata lives

| File | Records | What it holds | Written by |
|---|---:|---|---|
| `web/benchmarks_llm.json` | 109 benchmarks | The language-model benchmark registry: identity, description, taxonomy, decontamination, reference scores, battery scores, audit block, coverage | `build_llm_benchmarks.py`, `apply_bench_taxonomy.py`, `build_artifact_types.py`, `reconcile_benchmarks.py`, `build_eval_map.py` |
| `web/benchmark_audit.json` | 106 records | Audit source: `benchmark`, `panatlas_id`, `kind`, `purpose`, `capability`, `used_for`, `item_concept_linked`, `n_items`, `executable`, `how_to_run`, `engine`, `run_on_kos`, `kos_result`, `caveats`; partly joined into `audit` | audit pass |
| `web/wp-plugin/panatlas-explorer/data/benchmarks_llm.json` | 109 | The served copy. Byte-identical to `web/benchmarks_llm.json` at HEAD | `reconcile_benchmarks.py` writes both |
| `web/benchmark_ontology_facets.json` | 106 rows | The 26-dimension ontology classification, one row per benchmark | classification pass (`docs/benchmark-ontology.md`) |
| `web/bench_taxonomy.json` | 21 types, 10 domains, 106 classifications | Testing-type and domain taxonomy with definitions | taxonomy pass, applied by `apply_bench_taxonomy.py` |
| `web/bench_taxonomy_merged.json` | 21, 10, 103 | The same taxonomy; three classifications fewer (Natural Questions, Needle-in-a-Haystack, AlpacaEval) | taxonomy pass |
| `web/benchmark_suite_fit.json` | 106 dossiers | Suite-fit dossiers, the recommended suite, the fit rule, and 29 candidate benchmarks not yet catalogued | suite-fit audit |
| `web/qconcept/qconcept_<bench>_dist.json` | 21 files | First item-to-concept distribution per benchmark | `build_question_concept_map.py` |
| `web/pipeline/qconcept2/qconcept2_<bench>.jsonl` | 20 files, 48,931 rows | Judge-gated item-to-concept mapping, one row per item | cluster re-map, wired by `build_concept_remap.py` |
| `web/qconcept_stats.json` | 21 benchmarks | Fit statistics of the first mapping | `build_question_concept_map.py` |
| `web/pipeline/artifact_types.json` | 35 types | Artifact-type vocabulary and the benchmark task-format map | `build_artifact_types.py` reads it |
| Served graph | 106 `llm-benchmark`, 18 `benchmark` nodes | Benchmarks as graph nodes, with taxonomy and topic edges | see [Graph schema](graph-schema.md) |

Imaging and multimodal benchmarks (CT-RATE, RadGraph, pathology suites) are registered in
`mm_evals.json`, and the tabular and forecasting suites in `predictor_evals.json`. Both are
documented on [Evaluation records](evaluation-records.md), because those files carry results as
well as descriptions.

## The registry: `benchmarks_llm.json`

### Top-level keys

| Key | Type | Content |
|---|---|---|
| `suite` | string | `"KOS paper evaluation"`, the battery the registry was first built for |
| `arms` | object | `intrinsic` = "Arm A · intrinsic methods", `medical` = "Arm B · medical", `general` = "Arm C · general" |
| `capabilities` | list (35) | Capability vocabulary: `id` (`cap-<slug>`), `name`, `group` (one of 13 groups), `desc` |
| `benchmarks` | list (109) | One entry per benchmark, fields below |
| `taxonomy_types` | list (21) | Testing types: `name`, `definition` |
| `taxonomy_domains` | list (10) | Evaluation domains: `name`, `definition` |
| `_decontam_note` | string | Summary of the KOS-V4/V5 decontamination audit (6 benchmarks provably held out, 4 partial, the rest never on the blocklist) |
| `suite_meta` | object | `coverage` (counts) and `coverage_grid` (`capabilities`, `domains`, `grid` of capability × domain counts) |

### Benchmark entry fields

| Field | Entries | Type | Meaning |
|---|---:|---|---|
| `id` | 109 | string | `bench-<slug>`; the graph node id |
| `name` | 109 | string | Display name |
| `metric` | 109 | string | Headline metric as catalogued (for candidates this can be an arm note such as "Arm C, candidate") |
| `measures` | 109 | string | What the benchmark measures (Markdown) |
| `testing_type` | 109 | string | One of the 21 testing types |
| `provenance` | 109 | string | `official` (105) or `homegrown` (4: MedThink, Bias / demographic disparity, Long-context retrieval, DPM1 patient-management reasoning). Derived in `reconcile_benchmarks.py` |
| `verified_published` | 109 | bool | True when a verified published reference score exists to check the harness against (7: BFCL, IFEval, MedMCQA, MedQA, MMLU, PubMedQA, RGB) |
| `run_status` | 109 | string | `scored` (23) = run in the panAtlas battery; `cataloged` (86) = described, not yet run |
| `n_models_scored` | 109 | int | Number of models with a battery score |
| `arm` | 106 | string | `general` (67), `medical` (29), `intrinsic` (10) |
| `gated` | 106 | bool | Access is gated (2 true) |
| `composition` | 106 | string | Size and split description (Markdown) |
| `kos_usage` | 106 | string | How the KOS evaluation ran it (task name, metric, shots); empty for 64 |
| `tests` | 106 | list | Capability ids (`cap-*`) the benchmark tests; wired as `tests` edges |
| `scores` | 106 | object | Reference scores keyed by model variant, each `{value, metric, model, verified, source}`; populated for 7 benchmarks (BFCL, IFEval, MedMCQA, MedQA, MMLU, PubMedQA, RGB), 8 values |
| `domain` | 106 | string | Evaluation domain (taxonomy); one entry has `pathology` |
| `decontam` | 106 | object | Exact-document decontamination check, below |
| `audit` | 102 | object | Audit block, below |
| `artifact_types`, `artifact_type_ids` | 96 | list | Artifact-type labels and `atype-*` ids (see [Models and curriculum](models-and-curriculum.md)) |
| `tier` | 29 | string | KOS harness tier, for example `T6 MCQ`, `T7 BLURB`, `T10 context` |
| `higher_better` | 24 | bool | Direction of `battery_metric` (2 false: calibration ECE and demographic disparity) |
| `model_scores` | 23 | object | Battery scores keyed by model name, each `{value, metric}` |
| `battery_metric` | 23 | string | The metric the battery reports, for example `acc`, `macro-F1`, `ECE`, `disparity_score` |
| `topics_status` | 15 | string | State of the item-to-concept topic distribution |
| `mcq_floor` | 8 | string | Caveat that T6 MCQ is a floor for KOS base models |
| `topics` | 6 | object | `{n, distribution}`: item count and items per concept |
| `added_from_battery` | 3 | bool | Benchmark was added because it was run, not because it was catalogued |
| `score_is` | 2 | string | Which sub-test the score is ("the FCT test only", "RadGraph-XL only") |

### Decontamination block (`decontam`)

| Field | Meaning |
|---|---|
| `exact_doc_uid.checked` | Whether the exact-document membership check has been run (16 true, 90 false) |
| `exact_doc_uid.items` | Items checked |
| `exact_doc_uid.matched_either` | Items found in either training ledger |
| `exact_doc_uid.verdict` | Plain statement, for example "no verbatim-document match (held out at the exact-document level)" |
| `method` | "exact doc_uid membership (blake2b digest_size=16, raw text) vs doc_ledger_v4/v5 crosswalk; holdout_status from KOS decontamination-holdouts audit" |

On the graph node the same object also carries `holdout_status` and `holdout_note`. The status
values on the 106 `llm-benchmark` nodes are `unchecked` 85, `not_held_out` 10, `provably_held_out` 5,
`partial` 4, `proven_trained_on` 2.

!!! warning "Decontamination fields differ from the catalog document"
    `docs/evaluation-dimensions-and-metadata.md` (section G) documents
    `exact_doc_uid = {checked, matched_either, matched_v4, matched_v5}`. The data has
    `{checked, items, matched_either, verdict}`; no record has `matched_v4` or `matched_v5`.

### Audit block (`audit`)

102 entries carry an audit block with 15 keys. `build_eval_map.py` writes it by joining `benchmark_ontology_facets.json` (by name), `benchmark_audit.json` (by panAtlas id) and the suite-fit buckets of `benchmark_suite_fit.json` (by name):

| Field | Values |
|---|---|
| `kind` | Free text: `official-published (<citation>)` or homegrown |
| `what_it_does`, `how_it_works`, `the_document` | Free text |
| `executable` | `not-implemented` 42, `runnable-standard-harness` 19, `runnable-custom-driver` 16, `cached-not-run` 16, `homegrown-scorer` 8, `gated-unavailable` 1 |
| `run_on_kos` | `never-run` (58) or `v4-and-v5` (23), plus annotated variants of each |
| `item_concept_linked` | `no` 81, `yes-mesh; NO per-item correctness` 16, `yes-mesh; per-item correctness=TRUE` 5 |
| `n_items` | Integer item count |
| `data_on_disk` | true 52, false 50 |
| `concept_fit` | `partial` 35, `weak` 29, `strong` 23, `none` 15 |
| `concept_fit_how` | Free text justification |
| `suite` | `exclude` 61, `suite-core` 17, `suite-secondary` 15, `candidate` 9 |
| `domain` | Evaluation domain |
| `onto` | The ontology facets for this benchmark, joined by name from `benchmark_ontology_facets.json`: 18 controlled facets plus `subdomain` on every entry, `n_options` on 39; `typical_shots`, `decontam_checkable` and `panatlas_class` are not copied |
| `map` | `{x, y}`: position on the evaluation map, a UMAP projection of the benchmark's facet vector |

!!! warning "The audit block is smaller than documented"
    `docs/evaluation-dimensions-and-metadata.md` (section D) lists 23 audit fields, including
    `purpose`, `used_for`, `how_to_run`, `engine`, `kos_result`, `reporting`, `quality_notes`,
    `rationale` and `caveats`. None of these is in the served registry at HEAD. `purpose`,
    `used_for`, `how_to_run`, `engine`, `kos_result` and `caveats` exist in
    `web/benchmark_audit.json` (106 records), but `build_eval_map.py` does not copy them;
    `quality_notes` and `rationale` exist only in the `benchmark_suite_fit.json` dossiers.

## The benchmark ontology (facets)

`docs/benchmark-ontology.md` defines 26 dimensions in seven groups (A to G) and states that no model is
run to produce it: it is characterization only. `web/benchmark_ontology_facets.json` holds one row
per benchmark for 106 benchmarks. Each row has 27 keys: `benchmark` (the name), 22 controlled facets,
and four free-text fields (`subdomain`, `the_document`, `primary_metric`, `notes`).

Three of the documented dimensions are not in the facets file:

| Documented dimension | Where it is in the data |
|---|---|
| `executability` | `audit.executable` in the registry (same value set) |
| `suite_decision` | `audit.suite` in the registry (same value set) |
| `engine` | `engine` in `web/benchmark_audit.json` only, as free text (`n/a` for 38; otherwise strings such as "lm-eval-harness (pristine); stock task present"), not the documented controlled values; not copied into the registry |

Every facet and every value in use, with the number of benchmarks:

#### A. Identity and domain

| Facet | Values (benchmarks) |
|---|---|
| `domain` | `general` 45, `medical` 15, `biomedical` 9, `none` 9, `commonsense` 6, `clinical` 5, `science` 5, `math` 5, `code` 3, `safety` 3, `law` 1 |
| `subdomain` | free text; 105 distinct values over 106 rows |
| `language` | `english` 96, `multilingual` 10 |

#### B. What it measures

| Facet | Values (benchmarks) |
|---|---|
| `capability` | `knowledge-qa` 14, `commonsense-reasoning` 8, `representation-diagnostic` 8, `hallucination-faithfulness` 7, `long-context` 7, `multi-hop-qa` 6, `reading-comprehension` 5, `multi-step-reasoning` 5, `math-reasoning` 5, `clinical-reasoning` 4, `rag` 4, `safety-bias` 4, `instruction-following` 4, `code-generation` 3, `tool-use` 3, `truthfulness-factuality` 3, `named-entity-recognition` 2, `information-extraction` 2, `claim-verification` 2, `language-modeling` 2, `agentic` 2, `semantic-similarity` 1, `retrieval` 1, `clinical-note-generation` 1, `summarization` 1, `relation-extraction` 1, `calibration` 1 |
| `knowledge_source` | `web` 20, `mixed` 17, `crowd` 17, `synthetic` 13, `medical-exam` 11, `biomedical-literature` 9, `model-internal` 9, `clinical-notes-ehr` 6, `textbook` 4 |

#### C. Item and task shape

| Facet | Values (benchmarks) |
|---|---|
| `the_document` | free text; 106 distinct values over 106 rows |
| `task_format` | `mcq` 25, `open-generation` 21, `mixed` 17, `numeric-answer` 12, `binary-classification` 7, `multi-class-classification` 5, `agentic-trajectory` 3, `pairwise-preference` 3, `sequence-labeling` 2, `similarity-regression` 2, `cloze-continuation` 2, `code-completion` 2, `tool-call` 2, `retrieval` 1, `ranking` 1, `span-extraction` 1 |
| `n_options` | `null` 67, `4` 18, `2` 7, `5` 6, `3` 5, `10` 3 |
| `output_type` | `single-label` 36, `free-text` 33, `structured` 14, `numeric` 13, `boolean` 3, `code` 3, `entity-tags` 2, `ranked-list` 2 |
| `modality` | `text` 98, `code` 8 |

#### D. Scoring

| Facet | Values (benchmarks) |
|---|---|
| `scoring_method` | `accuracy` 32, `mixed` 15, `exact-match` 12, `llm-judge` 10, `custom-geometry` 10, `acc_norm` 6, `entity-f1` 3, `label-f1` 3, `pass@k` 3, `programmatic-verifier` 3, `token-f1` 2, `win-rate` 2, `correlation` 1, `rubric-score` 1, `macro-f1` 1, `bits-per-byte` 1, `ece-calibration` 1 |
| `primary_metric` | free text; 94 distinct values over 106 rows |
| `scoring_determinism` | `deterministic-programmatic` 67, `reference-metric` 18, `llm-judge` 15, `execution-based` 6 |
| `judge_dependency` | `none` 88, `llm-judge` 17, `user-simulator` 1 |

#### E. Running it

| Facet | Values (benchmarks) |
|---|---|
| `model_stage` | `instruct-only` 39, `both` 37, `base-safe` 30 |
| `typical_shots` | `0-shot` 57, `few-shot` 28, `n/a` 15, `cot` 6 |
| `compute_cost` | `cheap` 48, `medium` 41, `expensive` 17 |
| `license_access` | `open` 96, `gated-license` 4, `api-judge-required` 4, `gated-dua` 2 |

#### F. Quality and trust

| Facet | Values (benchmarks) |
|---|---|
| `reporting_prevalence` | `common` 45, `occasional` 33, `ubiquitous` 24, `rare` 4 |
| `difficulty` | `moderate` 71, `hard` 24, `saturated` 8, `anti-saturation-designed` 3 |
| `contamination_risk` | `medium` 42, `high` 41, `low` 23 |
| `decontam_checkable` | `yes` 57, `partial` 30, `no` 19 |

#### G. Fit to the concept model

| Facet | Values (benchmarks) |
|---|---|
| `concept_fit` | `partial` 35, `weak` 30, `strong` 23, `none` 18 |
| `concept_space` | `none` 57, `wikipedia-general` 23, `mesh-medical` 19, `ontology-entities` 7 |
| `panatlas_class` | `A-programmatic` 41, `mcq-standard` 36, `probe-diagnostic` 17, `B-llm-judge` 12 |

#### Free text

| Facet | Values (benchmarks) |
|---|---|
| `notes` | free text; 106 distinct values over 106 rows |

Values that `docs/benchmark-ontology.md` defines but no benchmark uses: `domain` `multilingual`;
`language` `other`; `knowledge_source` `code-repos`; `output_type` `span-set`; `modality`
`text+image`, `structured-ehr`; `scoring_method` `rouge`, `bertscore`, `bleu`;
`scoring_determinism` `human-required`; `judge_dependency` `human`; `license_access` `restricted`.

!!! warning "The per-benchmark table in the ontology document mislabels a column"
    In `docs/benchmark-ontology.md`, the per-benchmark table's column headed "scoring" contains
    `scoring_determinism` values (`deterministic-programmatic`, `reference-metric`, …), not
    `scoring_method` values.

The decision axis is group G. `concept_fit` grades whether individual items relate to concepts:
`strong` (each item maps to one dominant concept), `partial` (diffuse, or the scored quantity is a
relation or inference), `weak` (only coarse mapping), `none` (no item-to-concept relation).
`panatlas_class` gives the operational class: `A-programmatic` (deterministic or execution scoring,
suite-eligible), `B-llm-judge` (the score depends on a judge), `mcq-standard`, and
`probe-diagnostic` (no item-to-concept relation).

## Taxonomy: testing types, domains, capabilities

Three controlled axes place a benchmark in the graph. All three are graph nodes.

| Axis | Values | Graph nodes | Edges |
|---|---|---|---|
| Testing type | 21 (definitions in `bench_taxonomy.json`) | `testing-type`, ids `type-<name>` | `llm-benchmark` `is_type` → `testing-type` (106); `eval-suite` `has_type` → `testing-type` (21) |
| Evaluation domain | 10 (`medical`, `biomedical`, `science`, `math`, `law`, `commonsense`, `general`, `none`, `code`, `safety`) | `eval-domain`, ids `evdomain-<name>`; 9 nodes (no node for `none`) | `llm-benchmark` `in_domain` → `eval-domain` (97 = 106 minus the 9 `none` benchmarks) |
| Capability | 35 capabilities in 13 groups | `capability` (`cap-*`), `capability-group` (`capgroup-*`) | `llm-benchmark` `tests` → `capability` (247); `capability-group` `groups` → `capability` (35) |

The 21 testing types and their benchmark counts (from `bench_taxonomy.json` classifications):
`knowledge-qa` 20, `commonsense-reasoning` 8, `representation-diagnostic` 8, `rag` 7, `long-context` 7,
`multi-hop-qa` 6, `tool-use` 5, `multi-step-reasoning` 5, `arithmetic-math` 5,
`information-extraction` 5, `reading-comprehension` 5, `clinical-nlp` 4, `instruction-following` 4,
`truthfulness-factuality` 4, `safety-bias` 3, `code-generation` 3, `hallucination-faithfulness` 2,
`claim-verification` 2, `semantic-similarity` 1, `language-modeling` 1, `calibration` 1.

The 13 capability groups are `code`, `health`, `instruction`, `knowledge`, `language`, `meta`,
`nli`, `other`, `rag`, `reasoning`, `safety`, `summarization`, `truthfulness`.

The testing type (taxonomy, 21 values) and the ontology `capability` facet (27 values) are separate
vocabularies. For example the taxonomy has `arithmetic-math` and `clinical-nlp`; the facet has
`math-reasoning`, `clinical-reasoning`, `named-entity-recognition` and `agentic`.

## Suite fit: `benchmark_suite_fit.json`

The suite-fit audit decides which benchmarks belong to the concept-relational suite. Its rule, stated
in `suite.principles`, has a decisive first test: a benchmark belongs only if each individual item is
a document that maps to a dominant concept grounded in MeSH (clinical and biomedical) or Wikipedia
(general). This is judged before and independently of score quality. Reporting prevalence is the
second criterion.

| Key | Content |
|---|---|
| `dossiers` (106) | Per benchmark: `benchmark`, `capability`, `what_it_does`, `how_it_works`, `the_document`, `concept_fit`, `concept_fit_how`, `reporting_prevalence`, `quality_notes`, `recommendation`, `rationale` |
| `suite.suite_core` (17) | `benchmark`, `arm`, `concept_fit`, `reporting_prevalence`, `the_document`, `concept`, `why_core`, `open_work` |
| `suite.suite_secondary` (15) | Same, with `why_secondary` |
| `suite.diagnostic_or_excluded` (73) | `benchmark`, `concept_fit`, `category`, `reason` |
| `suite.add_to_fill_gaps` (24) | `name`, `concept_fit`, `reporting_prevalence`, `availability`, `gap_filled`, `priority` |
| `suite.coverage_map`, `suite.medical_coverage`, `suite.principles` | Free-text analysis |
| `missing.candidates` (29) | Benchmarks not in the registry: `name`, `what`, `how`, `the_document`, `concept_fit`, `reporting_prevalence`, `fills_gap`, `availability` |

The core suite is MedQA (USMLE 4-opt), MedMCQA, MedXpertQA (Text), Medical-MMLU (9-subject), MMLU,
MMLU-Pro, ARC-Challenge, ARC-Easy, OpenBookQA, PubMedQA, MIRAGE, SciFact, AfriMed-QA, TruthfulQA,
SimpleQA, GSM8K and MATH. The secondary suite is Medbullets, MedExpQA, CareQA, MedNLI, MEDEC,
Med-HALT, CommonsenseQA, HellaSwag, PIQA, WinoGrande, BoolQ, MedRAG, ASDiv (CoT), MathQA and GPQA.

!!! warning "Three suite-decision tallies disagree"
    The core (17) and secondary (15) lists agree everywhere. The rest does not:
    `dossiers[].recommendation` gives `candidate` 43, `exclude` 31;
    `suite.diagnostic_or_excluded` lists 73 benchmarks; the registry's `audit.suite` gives
    `exclude` 61, `candidate` 9 (over 102 audited entries). Treat `audit.suite` as the value the site
    reads.

## Coverage: catalogued against scored

`reconcile_benchmarks.py` matches each catalogued benchmark to the run battery (`full_eval.json`) by
normalised name and writes `suite_meta.coverage`. At HEAD:

| Quantity | Value |
|---|---:|
| Catalogued (`total`) | 109 |
| Scored | 23 |
| Gap (catalogued, not run) | 86 |
| Official | 105 |
| Homegrown | 4 |
| Verified against a published score | 7 |

By testing type (catalogued / scored): `knowledge-qa` 20/6, `representation-diagnostic` 8/0,
`long-context` 8/1, `commonsense-reasoning` 8/2, `rag` 7/0, `multi-hop-qa` 6/0,
`multi-step-reasoning` 6/2, `arithmetic-math` 5/1, `information-extraction` 5/4,
`reading-comprehension` 5/1, `tool-use` 5/0, `clinical-nlp` 4/0, `instruction-following` 4/1,
`safety-bias` 4/1, `truthfulness-factuality` 4/0, `code-generation` 3/0, `claim-verification` 2/0,
`hallucination-faithfulness` 2/2, `calibration` 1/1, `language-modeling` 1/0,
`semantic-similarity` 1/1.

!!! note "Snapshot in the model-evaluation document"
    `docs/model-evaluation-system.md` section 9 gives a snapshot of 110 catalogued, 24 scored, 86
    gaps, 106 official. The registry at HEAD has 109, 23, 86, 105. The evaluation index
    (`evals_index.json`) counts 26 scored language benchmarks because it also counts scored
    sub-benchmarks; see [Evaluation records](evaluation-records.md).

## Question → concept mapping

The mapping gives each benchmark item a concept, so a model's per-item correctness rolls up to
per-concept accuracy. It exists in two generations. Item text and answers are not in the
repository; only distributions and item-to-concept rows are.

### First mapping (`qconcept`)

Designed in `web/BENCHMARK-QUESTION-MAPPING.md` and implemented in
`build_question_concept_map.py`. Each question is embedded with BioClinical-ModernBERT-large (1024-d,
masked mean pool, `max_length` 1024, L2-normalised), assigned to the nearest of 4,096 corpus cell
centroids, and given that cell's dominant concept, the same path the corpus documents use.

| Row field (`qconcept_<bench>.jsonl`) | Meaning |
|---|---|
| `question_id` | Source id, else `<bench>__<index>` (six-digit, zero-padded) |
| `doc_uid` | `blake2b` hex digest of the question text |
| `benchmark` | `bench-<slug>` |
| `concept` | Concept node id, or `unmapped` |
| `cell` | Corpus cell key |
| `cosine` | Cosine to the cell centroid |

The repository holds the 21 distribution files (`{benchmark, n, distribution}`) and
`qconcept_stats.json` (per benchmark: `n`, `n_concepts`, `top_concept`, `top_share`,
`entropy_bits`, `mean_cosine`, `poor_fit_frac`). The row files are on the cluster. The 21
benchmarks are AfriMed-QA, AGIEval LSAT-AR, ARC-Challenge, ARC-Easy, ASDiv, BoolQ, CommonsenseQA,
COPA, GPQA, GSM8K, HellaSwag, LAMBADA, Medical-MMLU, MedMCQA, MedQA, MedXpertQA, MMLU-Pro, MMLU,
OpenBookQA, PubMedQA and WinoGrande. This mapping feeds `concept_accuracy.json` and the
`measured_on` edges ([Evaluation records](evaluation-records.md)).

!!! warning "The `doc_uid` in question rows is not the ledger `doc_uid`"
    `build_question_concept_map.py` computes `hashlib.blake2b(text).hexdigest()` with the default
    64-byte digest. The training-ledger identity used for decontamination is
    `blake2b(raw_text, digest_size=16)`. The two cannot be joined.

### Judge-gated mapping (`qconcept2`)

`build_concept_remap.py` wires a corrected mapping from `web/pipeline/qconcept2/`. Its rows carry
`question_id`, `benchmark`, `concept` and `cosine`. Over the 20 files there are 48,931 rows, of
which 2,925 are `unmapped`. The method string the script stamps is "judge-gated: BGE-large
retrieval + gemma-4-31B concept judge". The script:

1. creates the Wikipedia-grounded general concepts from `general_concept_space.json` (homes for
   math, science and reading items);
2. rebuilds each benchmark's distribution, stored on the node as
   `topics = {n, unmapped, distribution}`;
3. wires the 15 largest concepts per benchmark as `covers_topic` edges with `n` = number of items
   (300 edges at HEAD).

`hygiene_enrich.py` then derives a `grounded_in` edge (attribute `via: mesh:<UI>`) from a benchmark
to every MeSH-grounded concept it reaches through `covers_topic`, `tests` or `covers` (239 edges).

!!! warning "Design, graph and served registry disagree on the mapping"
    `BENCHMARK-QUESTION-MAPPING.md` requires one embedding space (BioClinical-ModernBERT) and lists
    MedMCQA (270 questions) as the only benchmark mapped. The served graph's topic edges come from
    the judge-gated BGE mapping over 20 benchmarks (MedMCQA is not among them). The served
    `benchmarks_llm.json` still carries `topics` on 6 entries and `topics_status` "pending general
    concept space" on 15, while the graph nodes carry judge-gated `topics` on 20. The per-concept
    accuracies on concept nodes still use the first mapping's concept ids.

## Benchmark nodes in the graph

### `llm-benchmark` (106)

Built from the registry. Fields on every node: `id`, `label`, `kind`, `layer` (`concept`), `arm`,
`metric`, `gated`, `measures`, `composition`, `kos_usage`, `benchmark` (always true), `modality`
(always `text`), `testing_type`, `domain`, `concept_class` (always `evaluation`), `decontam`.
On some: `artifact_types`, `artifact_type_labels`, `artifact_type_via` (96); `tier` (29); `topics`,
`topics_status` (20); `grounding`, `wp_topic`, `wp_url` (7: intrinsic methods given a Wikipedia
grounding by `hygiene_enrich.py`).

`artifact_type_via` records how the artifact types were assigned: `override` (34, from
`benchmark_overrides` in `artifact_types.json`) or `facet:<task_format>` (from
`benchmark_task_format_map`). Ten nodes have none; representation diagnostics are deliberately
untyped.

Edges out of an `llm-benchmark`: `is_type`, `in_domain`, `tests`, `covers_topic`, `grounded_in`,
`has_artifact_type`. Edges into it: `scored` and `evaluated_on` from models.

### `benchmark` (18): imaging benchmarks

| Field | CT benchmarks (10, `layer: dataset`) | WSI benchmarks (8, `layer: concept`) |
|---|---|---|
| `modality` | `imaging-ct` | `imaging-wsi` |
| `task` | Task description | not present |
| `status` | `verified` (8) or `needs-verification` (2) | not present |
| `test_sets` | Dataset ids of the held-out test sets | not present |
| `tests_concepts` | Concept labels the benchmark tests | not present |
| `held_out_total` | Number of held-out cases | not present |
| `decontam` | Same block as above | not present |
| `domain`, `metric`, `measures`, `n_models`, `source` | not present | present |
| `artifact_types` | `atype-medical-image` | `atype-whole-slide-image` |

CT benchmarks receive `test_set_of` edges from their test-set datasets (14 edges). WSI benchmarks
mirror benchmarks in `mm_evals.json`.
