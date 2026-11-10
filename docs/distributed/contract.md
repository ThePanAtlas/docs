# Wire contract and schemas

Every message and file on the federation path, field by field. Schemas are the files in `web/federation/` (copied
unchanged into `agent-deployment/contract/`; the two copies are identical at repo HEAD). Where the code writes
something the schema does not describe, this page says so.

| Artifact | Produced by | Consumed by | Section |
|---|---|---|---|
| Agent report (`report.schema.json`) | Participating agents, `pa_local_agent.py`, `pa_agent.py` | The plugin, `merge_reports.py` | [Agent report](#agent-report) |
| Dataset-manager report | `build_dataset_reports.py` | The plugin, `mesh_daemon.py` | [Dataset-manager report](#dataset-manager-report) |
| Manager instance configuration | `build_dataset_reports.py` | `deploy_managers.py`, the Cresco agent | [Instance configuration](#manager-instance-configuration) |
| Plugin MsgEvent replies | `cresco-panatlas` | The hub | [MsgEvent actions](#msgevent-actions) |
| Agent profile (`agent_profile.schema.json`) | The admin portal | The directory, `merge_reports.py` | [Agent profile](#agent-profile) |
| `merged_federation.json` | `merge_reports.py` | `build_layered.py` | [Merge output](#merge-output) |
| `mesh.json` | `mesh_daemon.py` | The site's Mesh view | [Mesh state](#mesh-state-meshjson) |
| `models.json` | Hub maintainers | Local agents, attach, the hub merge | [Model registry](#model-registry-modelsjson) |

## Agent report

`report.schema.json`, JSON Schema draft 2020-12, `$id` `https://panatlas.net/federation/report.schema.json`.
Top-level `additionalProperties: false`.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `agent_id` | string, `^agent-[a-z0-9-]+$` | yes | The reporting agent |
| `reported_at` | string, `date-time` | yes | The agent's own clock at report time. `pa_agent.py` takes it from `--reported-at` |
| `graph_version` | string | yes | The agent's version label for this snapshot, e.g. `2026.07.29-1`, or a `manifest_hash` for dataset managers |
| `content_hash` | string, `^sha256:[0-9a-f]{64}$` | yes | Hash of the node and edge set. Snapshots are idempotent by this value. See the [hashing caveat](agents.md#what-the-reporter-does-on-each-call) |
| `generator` | string | no | Producer and version: `pa_agent/0.1`, `pa_local_agent/0.1`, `cresco-panatlas/0.1` |
| `nodes` | array of node | yes | |
| `edges` | array of edge | yes | |

**Node** (`additionalProperties: false`; must have `canonical_id` **or** `local_id`):

| Field | Type | Meaning |
|---|---|---|
| `canonical_id` | string | The grounding join key, e.g. `mesh:D051436`. **Required for the node to merge** |
| `local_id` | string | Agent-local identifier for an ungrounded node. Namespaced at the hub as `fed:<agent_id>:<local_id>`; the design text also writes `<agent_id>:local:<local_id>`. Never enters the MeSH tree |
| `label` | string, max 200 | Human-readable name |
| `kind` | string | Node kind: `disease`, `concept`, `cluster`, … Free text; the merge defaults to `concept` |
| `grounding` | enum | `mesh`, `mesh_broader`, `fhir`, `chebi`, `foodon`, `fdc`, `snomed`, `loinc`, `rxnorm`, `umls`, `wikipedia`, `none` |
| `host` | string | Where the node's data lives |
| `claims` | object of number, integer, string or boolean | Counts, enums and flags only (e.g. `n_docs`, `modality`, `n_subtopics`, `cos_to_anchor`). Never text |

**Edge** (`additionalProperties: false`):

| Field | Type | Required | Meaning |
|---|---|---|---|
| `from` | string | yes | A `canonical_id`, a base-graph node id, or an agent-namespaced id |
| `to` | string | yes | Same |
| `rel` | string | yes | Relation, e.g. `part_of`, `classified_as`, `covers` |
| `claims` | object of scalars | no | For attach edges: `origin: "embedding"`, `model`, `version`, `cosine`, `canonical_id`. Only `cosine` and `model` survive the merge, as `evidence` |

**Forbidden anywhere** (schema `$comment`, enforced in code): `text`, `body`, `raw`, `content`, `document`,
`excerpt`, and in code also `abstract`.

**Example** (`web/federation/agent_report_example.json`, abridged):

```json
{
  "agent_id": "agent-site-kos",
  "reported_at": "2026-07-29T18:00:00Z",
  "graph_version": "2026.07.29-1",
  "content_hash": "sha256:…",
  "generator": "pa_agent/0.1",
  "nodes": [
    {"canonical_id": "mesh:D051436", "kind": "disease", "grounding": "mesh",
     "label": "Renal Insufficiency, Chronic", "claims": {"n_docs": 12043, "modality": "text"}},
    {"local_id": "run-2026-07-29-cluster-3187", "kind": "cluster", "grounding": "none",
     "label": "CKD dietary-management cluster", "claims": {"n_docs": 4210, "cos_to_anchor": 0.41}}
  ],
  "edges": [
    {"from": "mesh:D051436", "to": "concept-nephrology", "rel": "part_of", "claims": {}},
    {"from": "agent-site-kos:local:run-2026-07-29-cluster-3187", "to": "mesh:D051436",
     "rel": "classified_as", "claims": {"weight": 0.62}}
  ]
}
```

!!! warning "Cresco identities do not match the `agent_id` pattern"
    The plugin stamps `agent_id = "agent-<region>_<agent>"`, which contains an underscore. Both the schema pattern
    and the admin portal's registration check (`^agent-[a-z0-9-]+$`) reject underscores. A Cresco agent therefore
    cannot be registered under its own mesh identity, and `merge_reports.py` would treat its reports as coming from
    an unknown (provisional, pending) agent. One of the two rules has to change before an outside site's reports
    merge automatically; registering with `-` in place of `_` is the stop-gap.

## Dataset-manager report

`<slug>.report.json`, written by `web/build_dataset_reports.py`. This shape is **not** `report.schema.json`. It uses
`id`/`type` nodes and `source`/`target` edges, and the hub reads it directly.

| Top-level field | Type | Meaning |
|---|---|---|
| `urn` | string | The dataset URN, `panatlas:dataset:<slug>` |
| `nodes` | array | The dataset node, then modality, model and vocabulary nodes |
| `edges` | array | Structural edges from the dataset node |

**Nodes:**

| `type` | `id` | Other fields |
|---|---|---|
| `dataset` (one) | the URN | `label` (registry `name`), `modality` (list), `host`, `access`, `item_count`, `file_count`, `manifest_hash` |
| `modality` | `modality:<m>` | `label` |
| `model` | `model:<model>` | `label`, `modality`. Datasets whose model is `null` (a pending encoder) get no model node |
| `vocab` | `vocab:<v>` | `label`. `<v>` is each of `mesh`, `umls`, `foodatlas`, `fdc`, `nacc`, `v628` found as a substring of the registry's `grounding` text; `ungrounded` if none |

`item_count` is the first of these registry `scale` keys that is present: `volumes`, `studies`, `entities`,
`foods`, `worklist_cases`, `axial_cases`, `papers`. `file_count` and `manifest_hash` come from the registry
`manifest`. Field meanings are in [Dataset registry](../metadata/dataset-registry.md) and
[Manifests](../metadata/manifests.md).

**Edges** (`source`, `target`, `rel`): `has_modality` (dataset → modality), `embedded_by` (dataset → model),
`grounds_to` (dataset → vocab).

An optional `<slug>/grounded.json` (`{nodes: [], edges: []}`) layers grounded concept connectivity into the report.

## Manager instance configuration

`<slug>.instance.json`, one per dataset. Every value is a flat scalar.

| Key | Value |
|---|---|
| `pluginname` | `io.cresco.panatlas` |
| `jarfile` | `panatlas-0.1-SNAPSHOT.jar`. Dropped at deploy; the uploaded jar's `pluginname`, `md5` and `version` are merged in instead |
| `panatlas_dataset_id` | `panatlas:dataset:<slug>` |
| `panatlas_modalities` | Registry modalities, comma-joined |
| `panatlas_source` | `<reports dir>/<slug>.report.json` |
| `panatlas_manifest` | `<reports dir>/<slug>.manifest.json` |
| `panatlas_graph_version` | The dataset's `manifest_hash` at generation time, or `unversioned` |
| `panatlas_model.<modality>` | The registered model for that modality. Object-valued models are serialised as compact sorted JSON (from 2026-09-20; before then the agent refused six such instances) |
| `persistence_code` | Added only when `PANATLAS_PERSIST=1` (`"10"`) |

## MsgEvent actions

Both actions are `EXEC` messages addressed to `panatlas-global / <agent> / <plugin_id>` with parameter
`action`.

| Action | Request params | Reply params |
|---|---|---|
| `getgraphmanifest` | none | `agent_id`, `node_count` (string integer), `edge_count` (string integer), `content_hash`; or `error` |
| `getgraphinventory` | `since_hash` (optional) | `report` (compressed string; decode with `pycrescolib.utils.decompress_param`) and `content_hash`; or `unchanged = "true"` and `content_hash`; or `error` |

The decoded `report` is the source file's `nodes` and `edges` wrapped as
`{agent_id, graph_version, generator, nodes, edges, content_hash}`. A dataset-manager report's own `urn` key is
**not** carried into the reply; the dataset node's `id` holds the URN.

## Agent profile

`agent_profile.schema.json`. One registered agent, stored in `agents.json` as `{"agents": [ … ]}` under the site's
uploads directory.

| Field | Type | Visibility | Meaning |
|---|---|---|---|
| `agent_id` | string, `^agent-[a-z0-9-]+$` | public | Identity (required) |
| `display_name` | string ≤ 120 | public | Required |
| `purpose` | string ≤ 500 | public | What the agent reports and why |
| `institution` | string ≤ 160 | public | |
| `host` | string | public | Where it runs |
| `url` | string | public | Homepage or repository |
| `owner_name` | string ≤ 120 | public | Required |
| `owner_orcid` | string or null, ORCID pattern | public | Owner's ORCID iD |
| `tier` | `trusted` \| `provisional` | public | Required. See [Federation](federation.md#trust-tiers-and-status) |
| `status` | `active` \| `suspended` \| `revoked` | public | Required |
| `registered_at` | date-time | public | Required |
| `updated_at` | date-time or null | public | |
| `last_report_at` | string or null | public | |
| `last_content_hash` | string or null | public | |
| `stats` | object of integers | public | Per-agent counters |
| `token.prefix` | string | public | First 10 characters of the token: an identifier, not a secret |
| `token.sha256` | 64 hex | **admin-only, never served** | Hash of the token. The plaintext is shown once and never stored |
| `token.rotated_at` | string or null | admin | |
| `private.contact_email`, `private.phone`, `private.notes` | string or null | **admin-only** | Never returned by the public directory |

!!! warning "What the portal writes differs from the schema"
    `panatlas_fed_register` also stores `modalities` (a list, not in the schema, which forbids extra properties).
    It sets `status` to `pending`, a value the schema's enum lacks but the portal and `merge_reports.py` both use.
    It writes timestamps in MySQL format (`YYYY-MM-DD HH:MM:SS`), not ISO 8601 `date-time`. Treat the schema as
    describing the public fields and the portal as authoritative for stored values.

## Merge output

`web/federation/merged_federation.json`, written by `merge_reports.py` and read by `build_layered.py`.

**Node:** `id` (`fed:<canonical_id>` or `fed:<agent_id>:<local_id>`), `canonical_id` (or null), `kind`, `label`,
`grounding` (`mesh` or null), `federation_status` (`visible` | `pending`), `reported_by` (list of agent ids),
`origin` (`federation`).

**Edge:** `from`, `to`, `rel`, `origin` (`federation`), `federation_status`, `reported_by` (list), and `evidence`
(`{cosine, model}`) when the reported edge had those claims.

**Run statistics** (printed, not stored): `reports`, `rejected_not_active`, `matched_existing`, `new_nodes`,
`new_edges`, `dup_edges`, `by_tier`.

## Mesh state: `mesh.json`

Written every 1.5 s by `mesh_daemon.py` into the explorer plugin's `data/` directory and served to the Mesh view.

| Field | Meaning |
|---|---|
| `nodes[]` | `node` (`region_agent`), `region`, `role` (`global` \| `region` \| `agent`), `addrs`, `ageMs` (on the injected global node), `datasets[]` |
| `nodes[].datasets[]` | One per manager answering on that agent: `urn`, `name`, `modality`, `item_count`, `manifest_hash` (first 19 characters) |
| `edges[]` | `from`, `to`, `rtt` (ms), `cost`, `conns`. A `…_parent` target is rewritten to the global node |
| `routes` | Reserved, always empty |
| `source` | `push` (fresh `route_lsa` gossip) or `poll` (`getnetworkstate` fallback) |
| `ok` | Always `true` when written |
| `counts` | `nodes`, `agents`, `globals`, `links`, `datasets` |
| `updated_epoch` | Unix seconds of the write |

The global node is **injected** by the daemon, because a node's own route view omits itself. A `mesh.json` with only
the global node, no agents and 0 datasets means the daemon is writing but cannot see the mesh.

!!! danger "`addrs` is served publicly"
    `mesh.json` is a static file on the public site, and `addrs` carries each node's network address and discovery
    port. Strip or mask `addrs` in the daemon before the file is written if the mesh topology should not be
    public.

## Model registry: `models.json`

The per-modality embedding-model registry, `web/models.json`. Its top-level `_note` states the rule: an embedding is
comparable only within one `(modality, model, version)` space; cross-modality relation goes through shared
`canonical_id`.

**Structure:** `modalities.<modality>.models[]` (plus an optional `note`), and `predictors`.

**Embedding model fields** (the union over registered models):

| Field | Meaning |
|---|---|
| `id` | Registry identifier, used as the plugin's `panatlas_model.<modality>` value and the anchor cache name |
| `family` | Model family and lineage |
| `modality` | `text`, `imaging-ct`, … |
| `role` | `general`, or a specialised role |
| `applies_to` | Which data the model covers |
| `dim` | Embedding dimension |
| `version` | Space version (e.g. `v3w-2026.07`: the v3 mean-pool pipeline plus whitening) |
| `pooling`, `max_length`, `dtype`, `normalize`, `similarity` | How embeddings are produced and compared |
| `whitening` | Background population used to whiten. The calibrated `whitened_cutoff` travels in the anchor artifact |
| `cutoff` | Raw-space attach cutoff (0.25 for text). `null` means no attach |
| `cutoff_note` | How `cutoff` relates to `whitened_cutoff` |
| `location`, `model_location` | Where the weights live on the cluster |
| `anchors` | `{artifact, source, aligned_by}`; for imaging `{status: "held", decision, node_linkage}`: image embeddings are **not** linked directly to concept nodes |
| `centroids` | `{artifact, n_cells, dim}`: the corpus cell centroids |
| `embeddings` | For imaging: cache, per-slice shape, `count`, `materialized`, `id_scheme`, `coverage`, `catalog`, `role` |
| `status` | `active`, or a descriptive status for retrieval-only spaces |
| `hf` | Hugging Face repository of the stock weights |
| `provenance` | How the weights were verified (e.g. SHA-256 equal to the hub's LFS object) and whether they were fine-tuned in-house |
| `training_disclosed` | Whether the training data is disclosed |
| `license` | Weights licence |
| `note` | Free-text caveats |

At repo HEAD: **text** has one active model (`text-bioclinical-modernbert-large`, 1024-d, `v3w-2026.07`, cutoff
0.25). **imaging** has `imaging-rad-dino-ct` (768-d, retrieval only, anchors held). **genomics** and **structured**
have no registered embedder.

**Predictors** (`predictors.models[]`, 58 at HEAD: 37 time-series and 21 tabular; 45 foundation models and 13
baselines; 46 evaluated and 12 not run). These have no embedding space and are never attached. Fields: `id`, `name`,
`family`, `kind`, `role`, `source`, `embedding` (`none`), `open_weights`, `runs`, `status`, `results` (dataset URN →
pointer into `web/predictor_evals.json`), `wrapper`, and `not_run_reason` and `note` where they apply. Evaluation
metadata is in [Evaluation records](../metadata/evaluation-records.md).

## Local agent configuration

`~/.panatlas-agent/config.json`: `agent_id`, `site`, `model` (a registry `id`), `created`. The other store files are
listed in [Participating agents](agents.md#the-local-agent-kit).
