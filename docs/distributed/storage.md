# Storage on GaiaKeep

[GaiaKeep](https://gaiakeep.github.io/docs/) is the global file system for agents built on the same Cresco mesh:
versioned, erasure-coded, encrypted storage of raw blocks across memory, NVMe, disk and tape. panAtlas is one of its
primary intended users. GaiaKeep's documentation has a page on this binding:
[GaiaKeep: panAtlas](https://gaiakeep.github.io/docs/concepts/panatlas/). This page summarises it from the panAtlas
side.

!!! note "Status"
    The binding is **measured and designed**. The panAtlas index has not been stored in GaiaKeep yet. It is named
    there as a strong first real dataset.

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
makes 200 million documents traceable across corpus versions and checkable for training contamination. It also means
that anyone holding a candidate document can confirm whether it is in the corpus.

On write-once media that confirmation would last forever. GaiaKeep's rule: a field on unerasable media is allowed
only if an adversary holding a candidate plaintext, and no key, cannot reproduce it. All three panAtlas identifier
classes fail that test (`doc_uid`, `manifest_hash`, and `doc_ids_e8_order.txt`, which is 2.54 GB of nothing but
content hashes). They are therefore **payload only**: allowed inside encrypted objects, never in on-media
structures. A keyed form, `HMAC(K_idx, doc_uid)`, passes the rule but gives up cross-version joinability.

!!! danger "Decide before the imaging overlap job runs"
    The exact-overlap contamination check has so far run only on text: 16 benchmarks, all text. When the imaging
    version runs, the same unkeyed hash will be computed over protected health information. Whether to key it has
    to be decided first.

## Withdrawal

- **Parquet ledgers:** shard by redaction domain *before* storage, so that a withdrawal destroys one shard's key and
  blanks only those rows.
- **Derived arrays (`.npz`):** a row cannot be blanked without rewriting the whole array. The response is
  **invalidate and recompute**. That is possible because the recipe is kept (jobs 219233 and 219234, `p6_promote.py`,
  lexicon v5.3). The cost of a recompute has **not been measured**; the exhaustive nearest-neighbour search is the
  expensive part.

## Why the shared mesh matters here

The mesh that carries the dataset managers also carries GaiaKeep. A site that joins Cresco can contribute
compute, storage and datasets through one identity, one trust model and one tenancy boundary. The atlas then
records where each dataset and each copy lives, by URN and `manifest_hash`, without moving the data.
