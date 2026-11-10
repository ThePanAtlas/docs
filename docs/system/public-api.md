# Public API

The public API is a read-only HTTP interface to everything panAtlas indexes: statistics, graph search and lookup,
the dataset registry, every measured evaluation score for every model type, the literature feed, and the list of
knowledge graphs in the SPARQL store. It needs no key. It is separate from the gated `panatlas/v1` routes that the
explorer uses ([Web site](web-site.md#rest-routes-panatlasv1-gated)).

| Property | Value |
|---|---|
| Base URL | `https://panatlas.net/wp-json/panatlas/public/v1` |
| Version | 1.1.1 (2026-10-31) |
| Methods | `GET` only |
| Auth | None |
| Rate limit | 240 requests per client address per minute; requests from the web host itself are exempt. Over the limit: HTTP 429, code `rate_limited` |
| CORS | `Access-Control-Allow-Origin: *`, methods `GET, OPTIONS` |
| Caching | `Cache-Control: public` with `max-age` 300 s by default, 3,600 s for `/stats`, `/literature` and `/kg/graphs`, 86,400 s for `/teaser` |
| Description | `/openapi.json` (OpenAPI 3.1.0) and `/tools.json` (the same routes as LLM tool definitions); human-readable docs at `panatlas.net/api/` |
| Code | `web/wp-plugin/panatlas-explorer/includes/public-api.php` (statistics, search, node, dataset, literature, spec), `includes/public-evals.php` (evaluations) |
| Contract test | `web/tests/test_public_api.py` (`--stage DIR` or `--live`) |

## Rules the API keeps

From `docs/public-api.md` and the code:

- **Additive only.** Existing routes and tools keep their names and shapes; new behaviour is added.
- **Nothing internal leaves.** Fields are served from whitelists, and every string passes a scrubber that removes
  server paths, cluster host names and job numbers. Data itself is never served, only records about it. No raw
  SPARQL is accepted.
- **Fit an LLM's tool budget.** Results stay under 24,000 characters at default limits, because the first external
  client truncates there.
- **Say what is covered.** Every evaluation response carries a `coverage` block, so a search that misses cannot be
  read as missing data.
- **One metric per benchmark.** Values are compared only within one benchmark; cross-benchmark rankings are mean
  positions and say so.

## Response envelope

Every data route returns:

```json
{
  "as_of": "<ISO 8601 time or null>",
  "source": "snapshot",
  "data": { }
}
```

- `as_of` is the newest modification time of the snapshot files behind the answer (ISO 8601), or the store's build
  time for `/kg/graphs`. It is `null` when not applicable.
- `source` is `snapshot` for answers from the served files, `nightly PubMed feed` for `/literature`, and
  `SPARQL store manifest` for `/kg/graphs`.
- Errors use the standard WordPress REST error body `{"code", "message", "data": {"status"}}` with codes
  `not_found` (404), `bad_request` (400) and `rate_limited` (429). Not-found messages for models suggest the closest
  names.

Links into the explorer are returned as `https://panatlas.net/#node=<id>`.

## Routes

| Route | Tool name | Purpose |
|---|---|---|
| `GET /best` | `best_models` | Which model is best for a task, data type or domain. Start here |
| `GET /overview` | `atlas_overview` | What has been evaluated, by model type, with the leader of every scored benchmark |
| `GET /tasks` | `task_scores` | Rank models on one task inside a suite |
| `GET /scores` | `query_scores` | Filter every measured score |
| `GET /stats` | `stats` | Headline counts of everything indexed |
| `GET /search` | `search_atlas` | Search graph nodes by words |
| `GET /node/{id}` | `get_node` | One node with public fields and links grouped by relation |
| `GET /neighborhood` | `get_neighborhood` | Nodes and links around up to 12 ids |
| `GET /datasets` | `search_datasets` | Search the dataset registry |
| `GET /datasets/{slug}` | `get_dataset` | One dataset record |
| `GET /benchmarks` | `search_benchmarks` | Search benchmarks and suites of every model type |
| `GET /benchmarks/{id}` | `get_benchmark` | One benchmark: what it measures, full ranking, baselines, held-out models |
| `GET /models` | `list_models` | Every evaluated model of every type |
| `GET /models/{name}` | `get_model_scores` | Every score for one model |
| `GET /compare` | `compare_models` | One benchmark's ranking, or a head-to-head between named models |
| `GET /literature/{node}` | `get_literature` | Recent PubMed articles for a MeSH-grounded node |
| `GET /kg/graphs` | `list_knowledge_graphs` | Named graphs in the SPARQL store with triple counts |
| `GET /teaser/{part}` | (none) | Public binary geometry of the document universe |
| `GET /openapi.json` | (none) | The OpenAPI description |
| `GET /tools.json` | (none) | `{instructions, tools[]}` for LLM clients |

The model **types** are `language`, `vision`, `multimodal`, `tabular` and `forecasting`. Type and domain
parameters accept everyday words ("time series", "structured"), which the server maps to a type through a
vocabulary in `evals_index.json`.

### Evaluations

#### `GET /best`

| Parameter | Type | Notes |
|---|---|---|
| `task` (required) | string | The task in plain words: "tabular data", "forecasting hospital admissions", "pathology encoders". `q` and `question` are accepted as aliases |
| `type` | string | Optional model type |
| `domain` | string | Optional domain: medical, pathology, radiology, … |
| `limit` | integer | Models per benchmark, default 5, at most 25 |

Returns `question`, `interpreted_as {type, domain, words}`, `coverage`, `matched`, `count`, and `results[]` (up to
six benchmarks of one type, or two per type when several match, at most ten). Each result is a suite record: `id`,
`name`, `type`, `domain`, `metric`, `how_to_read`, `headline`, `ranking[]` (`rank`, `name`, `value`, optional
`mean_rank`, `beats_best_baseline`, flags `ours`, `published`, `verified`), `best_baseline`, `held_out[]` and `url`.
Also, when they apply: `answer_from: "matching_tasks"` with `matching_tasks[]` when a single task holds every
specific word of the question; `overall` (per type, with three or more matched benchmarks) with `overall_method`
explaining `avg_position`; `listed_not_run`; `listed_not_yet_scored`; `more_benchmarks`; `note`; and `advice`, a
sentence telling an LLM how to state the answer. When nothing matches, `matched: false` with advice to retry with a
type or call `atlas_overview`.

#### `GET /overview`

No parameters. Returns `types`, keyed by model type, each with `label`, `evaluated_models`, `evaluated_baselines`,
`scored_benchmarks`, `listed_not_run`, `benchmarks[]` (`id`, `name`, `domain`, `metric`, `n_models`, `leader`,
`leader_value`, `leader_mean_rank`) and `not_run[]` (`name`, `reason`), plus `how_to_use`. Parts of a benchmark
(such as one MMLU subject) are not listed as benchmarks of their own.

#### `GET /tasks`

| Parameter | Type | Notes |
|---|---|---|
| `q` | string | Words describing the task ("hospital admission", "diabetes") |
| `benchmark` | string | Suite id or name; alone, lists that suite's tasks with their leaders |
| `task` | string | Exact task name; returns that task's ranking |
| `type` | string | `tabular` or `forecasting` |
| `limit` | integer | Models per task, default 10, at most 40 |

Give at least one of `q`, `benchmark` or `task`, or the route returns 400. A benchmark without per-task tables
returns 404 listing the suites that have them.

#### `GET /scores`

| Parameter | Type | Notes |
|---|---|---|
| `model` | string | Model name or part of one |
| `type`, `domain` | string | Model type; domain |
| `benchmark` | string | Benchmark id or name |
| `metric` | string | Part of a metric name: `acc`, `F1`, `AUC`, `Elo` |
| `min`, `max` | number | Value range |
| `max_rank` | integer | Only rows at this rank or better; `1` lists benchmark leaders |
| `limit` | integer | Default 40, at most 200 |

Returns `count`, a `note` that values compare only within one benchmark, and `results[]` rows with `rank`, `of`,
`name`, `value`, `benchmark`, `benchmark_id`, `type`, `domain`, `metric`, sorted by rank.

#### `GET /benchmarks` and `GET /benchmarks/{id}`

`/benchmarks` takes `q`, `type`, `domain`, `capability` (a capability id such as `cap-clinical-knowledge`) and `limit`
(default 25, at most 150). It returns `count`, `interpreted_as`, `coverage`, `capabilities[]` and `results[]` with
`id`, `name`, `type`, `domain`, `metric`, `testing_type`, `measures`, `run_status`, `n_models_scored` and the
`leader` where models were scored.

`/benchmarks/{id}` accepts an id or a name and `limit` (default 40, at most 120). It returns the suite record
(above) merged with the benchmark's public catalog fields (`measures`, `composition`, `testing_type`, `arm`, `tests`,
`tier`, `gated`, `higher_better`, `verified_published`, `provenance`, …), `project` and `eval_type` for imaging and
multi-modal benchmarks, and `tasks_available` when per-task tables exist.

#### `GET /models` and `GET /models/{name}`

`/models` takes `q` (name filter), `type`, `role` (`foundation-model`, `baseline` or `model`), `include_not_run`
(boolean) and `limit` (default 60, at most 300). It returns `count`, `evaluated_models`, `evaluated_baselines`,
`how_to_count`, `coverage` and `results[]` with `name`, `type`, `role`, `status`, `n_benchmarks`, `modalities` and
`best_result {benchmark, rank, of, value}`. Baselines sort last.

`/models/{name}` accepts partial names. It returns `name`, `type`, `types`, `role`, `status`, `n_benchmarks`, where
present `family`, `source`, `open_weights`, `runs`, `note`, `not_run_reason` and `url`, then `scores[]` (each score
with its rank on that benchmark) and `published_leaderboard` rows for methods panAtlas did not run itself.

#### `GET /compare`

| Parameter | Type | Notes |
|---|---|---|
| `benchmark` | string | One benchmark's full ranking |
| `models` | string | Two or more model names, comma-separated, for a head-to-head |
| `limit` | integer | Maximum rows (head-to-head default 30, at most 60) |

A head-to-head returns `models[]`, `shared_benchmarks`, `ahead_on` and `results[]` (`benchmark`, `benchmark_id`,
`metric`, `how_to_read`, `scores {model: {value, rank}}`, `ahead`). Rows from a published leaderboard are kept apart
from `scores` and from every count. Fewer than two distinct models returns 400. Without `benchmark` or `models` the
route returns 400.

!!! note "Undocumented parameters"
    `/compare` also accepts `task`: with no `benchmark`, it answers as `/best` for that task. This parameter is not
    in `openapi.json` or `tools.json`.

### Graph, datasets and literature

#### `GET /stats`

No parameters. Returns counts grouped as `documents` (`mapped`, `by_role`, `sources`), `imaging` (CT volumes and
slices, MRI and chest X-ray studies), `graph` (`nodes`, `edges`, `kinds`), `concepts`, `food_atlas`, `datasets`
(`total`, `by_modality`, `by_access`, `by_status`), `benchmarks` (`language`, `language_scored`,
`imaging_multimodal`, `tabular`, `forecasting`, `capabilities`), `models` (`with_scores`, `baselines_scored`,
`by_type`, `evaluated`, `how_to_count`), `literature` (`concepts`, `articles`) and `knowledge_graphs` (`graphs`,
`triples`, `subjects`, `objects`, `predicates`, `built`). Cached for an hour per snapshot.

#### `GET /search`, `GET /node/{id}`, `GET /neighborhood`

`/search` takes `q` (required), `kind` (one of `concept`, `disease`, `food`, `dataset`, `llm-benchmark`, `model`,
`specialty`, `capability`) and `limit` (default 20, at most 100). Matching scores label hits above description hits;
terms of three characters or fewer must match a whole word; with several terms, at least half must match. Returns
`query`, `count` and `results[]` of `{id, label, kind, summary, modality, url}`.

`/node/{id}` returns the node's public fields (from a fixed whitelist: grounding, MeSH and Wikipedia identifiers,
description, modality, domain, metric, origin, stage, tokens, documents, access, contamination, training use, and
so on), `url`, `links` grouped by relation (incoming relations suffixed ` (in)`, at most 25 per relation, numeric edge
values such as `value` and `metric` kept), `link_count`, and an `evaluation` block for models and evaluated
benchmarks. Unknown id: 404.

`/neighborhood` takes `ids` (comma-separated, at most 12). It returns `nodes[]` (each with `role: seed` or `link`, up
to 14 links per seed) and `edges[]` of `{from, to, rel}`, at most 400.

#### `GET /datasets` and `GET /datasets/{slug}`

`/datasets` takes `q`, `modality` (for example `text`, `imaging-ct`, `knowledge-graph`, `structured`), `access`
(`open`, `public`, `internal`, `restricted`, `credentialed`), `status` (`listed`, `active`, `measured`, `on-disk`,
`acquiring`, `building`), `limit` (default 25, at most 200) and `offset`. Returns `count` and `results[]` with `slug`,
`name`, `desc` (trimmed), `modality`, `license`, `access`, `status`, `dtype`, `owner`, `url`.

`/datasets/{slug}` matches a slug or a URN and returns the public record: `urn`, `slug`, `name`, `desc`, modality
fields, licence fields, `access`, `status`, `citation`, `owner`, `scale`, `documents`, `split_role`, `stage`,
`domain_mix`, `corpus_membership`, `grounding`, `models_trained`, `artifact_types`, `linked_nodes`,
`used_in_training`, `caveats`, `url`, and `evaluation` when the dataset is a scored benchmark. Field meanings are in
[Dataset registry](../metadata/dataset-registry.md).

#### `GET /literature/{node}`

`limit` default 10, at most 50. Returns `node`, `count` (all stored articles) and `articles[]` with `pmid`, `title`,
`journal`, `date`, `pubdate`, `authors`, `doi`. See [the literature feed](web-site.md#node-detail-and-the-literature-feed).

#### `GET /kg/graphs`

No parameters. Returns the store manifest `kg_graphs.json`: `store`, `built`, `totals` (`triples`, `subjects`,
`objects`, `predicates`), `note`, and `graphs[]` (`name`, `graph` IRI, `triples`, `version`, `family`). The served
copy at the repository's HEAD describes 44 graphs and 6,994,341,217 triples, built 2026-10-03. See
[Knowledge store](knowledge-store.md).

#### `GET /teaser/{part}`

`part` is one of `xy`, `color`, `nodes`, `edges`. Returns the public low-resolution universe geometry as
`application/octet-stream`. This route is registered but not listed in `openapi.json` or `tools.json`.

## Using the API from a language model

A client needs only `tools.json`. Load the tools, call each tool's `path` with the model's arguments as query
parameters (substituting path parameters such as `{id}`), and return the result to the model. Each tool is
`{"type": "function", "path": "/best", "function": {"name", "description", "parameters"}}`. The file also carries
suggested system text:

> PanAtlas has measured scores for language, vision, multimodal, tabular and forecasting models. For "which model is
> best" questions call best_models first. Answer only from tool results. Name the benchmark, the score and the best
> baseline. Compare values only within one benchmark. Before saying PanAtlas has nothing on a topic, check
> atlas_overview.

Because clients load tools from `tools.json` at run time, a new tool reaches them without a change on their side.
The first external client works this way, with a one-hour cache (`docs/public-api.md`).

```bash
curl -s 'https://panatlas.net/wp-json/panatlas/public/v1/best?task=pathology%20encoders&limit=3'
curl -s 'https://panatlas.net/wp-json/panatlas/public/v1/search?q=cardiology&kind=specialty'
curl -s 'https://panatlas.net/wp-json/panatlas/public/v1/overview'
```

## Where the data comes from

The API reads the snapshot files in the plugin's `data/` directory, rebuilt by the [build pipeline](build-pipeline.md):

| File | Built by | Feeds |
|---|---|---|
| `evals_index.json` | `web/build_evals_index.py` from `benchmarks_llm.json`, `full_eval.json`, `mm_evals.json`, `predictor_evals.json`, `models.json` | Every evaluation route, the `evaluation` blocks on nodes and datasets, `/stats` model counts |
| `graph.json` | Graph builders and `build_all.sh` | `/search`, `/node`, `/neighborhood`, `/stats` |
| `datasets.json` | `sync_catalog.py` | `/datasets`, `/stats` |
| `benchmarks_llm.json`, `mm_evals.json` | Benchmark builders, `build_patho_evals.py`, cluster ingest | `/benchmarks/{id}` catalog fields, `/stats` |
| `kg_graphs.json` | The SPARQL store build | `/kg/graphs`, `/stats` |
| Literature files | Nightly feed on the web host | `/literature`, `/stats` |

The evaluation records themselves are described in [Evaluation records](../metadata/evaluation-records.md) and
[Benchmarks](../metadata/benchmarks.md).

## Changelog

- **1.1.1 (2026-10-31).** `best_models` leads with a task that holds every specific word of the question
  (`answer_from`); a word in a task's name outranks one in its description; pathology and radiology foundation models
  read as image encoders. `compare_models` covers held-out models, adds `head_to_head` on tasks both finished, and
  uses `published_leaderboard` rows for methods without a run of panAtlas's own, kept apart from scores and counts.
  `/models` and `/stats` explain their counts. `/best` accepts `q` or `question`.
- **1.1.0 (2026-10-31).** Every evaluation for every model type through one set of routes. New tools `best_models`,
  `atlas_overview`, `task_scores`, `query_scores`. Corrected scores that a substring join had attached to the wrong
  language benchmarks since 2026-08-05.
- **1.0.0 (2026-10-25).** First public release.
