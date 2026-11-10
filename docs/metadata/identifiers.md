# Identifiers

!!! info "Status"
    **Built and in use.** Every scheme on this page exists in the repository data or in the cluster-side
    artifacts it describes. Counts were computed from the repository at HEAD `57505c6` (2026-10-31) unless a
    different date is given. Counts for cluster-side artifacts (the document ledger, the estate index, the v5.3
    labels) come from dated measurements recorded by the project and are marked as such.

panAtlas follows one rule, stated in `web/ID-POLICY.md`: every entity and every relationship has a unique,
stable id. In practice there are several id families. They differ in how they are minted (assigned by hand,
derived from a name, or computed from content) and in what they promise:

| Family | Form | Minted from | Promise |
|---|---|---|---|
| Dataset URN | `panatlas:dataset:<slug>` | the slug, assigned at registration | global handle for one dataset; never reassigned |
| Dataset slug | `[a-z0-9]+(-[a-z0-9]+)*` | a name, assigned by the registering script | unique in the registry; equals the URN suffix |
| Item namespace | `id_namespace`, e.g. `ctrate:` | assigned at registration | scopes item ids inside one dataset (see the collision warning below) |
| Graph node id | `<prefix>-<slug>` | per builder | unique in `graph.json` |
| Graph edge id | `e-` + blake2b-10 of `from\|to\|rel` | content of the edge | duplicate edges collapse to one id |
| Document uid | `doc_uid` = blake2b-16 of raw text | the text itself | same text, same id, in every lineage |
| Estate document id | `doc_id`, e.g. `<source>__<NNNNNNNNN>__c<KKKK>` | position in a source | unique across estate tiers |
| Manifest hash | `sha256:` + 64 hex | the canonical file inventory | identical inventory, identical hash |
| Version tag | `model@version`, schema `/1`, upstream revisions | assigned or upstream | names one embedding space, schema or release |
| Job id | Slurm job number | the scheduler | provenance pointer to the run that produced a value |

The sections below define each one, name the script that mints it, and give the stability and collision rules.

## Dataset URN

```text
panatlas:dataset:<slug>
```

The URN is the single global handle for a dataset (`PLAN-datasets.md` §1). It is the key used by every
registry upsert, by the manager plugin configuration (`panatlas_dataset_id`), by manager reports, and by the
cross-references between registry entries (`derived_from`, `part_of`, `partition_of`, `members`, `corpus`).

**Only one URN kind exists.** A search of every JSON, Python, Markdown, Java, JavaScript and PHP file in the
repository finds 2,305 occurrences of a `panatlas:<kind>:` prefix, and all of them are `panatlas:dataset:`.
Models, benchmarks, concepts and other entities are identified by graph node ids, not URNs.

| Where | URNs | Notes |
|---|---:|---|
| `web/datasets.json` (the registry) | 200 | all distinct; `urn == "panatlas:dataset:" + slug` for all 200 |
| Fragment files `web/datasets_*.json` | 65 | every fragment URN is also in `web/datasets.json` |
| Served catalog `web/wp-plugin/panatlas-explorer/data/datasets.json` | 622 | the 200 registry URNs plus 422 catalog-only entries; `urn == prefix + slug` for all 622 |

How a URN is minted: the registering script writes `urn` and `slug` together. The minting scripts and their
slug rules are listed under [Dataset slug](#dataset-slug). Every upsert path asserts URN uniqueness before
writing (`assert len(urns) == len(set(urns))` in `web/register_fragment.py`, `web/register_tcga.py`,
`web/register_okn.py`; `sync_catalog.py` asserts the same over the catalog).

!!! warning "Dangling URN references"
    URN cross-references are not checked against the registry. At HEAD, 26 distinct URNs named in
    `derived_from` lists do not resolve to a registry entry (for example `panatlas:dataset:trialgpt`,
    `panatlas:dataset:ultrainteract-sft`, several router and tool packs). 16 of the 26 exist in the served
    catalog as catalog-only entries; 10 exist nowhere. Treat `derived_from` as a provenance claim, not a
    foreign key.

## Dataset slug

Rules, computed over all 200 registry entries at HEAD:

- Lowercase ASCII letters, digits and single hyphens: every slug matches `^[a-z0-9]+(-[a-z0-9]+)*$`.
- Longest slug: 35 characters.
- `slug` is the URN suffix, the manifest file stem (`web/manifests/<slug>.manifest.json`), the manager payload
  stem (`<slug>.report.json`, `<slug>.instance.json`), and (for registry entries that have a graph node) the
  suffix of the node id `dataset-<slug>`.

Slugs are assigned by the script that registers the dataset. The rule differs per script:

| Script | Slug rule | Example |
|---|---|---|
| `web/acquisition/okn/okn_agent.py` (`describe`) | `okn-` + the OKN graph short name | `okn-babel` |
| `web/register_openh.py` | `openh-rf-` + subset name lowercased, runs of non-`[a-z0-9]` replaced by `-` | `openh-rf-oslo` |
| `web/derive_source_manifests.py` (`slug_for`) | `ct-` + the corpus source directory name with `_` replaced by `-` | `ct-nlst` |
| `web/build_all_datasets.py`, `web/build_train_sources.py` (`nid`) | `dataset-` + source name lowercased, runs of non-`[a-z0-9]` replaced by `-`; the slug is the node id without `dataset-` | catalog-only entries |
| `web/register_arxiv.py`, `web/register_neuropath.py`, `web/renal_sbir_registry.py`, fragments | written literally in the script or fragment | `arxiv-complete`, `kits23` |

Stability and reuse:

- `web/ID-POLICY.md`: "a slug is never reused for a different thing." No code enforces this beyond the
  duplicate-URN assertion, which only prevents two live entries with one slug.
- Two retired slugs survive only as manifest files: `web/manifests/heartlens-ct.manifest.json` and
  `web/manifests/nlst-ct.manifest.json` (2026-07-31 manifests from the first registration in
  `PLAN-datasets.md` §3). Neither slug is in the registry today; the CT data they named is now registered
  under `heartlens-ct3d-native` and its `ct-*` partitions. Do not mint either slug again.

## Graph node id for a dataset

A registry entry is represented in the knowledge graph by the node `dataset-<slug>` (`web/ID-POLICY.md`).
At HEAD the served graph (`web/wp-plugin/panatlas-explorer/data/graph.json`, 6,187 nodes) has 513 nodes of
kind `dataset`: 400 with prefix `dataset-`, 101 with `dsft-` (SFT mixes) and 12 with `ext-`. 104 of the 200
registry entries have a `dataset-<slug>` node; the other 96 are catalogued without a graph node.

!!! warning "Node ids that do not follow the slug"
    `web/multimodal.json` keys its ten imaging entries by node ids such as `dataset-ctrate-train`, while the
    registry slug for the same dataset is `ct-rate`. One node with the `dataset-` prefix
    (`dataset-foodatlas`) has kind `kg`, not `dataset`. Join registry entries to graph nodes by
    `dataset-<slug>` only where that node exists, and do not infer one from the other.

The other graph node prefixes, with their counts in the served graph at HEAD, are listed below for
completeness. Their meaning is documented in [Graph schema](graph-schema.md).

| Prefix | Nodes | | Prefix | Nodes |
|---|---:|---|---|---:|
| `fa-` (`fa-dis-` 3,170, `fa-food-` 1,582) | 4,752 | | `capgroup-` | 13 |
| `dataset-` | 401 | | `ext-` | 12 |
| `concept-` | 206 | | `evdomain-` | 9 |
| `fndds-` | 172 | | `nacc-` | 5 |
| `mesh-` | 142 | | `domain-` | 5 |
| `bench-` | 124 | | `register-` | 5 |
| `dsft-` | 101 | | `codebase-` | 4 |
| `model-` | 90 | | `doc-` | 3 |
| `cap-` | 35 | | `gen-` | 3 |
| `atype-` | 35 | | `group-` | 2 |
| `type-` | 21 | | `atlas-`, `suite-`, `sys-`, `system-` | 1 each |
| `onto-` | 15 | | `null` (a literal node id) | 1 |
| `stage-` | 14 | | | |
| `fhir-` | 13 | | | |

!!! warning "A node whose id is the string `null`"
    The served graph contains one node with id `null`. `web/ID-POLICY.md` requires a non-empty id on every
    node; the string passes that check but is almost certainly a builder writing a missing value. All node
    ids are otherwise unique (verified at HEAD).

The `domain-*` / `evdomain-*` split is the one recorded collision: benchmark `domain-*` nodes once collided
with the knowledge-domain roots and deleted them, so benchmark domains moved to `evdomain-*`
(`web/ID-POLICY.md`).

## MeSH-derived ids

MeSH descriptors appear in four forms. DUIs are NLM descriptor unique ids (`D` followed by six or nine digits).

| Form | Where | Minted by | Count |
|---|---|---|---|
| `mesh:<DUI>` | `canonical_id` on concept nodes | concept builders | per node |
| `mesh-<DUI>` | graph node id for a MeSH descriptor node | `web/build_layered.py` (`nid = "mesh-" + dui`) | 142 nodes in the served graph, all kind `concept` |
| `mesh-<DUI>` | `slug` of a v5.3 cell record in the cluster's `cell2concept.json` | the v5.3 label promotion (job 219233, `p6_promote.py`) | 1,380 of 1,740 cells (measured 2026-09-07, verified by job 219234) |
| `fa-dis-<DUI>` | FoodAtlas disease nodes | FoodAtlas builders | 3,170 nodes |

The v5.3 promotion gave every cell with at least 200 labelled rows a primary MeSH descriptor and set its slug
to `mesh-<primary_dui>`; the 360 cells below that floor kept their v1 `concept-*` slug. The independent
verification job checked that every v5.3 cell's slug equals `mesh-` + its `primary_dui`. See
[Document index](document-index.md#registry-labels-v53).

!!! warning "The repository copy of `cell2concept.json` is the v1 table"
    `web/cell2concept.json` in the repository has 1,740 records whose slugs are all `concept-*` (50 distinct)
    and has no `primary_dui` field. It is the pre-v5.3 table from the initial commit. The v5.3 table with
    `mesh-<DUI>` slugs exists on the cluster only. Do not derive v5.3 cell ids from the repository copy.

## Item namespaces and item ids

Each registry entry may carry an `id_namespace`. Item ids (a volume, a slide, a study, a row) are written
inside that namespace so that they are distinguishable from items of other datasets (`PLAN-datasets.md` §1):
`ctrate:vol:train_10000_a_1` belongs to `panatlas:dataset:ct-rate`.

Measured at HEAD: 194 of 200 entries carry `id_namespace` (the six predictor-suite entries do not). 159 end in
`:`; the 35 OpenH-RF entries use a path-like form `openh-rf:<subset>/`. Namespaces are partly hierarchical:
all 46 OKN entries use `okn:<shortname>:`, ten JK-Decide components use `jkd1:<component>:`.

`web/multimodal.json` records the item-id scheme for ten imaging datasets (`unique_id_scheme`), for example:

| Dataset | Namespace | Item id scheme |
|---|---|---|
| CT-RATE | `ctrate:` | volume `ctrate:vol:<VolumeName>`; slice `ctrate:slice:<VolumeName>#z<NNNN>` |
| MR-RATE | `mrrate:` | study `mrrate:study:<study_uid>` |
| MIMIC-CXR | `mimic-cxr:` | study `mimic-cxr:study:<study_id>` |
| KiTS23 | `kits23:` | case `kits23:case_<NNNNN>` |
| TCIA TCGA-KIRC | `tcia_tcga_kirc:` | series `tcia_tcga_kirc:<SeriesInstanceUID>` |

These namespaces are separate from the text estate's `doc_id` space (`web/multimodal.json` `_note`): a
radiology report and its paired volume are two documents in two modalities.

!!! warning "Namespaces are not unique per dataset"
    `PLAN-datasets.md` says item ids are "globally unique" because each dataset has its own namespace. The
    data does not guarantee that: `gdc:` is shared by four entries (`gdc-tcga-kidney`, `gdc-tcga-slides-meta`,
    `tcga-diagnostic-slides`, `tcga-tissue-slides`) and a second namespace is shared by the two
    neuropathology entries. An item id in a shared namespace identifies the upstream object (a GDC file
    UUID, for example) but not which registry entry holds it. Qualify item ids with the dataset URN when
    the distinction matters.

## Graph edge id

```text
edge.id = "e-" + blake2b(f"{from}|{to}|{rel}".encode(), digest_size=10).hexdigest()
```

`web/ID-POLICY.md` defines an edge id as content-addressed on its endpoints and relation, so duplicate
edges collapse to one. The builders that add edges (`web/build_all_datasets.py`, `web/enrich_graph.py`,
`web/build_curriculum.py`, `web/model_wiring.py` and others) use `digest_size=10`, giving 20 hex characters.
The `link_*.py` scripts (`link_renal.py`, `link_neuropath.py`, `link_openh.py`, `link_predictors.py`) read
an existing edge id and choose `DIGEST = max(4, (len(sample) - 2) // 2)` so that they match whatever
length the graph already uses.

Verified at HEAD over the served graph (17,119 edges): all edge ids are unique; 16,916 recompute exactly
from the formula above; the remaining 203 have the form `e-arxiv-<DUI>-<target>` truncated to 60 characters,
minted by `web/fold_arxiv_alignment.py`. Those 203 are name-derived, not content-addressed.

## Document uid (`doc_uid`)

```python
doc_uid = hashlib.blake2b(raw_text.encode("utf-8"), digest_size=16).hexdigest()   # 32 hex characters
```

The text is the identity (`web/ID-POLICY.md`). The same text has the same `doc_uid` in every lineage
(`v4_clean`, `v4_dedup`, `v5_tier1`, `v5_clean`, pretrain or SFT). It is computed on raw text with no
normalisation. It serves four roles:

- **Join key** between training exposure and evaluation (`doc_uid → concept`, `doc_uid → (model, score)`).
- **Contamination detector**: an evaluation item whose `doc_uid` equals a training document's was trained on
  (`web/dgx/decontam_exact.py`; see [Document index](document-index.md#exact-decontamination-records)).
- **De-duplicator**: distinct documents are `len(set(doc_uid))`; exposure is counted on distinct `doc_uid`.
- **Cross-version tracker**: the ledger crosswalk records, per `doc_uid`, whether V4 and V5 trained on it.

Minted by the document-ledger build (spec-kit feature 017; ledger jobs 207724, merge 208237, crosswalk
208241, 2026-08-01) over every document that entered the V4 and V5 pretraining runs. Measured numbers are on
[Document index](document-index.md#document-ledger-and-doc_uid-crosswalk).

!!! warning "The question map does not use the ledger recipe"
    `web/build_question_concept_map.py` writes a `doc_uid` per benchmark question as
    `hashlib.blake2b(text.encode()).hexdigest()`, which is blake2b with its default 64-byte digest (128 hex
    characters). Those values can never equal a ledger `doc_uid`. `web/ID-POLICY.md` notes that the
    parameters "must be reconciled"; at HEAD they are not. The decontamination script
    (`web/dgx/decontam_exact.py`) does use `digest_size=16`, but encodes with `errors="ignore"`, so text with
    unencodable code points hashes differently from a strict encode.

!!! danger "`doc_uid` is unkeyed"
    Anyone holding a candidate document can recompute its `doc_uid` and confirm whether it is in the
    estate. On erasable storage that is the feature that makes decontamination possible. On write-once
    media it is a permanent membership oracle with no key to destroy. The project's storage rule (recorded
    2026-09-19) treats `doc_uid`, `manifest_hash` and the e8-ordered id list
    (`labels_v53/doc_ids_e8_order.txt`, 89.9 M unkeyed content hashes) as payload-only: they may be stored
    only inside encrypted objects, never in any cleartext index field. A keyed form, `HMAC(K, doc_uid)`, is
    safe but loses cross-lineage joinability.

## Estate document id (`doc_id`)

`doc_id` is positional, not content-addressed. It names a row in a source as that source was processed:

| Tier / role | Form | Source |
|---|---|---|
| Embedded, pretrain | `<source>__<NNNNNNNNN>__c<KKKK>` (document index, chunk index) | parsed by `web/licence/estate_licence_build.py`; e.g. `pmc__000000000__c0000` |
| Embedded, SFT | `<source>…<line number>` (the suffix is the source file line number, proved for all 53,505,117 stage-0 rows) | `web/licence/estate_licence_build.py`, vault reference on estate licences |
| Reference (arXiv) | `arxiv_complete__<paper_id>` | `web/acquisition/arxiv/arxiv_doc_index.py` |
| Benchmark question | `question_id = <bench>__<index>` | `docs/evaluation-dimensions-and-metadata.md` §E |

Rules enforced by `web/estate_doc_index.py`: every reference-tier id starts with `arxiv_complete__`; no
embedded-tier id may; the reference ids are probed against every embedded chunk and must not collide. Within
the embedded tier, duplicates are counted and reported, not rejected (measured 2026-09-23: 89,907,669 rows,
81,372,220 distinct). See [Document index](document-index.md).

`doc_id` and `doc_uid` are different keys. `doc_id` locates a row; `doc_uid` identifies text. The PMC
mapping table `pmc_doc_pmid_map.parquet` is the one recorded artifact that carries both kinds of key for a
source (`doc_uid, pmcid, pmid, in_v4, in_v5, corpus_index, match_offset`).

## Manifest hash

```text
manifest_hash = "sha256:" + sha256("\n".join(f"{relpath}\t{size}\t{int(mtime)}" for each file, sorted)).hexdigest()
```

The audit fingerprint of a dataset's files. Minted by `web/dataset_manifest.py` (and, byte-compatibly, by
`web/dataset_manifest_parallel.py` and `web/derive_source_manifests.py`). It changes whenever a file is added,
removed, moved, resized, or has its modification time changed. It does not hash file content. Full
definition, limits and audit procedure: [Manifests](manifests.md).

The hash is also used as a version string: the manager plugin's `panatlas_graph_version` is the dataset's
current `manifest_hash`, or the literal `unversioned` when the entry has none (`web/build_dataset_reports.py`).

## Version tags

| Tag | Form | Where | Notes |
|---|---|---|---|
| Embedding space | `<model-id>@<version>` | registry `embedding_models.<modality>` | the unit of comparability (`PLAN-dataset-plugins.md` §2). Values at HEAD: `imaging-rad-dino-ct@raddino` (33 entries), `text-bioclinical-modernbert-large@v3w` (18), and one value with no `@version` (`text-bioclinical-modernbert-large`, on `kos-v6-pretrain-corpus`). |
| Registry schema | `panatlas.datasets/1` | `meta.schema` (or top-level `schema`) of every registry file | other schema tags in the repository include `panatlas-model-curriculum/1`, `panatlas-okn-agent/1`, `panatlas-artifact-types/1`, `panatlas-record-level/1`, `panatlas-record-typing/2` |
| Upstream revision | git or Hugging Face commit SHA | `acquisition.revision`, `provenance.revision`, `source_of_record.registry_commit` | pins the exact upstream snapshot acquired |
| OKN graph version | `upstream_version`, `held_version` | `source_of_record` | upstream release vs the copy held; `held_version` is `null` until a verified copy exists |
| Restricted release | release name, e.g. `2026AA` | `restricted/umls/<version>/` on the cluster | see [Acquisition and licence](acquisition-and-licence.md#restricted-data) |
| Label release | `v1`, `v5.3` | cell table, lexicon, `labels_v53/` | see [Document index](document-index.md#registry-labels-v53) |

!!! warning "The registered text version differs from the tag datasets use"
    `web/models.json` registers the text model `text-bioclinical-modernbert-large` with version
    `v3w-2026.07`, while 18 registry entries name it `@v3w`. It also files the imaging model under modality
    key `imaging`, while the registry uses `imaging-ct`. `PLAN-datasets.md` and `PLAN-dataset-plugins.md`
    still name the CT space `imaging-v628-ct@v628`; no registry entry uses it at HEAD. A consumer that
    validates `model@version` strictly against `web/models.json` will reject every current entry; compare
    on the model id and treat the version strings as aliases until they are reconciled.

## Job ids as provenance

Slurm job numbers are recorded as provenance for values that a cluster job produced. They are pointers, not
identifiers of the data: a job id says which run computed a manifest, a label table or an evaluation output,
so the run's log and script can be found.

Forms found in the registry at HEAD:

| Field | Form | Example |
|---|---|---|
| `provenance.jobs[]` | `job:<n>` | `job:246943` |
| `provenance[]` (list-valued provenance) | `job:<n>` | `job:207661` |
| `provenance.job` | `<n>` | `220272` |
| `acquisition.jobs[]` | `<n> <purpose>` | `220405 probe` |
| `verification.<release>.job` | `<n>` | `220431` |
| free text in `computed`, `notes`, `input_convention` | `job <n>`, `SLURM job <n>` | `refreshed 2026-09-18, job 220280` |

33 `job:<n>` tokens and about 50 free-text job references occur in the registry. The public API removes job
numbers and cluster paths from every string it serves (`panatlas_pub_scrub` in
`web/wp-plugin/panatlas-explorer/includes/public-api.php`), so job ids are visible in the repository and to
authenticated tools but not in public responses.

## What is never reused

- A dataset slug or URN, once registered, names that dataset only (`web/ID-POLICY.md`). Retired slugs stay
  retired (`heartlens-ct`, `nlst-ct`).
- A graph node id is never given to a different kind of thing (the `domain-*` → `evdomain-*` move was made to
  restore this).
- `doc_uid`, edge ids and `manifest_hash` cannot be reused: they are functions of content, so the same value
  always means the same text, edge or inventory.
- `doc_id` values are positional. They are stable only for a fixed build of a source; a rebuild that reorders
  a source changes them. Use `doc_uid` for anything that must survive a rebuild.

Related pages: [Dataset registry](dataset-registry.md), [Manifests](manifests.md),
[Document index](document-index.md), [Graph schema](graph-schema.md),
[Models and curriculum](models-and-curriculum.md).
