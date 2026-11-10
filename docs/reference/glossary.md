# Glossary

**Agent.** A leaf node of the mesh: a JVM running the plugin host and plugins, attached to its
region's broker. Its identity is `region_agent`.

**Agent (panAtlas).** Anything that contributes to the atlas under its own identity: a participating mesh node, a
dataset manager, or a knowledge-graph agent that mirrors one external graph.

**Agent profile.** The panAtlas overlay on a mesh identity: display name, owner, institution, purpose, tier and
status, with a private contact block. See [Wire contract](../distributed/contract.md#agent-profile).

**Anchors.** One vector per grounded concept in one model's embedding space, used to attach new embeddings to
concepts. Only valid for that exact `model@version`.

**Attach.** Relating a new embedding to concepts by cosine similarity to the anchors, at or above the model's
cutoff. It produces `classified_as` connectivity edges and never creates new identities.

**Canonical identifier (`canonical_id`).** An ontology identifier such as `mesh:D051436`. The join key of
federation.

**Connectivity.** Relationships (edges), recorded as attributed claims. Contrast with substrate.

**`content_hash`.** SHA-256 over a report's nodes and edges, used for change detection. Not comparable across
producers; see [Participating agents](../distributed/agents.md#what-the-reporter-does-on-each-call).

**The mesh.** The hierarchical, secure, multi-tenant agent mesh (`global → region → agent`) that panAtlas runs on.
Documentation.

**Curriculum.** A model's ordered training stages, each answering: what data, when, which system, which
configuration, which codebase. See [Models and curriculum](../metadata/models-and-curriculum.md).

**Dataset manager.** The the panAtlas plugin plugin instance responsible for one dataset, running on the agent at the
dataset's site.

**`doc_uid`.** `blake2b(raw_text, 16 bytes)`: the unkeyed content identity of a document.

**Federation status.** `visible` (merged and shown) or `pending` (held for a curator), set by the reporting agent's
tier.

**GaiaKeep.** The global file system for agents, built on the same mesh. [Documentation](https://gaiakeep.github.io/docs/).

**Global controller.** The root of the panAtlas region, where inventories roll up and clients connect.

**Grounding.** Tying a node to a canonical vocabulary identifier. Ungrounded nodes stay private to their agent.

**Hub.** The panatlas.net side of federation: it pulls reports, merges permitted contributions and serves the graph.

**`manifest_hash`.** SHA-256 over a dataset's canonical sorted inventory of `(relpath, size, mtime)`. It detects
moves, growth and edits. It does not hash content.

**Mesh view.** The site's live view of the mesh nodes, links and the datasets each node hosts, drawn from `mesh.json`.

**Model space.** One registered `(modality, model, version)`. Embeddings compare only within one space.

**control-message.** the mesh's control-plane message. Manager calls (`getgraphmanifest`, `getgraphinventory`) are control-message
`EXEC` messages.

**the Python transport library.** the mesh's Python client library, used by the hub to list, deploy and call managers.

**Source of record.** The graph that maintains a node or triple. panAtlas curates only what it is the source of
record for.

**Status (agent).** `pending`, `active`, `suspended` or `revoked`. Only `active` agents contribute.

**Structure-only.** The federation rule that payloads carry identifiers, counts, edges, model stamps and hashes,
never content. Enforced by rejecting `text`, `body`, `raw`, `content`, `document`, `excerpt` and `abstract` at any
depth.

**Substrate.** Entity identity, keyed by canonical identifier. It merges by identity. Contrast with connectivity.

**Tier.** `trusted` (merged visibly on arrival) or `provisional` (held as pending claims).

**URN.** A dataset's global identifier, `panatlas:dataset:<slug>`.
