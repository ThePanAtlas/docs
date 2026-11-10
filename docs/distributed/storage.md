# Storage on GaiaKeep

[GaiaKeep](https://gaiakeep.github.io/docs/) (GaiaKeep GFS) is a global file system built for agents, running over
the same [Cresco](https://crescoedge.github.io/docs/) mesh. Its job is to keep versioned datasets durable and to stream
any version wherever it is needed. Its durable tier encrypts blocks at the origin and places them across
independent sites, on memory, NVMe, disk or tape. Durability is chosen per dataset: erasure coding (`ec:2+1`, the
default for new collections), full replicas, or a single copy for scratch and cache data
([Durability and redundancy](https://gaiakeep.github.io/docs/concepts/durability/)). A separate live tier near
compute holds committed versions as unencrypted native files and never counts toward durability
([The live tier](https://gaiakeep.github.io/docs/concepts/live-tier/)). Release 1.3 of its storage core shipped on
2026-10-01 ([Status at a glance](https://gaiakeep.github.io/docs/built/status/)).

GaiaKeep's first real use is as panAtlas's durable backend, with versioned, append-based ingest: add datasets,
append versions, retrieve (question P1 in GaiaKeep's
[open questions](https://gaiakeep.github.io/docs/roadmap/open-questions/), answered 2026-10-02). GaiaKeep's
documentation has a page on this binding, [GaiaKeep: panAtlas](https://gaiakeep.github.io/docs/concepts/panatlas/).
This page summarises it from the panAtlas side. GaiaKeep is the authority on how GaiaKeep works.

!!! note "Status"
    GaiaKeep's core is **built and tested**; the panAtlas binding is **measured and designed**. The panAtlas index has
    not been stored in GaiaKeep yet. GaiaKeep's answer on its first real data (P2, 2026-10-02) is no single hero
    dataset: several test fixtures of different sizes and shapes, with the panAtlas index among the candidates. It
    is a strong candidate because it is small, its sizes are measured, and it exercises identity, versioning and the
    identifier rules without needing tape.

## The index is a dataset

Measured on 2026-09-19 on the HPC cluster:

| Part | Size | Share |
|---|---:|---:|
| Source-of-record ledgers (five parquet files: `doc_ledger_{crosswalk,v4,v5}`, `master_doc_index`, `pmc_doc_pmid_map`) | 11.24 GB | 5.7 % |
| Derived labels, edges and nearest neighbours (`labels_v53/`) | 186.80 GB | 94.3 % |
| **Total** | **198.04 GB** | 200,497,968 documents, 988 B each |

In archive terms that is 185 one-GiB parcels, **0.66 % of one 30 TB cartridge**, and about 13–14 minutes to bring
back from cold tape with a single mount (the timing is modelled). "Everything indexed" is affordable as long as the
index is stored as an **ordinary versioned dataset**, not as a per-document index inside the archive's own on-media
structures, which would be 254 times larger per cartridge. [Document index](../metadata/document-index.md) has the
schemas.

## Identifiers and write-once media

panAtlas identifies documents by `doc_uid = blake2b(raw_text, 16 bytes)`, an **unkeyed** content hash. That is what
makes the 200,497,968 documents of the pretraining-ledger crosswalk traceable across corpus versions and checkable for
training contamination ([Document index](../metadata/document-index.md)). It also means that anyone holding a
candidate document can confirm whether it is in the corpus: in GaiaKeep's terms, the hash is a **confirmation oracle**.

On write-once media that confirmation would last forever. In GaiaKeep's design of record (§19.3 of its
specification), a field on unerasable media is allowed only if an adversary holding a candidate plaintext, and no
key, cannot reproduce it. All three panAtlas identifier classes fail that test (`doc_uid`, `manifest_hash`, and
`doc_ids_e8_order.txt`, which is 2.54 GB of nothing but content hashes). They are therefore **payload only**:
allowed inside encrypted objects, never in on-media structures. A keyed form, `HMAC(K_idx, doc_uid)`, passes the rule
but gives up cross-version joinability.

That rule is not absolute. Under the deduplication model built in GaiaKeep 1.3 it became **per-mode policy**
(GaiaKeep decision log, 2026-09-19, "Becomes policy"): it is mandatory in every dedup mode except `GLOBAL`, where the
plain content hash is the public block id. Public literature, most of today's text corpus, could therefore sit in the
`GLOBAL` mode with plain content hashes; protected clinical data could not
([Tenants, collections and deduplication](https://gaiakeep.github.io/docs/concepts/tenancy-and-dedup/),
[Decision log](https://gaiakeep.github.io/docs/roadmap/decisions/)).

GaiaKeep mints its own identifiers and dataset namespace. A panAtlas URN is not a GaiaKeep dataset name; the
crosswalk from URN and `manifest_hash` to a GaiaKeep version is a panAtlas service, not a storage-layer dependency
(GaiaKeep questions X1 and X6, answered 2026-10-02).

!!! danger "Decide before the imaging overlap job runs"
    The exact-overlap contamination check has so far run only on text: 16 benchmarks, all text. When the imaging
    version runs, the same unkeyed hash will be computed over protected health information. GaiaKeep's side is
    settled: its question X1 was answered on 2026-10-02, and GaiaKeep mints its own identifiers and never relies on
    external keys. Whether to key `doc_uid`, which would break the cross-version crosswalk at every key rotation, is
    panAtlas's decision, and it has to be made before that job runs.

## Withdrawal

- **Parquet ledgers:** shard by redaction domain *before* storage, so that a withdrawal destroys one shard's key and
  blanks only those rows.
- **Derived arrays (`.npz`):** a row cannot be blanked without rewriting the whole array. The response is
  **invalidate and recompute**. That is possible because the recipe is kept (jobs 219233 and 219234, `p6_promote.py`,
  lexicon v5.3). The cost of a recompute has **not been measured**; the exhaustive nearest-neighbour search is the
  expensive part.

What a redaction domain is for panAtlas data, and whether recompute is affordable, are open (GaiaKeep questions X3
to X5).

## Why the shared mesh matters here

The mesh that carries the dataset managers also carries GaiaKeep. A site that joins Cresco can contribute
compute, storage and datasets through one identity, one trust model and one tenancy boundary. The atlas then
records where each dataset and each copy lives, by URN and `manifest_hash` (crosswalked to GaiaKeep's own version
names), without moving the data.
