# Repository map

A map of the panAtlas repository at commit 57505c6. The repository has three directories (`atlas/`, `docs/`, `web/`)
and a set of design and operations documents at the root. Almost all code is under `web/`. Paths are relative to the
repository root.

The Cresco plugin (`cresco-panatlas`) and the operator kit for connecting a site (`agent-deployment`) are separate
repositories; see [Distributed](../distributed/index.md).

## Top level

| Path | What it is |
|---|---|
| `atlas/` | The markdown fact-graph seed: schema, pages, linter, Wikipedia seeder ([below](#atlas)) |
| `docs/` | Reference documents for the running system ([below](#docs)) |
| `web/` | Everything that builds, serves and federates the atlas ([below](#web)) |
| `README.md` | Operations handoff for the site (contains operational detail; not reproduced here) |
| `CLAUDE.md` | Operating notes for agents working on the site |
| `PLAN.md` | The current integrated plan: two-layer graph, sources, evaluation, substrate, governance, roadmap |
| `PLAN_v1_wordpress.md` | The first plan, built on WordPress; history |
| `ARCHITECTURE.md` | The federated markdown substrate design that replaced the WordPress plan |
| `ATLAS_SETUP_GUIDE.md` | How the Atlas knowledge-vault system that panAtlas follows is set up |
| `GRAPH_STANDARDS.md` | Decision record: one RDF graph, three layers, MeSH-canonical identity, named graphs as source of record, exactness of mirrors |
| `LAYERS.md` | Substrate, connectivity and embeddings as separate layers; the per-modality model registry; the attach process |
| `FEDERATION.md` | How agents contribute graph structure to one canonical panAtlas |
| `DATASET-MANAGERS.md` | One `cresco-panatlas` manager per dataset and how it reports |
| `PLAN-datasets.md` | Dataset inventory, global identity (URN) and audit (manifests) |
| `PLAN-dataset-plugins.md` | Dataset plugins and one canonical embedding model per modality |
| `PLAN-restricted-data-umls.md` | Plan for project-restricted data, starting with a licensed terminology release |
| `PanAtlas_Review_Recommendations.md` | An external-style review of the WordPress-era plan (psychometrics, API, governance) |
| `Medical_Curriculum_LLM_Training.md` | Research background: curriculum graphs, competency frameworks, evaluation |
| `Neuropath_FM.md`, `WSI_FM_PATH.md` | Research background on pathology foundation models |
| `.gitignore` | Keeps local credentials, environment files, embedding arrays and federation working files out of git |

## `atlas/`

| Path | What it is |
|---|---|
| `atlas/CLAUDE.md` | Schema and operating manual: page types, non-negotiables, provenance tag format |
| `atlas/index.md`, `atlas/log.md` | Entry map (spine plus generated catalog) and append-only log |
| `atlas/SOURCES.md`, `atlas/predicates.yaml` | Source roots table; the closed predicate vocabulary for facts |
| `atlas/00-maps/` | `map-cardiology-spine.md` |
| `atlas/20-concepts/` | 51 concept pages (medicine, 18 specialties, subspecialties, the cardiology teaching slice); read by `web/build_layered.py` |
| `atlas/22-documents/`, `24-entities/`, `26-facts/` | Sample document, entity and fact pages |
| `atlas/30-datasets/`, `32-items/` | Sample dataset and assessment item pages |
| `atlas/40-sources/` | Seven registered sources, including the internal curator source |
| `atlas/60-governance/` | Two domains, one jurisdiction and two stratification terms |
| `atlas/tools/lint_panatlas.py` | Schema and provenance linter (exit 0 clean, 1 errors, 2 warnings under `--strict`) |
| `atlas/tools/seed_wikipedia.py` | Seeds draft concept pages pinned to a Wikipedia revision |

## `docs/`

| File | What it is |
|---|---|
| `panatlas-system-and-interface.md` | System, data and interface reference written 2026-08-01, with an interface-design brief |
| `model-evaluation-system.md` | How language and imaging models are evaluated: battery, metric, lens, pipeline |
| `public-api.md` | The public API: where things live, rules, changelog |
| `artifact-types-and-model-curriculum.md` | The artifact-type vocabulary and the model curriculum record |
| `curriculum-gap-register.md` | Every known blank in training provenance, by severity, with a recovery lead |
| `evaluation-dimensions-and-metadata.md` | What panAtlas evaluates along, and its metadata schemas |
| `benchmark-ontology.md` | The multi-dimensional benchmark classification |
| `benchmark-suite-audit.md`, `benchmark-expansion-review.md` | Audit and inclusion rationale for the benchmark suite; proposed additions |

## `web/`

### Served site

| Path | What it is |
|---|---|
| `wp-plugin/panatlas-explorer/panatlas-explorer.php` | Plugin core: roles, audit, access gate, shortcodes, gated REST routes, Navigator, model lens ([Web site](../system/web-site.md)) |
| `wp-plugin/panatlas-explorer/includes/` | `public-api.php`, `public-evals.php` (public API), `wikimap.php`, `mesh.php`, `federation-admin.php` |
| `wp-plugin/panatlas-explorer/assets/` | `app.js`, `style.css`, `universe.js`, `wikimap.js`, `universe-bg.js`, `cosmos.bundle.mjs`, public `teaser_*.bin` |
| `wp-plugin/panatlas-explorer/data/` | Served snapshots: `graph.json`, `datasets.json`, `benchmarks_llm.json`, `mm_evals.json`, `evals_index.json`, `models.json`, `kg_graphs.json` |
| `wp-theme/panatlas/` | The site theme; `front-page.php` renders only the explorer shortcode |
| `infra/lockdown-wp-admin.conf` | The web server rule restricting login and admin paths, with the ORCID authorise exemption |
| `tests/` | `test_public_api.py` (API contract, `--stage`/`--live`), `public_api_harness.php`, `test_explore_e2e.py` |

### First interface (2026-07-26, superseded by the plugin)

| Path | What it is |
|---|---|
| `README.md` | Describes the first interface: a focus-plus-context explorer over the dataset inventory |
| `index.html`, `app.js`, `style.css` | Its static UI |
| `proxy.py` | Serves the UI and proxies the Navigator |
| `explorer/` | A PHP variant (`navigate.php`) and a builder that compiles `atlas/` pages into its `graph.json` |

### Build orchestration and deploy

| Path | What it is |
|---|---|
| `build_all.sh` | Ordered curation-layer build and verification ([Build pipeline](../system/build-pipeline.md)) |
| `deploy.sh` | Copies assets, data and API includes to the web host |
| `guard_eval_map.sh` | Rebuilds and redeploys the benchmark map if it goes missing or its sources change |
| `finish_v2.sh` | One-shot finish for one classifier pass: pull, merge, rebuild, verify, deploy |

### Graph builders and enrichment

| Path | What it is |
|---|---|
| `build_graph.py` | First-interface inventory graph from the vault's dataset catalog |
| `build_layered.py` | The core compiler of the served layered graph |
| `build_all_datasets.py`, `build_train_sources.py`, `build_source_topics.py`, `sft_wiring.py`, `build_corpus_structure.py` | Corpus-source accounting and training-data wiring |
| `build_benchmark_nodes.py`, `build_llm_benchmarks.py`, `build_missing_benchmarks.py`, `apply_bench_taxonomy.py`, `reconcile_benchmarks.py` | The benchmark catalog, its taxonomy, and reconciliation with what was run |
| `build_concept_remap.py`, `build_question_concept_map.py` | Benchmark items mapped to concepts |
| `build_artifact_types.py`, `build_curriculum.py`, `build_record_level.py`, `build_pretrain_multidim.py` | Artifact types, model curriculum, record-level typing, multi-dimension pretraining labels |
| `build_existing_meta.py`, `build_native_meta.py`, `build_field_values.py` | Existing per-document classification and native metadata, wired to concepts |
| `build_doc_relations.py` | Dataset-to-concept edges weighted by document count |
| `build_patho_evals.py`, `build_eval_map.py`, `build_evals_index.py` | Pathology results, the benchmark similarity map, the public evaluation index |
| `enrich_graph.py`, `decontam_enrich.py`, `hygiene_enrich.py`, `model_wiring.py`, `fix_registries.py` | Per-concept accuracy, decontamination status, honest relabelling, model wiring, registry fixes |
| `attach_full_eval.py`, `add_biomed_models.py` | Model nodes from the evaluation battery; external models with undisclosed training data |
| `strip_v6.py`, `dekos_v6strip.py` | Removed an unreleased model from the site (history; that model was later cleared and added) |
| `repair_foodatlas_nonmesh.py` | Splits FoodAtlas diseases that had been merged on a non-MeSH id |

### Registry, manifests, register, fold, link

| Path | What it is |
|---|---|
| `datasets.json` | The dataset registry, schema `panatlas.datasets/1` ([Dataset registry](../metadata/dataset-registry.md)) |
| `datasets_*.json` | Registry fragments by source (benchmarks, renal, TCGA, TCGA slides, foundation-model suite, stack embeddings, KOS-V6, …) |
| `models.json`, `codesystems.json`, `ID-POLICY.md` | Model and embedding-space registry; code systems; the rule that every entity and relation has a stable id |
| `dataset_manifest.py`, `dataset_manifest_parallel.py`, `derive_source_manifests.py` | Build and audit manifests ([Acquisition](../system/acquisition.md#manifests-and-folding)) |
| `manifests/` | Repository copies of dataset manifests (161 files) |
| `build_dataset_reports.py` | Each dataset manager's structure-only report |
| `register_*.py`, `renal_sbir_registry.py` | Upsert registry entries |
| `fold_*.py`, `test_fold_manifests.py` | Fold completion records and manifests into the registry; tests |
| `link_*.py` | Add dataset, concept and model nodes to the served graph |
| `sync_catalog.py` | Registry into the served catalog |
| `estate_doc_index.py`, `ledger_by_source.py` | Every estate document with its licence; per-source ledger counts |

### Embeddings, anchors and the local agent

| Path | What it is |
|---|---|
| `build_text_anchors.py`, `build_image_anchors.py`, `build_image_anchors_v2.py`, `precompute_pooled.py`, `exp_anchor_study.py`, `anchor_method_workflow.js` | Concept anchors in the text and CT image spaces, and the study that chose the image method |
| `embed_attach.py` | Relates new embeddings to concepts within one registered model space |
| `pa_local_agent.py` | The local agent a participating site runs; never ships raw data |
| `precompute_cellmap.py`, `pa_qmap.sbatch`, `pa_qmap_all.sbatch`, `BENCHMARK-QUESTION-MAPPING.md` | Question-to-concept mapping on the cluster: design and jobs |

### Pipelines and cluster-side code

| Path | What it is |
|---|---|
| `pipeline/` | Curation inputs and scripts: artifact types, model curriculum, groundings, `ui_harness.js`, `check_curriculum_vault.py`, evaluation ingest, existing-metadata harvest (`existing_meta/`), record-level typing (`record_level/`), pathology results (`patho_evals/`), item-to-concept maps (`qconcept2/`), universe builders (`universe/`), literature feed (`literature/`) |
| `dgx/` | Snapshot (2026-09-13) of the cluster-side build scripts ([Build pipeline](../system/build-pipeline.md#cluster-side-builds-webdgx)) |
| `acquisition/` | `okn/`, `openh/`, `renal/`, `umls/`, `arxiv/` ([Acquisition](../system/acquisition.md)) |
| `wikipedia_layer/` | The W-chain that builds the Wikipedia world-view layer (54 files) |
| `wikimap/` | Installer and notes for the world-map page |
| `licence/` | Per-document licence registry and builders |
| `rdf/` | RDF export, QLever store build, round trip, serving, the SPARQL client ([Knowledge store](../system/knowledge-store.md)) |
| `coverage/` | The W10 coverage service, its client, preparation and tests |
| `fm_suite/` | The tabular and time-series foundation-model evaluation suite: plan, model issues, runners and the export to panAtlas |

### Agents and federation

| Path | What it is |
|---|---|
| `astral/` | The Astral agent: service, tools, index, deploy files, tests ([Astral](../system/astral.md)) |
| `federation/` | Report and agent-profile schemas, a minimal agent client, the hub merge ([Federation](../distributed/federation.md)) |
| `mesh/` | The live mesh daemon, manager and file-repository deployers, and systemd units for supervision ([Operations](../distributed/operations.md)) |

### Reference data

| Path | What it is |
|---|---|
| `nacc/` | A neuropathology data dictionary, schemas, code lists and mappings |
| `qconcept/` | Per-benchmark distributions of items over concepts |
| `audit/` | Training-source manifests and the document-ledger summary |
| `concept_*.json`, `mesh_expand_clean.json`, `general_concept_space.json`, `subtopics.json`, `pa_concept_topics.json` | Concept grounding, similarity, accuracy and topic tables |
| `benchmark_*.json`, `bench_taxonomy*.json`, `benchmarks_llm.json`, `full_eval.json`, `predictor_evals.json`, `eval_readiness.json` | Benchmark audit, taxonomy, catalog and score inputs |
| `decontam_exact.json`, `doc_ledger_summary.json`, `footprint*.json`, `recount.json`, `master_rollup.json`, `estate_doc_rollup.json` | Contamination results and corpus footprint numbers |
| `foodatlas_*.json`, `fndds_*.json`, `nutrition.json`, `fhir.json`, `domains.json`, `multimodal.json` | Inputs to the layered graph: food and disease entities, FHIR resources, domains, the imaging registry |
| `dgx_sources.json`, `v4_train_sources.json`, `v5_train_sources.json`, `cell2concept.json` | Measured corpus sources, per-model training manifests, cell-to-concept table |
| `medicine_tree.dot`, `medicine_tree.png` | A rendering of the medicine concept tree |
