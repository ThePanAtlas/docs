# Document index

!!! info "Status"
    **Built and measured, on the cluster.** The document ledger and its `doc_uid` crosswalk (2026-08-01), the
    master document index (2026-07-27, labels remapped 2026-09-07, Wikipedia columns added 2026-09-10), the
    v5.3 registry labels (2026-09-07), the arXiv reference index and the estate document index (2026-09-23)
    exist as Parquet, NumPy and JSON files in `<cluster project storage>/panatlas/`. They are not in the
    repository. The repository holds the scripts that build them and their small JSON rollups
    (`web/doc_ledger_summary.json`, `web/master_rollup.json`, `web/estate_doc_rollup.json`,
    `web/licence/estate_licence_rollup.json`, `web/decontam_exact.json`). Numbers below are dated; none are
    projected.

The document index answers, for any text document panAtlas knows about: which source and role it belongs
to, whether a model trained on it, what concept it is about, what Wikipedia article it links to, and under what
licence. It is built from several tables that share two keys, `doc_id` (where a row is) and `doc_uid` (what
text it is); see [Identifiers](identifiers.md#document-uid-doc_uid).

| Artifact | Rows | Size | Key | Built by |
|---|---:|---:|---|---|
| `doc_ledger_v4.parquet` | 131,739,051 | 2.88 GB | `doc_uid` | document-ledger build, jobs 207724 / 208237 |
| `doc_ledger_v5.parquet` | 178,562,639 | 4.02 GB | `doc_uid` | same |
| `doc_ledger_crosswalk.parquet` | 200,497,968 | 3.03 GB | `doc_uid` | job 208241 |
| `master_doc_index.parquet` | 89,907,669 | 706,689,139 B before the Wikipedia columns were added | `doc_id` | `web/dgx/build_master_index.py` |
| `arxiv_doc_index.parquet` | 3,148,796 | 282,794,241 B | `doc_id` | `web/acquisition/arxiv/arxiv_doc_index.py` |
| `estate_doc_index.parquet` | 93,056,465 | not re-measured after the licence build | `doc_id` | `web/licence/estate_licence_build.py` |
| `pmc_doc_pmid_map.parquet` | 14,383,878 | | `doc_uid` | PMC identity recovery, job 212698 |
| `labels_v53/` | per document, e8 order | 186,798,930,278 B | e8 row | v5.3 promotion, job 219233 |

Measured 2026-09-19: the whole index estate is 198,036,273,201 B over 200,497,968 documents, about 988 B per
document. Of that, 11.24 GB (5.7 %) is the five source-of-record Parquet tables (the three ledger files,
`master_doc_index`, `pmc_doc_pmid_map`) and 186.80 GB (94.3 %) is the derived `labels_v53/` directory.

## Document ledger and `doc_uid` crosswalk

The ledger records every document that entered the V4 and V5 pretraining runs, one row per document as it
was trained, with its content-addressed id.

**Ledger columns** (`doc_ledger_v4.parquet`, `doc_ledger_v5.parquet`):

| Column | Meaning |
|---|---|
| `doc_uid` | `blake2b(raw_text, digest_size=16)` as 32 hex characters |
| `version` | `v4` or `v5` |
| `source` | training source name |
| `file` | the corpus file the row came from |
| `row_idx` | row index within that file |
| `n_chars` | text length in characters |

**Crosswalk columns** (`doc_ledger_crosswalk.parquet`): `doc_uid`, `in_v4`, `in_v5` (booleans). One row per
distinct `doc_uid` in either ledger. It is membership only: it does not carry concepts or positions.

Build: 11,848 input files (V4 610 over 14 sources, V5 11,238 over 56 units), a 500-task CPU array with zero
failures. The build gates failed closed on the audited census counts and both passed. It was acceptance-tested
by round-tripping a real document: text → `doc_uid` → exactly one ledger row with the correct file and
`row_idx` → crosswalk `in_v4 = true, in_v5 = true`.

`web/doc_ledger_summary.json` holds the summary:

| Key | V4 | V5 | Meaning |
|---|---:|---:|---|
| `rows_entered` | 131,739,051 | 178,562,639 | rows that entered training |
| `census_entered` | 131,739,051 | 178,562,639 | the audited census count |
| `gate_entered` | `PASS` | `PASS` | rows equal the census |
| `census_trained` | 131,577,161 | 178,344,619 | rows after the over-length drop |
| `dropped_overlength` | 161,890 | 218,020 | whole documents dropped for length (0.12 % of each) |
| `distinct_doc_uid` | 79,548,810 | 177,728,829 | distinct texts |
| `duplicate_rows` | 52,190,241 | 833,810 | rows beyond the first copy |
| `duplicate_pct` | 39.6164 | 0.467 | duplicate rows as a percentage of rows |
| `max_copies_of_one_doc` | 4,280 | 1,520 | the most-repeated single text |

| `crosswalk` key | Value |
|---|---:|
| `distinct_v4` | 79,548,810 |
| `distinct_v5` | 177,728,829 |
| `in_both` | 56,779,671 |
| `v4_only` | 22,769,139 |
| `v5_only` | 120,949,158 |
| `union` | 200,497,968 |

Owner ruling (2026-08-01): every document in the ledger counts as trained on. The over-length drop is not
distinguished per document. Exposure is counted on distinct `doc_uid`, never on rows.

!!! note "What the crosswalk revealed"
    The V4 run was never deduplicated: 39.6 % of its rows are exact duplicates, concentrated in the general
    web source (54.7 % duplicate) and PMC (22.3 %). V5 is nearly duplicate-free (0.47 %). Only 56.8 M documents
    are common to both runs; V5 dropped 22.8 M documents V4 trained on and added 120.9 M. These are
    measurements of the ledger, not estimates.

## Master document index

`master_doc_index.parquet` lists every document that was embedded and clustered: the pretraining chunk store
and the SFT assignment table. `web/dgx/build_master_index.py` builds it by joining each document's
`(topic_cluster, subtopic_cluster)` cell to a concept label through `cell2concept.json` and
`cell2concept_llm.json`.

| Column | Type | Meaning | Added |
|---|---|---|---|
| `doc_id` | string | `<source>__<NNNNNNNNN>__c<KKKK>` for pretrain chunks; SFT ids end in the source line number | build |
| `source` | string | source name (136 sources) | build |
| `topic_cluster` | integer | top-level cluster | build |
| `subtopic_cluster` | integer | cluster within the topic; with `topic_cluster`, identifies the cell | build |
| `role` | string | `pretrain` or `sft` | build |
| `concept` | string | the cell's concept label; remapped to the v5.3 primaries on 2026-09-07 | build, remapped |
| `wiki_primary_page_id` | int64 | the Wikipedia article this document's primary link points to | 2026-09-10 |
| `wiki_primary_cos` | float32 | cosine of that link | 2026-09-10 |
| `wiki_band` | uint8 | link strength: `0` weak · `1` medium · `2` strong · `3` curated bridge · `5` lexical agreement | 2026-09-10 |
| `wiki_channel` | uint8 | which linking channel produced the link | 2026-09-10 |

The four `wiki_*` columns were added by the Wikipedia-layer promotion; the schema of record is the cluster
file, not the build script (which writes the first six).

Measured: 89,907,669 rows (pretrain 77,327,492 · SFT 12,580,177), 89,907,665 with a concept (4 null); but only
**81,372,220 distinct `doc_id`s** (8,535,449 duplicate rows), because the pretrain and SFT frames overlap
(measured 2026-09-23). The "89.9 M documents" headline is a row count; for pretrain sources a row is a chunk,
not an article. `wiki_band` distribution over all rows (2026-09-10): strong 0.44 %, medium 4.1 %, lexical
agreement 5.04 %, bridge 79.8 %, weak 10.66 %.

`web/master_rollup.json` (repository copy) holds `total_docs`, `mapped`, `by_role`, `n_sources`,
`per_concept` (rows per concept) and `per_source` (`{role, docs, concepts: [[concept, percent], …]}`, top 8).

!!! warning "Read-only by contract"
    The Wikipedia chain asserts the master index's row count, so the estate builders read
    `master_doc_index.parquet` and never change it (`web/estate_doc_index.py` docstring). Re-running
    `build_master_index.py` would drop the `wiki_*` columns and revert the v5.3 remap.

## arXiv reference index

`arxiv_doc_index.parquet` holds the first **reference-tier** source: indexed, never embedded, never in a
training mix. One row per paper, sorted by `paper_id`. No text is stored.

| Column | Meaning |
|---|---|
| `doc_id` | `arxiv_complete__<paper_id>` |
| `source` | `arxiv_complete` |
| `role` | `reference` |
| `paper_id` | arXiv id |
| `license` | per-paper licence from the metadata config (null when arXiv holds none) |
| `license_text` | the same value from the assembled-text config (cross-check; the two agree on all 2,431,445 papers that have both) |
| `has_text` | an assembled text exists |
| `n_chars` | UTF-8 length of the assembled text |
| `n_abstract_chars` | abstract length |
| `title`, `primary_category`, `categories`, `doi` | metadata |
| `n_versions`, `first_version_date`, `latest_version_date` | version history |
| `text_sha256` | sha256 of the assembled text (content hash for decontamination) |
| `text_encoding`, `resolution`, `n_tex_files`, `n_files_used`, `n_unused_files` | how the text was assembled |

Measured 2026-09-23 (`web/acquisition/arxiv/arxiv_doc_rollup.json`): 3,148,796 rows, 2,856,227 with text,
246,780,951,228 characters in total, 452,715 papers with no licence.

## Estate document index

`estate_doc_index.parquet` is the only place the two tiers are unioned: one row per estate document, each with
its licence, Wikipedia link and MeSH concept. It is the table the licence policy is applied from.

| Column | Type | Meaning (embedded tier / reference tier) |
|---|---|---|
| `doc_id` | string | from `master_doc_index` / from `arxiv_doc_index` |
| `source` | dictionary string | source name |
| `role` | dictionary string | `pretrain`, `sft` / `reference` |
| `tier` | dictionary string | `embedded` / `reference` |
| `license` | dictionary string | resolved licence text |
| `license_id` | dictionary string | resolved licence id |
| `license_scope` | dictionary string | `dataset`, `document`, `derived`, `internal`, `mixed`, `unknown` |
| `license_status` | dictionary string | `verified`, `conflicting`, `not-found`, `internal`, `unresolved` |
| `license_upstream` | dictionary string | upstream key(s) in `web/licence/licence_registry.json` |
| `license_resolved_by` | dictionary string | resolution route |
| `wiki_primary_page_id` | int64 | Wikipedia primary link |
| `wiki_primary_cos` | float32 | its cosine |
| `wiki_band` | uint8 | band, as in the master index |
| `wiki_channel` | uint8 | channel |
| `wiki_basis` | dictionary string | `w5-primary-own_hub1` / `w5-primary-own_hub1 (arxiv_embed_align)` |
| `mesh_concept` | dictionary string | the cell concept / the cell concept only for MeSH-appropriate papers in non-boilerplate cells, else null |
| `mesh_basis` | dictionary string | `cell-v5.3` / `cell-v5.3 (arxiv_embed_align; MeSH-appropriate papers only)` |
| `mesh_appropriate` | boolean | reference tier only: whether MeSH applies to the paper |

Strings other than `doc_id` are dictionary-encoded; the file is zstd-compressed and replaced atomically
(written to `.tmp`, then renamed). If the arXiv embedding alignment is absent, the builder falls back to the
lexical alignment and writes `wiki_basis = arxiv-lexalign:<basis>` and `mesh_basis = arxiv-lexalign-v5.3-lexicon`.

Rules enforced by the builders: every reference `doc_id` starts with `arxiv_complete__`; no embedded `doc_id`
does; no reference id occurs in the embedded tier. Within-tier duplicates are counted and reported, not
rejected.

Measured 2026-09-23 (`web/licence/estate_licence_rollup.json`, `web/estate_doc_rollup.json`):

| Measure | Value |
|---|---|
| Rows | 93,056,465 (embedded 89,907,669 · reference 3,148,796) |
| Distinct documents | 84,521,016 (embedded 81,372,220 · reference 3,148,796) |
| Sources | 137 |
| Wikipedia-linked rows | embedded 89,907,669 · reference 3,148,796 |
| Rows with a MeSH concept | embedded 89,907,665 · reference 194,054 |
| Licence status, scope, resolution | see [Acquisition and licence](acquisition-and-licence.md#per-document-licence-on-the-estate-index) |

!!! warning "Reference-tier alignment numbers differ between records"
    The project's licence reference page (2026-09-23) reports 2,562,475 Wikipedia-linked and 213,809
    MeSH-labelled arXiv rows: those are the lexical-alignment figures, which the arXiv registry entry's
    `alignment` block also records (`wiki_linked: 2562475`). The estate rollup in the repository, built later
    the same day with the embedding alignment, reports 3,148,796 and 194,054. The current file follows the
    rollup. Also see the two-builder warning on
    [Acquisition and licence](acquisition-and-licence.md#per-document-licence-on-the-estate-index).

## Exact decontamination records

`web/decontam_exact.json` records whether any evaluation item's text is, verbatim, a document a model was
trained on. It is produced by `web/dgx/decontam_exact.py` and is the only contamination claim panAtlas
presents as proven.

**Method.**

1. For each benchmark, read the first lm-eval `samples_*.jsonl` file found (items are identical across
   checkpoints). All `mmlu_*` subtasks are merged into `mmlu`.
2. From each sample's `doc`, take every candidate string: `question`, `query`, `ctx`, `goal`, `sentence`,
   `premise`, `text`, `passage`, `activity_label`; each string or joined list under `context.<key>`; or
   `context` itself. A bare string `doc` is used as is.
3. Hash each with the ledger recipe, `blake2b(text.encode("utf-8", "ignore"), digest_size=16)`, raw, with
   no normalisation.
4. Semi-join the distinct hashes against `doc_ledger_crosswalk.parquet` (DuckDB, with a row-group scan
   fallback) to get `in_v4` and `in_v5`.

**Structure.** A JSON object keyed by benchmark task name; each value:

| Field | Type | Meaning |
|---|---|---|
| `items` | integer | number of samples-file lines read for the benchmark (lines, not distinct hashes) |
| `item_doc_uids_matched_v4` | integer | distinct item hashes found in the V4 ledger |
| `matched_v5` | integer | distinct item hashes found in the V5 ledger |
| `matched_either` | integer | distinct item hashes found in either |
| `trained_on` | boolean | `matched_either > 0` |
| `method` | string | `blake2b16 doc_uid membership vs doc_ledger_crosswalk` |

The asymmetric names (`item_doc_uids_matched_v4` but `matched_v5`) are as written by the script.

**Values at HEAD.** 16 benchmarks, 38,491 items in total, **zero matches and `trained_on: false` for all 16**:

| Benchmark key | Items | | Benchmark key | Items |
|---|---:|---|---|---:|
| `afrimedqa_mcq` | 3,600 | | `mathqa` | 2,985 |
| `arc_challenge` | 1,172 | | `medmcqa` | 4,183 |
| `arc_easy` | 2,376 | | `medqa_4options` | 1,273 |
| `asdiv` | 2,305 | | `medxpertqa_text` | 2,450 |
| `commonsense_qa` | 1,221 | | `mmlu` | 100 |
| `gsm8k` | 2,638 | | `piqa` | 1,838 |
| `hellaswag` | 10,042 | | `pubmedqa` | 500 |
| `ifeval` | 541 | | `winogrande` | 1,267 |

**Where it lands.** `web/decontam_enrich.py` maps task names to benchmark slugs (for example `medqa_4options`
→ `medqa`, `arc_challenge` → `arc-challenge`) and writes a `decontam` block on each benchmark node in the
served graph and on each entry of `web/benchmarks_llm.json`:

| Field | Meaning |
|---|---|
| `holdout_status` | `proven_trained_on`, `provably_held_out`, `partial`, `not_held_out` or `unchecked`, from a hand-maintained list per benchmark (the earlier 13-gram decontamination audit) |
| `holdout_note` | the sentence explaining that status |
| `exact_doc_uid.checked` | `true` if the benchmark is in `decontam_exact.json` |
| `exact_doc_uid.items`, `.matched_either` | copied from `decontam_exact.json` |
| `exact_doc_uid.verdict` | `no verbatim-document match (held out at the exact-document level)` or `EXACT doc_uid match in training ledger` |
| `method` | the recipe in words |

At HEAD the served graph has 124 benchmark nodes; 116 carry a `decontam` block, 16 with
`exact_doc_uid.checked: true`. `web/benchmarks_llm.json` has 106 blocks, 16 checked. See
[Benchmarks](benchmarks.md).

!!! warning "Documented fields differ from the data"
    `docs/evaluation-dimensions-and-metadata.md` §G lists `exact_doc_uid = {checked, matched_either,
    matched_v4, matched_v5}`. The data and `decontam_enrich.py` carry `{checked, items, matched_either,
    verdict}`; per-run V4/V5 matches are only in `decontam_exact.json`. The 106 blocks in
    `web/benchmarks_llm.json` also lack `holdout_status` and `holdout_note`, which the graph's blocks have.

!!! note "Limits of the exact check"
    It detects verbatim identity of a whole field with a whole training document. A reformatted, truncated
    or paraphrased copy, or an item embedded inside a longer training document, does not match. Zero
    matches means "not trained on verbatim", not "not seen". All 16 benchmarks are text; no imaging
    benchmark has an exact-overlap record.

## Registry labels v5.3

The v5.3 promotion (job 219233, 2026-09-07, 19 minutes) relabelled the estate's 1,740 cells with MeSH
descriptors and wrote per-document label artifacts. An independent job (219234, `p6_verify.py`) verified every
count below. Originals were backed up before the change; a promotion log and a labels manifest record it.

### Cell tables

`cell2concept.json` (the v5.3 table on the cluster; the v1 copy is kept beside it):

| Field | Meaning |
|---|---|
| `cell_id` | cell number |
| `topic_cluster`, `subtopic_cluster` | the cell's cluster coordinates (join key to `master_doc_index`) |
| `count` | documents in the cell |
| `slug` | `mesh-<primary_dui>` for a v5.3 cell; the v1 `concept-*` slug otherwise |
| `cos`, `cell_domain`, `topic_summary` | v1 fields (cosine to the v1 concept, domain, summary sentence) |
| `primary_dui`, `primary_name` | the v5.3 primary MeSH descriptor |
| enrichment, support and top-8 fields | the statistics that chose the primary |
| `boilerplate`, `primary_is_boilerplate` | boilerplate flags (the estate builder reads these two keys) |
| `label_source` | `v5.3` or `v1` |

The repository copy, `web/cell2concept.json`, is the v1 table: it has only the v1 fields above, and all
1,740 slugs are `concept-*` (see the warning on [Identifiers](identifiers.md#mesh-derived-ids)). The exact
key names of the enrichment, support and top-8 fields are recorded only in the cluster file and the labels
manifest; they could not be verified from the repository.

`cell2concept_llm.json` maps `cell_id` to the concept name used for the `concept` column.

Measured: 1,740 cells; **1,380 carry a v5.3 primary**; 360 cells with fewer than 200 labelled rows keep their
v1 label and say so. 114 cells (11,217,630 rows) are flagged boilerplate because their primary is in a fixed
set of 28 descriptors; their primaries are flagged, not replaced. In `master_doc_index.parquet`, the
`concept` column was remapped through the new table: 89,890,687 rows changed, and the verification found the
column agrees with the cell table on all 89,907,669 rows (0 mismatches, 4 null concepts).

### Per-document artifacts (`labels_v53/`)

All arrays are in **e8 row order** (the order of the embedding store), not master order.
`e8_to_master_rowmap.npy` maps an e8 row to a master row; e8 lists the SFT rows first, so e8 row 0 is master
row 77,327,492. The map is unique, and e8 ids 0 to 2,999 were checked equal to the registry `doc_id` at the
mapped row. The map carries ids only; there is no content join.

| Artifact | Size | Content | Measured |
|---|---:|---|---|
| `doc_mesh_labels_v53.npz` | 8.95 GiB | per-row lexical MeSH labels, CSR over e8 rows (estate linker, lexicon v5.3) | 83,752,006 labelled rows · 2,066,519,278 pairs |
| `doc_mesh_labels_v53_granular.npz` | 3.08 GiB | the most specific labels per row | 81,505,814 rows · 501,191,944 pairs |
| `doc_mesh_edges_v53_s1.npz`, `_s2.npz` | 55.67 GiB each | weighted document → descriptor edges for two seeds of a 10 % held-out split; fields `share`, `enr`, `nlp` (fp16), `flags` (bit 0 lexical, bit 1 neighbour), base rates, hold mask, neighbour count | s1: 5,292,977,718 edges over 85,546,517 documents; s2: 5,292,887,159 over 85,547,766; about 58.9 per document, median 13 neighbour edges, no cap |
| `knn_exact96/` | | the exact 96 nearest neighbours of every document: 86 parts of `idx` (int32) and `sim` (fp16), plus `mean.npy`; exhaustive search over the text-encoder vectors, centred on the corpus mean | last part 778,709 × 96 |
| `doc_ids_e8_order.txt` | 2.37 GiB | the document id of every e8 row | |
| `cell_boilerplate_flags.json`, `P4_relabel_report.json` | small | boilerplate flags and the relabel report | |

The edge build also wrote `P5_edges_report_s1.json` and `P5_edges_report_s2.json`, and the lexicon build
`lexicon_v53.jsonl` with `lexicon_v53_report.json`; the project record names them but not whether they sit
inside `labels_v53/`.

Total `labels_v53/`: 186,798,930,278 B, re-measured with `du -sb` on 2026-09-19 (an earlier "140 GB" figure
was low).

!!! danger "Derived label arrays cannot be redacted row by row"
    An `.npz` is a zip of whole arrays and a CSR row cannot be blanked without rewriting them. Removing one
    document from `labels_v53/` means invalidating and recomputing it from the retained recipe (jobs
    219233 and 219234, lexicon v5.3). The cost of that recompute has not been measured. The Parquet tables,
    by contrast, are row-group structured and can be sharded so that a withdrawal touches only its own rows.
    `doc_ids_e8_order.txt` is 89.9 M unkeyed content-derived ids; see the storage rule on
    [Identifiers](identifiers.md#document-uid-doc_uid).

## PMC identifier map

PMC documents in the V4 and V5 corpora were trained without per-article ids. Their identity was recovered by
content anchor (job 212698, 2026-08-16): a 12-word key from each trained document's opening matched against
the June-2026 Open Access baseline; a key that maps to two ids in one corpus is dropped as ambiguous (37,854,
0.5 %), never guessed. Result: 7,194,690 of 7,686,832 baseline members matched (93.6 %), giving
`pmc_doc_pmid_map.parquet` with columns `doc_uid, pmcid, pmid, in_v4, in_v5, corpus_index, match_offset`
(14,383,878 rows, V4 and V5 renditions) and a list of 6,978,012 exact trained PMIDs. It is the one table that
links a ledger `doc_uid` to a publisher identifier.

Related pages: [Identifiers](identifiers.md), [Acquisition and licence](acquisition-and-licence.md),
[Dataset registry](dataset-registry.md), [Benchmarks](benchmarks.md),
[Evaluation records](evaluation-records.md), [Models and curriculum](models-and-curriculum.md).
