# Graph schema

This page documents every node type and every edge type in the panAtlas served graph, with the
property keys each one carries and the script that writes it. Every count on this page was computed
with `python3` from the served graph file at repo HEAD `57505c6` on 2026-11-10. Nothing here is
taken from a summary block or a design document unless the text says so.

The served graph is `web/wp-plugin/panatlas-explorer/data/graph.json`. It is the property graph the
explorer renders, the input to the RDF export ([RDF vocabulary](rdf-vocabulary.md)) and the input to
the evaluation index behind the public API ([Evaluation records](evaluation-records.md)). In the
terms of `GRAPH_STANDARDS.md` it is layer 3, the "working / evidence property graph", which is a
projection of the terminology backbone and the clinical instance layer. See
[Knowledge layers](../concepts/layers.md) for how the layers relate.

## Totals

| Quantity | Value at HEAD `57505c6` |
|---|---:|
| Nodes | 6,187 |
| Edges | 17,119 |
| Node kinds (`kind`) | 32 |
| Edge relations (`rel`) | 36 |
| Values of `layer` | 7 |
| Duplicate node ids | 0 |
| Duplicate `(from, to, rel)` triples | 0 |
| Edges whose `from` or `to` is not a node | 0 |
| Self-loops | 0 |

The deployed site can lag or lead the repository. The vault records these live totals:

| Date | Nodes | Edges | Where recorded |
|---|---:|---:|---|
| 2026-09-12 | 6,078 | 16,680 | vault `project-panatlas`, deploy after the neuropathology and renal links |
| 2026-09-26 | 6,088 | 16,891 | vault `project-panatlas`, input to the first RDF export (213,647 quads) |
| 2026-10-16 | 6,136 | 17,035 | vault `project-panatlas`, deploy of the KOS-V6 curriculum (panAtlas commit `5af1a69`) |
| 2026-11-10 | 6,187 | 17,119 | this page, repo HEAD `57505c6` |

!!! warning "The `stats` block inside `graph.json` is stale"
    `graph.json` carries a `stats` object, but several scripts rewrite parts of it and
    `enrich_graph.py` replaces it wholesale, so it no longer matches the file. At HEAD:
    `stats.edges` says 13,869 (the file has 17,119); `stats.edges_by_rel` has no entry for ten
    relations that exist (for example `has_artifact_type`, `stage_trained_on`, `has_register`);
    `stats.layers` reports `concept` 203, `dataset` 174, `ontology` 43; `stats.concept_classes`
    reports 44 `model` nodes (there are 90); and `stats.curriculum.models_curriculum_undisclosed`
    is 1 (36 model nodes carry `curriculum_disclosed: false`). Compute counts from `nodes` and
    `edges`, never from `stats`.

## File format

`graph.json` is one JSON object with four keys:

| Key | Type | Content |
|---|---|---|
| `stats` | object | Summary counters written by the build scripts (stale, see above) plus measured corpus figures such as `footprint`, `documents_mapped` and `image_documents` |
| `roots` | list | `["atlas-root"]`, the entry node for navigation |
| `nodes` | list | 6,187 node objects |
| `edges` | list | 17,119 edge objects |

### Node object

Four keys are on every node: `id`, `label`, `kind`, `layer`. Every other key is optional and
depends on the kind. The most widely used optional keys are:

| Key | Nodes carrying it | Meaning |
|---|---:|---|
| `source` | 5,953 | Free-text statement of where the node's content came from |
| `modality` | 5,701 | `text`, `structured`, `imaging-ct`, `imaging-ultrasound-rf`, `time-series`, `imaging-wsi`, `imaging`, `genomics`, or an `omics-*` value |
| `concept_class` | 5,577 | `knowledge` (5,252), `evaluation` (195), `model` (90), `artifact-type` (35), `register` (5) |
| `built_by` | 5,543 | Free-text statement of the method that produced the node (for example "grounded to MeSH via UMLS UTS (resolver + adversarial audit + live confirmation)") |
| `desc` | 5,500 | Description |
| `grounding` | 5,328 | Which vocabulary grounds the node; see [Controlled vocabularies](codesystems.md) |
| `canonical_id` | 5,013 | Canonical identity, `<prefix>:<code>`; prefixes in use are `mesh` (3,390), `foodon` (1,558), `wikipedia` (24), `fdc` (24), `panatlas` (17) |
| `mesh_dui`, `mesh_name` | 3,400 | MeSH descriptor UI and preferred name |

### Edge object

Every edge has exactly four required keys: `from`, `to`, `rel`, `id`. Some relations add
attributes, listed per relation below.

The edge `id` is content-addressed:

```python
"e-" + hashlib.blake2b(f"{from}|{to}|{rel}".encode(), digest_size=10).hexdigest()
```

The same formula appears in `enrich_graph.py`, `hygiene_enrich.py`, `build_curriculum.py` and
`build_concept_remap.py`, so rerunning a script adds no duplicate edges. 16,916 of the 17,119 edges
match the formula. The other 203 are the `covers_topic` edges with `basis: arxiv-lexalign`, whose ids
have the form `e-arxiv-<MeSH UI>-<target id>`.

### `layer` values

`layer` is a coarse partition used by the explorer. It is not the same thing as the knowledge
layers of `LAYERS.md` or `GRAPH_STANDARDS.md` (see [Knowledge layers](../concepts/layers.md)).

| `layer` | Nodes | Kinds in it |
|---|---:|---|
| `foodatlas` | 4,752 | `disease`, `food` |
| `concept` | 679 | `concept`, `llm-benchmark`, `model`, `capability`, `artifact-type`, `specialty`, `testing-type`, `capability-group`, `eval-domain`, `benchmark` (8 WSI benchmarks), `register`, `modality`, `codebase`, `group`, `root`, `gate`, `system` (1), `eval-suite`, `measurement`, `method` |
| `dataset` | 527 | `dataset`, `benchmark` (10 CT benchmarks), `guideline`, `system` (1) |
| `fndds` | 172 | `food-category` |
| `ontology` | 34 | `fhir`, `authority`, `kg` |
| `process` | 14 | `training-stage` |
| `domain` | 9 | `domain`, `gen-category`, `atlas-root` |

## Node kinds

| Kind | Nodes | `layer` value | ID pattern | Emitted by |
|---|---:|---|---|---|
| `disease` | 3,170 | `foodatlas` | `fa-dis-<MeSH UI or upstream id>` | `build_layered.py` (FoodAtlas); `repair_foodatlas_nonmesh.py` (10 non-MeSH diseases) |
| `food` | 1,582 | `foodatlas` | `fa-food-<FoodOn or FDC id>` | `build_layered.py` (FoodAtlas) |
| `dataset` | 513 | `dataset` | `dataset-<slug>`, `dsft-<slug>` (SFT sources); one `kg` node also uses `dataset-` | `build_layered.py`, `build_graph.py`, `build_all_datasets.py`, `build_train_sources.py`, `sft_wiring.py`, `build_corpus_structure.py`, `link_datasets_to_nodes.py`, `link_arxiv.py`, `link_neuropath.py`, `link_openh.py`, `link_renal.py`, `link_predictors.py`, `build_curriculum.py` (inline datasets) |
| `concept` | 312 | `concept` | `concept-<slug>`; `mesh-D<UI>` (MeSH tree expansion) | `build_layered.py` (curated pages, MeSH tree expansion), `build_concept_remap.py` (general Wikipedia concepts), `enrich_graph.py` (pending concepts), `build_artifact_types.py` (4 topics), `build_existing_meta.py`, `build_doc_relations.py`, `link_renal.py` |
| `food-category` | 172 | `fndds` | `fndds-cat-<WWEIA code>` | `build_layered.py` (FNDDS) |
| `llm-benchmark` | 106 | `concept` | `bench-<slug>` | `build_llm_benchmarks.py`, `build_missing_benchmarks.py` |
| `model` | 90 | `concept` | `model-<slug>`, `model-predictor-<slug>` | `attach_full_eval.py`, `add_biomed_models.py`, `build_curriculum.py`, `link_neuropath.py`, `link_predictors.py` |
| `capability` | 35 | `concept` | `cap-<slug>` | `build_llm_benchmarks.py` |
| `artifact-type` | 35 | `concept` | `atype-<slug>` | `build_artifact_types.py` |
| `specialty` | 28 | `concept` | `concept-<slug>` | `build_layered.py` (atlas pages with `concept_kind: map`), `link_neuropath.py` |
| `testing-type` | 21 | `concept` | `type-<testing type>` | `apply_bench_taxonomy.py` |
| `fhir` | 18 | `ontology` | `fhir-<resource>`, `nacc-<record>` | `build_layered.py` (`fhir.json`, NACC schemas) |
| `benchmark` | 18 | `dataset` (10), `concept` (8) | `bench-<slug>` | `build_benchmark_nodes.py` (CT, layer `dataset`); `build_patho_evals.py`, `link_neuropath.py` (WSI, layer `concept`) |
| `authority` | 15 | `ontology` | `onto-<system>` | `build_layered.py` (`codesystems.json`, `nutrition.json`, `fhir.json`, NACC) |
| `training-stage` | 14 | `process` | `stage-<model>-<stage>` | `build_curriculum.py` |
| `capability-group` | 13 | `concept` | `capgroup-<group>` | `build_llm_benchmarks.py` |
| `eval-domain` | 9 | `concept` | `evdomain-<domain>` | `apply_bench_taxonomy.py` |
| `domain` | 5 | `domain` | `domain-<slug>` | `build_layered.py` (`domains.json`) |
| `register` | 5 | `concept` | `register-<slug>` | `build_existing_meta.py` |
| `modality` | 5 | `concept` | `concept-<slug>` | `link_openh.py` |
| `codebase` | 4 | `concept` | `codebase-<slug>` | `build_curriculum.py` |
| `guideline` | 3 | `dataset` | `doc-<slug>` | `build_layered.py` (`nutrition.json`) |
| `gen-category` | 3 | `domain` | `gen-<slug>` | `build_layered.py` (`domains.json`) |
| `group` | 2 | `concept` | `group-<slug>` | `build_layered.py` |
| `system` | 2 | `dataset` (1), `concept` (1) | `system-<cluster slug>`, `sys-<slug>` | `build_curriculum.py` (training cluster); `build_layered.py` (`nutrition.json`) |
| `root` | 1 | `concept` | `concept-medicine` | `build_layered.py` |
| `gate` | 1 | `concept` | `concept-<slug>` | `build_layered.py` |
| `kg` | 1 | `ontology` | `dataset-foodatlas` | `build_layered.py` (`nutrition.json`) |
| `atlas-root` | 1 | `domain` | `atlas-root` | `build_layered.py` (`domains.json`) |
| `eval-suite` | 1 | `concept` | `suite-<slug>` | `build_llm_benchmarks.py` |
| `measurement` | 1 | `concept` | `concept-<slug>` | `link_openh.py` |
| `method` | 1 | `concept` | `concept-<slug>` | `link_openh.py` |

!!! note "Two kinds named benchmark"
    `llm-benchmark` (106) is a language-model benchmark from the benchmark registry
    (`benchmarks_llm.json`). `benchmark` (18) is an imaging benchmark: 10 CT benchmarks built by
    `build_benchmark_nodes.py` with `layer: dataset`, and 8 whole-slide-image benchmarks built by
    `build_patho_evals.py` and `link_neuropath.py` with `layer: concept`. Both are described on
    [Benchmarks](benchmarks.md).

### Property keys by kind

For each kind, the first list holds the keys present on every node of that kind. The second list
holds the keys present on only some nodes, with the number of nodes that carry each. Field meanings
for the evaluation, model and vocabulary kinds are on [Benchmarks](benchmarks.md),
[Evaluation records](evaluation-records.md), [Models and curriculum](models-and-curriculum.md) and
[Controlled vocabularies](codesystems.md). Dataset fields are on
[Dataset registry](dataset-registry.md).

#### `disease` (3,170)

On every node: `id`, `label`, `kind`, `layer`, `grounding`, `modality`, `desc`, `source`, `built_by`, `fa_n_chem`, `fa_n_food`, `fa_top_foods`, `fa_top_chemicals`, `concept_class`.

On some nodes (count): `mesh_dui` (3,160), `mesh_name` (3,160), `canonical_id` (3,160), `mesh_url` (3,160), `mesh_tree` (3,160), `grounding_note` (10).

#### `food` (1,582)

On every node: `id`, `label`, `kind`, `layer`, `grounding`, `canonical_id`, `modality`, `fa_n_chem`, `fa_n_disease`, `fa_top_chemicals`, `fa_top_diseases`, `desc`, `source`, `built_by`, `concept_class`.

#### `dataset` (513)

On every node: `id`, `label`, `kind`, `layer`, `modality`.

On some nodes (count): `provenance` (502), `dtype` (502), `source` (481), `measured` (365), `built_by` (363), `benchmark` (332), `vault_desc` (280), `vault_page` (280), `vault_status` (280), `evalcap` (247), `origin` (231), `stage` (224), `tokens` (222), `docs` (209), `location` (195), `topics` (187), `access` (173), `data_stage` (162), `is_sft` (160), `artifact_types` (160), `artifact_type_labels` (159), `contamination` (132), `doc_concepts` (132), `doc_total` (132), `tier` (118), `domain` (118), `trained_by` (118), `used_in_training` (116), `corpus_status` (115), `tokens_measured` (107), `model` (105), `sft_type` (103), `records` (103), `sft_contents` (101), `parent_mix` (101), `record_topics` (101), `record_registers` (101), `record_register_atypes` (101), `record_topic_concepts` (100), `desc` (97), `cls_domain` (58), `cls_data_type` (58), `cls_register` (58), `per_model` (56), `share_pct` (56), `part_of_corpus` (56), `artifact_topics` (56), `cls_difficulty` (56), `cls_mean_quality` (56), `cls_docs` (56), `cls_sampled` (56), `cls_source` (56), `has_doc_embeddings` (56), `doc_classification_status` (56), `tok_per_doc` (55), `category` (52), `urn` (52), `docs_counted` (47), `license` (44), `host` (42), `scale` (42), `native_fields` (39), `native_field_values` (38), `native_field_sample_n` (38), `domain_mix` (30), `train_samples` (30), `quality` (30), `n_subtopics` (30), `n_domains` (30), `modality_detail` (30), `owner` (23), `data_type` (21), `register` (21), `modalities` (10), `status` (10), `embedding_refs` (9), `license_note` (9), `contamination_prior` (6), `contamination_note` (6), `n_sources` (4), `record_level_type_topic` (4), `id_namespace` (3), `unique_id_scheme` (3), `split_type` (3), `split_note` (3), `paired_text` (3), `store` (3), `n_patients` (2), `n_studies` (2), `is_sft_mix` (2), `doc_id_traceable` (2), `template` (2), `sft_recipe` (2), `sft_type_totals` (2), `pipeline` (2), `rl_stage` (2), `artifact_type_records` (2), `record_level_records` (2), `record_level_type_register` (2), `record_level_method` (2), `record_level_judge_audit` (2), `cls_sft_grammar` (2), `cls_sft_topology` (2), `cls_sft_orig_format` (2), `cls_sft_structural` (2), `cls_sft_source` (2), `artifact_type_tokens` (2), `artifact_type_pct` (2), `artifact_topic_tokens` (2), `record_level_coverage` (2), `cls_docs_classified` (2), `cls_sources` (2), `n_volumes` (1), `n_slices` (1), `n_patient_scans` (1), `n_curated_cases` (1), `n_human_annotated` (1), `human_annotation_type` (1), `identity_map` (1), `relations` (1), `fndds_total` (1), `fndds_resolved` (1), `wweia_categories` (1), `records_effective` (1), `file` (1), `blake2b` (1), `strata` (1), `domains_top` (1), `length_bands` (1), `over_cutoff_24576` (1), `tool_records` (1), `weld_tool_records` (1), `contaminated_in_mix` (1), `build_chain` (1), `caution` (1), `grounding` (1), `grounding_note` (1), `licence_note` (1), `wiki_linked` (1), `wiki_linked_fraction` (1), `wiki_distinct_pages` (1), `wiki_top` (1), `mesh_appropriate` (1), `wiki_bands` (1).

#### `concept` (312)

On every node: `id`, `label`, `kind`, `layer`, `source`.

On some nodes (count): `grounding` (311), `desc` (299), `concept_class` (293), `canonical_id` (194), `mesh_dui` (194), `mesh_name` (194), `mesh_url` (182), `mesh_tree` (176), `cui` (176), `built_by` (172), `wp_url` (143), `expanded` (142), `wiki_title` (121), `general_domain` (120), `granularity` (120), `snomed` (34), `loinc` (34), `icd10cm` (34), `corpus_docs` (23), `rxnorm` (22), `wiki_oldid` (22), `n_subtopics` (22), `subtopics` (22), `corpus_source_docs` (14), `corpus_sources` (13), `corpus_docs_caveat` (13), `eval_questions` (11), `eval_benchmarks` (11), `n_diseases` (8), `modality` (8), `fa_n_chem` (7), `fa_n_food` (7), `fa_top_foods` (7), `fa_top_chemicals` (7), `eval_accuracy` (6), `gene` (4), `panel_analyte` (4), `n_foods` (2), `mesh_mapped_to` (1).

#### `food-category` (172)

On every node: `id`, `label`, `kind`, `layer`, `grounding`, `modality`, `fndds_wweia_code`, `fndds_n_foods`, `fndds_n_resolved`, `fndds_sample_foods`, `desc`, `source`, `built_by`, `concept_class`.

#### `llm-benchmark` (106)

On every node: `id`, `label`, `kind`, `layer`, `arm`, `metric`, `gated`, `measures`, `composition`, `kos_usage`, `benchmark`, `modality`, `testing_type`, `domain`, `concept_class`, `decontam`.

On some nodes (count): `artifact_types` (96), `artifact_type_labels` (96), `artifact_type_via` (96), `tier` (29), `topics` (20), `topics_status` (20), `grounding` (7), `wp_topic` (7), `wp_url` (7).

#### `model` (90)

On every node: `id`, `label`, `kind`, `layer`, `concept_class`, `is_external`, `source`.

On some nodes (count): `modality` (85), `eval_status` (82), `family` (46), `role` (46), `open_weights` (46), `embedding` (46), `predictor_eval` (46), `curriculum_disclosed` (44), `full_eval` (39), `overall` (39), `cat_scores` (39), `ece` (39), `params_b` (39), `battery_n` (39), `owner` (38), `training_disclosed` (36), `curriculum_note` (36), `note` (9), `curriculum_verified` (8), `curriculum_summary` (8), `license` (6), `curriculum_stages` (5), `hf` (5), `architecture` (4), `params_h` (4), `leaderboard_eligible` (3), `withheld_reason` (3), `arxiv` (3), `params` (2), `pretrain_tokens_real` (2), `pretrain_slots` (2), `pretrain_steps` (2), `pretrain_sources` (2), `pretrain_job` (2), `sft` (2), `audit` (2), `training_audited` (2), `ledger` (2), `corpus_overlap` (2), `trained_on_caveat` (2), `embeddings` (2), `vocab` (2), `sft_mix` (2), `sft_records` (2), `sft_sources` (2), `sft_type_totals` (2), `pretrain_docs` (2), `pretrain_tokens_manifest` (2), `training_note` (2), `deployed` (1), `dedup_finding` (1), `rope_theta` (1), `corpus` (1).

#### `capability` (35)

On every node: `id`, `label`, `kind`, `layer`, `group`, `desc`, `concept_class`.

#### `artifact-type` (35)

On every node: `id`, `label`, `kind`, `layer`, `concept_class`, `group`, `desc`, `canonical_id`, `grounding`, `wiki_title`, `source`, `grounding_match`, `grounding_reason`, `grounding_judge`.

On some nodes (count): `related_mesh` (31), `related_mesh_name` (31), `wp_url` (18), `related_wikipedia` (17), `grounding_note` (17), `mesh_dui` (4), `mesh_name` (4), `mesh_url` (4).

#### `specialty` (28)

On every node: `id`, `label`, `kind`, `layer`, `canonical_id`, `grounding`, `mesh_dui`, `mesh_name`, `mesh_tree`, `mesh_url`, `cui`, `snomed`, `rxnorm`, `loinc`, `icd10cm`, `desc`, `source`, `built_by`, `concept_class`.

On some nodes (count): `wiki_oldid` (27), `corpus_docs` (27), `n_subtopics` (27), `subtopics` (27), `wp_url` (27), `corpus_sources` (26), `corpus_docs_caveat` (26), `corpus_source_docs` (26), `eval_questions` (23), `eval_benchmarks` (23), `eval_accuracy` (18), `n_diseases` (16).

#### `testing-type` (21)

On every node: `id`, `label`, `kind`, `layer`, `desc`, `concept_class`.

#### `fhir` (18)

On every node: `id`, `label`, `kind`, `layer`, `modality`, `desc`, `source`, `built_by`.

On some nodes (count): `fhir_group` (13).

#### `benchmark` (18)

On every node: `id`, `label`, `kind`, `layer`, `modality`, `artifact_types`.

On some nodes (count): `task` (10), `status` (10), `benchmark` (10), `test_sets` (10), `tests_concepts` (10), `held_out_total` (10), `concept_class` (10), `decontam` (10), `artifact_type_labels` (10), `domain` (8), `metric` (8), `measures` (8), `n_models` (8), `source` (8).

#### `authority` (15)

On every node: `id`, `label`, `kind`, `layer`, `modality`, `canonical`, `authority_org`, `source`, `built_by`, `note`.

On some nodes (count): `fhir_system` (14), `iri_stem` (13), `code_example` (10), `version` (1), `n_variables` (1), `n_codelists` (1).

#### `training-stage` (14)

On every node: `id`, `label`, `kind`, `layer`, `stage_type`, `order`, `model`, `data`, `when`, `system`, `config`, `codebase`, `results`, `provenance`, `source`.

#### `capability-group` (13)

On every node: `id`, `label`, `kind`, `layer`, `concept_class`.

#### `eval-domain` (9)

On every node: `id`, `label`, `kind`, `layer`, `desc`, `concept_class`.

#### `domain` (5)

On every node: `id`, `label`, `kind`, `layer`, `grounding`, `wp_url`, `mesh_cat`, `desc`, `source`, `built_by`, `modality`.

On some nodes (count): `n_diseases` (3), `n_foods` (2), `gen_docs` (1).

#### `register` (5)

On every node: `id`, `label`, `kind`, `layer`, `concept_class`, `grounding`, `canonical_id`, `wiki_title`, `wp_url`, `mesh_dui`, `mesh_name`, `desc`, `source`.

#### `modality` (5)

On every node: `id`, `label`, `kind`, `layer`, `canonical_id`, `grounding`, `mesh_dui`, `mesh_name`, `mesh_tree`, `mesh_url`, `cui`, `snomed`, `rxnorm`, `loinc`, `icd10cm`, `desc`, `source`, `built_by`, `concept_class`.

#### `codebase` (4)

On every node: `id`, `label`, `kind`, `layer`, `path`, `framework`, `desc`.

#### `guideline` (3)

On every node: `id`, `label`, `kind`, `layer`, `modality`, `origin`, `desc`, `wp_url`, `cites`, `access`, `measured`, `source`, `built_by`.

#### `gen-category` (3)

On every node: `id`, `label`, `kind`, `layer`, `grounding`, `wp_url`, `desc`, `source`, `built_by`, `modality`.

#### `group` (2)

On every node: `id`, `label`, `kind`, `layer`.

#### `system` (2)

On every node: `id`, `label`, `kind`, `layer`, `desc`.

On some nodes (count): `modality` (1), `origin` (1), `access` (1), `license_note` (1), `measured` (1), `source` (1), `built_by` (1).

#### `root` (1)

`concept-medicine`, the root of the medical concept curriculum (the 51 atlas concept pages), not of
the atlas. It is `part_of` `domain-health` (Health & Medicine), one of the five `domain` nodes that
are `part_of` `atlas-root`.

On every node: `id`, `label`, `kind`, `layer`, `canonical_id`, `grounding`, `mesh_dui`, `mesh_name`, `mesh_tree`, `mesh_url`, `cui`, `snomed`, `rxnorm`, `loinc`, `icd10cm`, `desc`, `wiki_oldid`, `corpus_docs`, `n_subtopics`, `subtopics`, `wp_url`, `source`, `built_by`, `n_diseases`, `n_foods`, `corpus_sources`, `eval_questions`, `eval_benchmarks`, `corpus_docs_caveat`, `corpus_source_docs`, `eval_accuracy`.

#### `gate` (1)

On every node: `id`, `label`, `kind`, `layer`, `canonical_id`, `grounding`, `mesh_dui`, `mesh_name`, `mesh_tree`, `mesh_url`, `cui`, `snomed`, `rxnorm`, `loinc`, `icd10cm`, `desc`, `wiki_oldid`, `corpus_docs`, `n_subtopics`, `subtopics`, `wp_url`, `source`, `built_by`, `corpus_sources`, `eval_questions`, `eval_benchmarks`, `corpus_docs_caveat`, `corpus_source_docs`, `eval_accuracy`.

#### `kg` (1)

On every node: `id`, `label`, `kind`, `layer`, `modality`, `origin`, `desc`, `measured`, `relations`, `source`, `built_by`, `fa_entities`, `fa_triplets`, `fa_evidence`, `fa_relations`, `fa_license`, `fa_version`, `fa_external_ids`, `fa_top_diseases`, `fa_overlap`, `docs`, `access`.

#### `atlas-root` (1)

The top of the atlas (label "PanAtlas"). The five `domain` nodes (`domain-health`, `domain-food`,
`domain-lifesci`, `domain-standards`, `domain-general`) are `part_of` it; medicine's curriculum
root, `concept-medicine`, sits under `domain-health`.

On every node: `id`, `label`, `kind`, `layer`, `desc`, `source`, `built_by`, `n_diseases`, `n_foods`, `modality`.

#### `eval-suite` (1)

On every node: `id`, `label`, `kind`, `layer`, `desc`, `canonical_standard`, `externals`, `peer_note`, `discipline`, `audit_chain`, `battery`, `decontam_gap`, `concept_class`.

#### `measurement` (1)

On every node: `id`, `label`, `kind`, `layer`, `canonical_id`, `grounding`, `mesh_dui`, `mesh_name`, `mesh_tree`, `mesh_url`, `cui`, `snomed`, `rxnorm`, `loinc`, `icd10cm`, `desc`, `source`, `built_by`, `concept_class`.

#### `method` (1)

On every node: `id`, `label`, `kind`, `layer`, `canonical_id`, `grounding`, `mesh_dui`, `mesh_name`, `mesh_tree`, `mesh_url`, `cui`, `snomed`, `rxnorm`, `loinc`, `icd10cm`, `desc`, `source`, `built_by`, `concept_class`.

## Edge relations

Each row gives the number of edges, every source-kind to target-kind pair that occurs, the edge
attributes that occur, and the scripts that write the relation.

| Relation | Edges | Source kind → target kind (count) | Edge properties (count) | Emitted by |
|---|---:|---|---|---|
| `part_of` | 5,430 | `disease`→`specialty` (2,478)<br>`food`→`concept` (1,582)<br>`disease`→`concept` (682)<br>`dataset`→`dataset` (205)<br>`food-category`→`concept` (172)<br>`concept`→`specialty` (116)<br>`concept`→`concept` (53)<br>`dataset`→`gen-category` (43)<br>`concept`→`root` (35)<br>`specialty`→`root` (16)<br>`authority`→`domain` (15)<br>`specialty`→`concept` (7)<br>`specialty`→`specialty` (5)<br>`domain`→`atlas-root` (5)<br>`modality`→`modality` (4)<br>`gen-category`→`domain` (3)<br>`artifact-type`→`artifact-type` (3)<br>`concept`→`domain` (2)<br>`specialty`→`domain` (2)<br>`root`→`domain` (1)<br>`group`→`domain` (1) | `src` (5,256), `via` (5) | `build_layered.py` (`src: mesh_tree` / `curated`), `build_artifact_types.py`, `build_corpus_structure.py`, `sft_wiring.py`, `link_openh.py`, `link_renal.py`, `register_neuropath.py`, `sync_catalog.py` |
| `covers` | 3,607 | `kg`→`disease` (3,170)<br>`dataset`→`food-category` (172)<br>`dataset`→`specialty` (105)<br>`dataset`→`concept` (47)<br>`dataset`→`modality` (40)<br>`dataset`→`disease` (24)<br>`dataset`→`root` (20)<br>`kg`→`concept` (14)<br>`dataset`→`group` (10)<br>`dataset`→`measurement` (3)<br>`kg`→`specialty` (1)<br>`dataset`→`method` (1) | `via` (193), `src` (94) | `build_layered.py`, `build_graph.py`, `link_datasets_to_nodes.py`, `link_neuropath.py`, `link_openh.py`, `link_renal.py`, `link_predictors.py`, `repair_foodatlas_nonmesh.py` |
| `covers_topic` | 2,209 | `dataset`→`specialty` (1,099)<br>`dataset`→`concept` (492)<br>`llm-benchmark`→`concept` (297)<br>`dataset`→`disease` (165)<br>`dataset`→`root` (96)<br>`dataset`→`authority` (48)<br>`benchmark`→`specialty` (8)<br>`llm-benchmark`→`specialty` (2)<br>`llm-benchmark`→`gate` (1)<br>`dataset`→`artifact-type` (1) | `n` (503), `basis` (203) | `build_concept_remap.py` (benchmark topics), `build_artifact_types.py`, `build_record_level.py`, `build_existing_meta.py`, `build_pretrain_multidim.py`, `fold_arxiv_alignment.py` (`basis: arxiv-lexalign`), `build_patho_evals.py`, `build_curriculum.py` |
| `classified_as` | 1,756 | `dataset`→`specialty` (1,252)<br>`dataset`→`concept` (324)<br>`dataset`→`root` (124)<br>`dataset`→`gate` (49)<br>`guideline`→`concept` (6)<br>`guideline`→`specialty` (1) | `n_docs` (1,749), `pct` (7) | `build_layered.py`, `build_corpus_structure.py`, `build_doc_relations.py`; agent side `embed_attach.py`, `pa_local_agent.py` |
| `structured_as` | 1,592 | `food`→`authority` (1,582)<br>`dataset`→`authority` (7)<br>`kg`→`authority` (3) | none | `build_layered.py` |
| `has_artifact_type` | 816 | `dataset`→`artifact-type` (684)<br>`llm-benchmark`→`artifact-type` (113)<br>`benchmark`→`artifact-type` (19) | `src` (4) | `build_artifact_types.py`; also `build_curriculum.py`, `build_existing_meta.py`, `build_patho_evals.py`, `build_record_level.py`, `link_neuropath.py`, `link_openh.py` |
| `resolves_to` | 251 | `food-category`→`food` (250)<br>`dataset`→`kg` (1) | `src` (250) | `build_layered.py` |
| `tests` | 247 | `llm-benchmark`→`capability` (247) | none | `build_llm_benchmarks.py`, `build_missing_benchmarks.py` |
| `grounded_in` | 239 | `llm-benchmark`→`concept` (132)<br>`llm-benchmark`→`specialty` (101)<br>`llm-benchmark`→`root` (6) | `via` (239) | `hygiene_enrich.py` |
| `has_register` | 162 | `dataset`→`register` (162) | none | `build_existing_meta.py` |
| `is_type` | 106 | `llm-benchmark`→`testing-type` (106) | none | `apply_bench_taxonomy.py`, `build_missing_benchmarks.py` |
| `measured_on` | 104 | `model`→`specialty` (72)<br>`model`→`concept` (24)<br>`model`→`root` (4)<br>`model`→`gate` (4) | `acc` (104), `n` (104) | `enrich_graph.py` |
| `in_domain` | 97 | `llm-benchmark`→`eval-domain` (97) | none | `apply_bench_taxonomy.py`, `build_missing_benchmarks.py` |
| `scored` | 85 | `model`→`dataset` (79)<br>`model`→`llm-benchmark` (6) | `value` (85), `metric` (85), `src` (79), `ratio_to_published` (26), `mean_rank` (15), `variant` (6) | `link_predictors.py` (79, `src: link_predictors`); the 6 `variant` edges: no emitter found at HEAD |
| `in_collection` | 83 | `dataset`→`group` (83) | `src` (10) | `build_layered.py`, `link_renal.py` |
| `stage_trained_on` | 45 | `training-stage`→`dataset` (45) | none | `build_curriculum.py` |
| `related` | 44 | `concept`→`concept` (18)<br>`concept`→`specialty` (11)<br>`specialty`→`concept` (8)<br>`specialty`→`specialty` (5)<br>`specialty`→`root` (1)<br>`root`→`specialty` (1) | `sim` (31), `src` (13), `basis` (13) | `build_layered.py` (`sim` from `concept_similarity.json`, cutoff 0.72), `link_renal.py` (`basis`) |
| `instantiates` | 36 | `dataset`→`fhir` (36) | none | `build_layered.py` |
| `groups` | 35 | `capability-group`→`capability` (35) | none | `build_llm_benchmarks.py` |
| `has_type` | 21 | `eval-suite`→`testing-type` (21) | none | `apply_bench_taxonomy.py` |
| `trained_on` | 20 | `model`→`dataset` (20) | `src` (3) | `model_wiring.py`, `build_train_sources.py`, `build_corpus_structure.py`, `link_neuropath.py` |
| `has_resource` | 18 | `authority`→`fhir` (18) | none | `build_layered.py` |
| `binds` | 15 | `fhir`→`authority` (15) | none | `build_layered.py` |
| `test_set_of` | 14 | `dataset`→`benchmark` (14) | `src` (3) | `build_benchmark_nodes.py`, `link_neuropath.py` |
| `has_training_stage` | 14 | `model`→`training-stage` (14) | none | `build_curriculum.py` |
| `executed_on` | 14 | `training-stage`→`system` (14) | none | `build_curriculum.py` |
| `built_with` | 14 | `training-stage`→`codebase` (14) | none | `build_curriculum.py` |
| `grounds` | 13 | `authority`→`specialty` (6)<br>`authority`→`root` (5)<br>`authority`→`concept` (2) | none | `build_layered.py`, `register_neuropath.py`, `renal_sbir_registry.py` |
| `follows` | 9 | `training-stage`→`training-stage` (9) | none | `build_curriculum.py` |
| `evaluated_on` | 8 | `model`→`llm-benchmark` (8) | none | `model_wiring.py` |
| `prereq` | 6 | `concept`→`concept` (4)<br>`gate`→`concept` (2) | none | `build_layered.py` |
| `derived_from` | 3 | `dataset`→`dataset` (3) | `src` (3) | `link_predictors.py` |
| `evaluated_by` | 2 | `model`→`eval-suite` (2) | none | `build_llm_benchmarks.py` |
| `sft_trained_on` | 2 | `model`→`dataset` (2) | none | `sft_wiring.py` |
| `defines` | 1 | `authority`→`root` (1) | none | `build_layered.py` |
| `uses` | 1 | `system`→`kg` (1) | none | `build_layered.py` |

### Edge attributes

| Attribute | On edges | Meaning |
|---|---:|---|
| `src` | 5,715 | Which build step or source asserted the edge: `mesh_tree` (3,360 `part_of` edges derived from MeSH tree numbers), `curated` (1,845), `entity_resolution` (250), `link_predictors`, `link_openh`, `link_renal`, `link_neuropath` |
| `n_docs` | 1,749 | `classified_as`: number of corpus documents of the dataset classified to the concept |
| `pct` | 7 | `classified_as` from a guideline document: share in percent |
| `n` | 607 | `covers_topic`: number of benchmark items (or documents) mapped to the topic; `measured_on`: number of scored items |
| `basis` | 216 | Why the edge exists: `arxiv-lexalign` (203 `covers_topic` edges), or a short reason on `related` edges from `link_renal.py` |
| `via` | 437 | `grounded_in`: the MeSH code that grounds the target (`mesh:D…`); `covers`: `metadata`, `modality` or `finding-label`; `part_of`: path note |
| `sim` | 31 | `related`: cosine similarity between concept anchors (edges written only at 0.72 or above) |
| `acc` | 104 | `measured_on`: accuracy of the model on the items mapped to the concept |
| `value`, `metric` | 85 | `scored`: the score and its metric |
| `mean_rank` | 15 | `scored`: mean rank over the suite tasks (predictor suites) |
| `ratio_to_published` | 26 | `scored`: ratio of our run to the published leaderboard value (fev-bench) |
| `variant` | 6 | `scored`: which release of the model the score belongs to (for example `V5-Instruct`) |

## Standards that govern the graph

`GRAPH_STANDARDS.md` is the decision record, adopted 2026-07-26 and extended 2026-09-26. Its binding
rules are summarised here with what the served graph does.

### Identity and grounding

`GRAPH_STANDARDS.md` was written for medicine, the domain the atlas started with, so its grounding
rules name medical vocabularies. The served graph applies the same idea to other domains with their
own vocabularies (FoodOn and FoodData Central for foods, Wikipedia for general concepts; see
[Code systems](codesystems.md)). As written:

- Every node must be tied to a real MeSH descriptor or another core concept (SNOMED CT or a UMLS
  concept). There are to be no orphan nodes.
- A concept's canonical identity is its MeSH descriptor UI, for example `mesh:D002309` for
  Cardiology. The MeSH UI is the deduplication key: two nodes with the same UI are the same concept.
- MeSH is canonical over Wikipedia. Wikipedia is a readable overlay on a MeSH concept (an `oldid`
  attribute), never a second node. Wikipedia is the fallback identity only for non-MeSH,
  non-medical nodes, which may instead carry a Wikidata QID.
- `LAYERS.md` restates the same rule as the substrate: identity is `canonical_id`, and two systems
  that emit the same `canonical_id` name the same entity without reconciliation.

!!! warning "1,174 nodes carry no `canonical_id`"
    The grounding rule is written for concepts, but it says "every node". At HEAD 1,174 nodes have
    no `canonical_id`: all 513 `dataset`, 172 `food-category`, 106 `llm-benchmark`, 90 `model`,
    35 `capability`, 21 `testing-type`, 18 `fhir`, 18 `benchmark`, 15 `authority`, 14
    `training-stage`, 13 `capability-group`, 9 `eval-domain`, 5 `domain`, 4 `codebase`, 3
    `guideline`, 3 `gen-category`, 2 `group`, 2 `system`, 1 `kg`, 1 `atlas-root` and 1
    `eval-suite` node, and also 118 `concept` and 10 `disease` nodes. The 118 concepts are the 117
    Wikipedia-grounded general concepts that `build_concept_remap.py` creates with `wiki_title` and
    `wp_url` but no `canonical_id` (where `build_layered.py` would write `wikipedia:<slug>`), plus
    one corpus-classification concept. The 10 diseases are FoodAtlas diseases whose upstream id is
    OMIM, flagged with `grounding: none` and a `grounding_note`.

### Hierarchy and edge direction

- The medical concept hierarchy comes from MeSH tree numbers. A descriptor's parent is the descriptor whose
  tree number is the immediate prefix. Specialties live in the MeSH H02 tree, diseases in C,
  techniques in E. In the served graph this hierarchy is the `part_of` relation with
  `src: mesh_tree` (3,360 edges); hand-curated links carry `src: curated` (1,845).
- Backbone edges are SKOS-aligned. The property graph does not use SKOS names. The RDF export
  declares `pa:partOf rdfs:subPropertyOf skos:broader` and `pa:related rdfs:subPropertyOf
  skos:related`, and writes every code as `skos:exactMatch`. It writes no `skos:narrower`.
- Edges point from the specific or owning node to the general or target node: a child is
  `part_of` its parent, a dataset `covers` a concept, a model is `scored` against a benchmark, a
  training stage `follows` the stage before it.

`GRAPH_STANDARDS.md` does not state naming rules. The served graph follows these conventions
consistently: `kind` values are lower case with hyphens; `rel` values are lower case snake case
verb phrases; node ids are lower case, prefixed by kind (`concept-`, `bench-`, `model-`,
`dataset-`, `atype-`, `stage-`), with MeSH expansion nodes as `mesh-D<UI>` and FoodAtlas nodes as
`fa-dis-` and `fa-food-`. Identifier rules are on [Identifiers](identifiers.md).

### Provenance

- Sources are evidence, not authority. Only panAtlas verification makes a fact `verified`, and a
  curator sign-off is recorded as `verified_by`.
- FHIR-derived and vocabulary-derived assertions enter as evidence with provenance. Automatic MeSH
  groundings are adversarially verified, one agent per concept, each confirming the descriptor with
  a live UTS call, before they are trusted.
- Every triple lives in exactly one named graph, and the named graph is its source of record.
  panAtlas curates only `https://panatlas.net/graph/panatlas`; mirrored graphs are read-only. See
  [RDF vocabulary](rdf-vocabulary.md).
- A dataset maintained elsewhere carries `maintained_externally: true` and a `source_of_record`
  block with the keys `system`, `graph`, `agent`, `upstream_version`, `upstream_last_updated_on`,
  `held_version`, `endpoint`, `registry_file`, `registry_commit`, `funding`, `homepage`,
  `authoritative_namespaces`, `authoritative_declared`. See [Dataset registry](dataset-registry.md).
- `LAYERS.md` requires every edge to carry an `origin` (ontology-tree, curated, embedding-derived,
  agent-contributed) and `evidence` (for example `{model, version, cosine}`), so that connectivity
  merges as attributed claims.

!!! warning "Edge provenance in the served graph is partial"
    No edge in the served graph has an `origin` or an `evidence` attribute, and no node or edge has
    a `verified_by` attribute. Provenance is carried instead by `src` (5,715 edges), `via` (437),
    `basis` (216) and, for measured edges, `n_docs`, `n`, `sim` and `acc`. 10,863 edges carry
    none of `src`, `via` or `basis`. On nodes, provenance is the free-text `source` and `built_by`
    fields. The closest implementation of the contract is in the attach process (`embed_attach.py`
    and the local agent report, see [Knowledge layers](../concepts/layers.md)), which writes one
    nested attribute, `claims: {origin: "embedding", model, version, cosine, canonical_id}`, on its
    `classified_as` edges. Those edges are federation reports and are not in the served graph.

## Other graph files in the repository

| File | Nodes | Edges | Status |
|---|---:|---:|---|
| `web/wp-plugin/panatlas-explorer/data/graph.json` | 6,187 | 17,119 | Served graph, documented on this page |
| `web/graph.json` | 200 | 386 | First interface graph from `build_graph.py` (kinds `dataset`, `external-benchmark`, `topic`, `origin`, `role`; relations `has_origin`, `has_role`, `in_topic`, `covers`). Not served |
| `web/explorer/graph.json` | 66 | 174 | Prototype explorer graph from `web/explorer/build_graph.py`. Not served |

## Build order

Each build script reads the served `graph.json`, changes it in place and writes it back. The
ordered entry point is `web/build_all.sh`. Its stated precondition is that the upstream builders
(`build_graph.py`, `build_layered.py`, `build_all_datasets.py`, `build_train_sources.py`,
`build_source_topics.py`, `sft_wiring.py`, `build_corpus_structure.py`, `model_wiring.py`,
`build_benchmark_nodes.py`, `build_concept_remap.py`, `apply_bench_taxonomy.py`) have already run. It
then runs, in order:

```bash
python3 build_artifact_types.py
python3 build_curriculum.py
python3 build_record_level.py
python3 pipeline/existing_meta/merge_gap.py || true
python3 build_existing_meta.py
python3 build_native_meta.py
python3 build_field_values.py
python3 build_patho_evals.py
python3 build_eval_map.py
python3 pipeline/check_curriculum_vault.py
node pipeline/ui_harness.js
```

Scripts outside this sequence also write the graph: `enrich_graph.py` (`measured_on`,
`eval_accuracy`), `hygiene_enrich.py` (`grounded_in`, contamination downgrades),
`attach_full_eval.py` (model evaluation fields), `reconcile_benchmarks.py`, the `link_*.py` scripts
and `register_*.py` fragments. No single script rebuilds the whole graph from scratch, so the order
in which these were last run determines the file.
