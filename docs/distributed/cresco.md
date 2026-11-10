# Cresco for panAtlas

This page covers only the parts of Cresco that panAtlas depends on, and how panAtlas uses each one. The canonical
reference is the [Cresco documentation](https://crescoedge.github.io/docs/); where a statement here and that site
differ on how Cresco works, the Cresco site is right. Where panAtlas's own deployment is configured differently from
Cresco's defaults, this page says so. Cresco's own summary of panAtlas is on its
[Projects built on Cresco](https://crescoedge.github.io/docs/reference/projects/#panatlas) page.

## The hierarchy

A Cresco node is a JVM running an OSGi (Apache Felix) host that loads the controller and a set of plugins. Each
node runs in one controller mode: `AGENT` (a leaf), `REGION` (a regional controller running an embedded ActiveMQ
broker, not yet federated to a global), `REGION_GLOBAL` (a regional controller federated up to a global), `GLOBAL`
(federates regions, and is also its own region and agent), or `STANDALONE`. Agents are JMS clients of their region's broker.
Regions bridge to the global, and globals can bridge to each other
([Architecture overview](https://crescoedge.github.io/docs/architecture/overview/)).

**The panAtlas fabric** is one region, `panatlas-global`, with a global controller and two agents. Both agents
start with `is_agent=true` and a fixed `regional_controller_host` pointing at the controller node:

| Node | Mode | Role in panAtlas |
|---|---|---|
| global controller | `GLOBAL` / region root | The rollup point. Inventories roll up here, and the hub's calls to managers on other agents are routed through it |
| HPC cluster agent | `AGENT` | Hosts the dataset managers for every dataset stored on the cluster: 194 of the 200 entries in `web/datasets.json` at repo HEAD |
| web host agent | `AGENT`, wsapi enabled | Hosts the hub's client side (`mesh_daemon.py`, `deploy_managers.py`); can host managers for datasets stored on the web host |

Every node addresses every other by `region_agent[_plugin]`, so a dataset manager is addressed as
`panatlas-global / <agent> / <plugin_id>`.

## The two planes

| Plane | Carrier | panAtlas uses it for |
|---|---|---|
| **Control plane** | MsgEvent over ActiveMQ queues | Every manager call: `getgraphmanifest`, `getgraphinventory`; deploying and removing manager instances; `getnetworkstate` for the Mesh view |
| **Data plane** | ActiveMQ topics (pub/sub) | The live Mesh view subscribes to the `route_lsa` link-state advertisements that every controller publishes on the `GLOBAL` topic ([Data plane](https://crescoedge.github.io/docs/architecture/dataplane/)). The designed `panatlas.graph` change topic is **not built** (see [Federation](federation.md#designed-not-built)) |

Reports are small. In 2026-07 the full set of structure-only reports was about 40 KB. They ride the control plane
as a **compressed MsgEvent parameter**. The data plane and `filerepo` are kept for large artifacts. That split is
deliberate and was learned the hard way: see [Operations](operations.md#a-second-filerepo-bundle).

## Plugins and self-describing actions

A Cresco plugin is an OSGi bundle. `cresco-panatlas` (`io.cresco.panatlas`) is built from the Cresco skeleton
plugin. Its executor carries `@CrescoCapabilities` and its actions `@CrescoAction` annotations, so they appear in the
mesh-wide capability inventory
(`getcapabilityinventory`) with their parameters and return types. That makes every dataset manager callable as a
tool by any Cresco client, including an AI agent using Cresco's tool interface
([Plugin actions](https://crescoedge.github.io/docs/api/plugin-actions/)).

A plugin can run as **many instances** on one agent, each with its own configuration. panAtlas relies on that: one
bundle, one instance per dataset, each configured with a different `panatlas_dataset_id` and `panatlas_source`.

## Identity, trust and tenancy

Cresco 1.3 is **secure by default**: a node started with no security setting runs with mutual TLS, broker
authorization, tenant namespacing, end-to-end message authentication and signed plugin installs
([Security in Cresco 1.3](https://crescoedge.github.io/docs/security/), [Secure defaults](https://crescoedge.github.io/docs/security/secure-defaults/)).
The table maps each panAtlas need to the Cresco mechanism that meets it. What a panAtlas node needs to run under
those defaults is in [Version and security build](#version-and-security-build).

| panAtlas need | Cresco mechanism |
|---|---|
| A node's identity | Messages address a node as `region_agent`. The identity itself is the node's X.509 certificate subject, `CN=<agent>, OU=<region>, O=<tenant>`, verified at every TLS handshake. The plugin stamps reports `agent-<region>_<agent>` |
| Admission to the mesh | An authenticated discovery exchange. In the `standard` security profile it is keyed by the per-tier join secret (`discovery_secret_global`, `_region`, `_agent`); in the `production` profile it is signed under the operator's PKI and no join secret is used ([Discovery](https://crescoedge.github.io/docs/architecture/discovery/), [Security profiles](https://crescoedge.github.io/docs/security/profiles/), [Operator PKI](https://crescoedge.github.io/docs/security/pki/)). panAtlas's agents join with join secrets |
| Authenticated transport | Mutual TLS on every broker connection, with the connection bound to the identity its certificate names; optional regional-CA enrollment (`security_regional_ca`, standard profile only) ([Security & Identity](https://crescoedge.github.io/docs/architecture/security/)) |
| Authenticated messages | Every MsgEvent a node originates is authenticated end to end and bound to its recipient (`cresco_sig_to`), so a manager's reply or a call to a manager is accepted only by the node it names ([Message authentication](https://crescoedge.github.io/docs/security/message-auth/)) |
| Trusted plugin code | A plugin jar installed over the network must be signed by a signer that chains to `plugin_signing_truststore` ([Signed plugins](https://crescoedge.github.io/docs/security/signed-plugins/)). See [Version and security build](#version-and-security-build) |
| Keeping tenants apart | Tenant namespacing in the broker (`T.<tenant>.*`), with the tenant bound into the certificate as `O=<tenant>` ([Multi-tenancy](https://crescoedge.github.io/docs/architecture/tenancy/)) |
| Who may contribute to the graph | **panAtlas's own overlay**: the agent profile, trust tier and admin status. See [Federation](federation.md#trust-tiers-and-status) |

Cresco answers "is this really node X, and may it talk to me?" panAtlas answers "may node X's claims enter the
atlas, and are they shown at once or held for a curator?"

## Clients: the wsapi and pycrescolib

Cresco's external clients connect to the [wsapi](https://crescoedge.github.io/docs/plugins/wsapi/) plugin, a
secure WebSocket API on port 8282 (`wss://`). In Cresco's reference topology the global serves clients; **panAtlas's
configuration** also runs wsapi on the web host agent (`enable_wsapi=true`), so the hub's Python code connects
locally (`localhost:8282`). It uses [pycrescolib](https://crescoedge.github.io/docs/clients/python/) with the wsapi
**service key**, the legacy credential that Cresco's standard profile still accepts and its production profile refuses
([API authentication](https://crescoedge.github.io/docs/security/api-auth/)):

| pycrescolib call | Used by | For |
|---|---|---|
| `agents.list_plugin_agent(region, agent)` | `mesh_daemon.py`, `deploy_managers.py` | List plugin instances; filter `pluginname == io.cresco.panatlas` |
| `messaging.global_plugin_msgevent(True, "EXEC", {"action": "getgraphinventory"}, region, agent, plugin_id)` | both | Pull one manager's report (RPC, waits for the reply) |
| `messaging.global_controller_msgevent(True, "EXEC", {"action": "getnetworkstate"}, ...)` | `mesh_daemon.py` | Nodes and links for the Mesh view (polling fallback) |
| `get_dataplane("cresco_msg_type='route_lsa'", cb)` | `mesh_daemon.py` | Subscribe to pushed link-state advertisements (live path) |
| `agents.upload_plugin_agent`, `add_plugin_agent`, `remove_plugin_agent` | `deploy_managers.py` | Ship the bundle, create or remove manager instances |
| `utils.decompress_param` | both | Decode the compressed `report` parameter |

## State: the embedded Derby database

Each controller keeps nodes, plugins, edges and health in an embedded **Derby** database
([controller](https://crescoedge.github.io/docs/plugins/controller/)), under `cresco-data/` in the node's working
directory; Cresco's [Deployment](https://crescoedge.github.io/docs/operations/deployment/#one-node-one-directory) page
says two nodes must never share that directory. That database sits behind three of the six recorded federation
outages: stale lock files after an unclean JVM exit (the cluster agent's working directory is on a shared parallel
filesystem), duplicated persisted plugin records, and a second Derby engine started by a second `filerepo` bundle.
[Operations](operations.md) covers each one and the guard now in place.

## Version and security build

Both panAtlas agents run a Cresco **1.3-SNAPSHOT** agent jar (`agent-1.3-SNAPSHOT.jar`) on a Java 21 runtime. The
plugin builds against `io.cresco:library:1.3-SNAPSHOT` with JDK 21 and Maven (`mvn package bundle:bundle` →
`target/panatlas-0.1-SNAPSHOT.jar`).

!!! note "Running panAtlas under Cresco 1.3 secure defaults"
    Under the secure defaults a node refuses an unsigned plugin upload, so the `cresco-panatlas` bundle must be
    signed and each agent given a `plugin_signing_truststore`. Keep every secret in an owner-only file or a
    `CRESCO_<NAME>` environment variable rather than a `-D` property, and give the hub's pycrescolib client the wsapi
    certificate fingerprint, because current pycrescolib releases verify the wsapi certificate by default. The full
    procedure is Cresco's [Upgrading to 1.3](https://crescoedge.github.io/docs/security/upgrade/) and
    [API authentication](https://crescoedge.github.io/docs/security/api-auth/).
