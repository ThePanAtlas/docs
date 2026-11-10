# The site: panatlas.net

panatlas.net is a WordPress site on the web host. Almost all of panAtlas's behaviour lives in one custom plugin,
`panatlas-explorer` (version 0.2.2, `web/wp-plugin/panatlas-explorer/`), with a small custom theme
(`web/wp-theme/panatlas/`). The plugin reads static JSON files and streams large assets; it does not keep the atlas
in the database.

| Part | Files |
|---|---|
| Plugin core: roles, audit, access gate, explorer and universe shortcodes, gated REST routes, Navigator, model lens | `panatlas-explorer.php` |
| Public read-only API | `includes/public-api.php`, `includes/public-evals.php` |
| World map | `includes/wikimap.php`, `assets/wikimap.js` |
| Agent-network panel | `includes/mesh.php` |
| Federation admin portal | `includes/federation-admin.php` |
| Front end | `assets/app.js` (Cytoscape.js 3.30.2 from a CDN), `assets/style.css`, `assets/universe.js`, `assets/universe-bg.js` with `assets/cosmos.bundle.mjs` |
| Served data | `data/graph.json`, `datasets.json`, `benchmarks_llm.json`, `mm_evals.json`, `evals_index.json`, `models.json`, `kg_graphs.json`; `data/mesh.json` is written live on the server |

## Pages

| Page | Shortcode | What it shows |
|---|---|---|
| Front page | `[panatlas_explorer]` (the theme's `front-page.php` emits only this) | The explorer, or the teaser for visitors without access |
| `/universe/` | `[panatlas_universe]` | Every document placed by concept, with the graph overlaid |
| `/world-map/` | `[panatlas_wikimap]` | The known-world map from the Wikipedia layer |
| `/agent-network` | `[panatlas_mesh]` | The live [Cresco](https://crescoedge.github.io/docs/) mesh (also rendered inside the explorer's Mesh view) |
| `/api/` | `[panatlas_api_docs]` | Generated documentation of the public API |

## The explorer

The explorer is a single-page app (`assets/app.js`) inside the `[panatlas_explorer]` shortcode. Its header has
these views:

| View | What it is |
|---|---|
| **Home** | What panAtlas is and where to start; headline counts and entry cards |
| **Map** | The ontology-grounded concept hierarchy, as a tree or an interactive graph. Clicking a node re-centres on its neighbourhood (focus plus context; never the whole graph) |
| **Datasets** | The audited data catalog: every dataset with modality, scale, embedding model, host and audit manifest |
| **Models** | Each model with what it was trained on and evaluated on, per-concept accuracy, a modality filter, and the model lens |
| **Coverage & Gaps** | Per-concept training exposure set against model scores, artifact-type gaps, decontamination status |
| **Benchmarks** | Every benchmark as an audited list or a similarity map (the `audit.map` projection from [the build](build-pipeline.md#stage-2-build_allsh)) |
| **Universe** | Opens `/universe/` |
| **Mesh** | The live Cresco agent mesh |

Alongside the views are a search box, a context bar, a detail panel for the selected node, and the **Navigator**
panel. A deep link of the form `/#node=<id>` opens a node's detail panel; the public API returns links in that form.

### Node detail and the literature feed

A node's detail panel shows its grounding, provenance and links. For concepts, specialties and diseases that carry
a MeSH descriptor, the panel loads a **Recent literature** block from `GET /panatlas/v1/literature?node=<id>`.

The feed is built nightly on the web host by `web/pipeline/literature/fetch_literature.py` (standard library only,
run from cron with a lock). For every MeSH-grounded node it searches PubMed by MeSH term, sorted by date, diffs the
PMIDs against what it already stores, and fetches only new ones. It stores **verified NCBI metadata only**: PMID,
title, journal, date, authors and DOI; no model output. A partial failure skips that concept and never kills the
run. Measured on the full run of 2026-08-15: 3,368 nodes, 31,634 articles, 0 failures. An "in training corpus" badge
is shown only from the exact PMC identity map (`web/pipeline/literature/attach_pmc_identity.py`), never from an
approximation.

### Navigator: ask where to go

The Navigator turns a question into a focused view of the graph. `POST /panatlas/v1/navigate` with `{query}`
(at most 2,000 characters) does this in `panatlas_navigate()`:

1. **Retrieve.** Score every node by term overlap: label hits weigh more than hits in descriptions, audit fields,
   domains or capabilities. Keep the top 24 seeds.
2. **Expand.** Add the seeds' neighbours, up to 220 nodes, and collect the edges among them (at most 600).
3. **Ground.** Add a modality census from `mm_evals.json`, so a question about multi-modal or vision models is never
   answered with a text model.
4. **Ask.** Send the subgraph and the question to the hosted LLM endpoint with temperature 0 and a JSON-schema
   response format `{answer, focus[], intent}` (constrained decoding).
5. **Validate.** Drop any focus id not in the subgraph, default the intent, and supply a fallback answer if the model
   returned none. The UI then re-centres the map on the focus nodes.

Every call is written to the audit log. Without a configured key the route answers "Navigator offline".

!!! note "A debug path exists"
    A query that begins with `DEBUG` returns diagnostics (HTTP status from the LLM endpoint, seed, node and edge
    counts, finish reason, and the start of the raw body) instead of an answer. It is reachable by any user who
    passes the access gate.

### Model lens

In the Models view, `POST /panatlas/v1/model-lens` with `{query}` (at most 500 characters) asks the same endpoint which
benchmarks measure what the user cares about: an evaluation type, a medical topic, or a combination ("cardiology
QA", "reading reports, not multiple-choice"). The lens prompt is written for today's holdings, where medicine runs
deepest. The catalog it chooses from is the union of benchmarks in the model
batteries plus the imaging and multi-modal benchmarks. The reply is constrained to `{explanation, benchmarks[]}`;
names not in the catalog are dropped, and an empty selection falls back to the medical knowledge core. The ranking
then re-scores models over just that subset. The route releases the PHP session lock first, so a second lens call
from the same browser does not queue behind the first.

!!! warning "Navigator model: documentation and code differ"
    `web/README.md` and `docs/panatlas-system-and-interface.md` name a Gemma model as the Navigator. The code sets
    `PANATLAS_NAV_MODEL` to the WordPress option `panatlas_nav_model`, defaulting to `zai-org/GLM-5.3-Flash`, with
    a comment that the Gemma model was retired on the endpoint. The code is authoritative.

## Universe

The universe page draws every document as a point placed by concept, with the knowledge graph overlaid as a
backbone. Its assets are built on the cluster (`web/dgx/build_universe*.py`, `web/pipeline/universe/`), stored
**outside the web root**, and streamed through `GET /panatlas/v1/universe-asset?f=<part>&tier=<tier>`:

| `f` | Content |
|---|---|
| `xy` | Point positions, `uint16` pairs (per tier) |
| `color` | Point colours, `uint8` (per tier) |
| `meta` | `universe_meta.json` |
| `nodes`, `edges` | The backbone overlay |

Tiers, measured on the 2026-09-24 rebuild that added arXiv: `xs` 250,107 points, `s` 1,500,021, `m` 5,998,856, `full`
93,056,465. The page then fetches the graph to link points back to the explorer.

!!! warning "Default tier"
    A code comment says `s` (1.5M) is the light default. The code falls back to `xs` when no tier is given.

The **teaser** shown to visitors without access uses a separate, public, low-resolution version of the same cloud
(`assets/teaser_*.bin`, drawn by `assets/universe-bg.js`).

## World map

`/world-map/` renders the known-world map from the Wikipedia world-view layer: the pinned English Wikipedia run
20260901 (7,234,748 articles) laid out by topic, with each article coloured by how strongly the atlas's documents
cover it. The layer gives every document one primary Wikipedia link with an evidence class (strong, medium, lexical
agreement, curated bridge, weak). Assets stream from outside the web root through
`GET /panatlas/v1/wikimap-asset?f=<part>`, where `f` is one of `lod_top`, `lod_links`, `lod_covered`, `mesh`,
`categories`, `art_xy`, `art_cov`, `manifest`. The page is installed by `web/wikimap/install_wikimap.sh`; the chain
that builds the layer is in `web/wikipedia_layer/`.

## Sign-in and the access gate

### Identity

Sign-in is ORCID through OpenID Connect, using the OpenID Connect Generic plugin with the `openid` scope (`README.md`
§5). The ORCID iD (the OIDC `sub`) becomes the WordPress username. ORCID does not release email under that scope, so
each account gets a synthetic, non-delivering address. Any ORCID holder can create an account; new accounts get the
WordPress `subscriber` role, which the plugin grants `pa_read` and `pa_suggest`.

### Roles and capabilities

| Role | Capabilities |
|---|---|
| `pa_member_viewer` | `pa_read` |
| `pa_domain_editor` | `pa_read`, `pa_suggest`, `pa_edit` |
| `pa_reviewer` | `pa_read`, `pa_suggest`, `pa_verify` |
| `pa_super_curator` | all five, including `pa_admin` |
| WordPress `administrator` | all five (the fallback account) |

### The gate

Having an account is not enough to see the atlas. Every atlas view and every gated route goes through
`panatlas_may_access()`, which allows:

1. the site administrator (`manage_options`), or
2. a signed-in user whose username contains an ORCID iD on an **allowlist** held as a constant in the plugin.

Everyone else gets the teaser: anonymous visitors see "Sign in with ORCID", and signed-in users who are not on the
list see "Your account is not authorized to view the atlas" with a switch-account link. The same allowlist is
configured in the Astral agent, and `web/astral/tests/test_authorized_identities.py` asserts that the required iDs
are present in both places, so a change to one cannot silently drop a curator from the other.

**Why the sign-in link points straight at ORCID.** On 2026-08-06 the shared web host restricted WordPress's login
and admin paths to internal networks after an incident. Both sign-in links (the theme header and the teaser) were
changed on 2026-08-24 to render the plugin-generated ORCID authorisation URL, and the restriction gained a narrow
exemption for the OIDC authorise action only. The OIDC callback goes through a public endpoint. Password login and
the admin area stay restricted. The server-side rule is kept in the repository as `web/infra/lockdown-wp-admin.conf`.

**Hardening.** For anonymous visitors the plugin removes the WordPress users REST endpoints and redirects author
archives and `?author=` probes to the home page, so usernames cannot be enumerated.

!!! warning "Older text says viewing is public"
    `docs/panatlas-system-and-interface.md` (written 2026-08-01) lists `/graph`, `/datasets`, `/benchmarks`,
    `/navigate` and `/mesh` as public, a comment in the plugin still says "Public read endpoints (viewing is open to
    everyone)", and the Navigator's hint text says "Anyone can explore". In the code every one of these routes
    checks `panatlas_may_access`; anonymous requests get 401 (confirmed live on 2026-09-12 for `graph` and
    `datasets`). The open, read-only surface is the [public API](public-api.md).

### The audit log

The plugin creates a table `panatlas_audit` (with the WordPress prefix) holding the time, user id, ORCID iD, the
roles held at that moment, the action, a detail string and the client address. Actions written by the code are
`view_explorer`, `view_universe`, `view_wikimap`, `navigate`, `navigate_error`, `model_lens`, `propose_change` and
`link_astral_orcid`; the federation portal also writes its actions here. Site administrators see the latest 200
rows under the **PanAtlas Audit** admin menu.

## Gated private assets

Large or sensitive files live in a private directory beside, not inside, the web document root, and reach the
browser only through gated routes:

| Asset | Route | Notes |
|---|---|---|
| Universe tiers and backbone | `universe-asset` | `Cache-Control: private, max-age=3600`; streamed in 1 MB chunks |
| World-map layout | `wikimap-asset` | Same pattern |
| Literature feed (`lit_<node>.json`) | `literature` | Rebuilt nightly |

Each request carries the WordPress REST nonce and the session cookie. An unknown part returns 404 `unknown asset`;
a part not built yet returns 404 `not built yet`.

## REST routes (`panatlas/v1`, gated)

All paths are under `https://panatlas.net/wp-json/panatlas/v1`. Responses are raw JSON, not wrapped.

| Method | Path | Permission | Returns |
|---|---|---|---|
| GET | `/graph` | access gate | `graph.json`: `{stats, roots, nodes[], edges[]}` |
| GET | `/datasets` | access gate | `{datasets[], meta, models}` from `datasets.json` and `models.json` |
| GET | `/benchmarks` | access gate | `benchmarks_llm.json` |
| GET | `/mm-evals` | access gate | `mm_evals.json` |
| POST | `/navigate` | access gate | `{answer, focus[], intent}` |
| POST | `/model-lens` | access gate | `{explanation, benchmarks[], task_types[], catalog[]}` |
| GET | `/literature?node=<id>` | access gate | The stored feed for that node, or `{articles: []}` |
| GET | `/universe-asset?f=&tier=` | access gate | Binary or JSON stream |
| GET | `/wikimap-asset?f=` | access gate | Binary or JSON stream |
| GET | `/mesh` | access gate (since 2026-10-25, because the snapshot carries internal node addresses) | The mesh snapshot from `data/mesh.json` |
| GET | `/whoami` | open | `{orcid, name, roles[], rights[]}`; a guest gets `name: "guest"` and empty lists |
| POST | `/propose` | signed in with `pa_suggest` | Records `{target, change}` (change ≤ 4,000 characters) in the audit log; returns `{ok, status, by, rights}`. Never publishes |
| GET | `/federate/agents` | open (redacted); full profiles for `pa_admin` | The federation agent directory, never token hashes |
| POST | `/federate/agents/register` | `pa_admin` | Registers an agent and mints a one-time token |
| POST | `/federate/agents/update` | `pa_admin` | Changes tier or status, rotates a token |

The federation routes and the admin portal are described in [Federation](../distributed/federation.md) and
[Contract](../distributed/contract.md).

!!! warning "No agent submission route"
    `web/federation/pa_agent.py` posts reports to `POST /panatlas/v1/federate`. The plugin registers no such route;
    contributions arrive over the Cresco control plane instead. See [Distributed](../distributed/index.md).

The Astral identity link has its own entry point on the front controller, `/?panatlas_astral_orcid_link=1`, so it
works from outside the restricted login paths ([Astral](astral.md#identity-orcid-allowlist-and-the-link-flow)).

## Deployment

The front-end assets, the served data and the public API includes are deployed by `web/deploy.sh`; other plugin
files, the world map and the universe assets are deployed separately. See [Build pipeline](build-pipeline.md#deploy-deploysh).
A repository audit on 2026-09-13 found the live plugin identical to the repository for all 28 shared files, with
`data/mesh.json` the only file that exists only on the server by design.
