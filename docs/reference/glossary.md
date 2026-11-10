# Glossary

**Agent (Cresco).** A leaf node of the Cresco mesh: a JVM running the OSGi host and plugins, attached as a client to
its region's broker. Messages address it as `region_agent`; its identity is its certificate subject
(`CN=<agent>, OU=<region>, O=<tenant>`). See [Cresco's glossary](https://crescoedge.github.io/docs/reference/glossary/).

**Agent (panAtlas).** Anything that contributes to the atlas under its own identity: a participating Cresco node, a
dataset manager, or a knowledge-graph agent that mirrors one external graph.

**Agent profile.** The panAtlas overlay on a Cresco identity: display name, owner, institution, purpose, tier and
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

**Cresco.** The hierarchical, secure, multi-tenant distributed agent mesh (`global → region → agent`) that panAtlas
runs on. Secure by default since its 1.3 hardening. [Documentation](https://crescoedge.github.io/docs/).

**Curriculum.** A model's ordered training stages, each answering: what data, when, which system, which
configuration, which codebase. See [Models and curriculum](../metadata/models-and-curriculum.md).

**Dataset manager.** The `cresco-panatlas` plugin instance responsible for one dataset, running on the agent at the
dataset's site.

**`doc_uid`.** `blake2b(raw_text, 16 bytes)`: the unkeyed content identity of a document.

**Domain.** A field of knowledge the atlas maps, such as medicine, food and nutrition, or general knowledge. panAtlas
covers every domain; medicine is where its holdings run deepest today. In the served graph the top-level domains are
`domain` nodes under `atlas-root`. Not the same as an evaluation domain (`eval-domain`), which classifies benchmarks.
See [Purpose and principles](../concepts/purpose.md).

**Federation status.** `visible` (merged and shown) or `pending` (held for a curator), set by the reporting agent's
tier.

**GaiaKeep.** A global file system built for agents, running on the same Cresco mesh: versioned datasets, kept
durable and streamed wherever they are needed. The intended durable backend for panAtlas.
[Documentation](https://gaiakeep.github.io/docs/); see [Storage on GaiaKeep](../distributed/storage.md).

**Global controller.** The root of the panAtlas Cresco region, where inventories roll up and through which the hub's
calls to managers are routed. In panAtlas's configuration the hub's client connects to the web host agent's wsapi,
not to the global's.

**Grounding.** Tying a node to a canonical vocabulary identifier. Ungrounded nodes stay private to their agent.

**Hub.** The panatlas.net side of federation: it pulls reports, merges permitted contributions and serves the graph.

**Join secret.** Cresco's per-tier discovery secret (`discovery_secret_agent`, `_region`, `_global`) that admits a
node to the mesh in the standard security profile; the production profile uses the operator's PKI instead.
See [Discovery](https://crescoedge.github.io/docs/architecture/discovery/).

**`manifest_hash`.** SHA-256 over a dataset's canonical sorted inventory of `(relpath, size, mtime)`. It detects
moves, growth and edits. It does not hash content.

**Mesh view.** The site's live view of Cresco nodes, links and the datasets each node hosts, drawn from `mesh.json`.

**Model space.** One registered `(modality, model, version)`. Embeddings compare only within one space.

**MsgEvent.** Cresco's control-plane message. Under Cresco 1.3's secure defaults each one is authenticated end to
end by its origin and bound to its recipient. Manager calls (`getgraphmanifest`, `getgraphinventory`) are MsgEvent `EXEC` messages.
See [MsgEvent](https://crescoedge.github.io/docs/api/msgevent/).

**pycrescolib.** Cresco's Python client library, used by the hub to list, deploy and call managers.

**Source of record.** The graph that maintains a node or triple. panAtlas curates only what it is the source of
record for.

**Status (agent).** `pending`, `active`, `suspended` or `revoked`. Only `active` agents contribute.

**Structure-only.** The federation rule that payloads carry identifiers, counts, edges, model stamps and hashes,
never content. Enforced by rejecting `text`, `body`, `raw`, `content`, `document`, `excerpt` and `abstract` at any
depth.

**Substrate.** Entity identity, keyed by canonical identifier. It merges by identity. Contrast with connectivity.

**Tier.** `trusted` (merged visibly on arrival) or `provisional` (held as pending claims).

**URN.** A dataset's global identifier, `panatlas:dataset:<slug>`.
