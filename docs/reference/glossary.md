# Glossary

**Agent (panAtlas).** Anything that contributes to the atlas under its own identity, such as a knowledge-graph agent
that mirrors one external graph.

**Agent profile.** The panAtlas record of a contributing agent: display name, owner, institution, purpose, tier and
status, with a private contact block (`web/federation/agent_profile.schema.json`).

**Anchors.** One vector per grounded concept in one model's embedding space, used to attach new embeddings to
concepts. Only valid for that exact `model@version`.

**Attach.** Relating a new embedding to concepts by cosine similarity to the anchors, at or above the model's
cutoff. It produces `classified_as` connectivity edges and never creates new identities.

**Canonical identifier (`canonical_id`).** An ontology identifier such as `mesh:D051436`. The join key when graphs
merge.

**Connectivity.** Relationships (edges), recorded as attributed claims. Contrast with substrate.

**`content_hash`.** SHA-256 over a report's nodes and edges, used for change detection. Not comparable across
producers.

**Curriculum.** A model's ordered training stages, each answering: what data, when, which system, which
configuration, which codebase. See [Models and curriculum](../metadata/models-and-curriculum.md).

**`doc_uid`.** `blake2b(raw_text, 16 bytes)`: the unkeyed content identity of a document.

**Domain.** A field of knowledge the atlas maps, such as medicine, food and nutrition, or general knowledge. panAtlas
covers every domain; medicine is where its holdings run deepest today. In the served graph the top-level domains are
`domain` nodes under `atlas-root`. Not the same as an evaluation domain (`eval-domain`), which classifies benchmarks.
See [Purpose and principles](../concepts/purpose.md).

**Federation status.** `visible` (merged and shown) or `pending` (held for a curator), set by the reporting agent's
tier.

**Grounding.** Tying a node to a canonical vocabulary identifier. Ungrounded nodes stay private to their agent.

**Hub.** The panatlas.net site. It serves the graph, the explorer and the public API.

**`manifest_hash`.** SHA-256 over a dataset's canonical sorted inventory of `(relpath, size, mtime)`. It detects
moves, growth and edits. It does not hash content.

**Model space.** One registered `(modality, model, version)`. Embeddings compare only within one space.

**Source of record.** The graph that maintains a node or triple. panAtlas curates only what it is the source of
record for.

**Status (agent).** `pending`, `active`, `suspended` or `revoked`. Only `active` agents contribute.

**Structure-only.** The rule that what leaves a site carries identifiers, counts, edges, model stamps and hashes,
never content. Enforced by rejecting `text`, `body`, `raw`, `content`, `document`, `excerpt` and `abstract` at any
depth.

**Substrate.** Entity identity, keyed by canonical identifier. It merges by identity. Contrast with connectivity.

**Tier.** `trusted` (merged visibly on arrival) or `provisional` (held as pending claims).

**URN.** A dataset's global identifier, `panatlas:dataset:<slug>`.
