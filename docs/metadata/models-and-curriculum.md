# Models and curriculum

This page documents how panAtlas describes models and how they were trained: the artifact-type
vocabulary that types training and evaluation data on the same axis, the model records, the
per-modality embedding-model registry, the training-curriculum record, and the register of
training-provenance gaps. Evaluation results are on [Evaluation records](evaluation-records.md).
Counts were computed with `python3` from the files at repo HEAD `57505c6` on 2026-11-10.

## Artifact types

An artifact type says what kind of record a training or evaluation document is (a QA pair, a
discharge summary, a reasoning trace, a whole-slide image). It is the second axis next to the
topic (what the record is about, a concept node). Both axes apply to training sources and to
benchmarks, so training exposure and evaluation coverage can be compared cell by cell. The layer was
added 2026-08-08 (`docs/artifact-types-and-model-curriculum.md`).

### Vocabulary file: `web/pipeline/artifact_types.json`

Schema id `panatlas-artifact-types/1`.

| Key | Content |
|---|---|
| `_schema` | `panatlas-artifact-types/1` |
| `note` | Purpose statement |
| `grounding_verified` | "2026-08-08 via the NLM MeSH descriptor lookup (match=exact) and the Wikipedia REST page summary (see `pipeline/groundings_verified.json`)" |
| `types` (35) | The vocabulary, fields below |
| `new_topic_concepts` (4) | Topic concepts added with the layer: rare disease (MeSH D035583), genomics (D023281), pharmacovigilance (D060735), consumer health information (D054626) |
| `pretrain_source_map` (56) | Pretraining source → `{types, topics}` |
| `sft_type_map` (19) | SFT type string → artifact type ids |
| `benchmark_task_format_map` (16) | Ontology `task_format` value → artifact type ids |
| `benchmark_overrides` (36) | Benchmark slug → artifact type ids, overriding the task-format map |
| `adversarial_review` | `date` (2026-08-08), `method`, `applied`, `rejected` |

Type fields: `id` (`atype-<slug>`), `label`, `group`, `desc`, `wikipedia_title`, `wp_canonical`,
`mesh_dui`, `mesh_name`, and on three types `parent`.

| Group | Types |
|---|---|
| `interaction` (12) | `atype-question-answer`, `atype-multiple-choice`, `atype-dialogue`, `atype-instruction-response`, `atype-tool-call`, `atype-agentic-trajectory`, `atype-rag-grounded`, `atype-reasoning-trace`, `atype-math-problem`, `atype-source-code`, `atype-text-transformation`, `atype-cloze-continuation` |
| `literature` (7) | `atype-scholarly-article`, `atype-abstract`, `atype-preprint`, `atype-textbook`, `atype-encyclopedia-article`, `atype-web-text`, `atype-legal-text` |
| `regulatory-structured` (7) | `atype-practice-guideline`, `atype-trial-registration`, `atype-drug-label`, `atype-adverse-event-report`, `atype-structured-records`, `atype-ontology`, `atype-annotated-corpus` |
| `narrative` (4) | `atype-case-report`, `atype-clinical-note`, `atype-discharge-summary`, `atype-diagnostic-report` |
| `imaging` (3) | `atype-medical-image`, `atype-image-text-pair`, `atype-whole-slide-image` |
| `trait` (2) | `atype-synthetic-data`, `atype-benchmark-item` (cross-cutting traits) |

`part_of` edges link three types to a parent: discharge summary and diagnostic report are part of
clinical note; whole-slide image is part of medical image.

!!! warning "Type count and SFT map size differ from the layer document"
    `docs/artifact-types-and-model-curriculum.md` says 33 types and 16 SFT type values. The file
    has 35 types (the adversarial review added `atype-text-transformation` and
    `atype-cloze-continuation`) and 19 `sft_type_map` keys.

### Artifact-type nodes and their grounding

`build_artifact_types.py` writes one `artifact-type` node per type (`concept_class:
artifact-type`). Every node carries `canonical_id`, `grounding`, `wiki_title`, `grounding_match`,
`grounding_reason` and `grounding_judge`; some carry `wp_url`, `related_wikipedia`, `related_mesh`,
`related_mesh_name`, `grounding_note`, `mesh_dui`, `mesh_name`, `mesh_url`.

The 2026-08-08 pass grounded 24 types to a MeSH descriptor. A later concept-identity check
(`grounding_judge`: "gemma-4-31B concept-identity judge (2026-08-09)") asked whether the public
concept is the same thing as the record type, and recorded the answer in `grounding_match` (`yes`
17, `no` 17, `partial` 1) with a `grounding_reason`. In the served graph:

| `grounding` | Nodes | `canonical_id` |
|---|---:|---|
| `internal-vocabulary` | 17 | `panatlas:atype-<slug>`; the near public concept is kept as `related_wikipedia` / `related_mesh` |
| `wikipedia` | 16 | `wikipedia:<title>` |
| `mesh+wikipedia` | 2 | `mesh:D063886` (discharge summary), `mesh:D008499` (diagnostic report) |

So the vocabulary file lists 24 MeSH descriptors, but only two types use one as identity; the others
keep it as `related_mesh`.

### Where artifact types attach

| Structure | Count at HEAD |
|---|---:|
| `dataset` `has_artifact_type` → `artifact-type` | 684 |
| `llm-benchmark` `has_artifact_type` → `artifact-type` | 113 |
| `benchmark` `has_artifact_type` → `artifact-type` | 19 |
| `llm-benchmark` nodes with `artifact_type_via` (`override` or `facet:<task_format>`) | 96 |

Measured rollups (tokens per type and topic per pretraining corpus, records per type per SFT mix) are
written to `web/pipeline/corpus_type_profile.json`. Types are not mutually exclusive, so shares can
sum past 100 %.

Record-level typing (added 2026-08-08, second pass) types documents individually rather than per
source. Pretraining coverage is stamped honestly (V4 55.89 % of manifest documents, V5 43.35 %);
uncovered sources are excluded, not guessed. Every SFT record of the V5 (736,990) and V4 (825,504)
mixes is typed by deterministic rules in a record-typing script under `web/pipeline/record_level/`. Results land
on corpus and mix nodes as `record_level_type_topic`, `record_level_type_register`,
`record_level_coverage`, `record_level_records`, `record_level_method`, `record_level_judge_audit`,
and on SFT source nodes as `record_topics`, `record_registers`, `record_register_atypes`,
`record_topic_concepts`.

The register (tone) of a record is a third small vocabulary: five `register` nodes written by
`build_existing_meta.py` (Academic writing, Technical writing, Medical writing, Plain language,
Colloquialism), each grounded to a Wikipedia article, with 162 `dataset` `has_register` →
`register` edges.

## Model records

### Model nodes in the graph (90)

| Group | Nodes | Written by | Distinguishing fields |
|---|---:|---|---|
| Language models on the battery | 36 | `attach_full_eval.py`, `add_biomed_models.py` | `full_eval`, `overall`, `cat_scores`, `ece`, `params_b`, `battery_n`, `eval_status`, `is_external: true` |
| In-house models with a curriculum | 5 | `build_curriculum.py` (KOS-V4, KOS-V5, KOS-V6, KOS-V6-Instruct, `lesion_lg_cohort_reg_dino`) | `curriculum_*`, `leaderboard_eligible`, `is_external: false` |
| In-house WSI encoders | 3 | `link_neuropath.py` (MAD-NP, NP-GIANT, NP-TEST-0) | `modality: imaging-wsi`, `trained_on` edges |
| Predictor models | 46 | `link_predictors.py` | `predictor_eval`, `role`, `family`, `open_weights`, `embedding` |

KOS-V4, KOS-V5 and KOS-V6 also carry the language-battery fields, so 39 model nodes have
`full_eval`.

Every model node has `id`, `label`, `kind`, `layer` (`concept`), `concept_class` (`model`),
`is_external` and `source`. The remaining fields, with the number of model nodes that carry each:

| Field | Nodes | Meaning |
|---|---:|---|
| `modality` | 85 | `text`, `imaging-wsi`, `structured`, `time-series` |
| `eval_status` | 82 | How and where the model was evaluated |
| `family`, `role`, `open_weights`, `embedding`, `predictor_eval` | 46 | Predictor models; see [Evaluation records](evaluation-records.md) |
| `curriculum_disclosed` | 44 | Whether a stage-level curriculum is on record (below) |
| `full_eval`, `overall`, `cat_scores`, `ece`, `params_b`, `battery_n` | 39 | Language battery results |
| `owner` | 38 | Who publishes the model |
| `training_disclosed` | 36 | Whether the vendor discloses training data |
| `curriculum_note` | 36 | Why no curriculum is recorded |
| `note` | 9 | Free text |
| `curriculum_verified` | 8 | Copy of the curriculum record's `verified` statement |
| `license` | 6 | Licence |
| `curriculum_stages`, `curriculum_summary` | 5 | Ordered stage ids; stage types joined by " -> " |
| `hf` | 5 | Hugging Face repository |
| `architecture` | 4 | Architecture statement (for example "bespoke from-scratch (NOT a Qwen mirror)") |
| `params_h` | 4 | Human-readable parameter count |
| `leaderboard_eligible`, `withheld_reason` | 3 | Ranking eligibility (below) |
| `arxiv` | 3 | Paper |
| `params`, `vocab`, `rope_theta`, `embeddings` | 2 | Architecture facts (`embeddings`: tied or untied) |
| `pretrain_tokens_real`, `pretrain_slots`, `pretrain_steps`, `pretrain_sources`, `pretrain_job`, `pretrain_docs`, `pretrain_tokens_manifest` | 2 | KOS-V4 and KOS-V5 pretraining facts |
| `sft`, `sft_mix`, `sft_records`, `sft_sources`, `sft_type_totals` | 2 | SFT summary; `sft_mix` points to the mix dataset node |
| `ledger` | 2 | Training-ledger audit: `rows_entered`, `census_trained`, `dropped_overlength`, `distinct_doc_uid`, `duplicate_pct`, `max_copies_of_one_doc` |
| `corpus_overlap` | 2 | V4/V5 corpus overlap: `distinct_v4`, `distinct_v5`, `in_both`, `v4_only`, `v5_only`, `union` |
| `training_audited`, `audit`, `trained_on_caveat`, `training_note` | 2 | Audit status and caveats |
| `dedup_finding` | 1 | KOS-V4: `status`, `rows`, `distinct`, `dup_pct` (39.6), `per_source`, `note`, `eval_implication` |
| `deployed`, `corpus` | 1 | Deployed checkpoint; corpus note |

Edges from model nodes: `scored`, `evaluated_on`, `evaluated_by`, `measured_on` (results);
`trained_on` (20), `sft_trained_on` (2), `has_training_stage` (14) (training).

### Embedding-model registry: `web/models.json`

`models.json` is the per-modality registry of embedding models that place new items in the
connectivity graph ([Knowledge layers](../concepts/layers.md)). Its rule: an embedding is
comparable only within one `(modality, model, version)` space; cross-modality relation goes through
shared `canonical_id`, never through embedding arithmetic.

| Modality | Registered model | Status |
|---|---|---|
| `text` | `text-bioclinical-modernbert-large`, version `v3w-2026.07`: stock BioClinical-ModernBERT-large weights (SHA-256 verified 2026-08-08 to equal the published weights; not fine-tuned in-house), 1024-d, masked mean pool, `max_length` 1024, L2, cosine, raw cutoff 0.25 with a whitened cutoff in the anchor artifact | `active` |
| `imaging` | `imaging-rad-dino-ct`, version `raddino`: stock RAD-DINO (768-d) | Embeddings are a retrieval asset; concept anchors are `held` (image embeddings are not linked directly to concept nodes) |
| `genomics` | none | "no registered embedder yet" |
| `structured` | none | "no registered embedder yet" |

Entry fields: `id`, `family`, `modality`, `role`, `applies_to`, `dim`, `version`, `normalize`,
`similarity`, `cutoff`, `anchors`, `status`, `provenance`; text adds `pooling`, `max_length`,
`dtype`, `whitening`, `cutoff_note`, `location`, `centroids` (`artifact`, `n_cells` 4,096, `dim`
1,024), `hf`, `training_disclosed`, `license`; imaging adds `model_location`, `note`, `embeddings`.

The vault page `concept-panatlas-text-embedding-space-v3w` records that `@v3w` tags the embedding
space, not the weights: `v3` is the third concept-embedding pipeline (`embed_concepts_v3.py`), `w` the
per-dimension whitening `(x − mu) / sd` stored with the 201 concept anchors.

`models.json` also holds `predictors` (58 tabular and forecasting model records), documented on
[Evaluation records](evaluation-records.md).

!!! warning "Imaging model differs from `LAYERS.md`"
    `LAYERS.md` says imaging is embedded "by the LeJEPA-3D CT encoder". The registry's only imaging
    entry is stock RAD-DINO, and its anchors are held.

## The curriculum record: `panatlas-model-curriculum/1`

`web/pipeline/model_curriculum.json` records, for any model, the ordered training stages that
produced it. Each stage answers five questions: (a) what data, (b) when, (c) on what system,
(d) with what configuration, (e) from what codebase. The record is model-agnostic: an external model
that does not disclose its curriculum reports `curriculum_disclosed: false` with no stages, through
the same fields.

### Top level

| Key | Type | Content |
|---|---|---|
| `_schema` | string | `panatlas-model-curriculum/1` |
| `note` | string | Purpose and sourcing: in-house facts come from the vault's verified audits |
| `models` | list | One record per model (6 at HEAD) |

### Model record

| Field | Required | Type | Meaning |
|---|---|---|---|
| `model_id` | yes | string | Graph node id of the model (`model-<slug>`) |
| `name` | yes | string | Display name |
| `curriculum_disclosed` | yes | bool | A stage-level curriculum is on record |
| `stages` | yes | list | Ordered training stages; empty when not disclosed |
| `verified` | when disclosed | string | Free text stating when and how the record was verified, for example "2026-08-01 vault audit (two independent token censuses agree to 0.0001%)" or "2026-10-14: vault experiment/dataset pages + Slurm accounting (sacct) for every training job" |
| `leaderboard_eligible` | optional | bool | False keeps the model out of rankings |
| `withheld_reason` | with `leaderboard_eligible: false` | string | Why |
| `note` | optional | string | Free text |

### Stage record

| Field | Stages (of 14) | Meaning |
|---|---:|---|
| `id` | 14 | Stage node id, `stage-<model>-<stage>` |
| `order` | 14 | Position in the curriculum, from 1 |
| `stage_type` | 14 | `pretraining`, `sft`, `rl-grpo`, `ssl-dino` |
| `name` | 14 | Display name |
| `data` | 14 | (a) What was trained |
| `when` | 14 | (b) When |
| `system` | 14 | (c) On what system |
| `config` | 14 | (d) With what configuration |
| `codebase` | 14 | (e) From what codebase |
| `results` | 12 | Outcome of the stage |
| `provenance` | 14 | List of provenance tags (`file:<path>`, `job:<id>`) |

**(a) `data`.** `dataset_nodes` (14; list of dataset node ids, empty for the RL stages),
`description` (14), `tokens_real` (8), `epochs` (7), `docs` (6), `sources` (5), `records` (4),
`epochs_planned` (1), `inline_datasets` (1; dataset records to create when the training data is not
yet in the inventory, each with `id`, `label`, `modality`, `docs`, `desc`, `artifact_types`,
`topics`).

**(b) `when`.** `jobs` (14; list of `{id, status, note?}`; statuses in use are `COMPLETED`,
`CANCELLED`, `FAILED`, `TIMEOUT` and `INTERMEDIATE`), `start` (7), `end` (9). Failed and cancelled
legs are kept, so the record shows the whole chain, not only the final job.

**(c) `system`.** `cluster` (14), `nodes` (12), `gpus` (12), `gpu_type` (11), `gpu_hours` (7),
`gpu_hours_note` (6), `launcher` (6), `parallelism` (2), and once each `nodelist`, `gpus_note`,
`container`, `trained_by`, `precision`.

**(d) `config`.** `framework` (14), `file` (13; repository-relative config path), `lr` (11),
`seq_len` (8), `tokens_per_step` (8), `packing` (7), `micro_batch` (7), `grad_accum` (7),
`parallelism` (7), `objective` (7), `precision` (6), `attention` (6), `stage` (5), `schedule` (5),
`tokenizer` (5), `algorithm` (4), `warmup_ratio` (3), `epochs` (3), and on fewer stages
`neftune_alpha`, `template`, `batch`, `rollout_n`, `weight_decay`, `thinking_budget`, `objectives`,
`rope_theta`, `ppo_mini_batch`, `kl_coef`, `betas`, `max_grad_norm`, `note`, `steps`, `kl`,
`reward`, `gradient_checkpointing`, `out_dim`, `momentum_teacher`, `teacher_temp`, `crops`.

**(e) `codebase`.** `repo` (14), `path` (14), `framework` (14), `spec` (5). Frameworks in use:
LlamaFactory, verl, DINOMX.

**`results`.** Keys vary by stage: `steps`, `final_loss`, `architecture`, `published_as`,
`checkpoint`, `checkpoints`, `known_gap`, `known_defect`, `contamination`, `evals`, `evals_note`,
`endpoint`, `tokens_slots`, `tokens_cumulative_slots`, `schedule_steps`, and benchmark values
(`ifeval`, `ifeval_avg4`, `bfcl`, `mmlu`, `pubmedqa`).

!!! note "Host-specific values"
    `system.cluster`, `system.nodelist`, `codebase.path`, `codebase.repo` and some `provenance` tags
    hold host names, cluster paths and account names. They are needed to resolve a fact against the
    vault, and this documentation does not reproduce them. The public API does not return paths,
    hosts or job numbers (`docs/public-api.md`).

### Populated records at HEAD

| `model_id` | Stages | Stage types | `curriculum_disclosed` | `leaderboard_eligible` |
|---|---:|---|---|---|
| `model-kos-v4` | 3 | pretraining → sft → rl-grpo | true | not set |
| `model-kos-v5` | 4 | pretraining → sft → rl-grpo (leg A) → rl-grpo (leg T) | true | not set |
| `model-kos-v6` | 5 | pretraining phases 1 to 5 | true | true |
| `model-kos-v6-instruct` | 1 | rl-grpo | true | false ("contamination unchecked; V6 pretrain lineage still in flight - shown for curriculum record only, not ranked") |
| `model-lesion-lg-cohort-reg-dino` | 1 | ssl-dino | true | false ("intermediate checkpoint (iter 170k of 200k), no downstream KOS-run measurement") |
| `model-qwen3-4b-instruct` | 0 | none | false | not set |

The KOS-V6 base record was added 2026-10-14 (feature 020): five pretraining stages with their
scheduler jobs read from Slurm accounting.

### Graph wiring (`build_curriculum.py`)

```
model  -has_training_stage->  training-stage  -stage_trained_on->  dataset
training-stage  -follows->      previous training-stage
training-stage  -executed_on->  system      (id: system-<slug of system.cluster>)
training-stage  -built_with->   codebase    (id: codebase-<slug of the last segment of codebase.repo>)
```

| Edge | Count at HEAD |
|---|---:|
| `has_training_stage` | 14 |
| `stage_trained_on` | 45 |
| `follows` | 9 (14 stages minus the first stage of each of the 5 curricula) |
| `executed_on` | 14 |
| `built_with` | 14 |

`training-stage` nodes (14, `layer: process`) carry `id`, `label` (stage `name`), `kind`, `layer`,
`stage_type`, `order`, `model`, `data` (without `inline_datasets`), `when`, `system`, `config`,
`codebase`, `results`, `provenance` and `source`. The script also stamps model nodes with
`curriculum_disclosed`, `leaderboard_eligible` and `withheld_reason` (when set),
`curriculum_verified`, `curriculum_stages`, `curriculum_summary`, and `curriculum_note` for models
without stages. Any model node still lacking `curriculum_disclosed` when the script runs gets
`false` and the note "no published stage-level curriculum (data-by-stage, schedule, system, config,
codebase)". Edge ids are content-hashed, so reruns add no edges.

!!! warning "Not every model node carries `curriculum_disclosed`"
    The layer document and the vault say every model node carries `curriculum_disclosed`. At HEAD
    44 of 90 do (8 true, 36 false). The 46 predictor models were added by `link_predictors.py` after
    `build_curriculum.py` last ran and have no value. The stale `stats.curriculum` block reports 1
    undisclosed model.

### Verification gate

`pipeline/check_curriculum_vault.py` checks that every hard fact in the curriculum (each scheduler
job id other than `n/a`, each config file path, each codebase repository other than a container)
appears in at least one page of the knowledge vault, and exits 1 on any miss. It runs in
`build_all.sh`. The vault records 39/39 facts found on 2026-08-08 and 61/61 after the KOS-V6 record
was added on 2026-10-14.

## The training-provenance gap register

`docs/curriculum-gap-register.md` lists every blank that prevents a complete "look at the model, see
exactly how it was trained" record, compiled 2026-08-08 from a sweep of the vault and the curriculum
layer. Blanks are tracked with the same rigour as facts.

Format:

- **Legend.** Each gap names the missing curriculum field by its letter: (a) data, (b) when/jobs,
  (c) system, (d) config, (e) codebase.
- **Sections.** `CRITICAL` (zero or deleted records), `HIGH` (partial records), `KNOWN DEFECTS`
  (measured caveats, not blanks), `RESOLVED` (kept so nobody reopens them), and "Curriculum entries
  to ADD once facts land".
- **Table columns** (CRITICAL and HIGH): `#`, `Artifact`, `Missing` (the field letters and what is
  missing), `Best lead` (where the fact can be recovered). A resolved row is struck through and
  annotated **RESOLVED** with the date and the evidence.
- **Closing a gap.** The fact is filed in the vault; `check_curriculum_vault.py` then picks it up.

At HEAD the register has five CRITICAL rows (one resolved: the BioClinical-ModernBERT weights were
shown to be the stock published weights), five HIGH rows, four known defects (for example "V4
pretrain: 39.62% exact-duplicate text"; "V6 SFT/RL mix: contamination unchecked"), four resolved
items, and one completed addition (the KOS-V6 base curriculum, 2026-10-14).
