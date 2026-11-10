# RDF vocabulary and SPARQL stores

RDF is panAtlas's canonical graph form (owner decision 2026-09-26, recorded in
`GRAPH_STANDARDS.md`). This page documents how the served property graph becomes RDF: the
namespaces, classes and predicates, the named graph, the mapping rules, and the SPARQL stores that
serve panAtlas together with mirrored external graphs. Code: `web/rdf/build_rdf.py` (export),
`web/rdf/qlever_build.py`, `qlever_serve.py`, `qlever_fold.py`, `qlever_export.py`, `nt_canon.py`,
`sparql_client.py` (stores), and `web/acquisition/okn/` (mirrors).

| Item | Status |
|---|---|
| Export of the served graph to N-Quads | **Built** (`build_rdf.py`) |
| SPARQL store `panatlas-okn` (panAtlas + NSF OKN mirrors) | **Built and served** inside the HPC cluster (vault, 2026-10-16) |
| SPARQL store `wikidata` | **Built**, held back in verification (vault, 2026-10-16) |
| SPARQL store `panatlas-restricted` (licensed vocabularies, per-project access) | **Designed** only (`PLAN-restricted-data-umls.md`) |
| Public SPARQL endpoint | None. The stores answer only inside the cluster network |

## Namespaces

| Prefix | IRI | Use |
|---|---|---|
| `pa:` | `https://panatlas.net/ontology#` | panAtlas classes and properties |
| (nodes) | `https://panatlas.net/id/{id}` | One IRI per graph node; `{id}` is the node id, percent-encoded with no safe characters |
| (statements) | `https://panatlas.net/id/edge%2F{edge id}` | Reified edges; the `/` after `edge` is percent-encoded because the whole string goes through the same encoder |
| (graph) | `https://panatlas.net/graph/panatlas` | The named graph panAtlas curates |
| (graph) | `https://purl.org/okn/frink/kg/{shortname}` | A mirrored NSF OKN graph |
| (graph) | `http://www.wikidata.org/` | The Wikidata mirror (source of record: Wikimedia) |
| `rdf:` | `http://www.w3.org/1999/02/22-rdf-syntax-ns#` | `rdf:type`, reification, `rdf:JSON` literals |
| `rdfs:` | `http://www.w3.org/2000/01/rdf-schema#` | `rdfs:label`, `rdfs:Class`, `rdfs:subPropertyOf` |
| `skos:` | `http://www.w3.org/2004/02/skos/core#` | `skos:Concept`, `skos:prefLabel`, `skos:exactMatch`, `skos:broader`, `skos:related` |
| `dct:` | `http://purl.org/dc/terms/` | `dct:description`, `dct:identifier`, `dct:title`, `dct:license`, `dct:publisher` |
| `dcat:` | `http://www.w3.org/ns/dcat#` | `dcat:Dataset` |
| `foaf:` | `http://xmlns.com/foaf/0.1/` | `foaf:isPrimaryTopicOf` (Wikipedia pages) |
| `void:` | `http://rdfs.org/ns/void#` | Named-graph descriptions |
| `prov:` | `http://www.w3.org/ns/prov#` | `prov:Entity`, `prov:generatedAtTime` |
| `pav:` | `http://purl.org/pav/` | `pav:version` (upstream version of a mirrored graph) |
| `xsd:` | `http://www.w3.org/2001/XMLSchema#` | Literal datatypes |

Code IRIs are built from the `rdf_iri_stem` of each system in `web/codesystems.json` (see
[Controlled vocabularies](codesystems.md)):

| Node field | Stem | Predicate |
|---|---|---|
| `mesh_dui` | `http://id.nlm.nih.gov/mesh/` | `skos:exactMatch` |
| `snomed` | `http://snomed.info/id/` | `skos:exactMatch` |
| `loinc` | `http://loinc.org/rdf/` | `skos:exactMatch` |
| `rxnorm` | `http://purl.bioontology.org/ontology/RXNORM/` | `skos:exactMatch` |
| `cui` | the UMLS identifier stem registered in `codesystems.json` | `skos:exactMatch` |
| `icd11` | `http://id.who.int/icd/entity/` | `skos:exactMatch` |
| `go` | `http://purl.obolibrary.org/obo/GO_` (the `GO:` prefix is stripped) | `skos:exactMatch` |
| `icd10cm` | none registered | literal `pa:icd10cmCode` |
| `wiki_title` | `https://en.wikipedia.org/wiki/` | `foaf:isPrimaryTopicOf` |
| `wp_url` | (the URL itself) | `foaf:isPrimaryTopicOf` |
| `mesh_url` | (the URL itself) | `pa:meshUrl` |

The MeSH stem is `http`, not `https`, because NLM mints `http` IRIs and only redirects `https`
(vault `project-panatlas`, 2026-09-26). Site browser links in `mesh_url` stay `https`.

## Mapping rules (`build_rdf.py`)

Inputs: the served graph (`web/wp-plugin/panatlas-explorer/data/graph.json`), the dataset registry
(`web/datasets.json`) and `web/codesystems.json`. Optional: `--okn-agents <dir>` with each mirror
agent's `state.json`, `sor.json` and `provenance.json`. Output: `rdf/panatlas.nq` and
`rdf/panatlas.stats.json`. Every quad is in the named graph `https://panatlas.net/graph/panatlas`
and is written once; repeats (for example `wp_url` and `wiki_title` naming the same page) are counted
as `duplicates_suppressed`.

### Nodes

| Graph content | RDF |
|---|---|
| Every node | `<id> rdf:type pa:{Kind}`, where `{Kind}` is the `kind` in upper camel case (`llm-benchmark` → `pa:LlmBenchmark`, `fhir` → `pa:Fhir`) |
| Concept-like kinds: `concept`, `disease`, `specialty`, `food`, `food-category`, `domain`, `capability`, `capability-group`, `eval-domain`, `gen-category`, `artifact-type`, `testing-type`, `register`, `training-stage`, `group`, `root`, `atlas-root` | Also `rdf:type skos:Concept`; `label` also as `skos:prefLabel` |
| `dataset` | Also `rdf:type dcat:Dataset` |
| `benchmark`, `llm-benchmark` | Also `rdf:type dcat:Dataset` and `rdf:type pa:Benchmark` |
| `model` | `rdf:type pa:Model` |
| `label` | `rdfs:label` |
| `desc` | `dct:description` |
| Codes and links | The table above |
| Code-system nodes (`onto-*`) | `iri_stem`, `rdf_iri_basis` and `fhir_system` are taken from `codesystems.json`, not from the graph, because the graph copy may predate an edit |
| Any other field | `pa:{camelCase(field)}`; a list of scalars repeats the predicate once per value |

Literal typing: booleans are `xsd:boolean`, integers `xsd:integer`, floats `xsd:double`; objects and
lists of objects are serialised as sorted JSON with datatype `rdf:JSON`; strings are plain literals.
Empty values (`null`, `""`, `[]`, `{}`) are skipped, as are `id`, `kind` and `label` (already
expressed).

!!! note "Kinds typed as `skos:Concept`"
    `training-stage`, `capability`, `testing-type` and `register` nodes are typed `skos:Concept`
    because they are in the script's `CONCEPT_KINDS`. `model`, `dataset`, `fhir`, `authority`,
    `codebase`, `system`, `guideline`, `kg`, `eval-suite`, `modality`, `measurement` and `method`
    nodes are not. The last three are MeSH-grounded concepts whose kind is not in the list.

### Edges

Every edge whose two ends exist becomes `<from> pa:{camelCase(rel)} <to>`. An edge with attributes is
also reified:

```turtle
<https://panatlas.net/id/edge%2Fe-ca547f136f6d8d89b80f>
    a rdf:Statement ;
    rdf:subject   <https://panatlas.net/id/mesh-D000089323> ;
    rdf:predicate pa:partOf ;
    rdf:object    <https://panatlas.net/id/concept-geriatrics> ;
    pa:src        "mesh_tree" .
```

The 36 relation predicates, with the number of triples at HEAD:
`pa:binds` 15, `pa:builtWith` 14, `pa:classifiedAs` 1,756, `pa:covers` 3,607, `pa:coversTopic` 2,209,
`pa:defines` 1, `pa:derivedFrom` 3, `pa:evaluatedBy` 2, `pa:evaluatedOn` 8, `pa:executedOn` 14,
`pa:follows` 9, `pa:groundedIn` 239, `pa:grounds` 13, `pa:groups` 35, `pa:hasArtifactType` 816,
`pa:hasRegister` 162, `pa:hasResource` 18, `pa:hasTrainingStage` 14, `pa:hasType` 21,
`pa:inCollection` 83, `pa:inDomain` 97, `pa:instantiates` 36, `pa:isType` 106, `pa:measuredOn` 104,
`pa:partOf` 5,430, `pa:prereq` 6, `pa:related` 44, `pa:resolvesTo` 251, `pa:scored` 85,
`pa:sftTrainedOn` 2, `pa:stageTrainedOn` 45, `pa:structuredAs` 1,592, `pa:testSetOf` 14,
`pa:tests` 247, `pa:trainedOn` 20, `pa:uses` 1. Their meaning is on [Graph schema](graph-schema.md).

The only alignment axioms asserted are:

```turtle
pa:partOf  rdfs:subPropertyOf skos:broader .
pa:related rdfs:subPropertyOf skos:related .
```

Nothing else is asserted about the vocabulary. In particular there is no `skos:narrower`, no
domain or range, and no class hierarchy.

### Dataset registry

Each entry of `datasets.json` is written to `<https://panatlas.net/id/dataset-{slug}>`:

| Registry field | RDF |
|---|---|
| (entry) | `rdf:type dcat:Dataset` |
| `urn` | `dct:identifier` |
| `name` | `dct:title` |
| `modality[]` | `pa:modality` |
| `license` | `dct:license <IRI>` when it is a URL, else `pa:licenseStatement` |
| `license_status`, `license_scope`, `status`, `role`, `host`, `access`, `used_in_training` | `pa:licenseStatus`, `pa:licenseScope`, `pa:status`, `pa:role`, `pa:host`, `pa:access`, `pa:usedInTraining` |
| `manifest.manifest_hash`, `manifest.file_count`, `manifest.total_bytes` | `pa:manifestHash`, `pa:fileCount`, `pa:totalBytes` |
| `maintained_externally` | `pa:maintainedExternally true` |
| `source_of_record.graph` | `pa:sourceOfRecord <external graph IRI>`, plus `pa:agent`, `pa:upstreamVersion`, `pa:heldVersion`, `pa:upstreamLastUpdatedOn`, `pa:registryCommit` |
| (no external source of record) | `pa:sourceOfRecord <https://panatlas.net/graph/panatlas>` |

Registry fields are documented on [Dataset registry](dataset-registry.md) and
[Manifests](manifests.md).

### Named-graph descriptions

With `--okn-agents`, each mirrored graph is described (not copied) inside the panAtlas graph:

| Triple | Source |
|---|---|
| `<graph> rdf:type void:Dataset, prov:Entity` | always |
| `<graph> pa:mirroredBy <…/id/dataset-okn-{sn}>` | always |
| `<graph> pa:agent "okn-agent:{sn}"` | `sor.json` |
| `<graph> pav:version` | upstream version, `provenance.json` |
| `<graph> pa:heldVersion` | held version, `state.json` |
| `<graph> prov:generatedAtTime` | fetch time, `state.json` |
| `<graph> void:triples` | endpoint count, `state.json` |
| `<graph> void:sparqlEndpoint` | upstream endpoint, `provenance.json` |
| `<graph> dct:license`, `dct:publisher` | `provenance.json` |
| `<graph> pa:authoritativeNamespace <ns>` (repeated) | `sor.json` |
| `<graph> pa:authoritativeDeclared` | whether the publisher declared its namespaces or panAtlas inferred them |

The panAtlas graph describes itself as `void:Dataset` with `dct:title` "panAtlas (source of record:
panAtlas)" and `prov:generatedAtTime` (the export time).

Every `pa:` class used is declared `rdf:type rdfs:Class` with an `rdfs:label`, and every `pa:`
property `rdf:type rdf:Property` with an `rdfs:label`.

## Export statistics

| Measure | Committed `rdf/panatlas.stats.json` (2026-09-26) | Export of HEAD `57505c6` (run for this page, 2026-11-10; not committed) |
|---|---:|---:|
| Quads | 213,647 | 216,627 |
| Duplicates suppressed | 361 | 565 |
| Graph nodes | 6,088 | 6,187 |
| Graph edges | 16,891 | 17,119 |
| Registry entries | 139 | 200 |
| External graphs described | 46 | 0 (no agent directory available off-cluster) |
| `pa:` classes | 29 | 32 |
| `pa:` properties | 346 | 349 |

`panatlas.nq` itself is not committed; it is regenerated on the cluster.

### Classes in the HEAD export

| Class | Instances |
|---|---:|
| `rdf:Statement` | 8,453 |
| `skos:Concept` | 5,408 |
| `pa:Disease` | 3,170 |
| `pa:Food` | 1,582 |
| `dcat:Dataset` | 734 (513 dataset nodes, 124 benchmark nodes, 96 registry entries with no graph node, and the FoodAtlas `kg` node, which is also a registry entry) |
| `pa:Dataset` | 513 |
| `pa:Concept` | 312 |
| `pa:FoodCategory` | 172 |
| `pa:Benchmark` | 124 (106 `llm-benchmark`, 18 `benchmark`) |
| `pa:LlmBenchmark` | 106 |
| `pa:Model` | 90 |
| `pa:Capability`, `pa:ArtifactType` | 35 each |
| `pa:Specialty` | 28 |
| `pa:TestingType` | 21 |
| `pa:Fhir` | 18 |
| `pa:Authority` | 15 |
| `pa:TrainingStage` | 14 |
| `pa:CapabilityGroup` | 13 |
| `pa:EvalDomain` | 9 |
| `pa:Domain`, `pa:Register`, `pa:Modality` | 5 each |
| `pa:Codebase` | 4 |
| `pa:Guideline`, `pa:GenCategory` | 3 each |
| `pa:Group`, `pa:System` | 2 each |
| `pa:Root`, `pa:Gate`, `pa:Kg`, `pa:AtlasRoot`, `pa:EvalSuite`, `pa:Measurement`, `pa:Method` | 1 each |
| `void:Dataset` | 1 (the panAtlas graph) |

Standard predicates in the HEAD export: `rdf:type` 21,270; `rdf:subject`, `rdf:predicate`,
`rdf:object` 8,453 each; `rdfs:label` 6,568; `dct:description` 5,477; `skos:prefLabel` 5,408;
`skos:exactMatch` 3,821; `foaf:isPrimaryTopicOf` 230; `dct:title` 201; `dct:identifier` 200;
`dct:license` 21; `rdfs:subPropertyOf` 2; `prov:generatedAtTime` 1.

### All `pa:` properties for node and edge attributes

Besides the 36 relation predicates, the HEAD export declares these 313 `pa:` properties, each the
camel-case form of a node field, an edge attribute or a registry field:

`acc`, `access`, `agent`, `architecture`, `arm`, `artifactTopicTokens`, `artifactTopics`, `artifactTypeLabels`, `artifactTypePct`, `artifactTypeRecords`, `artifactTypeTokens`, `artifactTypeVia`, `artifactTypes`, `arxiv`, `audit`, `auditChain`, `authorityOrg`, `basis`, `battery`, `batteryN`, `benchmark`, `blake2b`, `buildChain`, `builtBy`, `canonical`, `canonicalId`, `canonicalStandard`, `catScores`, `category`, `caution`, `cites`, `clsDataType`, `clsDifficulty`, `clsDocs`, `clsDocsClassified`, `clsDomain`, `clsMeanQuality`, `clsRegister`, `clsSampled`, `clsSftGrammar`, `clsSftOrigFormat`, `clsSftSource`, `clsSftStructural`, `clsSftTopology`, `clsSource`, `clsSources`, `codeExample`, `codebase`, `composition`, `conceptClass`, `config`, `contaminatedInMix`, `contamination`, `contaminationNote`, `contaminationPrior`, `corpus`, `corpusDocs`, `corpusDocsCaveat`, `corpusOverlap`, `corpusSourceDocs`, `corpusSources`, `corpusStatus`, `curriculumDisclosed`, `curriculumNote`, `curriculumStages`, `curriculumSummary`, `curriculumVerified`, `data`, `dataStage`, `dataType`, `decontam`, `decontamGap`, `dedupFinding`, `deployed`, `discipline`, `docClassificationStatus`, `docConcepts`, `docIdTraceable`, `docTotal`, `docs`, `docsCounted`, `domain`, `domainMix`, `domainsTop`, `dtype`, `ece`, `embedding`, `embeddingRefs`, `embeddings`, `evalAccuracy`, `evalBenchmarks`, `evalQuestions`, `evalStatus`, `evalcap`, `expanded`, `externals`, `faEntities`, `faEvidence`, `faExternalIds`, `faLicense`, `faNChem`, `faNDisease`, `faNFood`, `faOverlap`, `faRelations`, `faTopChemicals`, `faTopDiseases`, `faTopFoods`, `faTriplets`, `faVersion`, `family`, `fhirGroup`, `fhirSystem`, `file`, `fileCount`, `fnddsNFoods`, `fnddsNResolved`, `fnddsResolved`, `fnddsSampleFoods`, `fnddsTotal`, `fnddsWweiaCode`, `framework`, `fullEval`, `gated`, `genDocs`, `gene`, `generalDomain`, `granularity`, `grounding`, `groundingJudge`, `groundingMatch`, `groundingNote`, `groundingReason`, `group`, `hasDocEmbeddings`, `heldOutTotal`, `hf`, `host`, `humanAnnotationType`, `icd10cmCode`, `idNamespace`, `identityMap`, `iriStem`, `isExternal`, `isSft`, `isSftMix`, `kosUsage`, `layer`, `leaderboardEligible`, `ledger`, `lengthBands`, `licenceNote`, `license`, `licenseNote`, `licenseScope`, `licenseStatement`, `licenseStatus`, `location`, `maintainedExternally`, `manifestHash`, `meanRank`, `measured`, `measures`, `meshAppropriate`, `meshCat`, `meshMappedTo`, `meshName`, `meshTree`, `meshUrl`, `metric`, `modalities`, `modality`, `modalityDetail`, `model`, `n`, `nCodelists`, `nCuratedCases`, `nDiseases`, `nDocs`, `nDomains`, `nFoods`, `nHumanAnnotated`, `nModels`, `nPatientScans`, `nPatients`, `nSlices`, `nSources`, `nStudies`, `nSubtopics`, `nVariables`, `nVolumes`, `nativeFieldSampleN`, `nativeFieldValues`, `nativeFields`, `note`, `openWeights`, `order`, `origin`, `overCutoff24576`, `overall`, `owner`, `pairedText`, `panelAnalyte`, `params`, `paramsB`, `paramsH`, `parentMix`, `partOfCorpus`, `path`, `pct`, `peerNote`, `perModel`, `pipeline`, `predictorEval`, `pretrainDocs`, `pretrainJob`, `pretrainSlots`, `pretrainSources`, `pretrainSteps`, `pretrainTokensManifest`, `pretrainTokensReal`, `provenance`, `quality`, `ratioToPublished`, `rdfIriBasis`, `recordLevelCoverage`, `recordLevelJudgeAudit`, `recordLevelMethod`, `recordLevelRecords`, `recordLevelTypeRegister`, `recordLevelTypeTopic`, `recordRegisterAtypes`, `recordRegisters`, `recordTopicConcepts`, `recordTopics`, `records`, `recordsEffective`, `register`, `registryCommit`, `relatedMesh`, `relatedMeshName`, `relatedWikipedia`, `relations`, `results`, `rlStage`, `role`, `ropeTheta`, `scale`, `sft`, `sftContents`, `sftMix`, `sftRecipe`, `sftRecords`, `sftSources`, `sftType`, `sftTypeTotals`, `sharePct`, `sim`, `source`, `sourceOfRecord`, `splitNote`, `splitType`, `src`, `stage`, `stageType`, `status`, `store`, `strata`, `subtopics`, `system`, `task`, `template`, `testSets`, `testingType`, `testsConcepts`, `tier`, `tokPerDoc`, `tokens`, `tokensMeasured`, `toolRecords`, `topics`, `topicsStatus`, `totalBytes`, `trainSamples`, `trainedBy`, `trainedOnCaveat`, `trainingAudited`, `trainingDisclosed`, `trainingNote`, `uniqueIdScheme`, `upstreamLastUpdatedOn`, `upstreamVersion`, `urn`, `usedInTraining`, `value`, `variant`, `vaultDesc`, `vaultPage`, `vaultStatus`, `version`, `via`, `vocab`, `weldToolRecords`, `when`, `wikiBands`, `wikiDistinctPages`, `wikiLinked`, `wikiLinkedFraction`, `wikiOldid`, `wikiTop`, `withheldReason`, `wpTopic`, `wweiaCategories`

## SPARQL stores

### `panatlas-okn`

A read-only SPARQL 1.1 endpoint (QLever) holding panAtlas's own graph and every deployed NSF Open
Knowledge Network graph that has been proven exact, each in the named graph of its source of record.

| Fact | Value | Source |
|---|---|---|
| Build | `panatlas-okn-20261003T0039` | `web/rdf/README.md`; vault `reference-panatlas-sparql-endpoint` |
| Named graphs | 44: panAtlas plus 43 OKN graphs | same |
| Triples | 6,994,341,217 | same; re-checked 2026-10-16 |
| Served | 2026-10-03 to 2026-10-08 (Slurm job 226412), and since 2026-10-16 08:06 (job 237423) | same |
| Where | A CPU-only Slurm job on a cluster compute node; reachable only inside the cluster network | same |
| Every graph | Passed the exact round trip before the store went live (2026-10-03 07:43) | vault |

The host and port change whenever a new build is switched live, so clients read them from the
endpoint record `stores/<name>.endpoint` (`host`, `port`, `url`, `job`, `started`) under the store
directory in `<cluster project storage>/panatlas/qlever/`. Queries run inside a Slurm job, never on
a login node. A served query is stopped after one hour; whole-store scans take minutes.

Agents query through the `query_knowledge_graph` tool of the Astral agent, which runs
`sparql_client.py` over a forced-command key: parameters `query`, `store` (`panatlas-okn` or
`wikidata`), `describe=true` (the named graphs with versions, sizes and proofs) and `max_rows`
(at most 1,000); requests are base64 JSON (`{"action": "describe", "store": …}` or
`{"query": …, "store": …, "max_rows": …}`); SPARQL Update is refused; timeout 120 s.

### `wikidata`

A separate store from the Wikidata agent's md5-verified Wikimedia dump, in the named graph
`http://www.wikidata.org/`. 21,350,107,674 triples, indexed 2026-10-02. It is held back: its first
smoke test assumed English labels, but Wikidata stores a name shared by every language once under
the language code `mul` (vault `defect-wikidata-store-test-assumed-english-label`). A verification
rerun was submitted 2026-10-16 (job 237432). For English labels use
`FILTER(LANG(?l) IN ('en', 'mul'))` and prefer `en`. The two stores are joined at query time with
`SERVICE`.

### `panatlas-restricted` (designed)

`PLAN-restricted-data-umls.md` designs a third QLever store for licensed vocabularies, never merged
into `panatlas-okn`, with one named graph per source restriction level under
`https://panatlas.net/graph/restricted/…`, panAtlas-derived relations in a separate derived graph,
and per-user, per-project entitlements enforced in `sparql_client.py` (default deny, every call
audited). Licensed content is internal and entitlement-gated; none of it enters the public graph
or this documentation. At HEAD only acquisition (phase P1) has passed; the store is not built.

## Versioning and exactness

### Mirrors: one agent per graph

Each OKN graph has its own agent (`okn-agent:{shortname}`, `web/acquisition/okn/okn_agent.py`) with
its own state, provenance, source-of-record file, lock and update job. A six-hourly tick snapshots
the OKN registry and VoID records (`pav:version`, `lastUpdatedOn`, `void:triples` per graph) and
submits an independent sync job for each changed graph. Held copies live as
`raw/<sn>/<version>/part_*.nt` with `DONE` and `PROOF.json`, and `raw/<sn>/current` points at the
adopted version. A sync proves its new version and falls back to the previous one if any proof
fails. Mirrored graphs are read-only and replaced wholesale; panAtlas never edits an externally
maintained node or edge, it only links to it from its own graph.

The source-of-record rule for nodes: a node IRI is maintained by whichever source's authoritative
namespace covers it, by longest prefix (`sor_index.json`). Where a graph declares no namespaces, its
own base IRI is taken as authoritative and marked inferred. An IRI no source claims belongs to its
external authority (OBO, Wikidata, identifiers.org, NCBI).

### Proof levels (`okn_prove.py`, `PROOF.json`)

| Level | Check |
|---|---|
| fingerprint | sha256 of the sorted distinct triples; per-predicate counts; blank-node count |
| upstream | Per-predicate counts equal the endpoint's; 20 random slices byte-identical at their offsets; 2,000 random triples byte-identical among the endpoint's objects for their subject and predicate |
| reextract | A second full extraction at page size 999,983 hashes identically |
| store | The triples exported back out of the local store equal the source (`qlever_build.py`) |

A graph is admitted to a store build only if its extraction verified and `PROOF.json` shows
fingerprint, upstream and reextract ok.

### The store round trip

A store is a query view, proven before it is served. `qlever_build.py` builds into
`stores/<name>-<stamp>/`, then requires: every graph's triple count equals its verified count; no
graph appears that was not admitted; the panAtlas MeSH joins hold; and the exact round trip passes.
Only then does `stores/<name>` switch to the new build. A failed build writes
`stores/<name>.last_failure` and is not resubmitted until fixed and re-verified.

The round trip exports every graph back out of the store and requires that the sorted distinct
non-blank triples of `canon(export)` hash identically to `canon(fold(source))`, that blank-node
triple counts are equal (the store assigns its own labels), and that `COUNT(*)` equals the source's
distinct stored values. `nt_canon.py` writes one spelling per RDF term; `qlever_fold.py` applies
QLever's literal folding to the source. QLever cannot keep literals verbatim and has no setting to
stop it (vault `reference-qlever-literal-folding`):

| Rule | Effect |
|---|---|
| integer | `xsd:integer` becomes `xsd:int` (60-bit range) |
| decimal / double | Stored as a double minus its 4 lowest mantissa bits; printed `%.1f` or `%.13g` as `xsd:decimal` (lossy past 13 significant digits) |
| point | WKT POINT quantized to a 30-bit grid per coordinate, printed `%f` (sub-metre loss) |
| dateTime | A year beyond 4 digits loses its `Z` |
| unparseable | A folded-type literal QLever cannot parse loses its datatype |
| spelling | `\uXXXX` escapes, `^^xsd:string`, language-tag case (same RDF term) |

Exact recreation therefore always comes from the verified raw files, never from a store.

## Joins the store enables

Measured in the store and recorded in the vault (`project-panatlas`, 2026-09-26):

- 3,373 of 3,377 panAtlas MeSH IRIs exist in NLM's MeSH RDF (OKN graph `biobricks-mesh`).
- 3,310 panAtlas concepts reach 3,313 Wikidata entities through the OKN `identifier-mappings` graph.
- 137 MeSH IRIs join the OKN graph `spoke-okn` only through their `https` variant.
- panAtlas concepts carry no Wikidata identifiers of their own.

Example (from `web/rdf/README.md`, run against the live store 2026-10-08, 1.2 s):

```sparql
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?c ?m ?label WHERE {
  GRAPH <https://panatlas.net/graph/panatlas>              { ?c skos:exactMatch ?m }
  GRAPH <https://purl.org/okn/frink/kg/biobricks-mesh>     { ?m rdfs:label ?label } } LIMIT 3
# -> panatlas:fa-dis-C531609  mesh:C531609  "Diffuse alopecia"@en
```

```sparql
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?c ?w WHERE {
  GRAPH <https://panatlas.net/graph/panatlas>                 { ?c skos:exactMatch ?m }
  GRAPH <https://purl.org/okn/frink/kg/identifier-mappings>   { ?w skos:exactMatch ?m } } LIMIT 3
# -> panatlas:fa-dis-C531609  wd:Q9394945   (7.2 s)
```
