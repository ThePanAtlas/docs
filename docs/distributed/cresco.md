# Cresco for panAtlas

This page covers only the parts of Cresco that panAtlas depends on, and how panAtlas uses each one. The canonical
reference is the [Cresco documentation](https://crescoedge.github.io/docs/).

## The hierarchy

A Cresco node is a JVM running an OSGi (Apache Felix) host that loads the controller and a set of plugins. Each
node runs in one controller mode: `AGENT` (a leaf), `REGION` (runs an embedded ActiveMQ broker and federates up),
`GLOBAL` (federates regions), `REGION_GLOBAL`, or `STANDALONE`. Agents are JMS clients of their region's broker.
Regions bridge to the global, and globals can bridge to each other
([Architecture overview](https://crescoedge.github.io/docs/architecture/overview/)).

**The panAtlas fabric** is one region, `panatlas-global`, with a global controller and two agents:

| Node | Mode | Role in panAtlas |
|---|---|---|
| global controller | `GLOBAL` / region root | The rollup point. The hub's clients connect to its wsapi |
| HPC cluster agent | `AGENT` | Hosts the dataset managers for every dataset stored on the cluster: 194 of the 200 entries in `web/datasets.json` at repo HEAD |
| web host agent | `AGENT`, wsapi enabled | Hosts the hub's client side (`mesh_daemon.py`, `deploy_managers.py`); can host managers for datasets stored on the web host |

Every node addresses every other by `region_agent[_plugin]`, so a dataset manager is addressed as
`panatlas-global / <agent> / <plugin_id>`.

## The two planes

| Plane | Carrier | panAtlas uses it for |
|---|---|---|
| **Control plane** | MsgEvent over ActiveMQ queues | Every manager call: `getgraphmanifest`, `getgraphinventory`; deploying and removing manager instances; `getnetworkstate` for the Mesh view |
| **Data plane** | ActiveMQ topics (pub/sub) | The live Mesh view subscribes to `route_lsa` link-state gossip. The designed `panatlas.graph` change topic is **not built** (see [Federation](federation.md#designed-not-built)) |

Reports are small. In 2026-07 the full set of structure-only reports was about 40 KB. They ride the control plane
as a **compressed MsgEvent parameter**. The data plane and `filerepo` are kept for large artifacts. That split is
deliberate and was learned the hard way: see [Operations](operations.md#a-second-filerepo-bundle).

## Plugins and self-describing actions

A Cresco plugin is an OSGi bundle. `cresco-panatlas` (`io.cresco.panatlas`) is built from the Cresco skeleton
plugin. Its actions carry `@CrescoAction` annotations, so they appear in the mesh-wide capability inventory
(`getcapabilityinventory`) with their parameters and return types. That makes every dataset manager callable as a
tool by any Cresco client, including an AI agent using Cresco's tool interface
([Plugin actions](https://crescoedge.github.io/docs/api/plugin-actions/)).

A plugin can run as **many instances** on one agent, each with its own configuration. panAtlas relies on that: one
bundle, one instance per dataset, each configured with a different `panatlas_dataset_id` and `panatlas_source`.

## Identity, trust and tenancy

| panAtlas need | Cresco mechanism |
|---|---|
| A node's identity | `region_agent`, stable across restarts. The plugin stamps reports `agent-<region>_<agent>` |
| Admission to the mesh | Discovery with a per-tier join secret (`discovery_secret_global`, `_region`, `_agent`), or the operator's PKI ([Discovery](https://crescoedge.github.io/docs/architecture/discovery/)) |
| Authenticated transport | X.509 identities, mutual TLS, regional-CA trust ([Security](https://crescoedge.github.io/docs/architecture/security/)) |
| Keeping institutions apart | Tenant namespacing in the broker, with the tenant bound into the certificate ([Multi-tenancy](https://crescoedge.github.io/docs/architecture/tenancy/)) |
| Who may contribute to the graph | **panAtlas's own overlay**: the agent profile, trust tier and admin status. See [Federation](federation.md#trust-tiers-and-status) |

Cresco answers "is this really node X, and may it talk to me?" panAtlas answers "may node X's claims enter the
atlas, and are they shown at once or held for a curator?"

## Clients: the wsapi and pycrescolib

The global controller (and any agent started with `enable_wsapi=true`) serves a WebSocket API. The hub's Python
code uses [pycrescolib](https://crescoedge.github.io/docs/clients/python/) against the web host agent's wsapi with a
service key:

| pycrescolib call | Used by | For |
|---|---|---|
| `agents.list_plugin_agent(region, agent)` | `mesh_daemon.py`, `deploy_managers.py` | List plugin instances; filter `pluginname == io.cresco.panatlas` |
| `messaging.global_plugin_msgevent(True, "EXEC", {"action": "getgraphinventory"}, region, agent, plugin_id)` | both | Pull one manager's report (RPC, waits for the reply) |
| `messaging.global_controller_msgevent(True, "EXEC", {"action": "getnetworkstate"}, ...)` | `mesh_daemon.py` | Nodes and links for the Mesh view (polling fallback) |
| `get_dataplane("cresco_msg_type='route_lsa'", cb)` | `mesh_daemon.py` | Subscribe to pushed link-state gossip (live path) |
| `agents.upload_plugin_agent`, `add_plugin_agent`, `remove_plugin_agent` | `deploy_managers.py` | Ship the bundle, create or remove manager instances |
| `utils.decompress_param` | both | Decode the compressed `report` parameter |

## State: the embedded Derby database

Each controller keeps nodes, plugins, edges and health in an embedded **Derby** database. That database sits behind
three of the six recorded federation outages: stale lock files after an unclean JVM exit, duplicated persisted plugin
records, and a second Derby engine started by a second `filerepo` bundle. [Operations](operations.md) covers each
one and the guard now in place.

## Version

Both panAtlas agents run Cresco **1.3-SNAPSHOT** on a Java 21 runtime. The plugin builds against
`io.cresco:library:1.3-SNAPSHOT` with JDK 21 and Maven (`mvn package bundle:bundle` →
`target/panatlas-0.1-SNAPSHOT.jar`).
