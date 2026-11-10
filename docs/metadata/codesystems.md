# Controlled vocabularies

panAtlas grounds its nodes in external vocabularies and in a small number of internal ones. This
page documents each vocabulary, the fields that carry it on graph nodes, the files that define it,
and how a grounding is verified. Counts were computed with `python3` from the files at repo HEAD
`57505c6` on 2026-11-10. How grounded identity becomes RDF is on
[RDF vocabulary](rdf-vocabulary.md); identifier syntax is on [Identifiers](identifiers.md).

## Roles of the vocabularies

| Vocabulary | Role in panAtlas | Canonical? |
|---|---|---|
| MeSH (NLM) | Identity and hierarchy of medical concepts; the deduplication key | Yes, for medical concepts |
| Wikipedia | Identity of general, non-medical concepts; readable overlay on MeSH concepts | Yes, for general concepts only |
| Wikidata | Machine-readable identity behind Wikipedia concepts | Registered; not yet carried on nodes |
| SNOMED CT, LOINC, RxNorm, ICD-10-CM, ICD-11 | Cross-codes on MeSH concepts; terminology bindings of FHIR resources | No |
| UMLS Metathesaurus | Licensed crosswalk used to obtain cross-codes; internal and entitlement-gated | No |
| Gene Ontology | Anchors the genomics modality | No |
| HL7 FHIR R4 | Data model of the clinical instance layer | Yes, for instance records |
| NACC Neuropathology Metadata | Data model of neuropathology records | Yes, for that domain |
| FoodOn, ChEBI, FoodData Central, FNDDS | Food and chemical entities | Yes, for food nodes |
| Internal vocabularies | Artifact types, registers, testing types, capabilities, domains | Internal (`panatlas:` prefix where a canonical id is given) |

Each domain is grounded in its own field's vocabularies. Medicine has the most today, because it is where the
atlas's holdings run deepest; foods are grounded in FoodOn and FoodData Central, and general knowledge in
Wikipedia. A new domain registers its own vocabularies the same way.
`GRAPH_STANDARDS.md`, written for the medical holdings, names MeSH, SNOMED CT, LOINC, RxNorm, UMLS and ICD as the
terminology backbone, with MeSH canonical. `web/domains.json` lists the full `ontology_backbone`: `onto-mesh`,
`onto-fhir`, `onto-snomed`, `onto-loinc`, `onto-rxnorm`, `onto-icd11`, `onto-icd10cm`, `onto-umls`,
`onto-go`, `onto-foodon`, `onto-chebi`, `onto-fdc`, `onto-wikidata`, `onto-nacc`, `onto-wikipedia`.

## `web/codesystems.json`

The registry of terminology code systems. Its `_note`: `fhir_system` is the URI a FHIR
`CodeableConcept.coding.system` uses; `rdf_iri_stem` concatenated with a code gives the concept's RDF
IRI (per the FHIR RDF specification and HL7 THO). These replaced earlier "decorative" authority
nodes with sourced identifiers.

| Field | Meaning |
|---|---|
| `id` | `onto-<system>`; also the graph node id of the system |
| `label` | Name |
| `authority` | Publisher |
| `fhir_system` | FHIR coding system URI, or null |
| `rdf_iri_stem` | IRI stem for codes, or null when none is registered |
| `rdf_iri_basis` | Why that stem (dated inventory), where it was contested |
| `code_example` | An example code |
| `canonical` | Whether the system is a canonical identity source |
| `anchor` | The concept node the system anchors, or null |
| `note` | Role statement |

| `id` | Authority | `fhir_system` | `rdf_iri_stem` | Canonical |
|---|---|---|---|---|
| `onto-mesh` | US National Library of Medicine | `https://www.nlm.nih.gov/mesh` | `http://id.nlm.nih.gov/mesh/` | yes |
| `onto-snomed` | SNOMED International / NLM (US Edition) | `http://snomed.info/sct` | `http://snomed.info/id/` | no |
| `onto-loinc` | Regenstrief Institute | `http://loinc.org` | `http://loinc.org/rdf/` | no |
| `onto-rxnorm` | US National Library of Medicine | `http://www.nlm.nih.gov/research/umls/rxnorm` | `http://purl.bioontology.org/ontology/RXNORM/` | no |
| `onto-umls` | US National Library of Medicine | `http://www.nlm.nih.gov/research/umls` | an identifier-only prefix expansion (see below) | no |
| `onto-icd10cm` | US CDC / NCHS | `http://hl7.org/fhir/sid/icd-10-cm` | none | no |
| `onto-icd11` | World Health Organization | `http://id.who.int/icd/release/11/mms` | `http://id.who.int/icd/entity/` | no |
| `onto-go` | Gene Ontology Consortium | `http://purl.obolibrary.org/obo/go.owl` | `http://purl.obolibrary.org/obo/GO_` | no |
| `onto-wikipedia` | Wikimedia | none | `https://en.wikipedia.org/wiki/` | yes |
| `onto-wikidata` | Wikimedia | none | `http://www.wikidata.org/entity/` | no |

The MeSH stem is `http` because NLM mints `http` IRIs and `https` only redirects; the OKN graphs that
hold MeSH also use `http` (inventory 2026-09-26). The UMLS stem is the Biolink prefix expansion used
by the OKN identifier-mapping graph; `codesystems.json` records that it is an identifier only and no
longer resolves, and that NLM publishes no UMLS RDF.

### Authority nodes in the graph

`build_layered.py` turns the registered systems into 15 `authority` nodes (`layer: ontology`): the ten
above plus `onto-fhir` (from `fhir.json`), `onto-nacc` (from `web/nacc/`), and `onto-foodon`,
`onto-chebi`, `onto-fdc` (from `nutrition.json`). Fields: `id`, `label`, `kind`, `layer`, `modality`,
`canonical`, `authority_org`, `source`, `built_by`, `note`; most also carry `fhir_system` (14),
`iri_stem` (13) and `code_example` (10); `onto-nacc` adds `version`, `n_variables`, `n_codelists`.

| Edge | Count | Meaning |
|---|---:|---|
| `authority` `grounds` → concept (`specialty`, `root`, `concept`) | 13 | The system anchors that concept |
| `authority` `defines` → `root` | 1 | MeSH defines Medicine |
| `authority` `has_resource` → `fhir` | 18 | FHIR and NACC own their resource and record types |
| `fhir` `binds` → `authority` | 15 | A FHIR resource's coded elements bind that code system |
| `dataset`/`kg`/`food` `structured_as` → `authority` | 1,592 | The node's records follow that vocabulary (1,582 foods) |
| `authority` `part_of` → `domain` | 15 | All systems sit under "Data & Standards" |

!!! warning "Stale IRI stems on two authority nodes"
    In the served graph `onto-mesh` carries `iri_stem: https://id.nlm.nih.gov/mesh/` and `onto-umls`
    carries the former UTS REST URL, while `codesystems.json` has the corrected stems (changed
    2026-09-26). `build_rdf.py` takes `iri_stem`, `rdf_iri_basis` and `fhir_system` from
    `codesystems.json`, so the RDF is correct; consumers of `graph.json` should read the stems from
    `codesystems.json`.

## MeSH grounding

### Fields on a grounded node

| Field | Nodes | Meaning |
|---|---:|---|
| `canonical_id` | 3,390 with prefix `mesh:` | `mesh:<descriptor UI>` (for example `mesh:D002309`, Cardiology) |
| `grounding` | | `mesh` (3,387), `mesh_broader` (2: grounded through a parent descriptor), `mesh-scr` (1: a supplementary concept record), `mesh+wikipedia` (2) |
| `mesh_dui` | 3,400 | Descriptor UI |
| `mesh_name` | 3,400 | Descriptor preferred name |
| `mesh_tree` | 3,175 | List of MeSH tree numbers (a descriptor can sit in several trees) |
| `mesh_url` | | Browser link to the descriptor (`https`) |
| `cui`, `snomed`, `loinc`, `rxnorm`, `icd10cm` | 202, 47, 42, 0, 2 non-empty | Cross-codes from the licensed UMLS crosswalk |
| `wiki_oldid`, `wp_url` | 51, 211 | Pinned Wikipedia revision and page, as a readable overlay |
| `built_by` | | The grounding method (below) |

### Node identifiers by origin

| Origin | Id form | Nodes | `built_by` |
|---|---|---:|---|
| Curated concept pages (`atlas/20-concepts/*.md`) | `concept-<slug>` | 51 | "grounded to MeSH via UMLS UTS (resolver + adversarial audit + live confirmation); hierarchy from MeSH tree numbers; …" |
| MeSH tree expansion (`mesh_expand_clean.json`) | `mesh-D<UI>` | 142 | "MeSH tree expansion: real child descriptor of a curated specialty, via UMLS UTS" |
| FoodAtlas diseases | `fa-dis-<UI>` | 3,160 grounded | "FoodAtlas KG; grounded to MeSH; specialty by tree number" |
| Domain registrations (neuropathology, renal, ultrasound) | `concept-<slug>` | | dated lookup statements, for example "2026-10-11 id.nlm.nih.gov descriptor + preferred-concept JSON" |

### Grounding files

| File | Records | Fields |
|---|---:|---|
| `web/concept_mesh_grounded.json` | 71 | `slug`, `label`, `kind`, `part_of`, `grounding`, `mesh_dui`, and on most `mesh_name`, `mesh_tree`, `cui`, `snomed`, `rxnorm`, `loinc`, `icd10cm`, `overridden` (12 true), `scope_note`; on some `verified` (20), `gene`, `panel_analyte`, `reason`, `mesh_mapped_to` |
| `web/concept_mesh_v2.json` | 51 | Earlier candidate pass: `slug`, `label`, `kind`, `our_part_of`, `candidates[{dui, name, tree}]`, the chosen `mesh_dui`, `mesh_name`, `mesh_tree`, cross-codes, `non_mesh` |
| `web/mesh_expand_clean.json` | 142 | `mesh_dui`, `mesh_name`, `mesh_tree`, `parents` (descriptor UIs), `parent_slugs`, `cui`, `scope_note` |

`concept_mesh_grounded.json` is the verified concept → MeSH mapping that `build_layered.py` consumes.
Its kinds are `concept` 34, `map` 28 (written to the graph as `specialty`), `modality` 5, `gate`,
`specialty`, `measurement`, `method` 1 each.

### Hierarchy from tree numbers

A descriptor's parent is the descriptor whose tree number is the immediate prefix, for example
Cardiology `H02.403.429.163` under Internal Medicine `H02.403.429` under Medicine `H02.403`.
Specialties are in the H02 (Health Occupations) tree, diseases in C, techniques in E. In the graph
these are `part_of` edges with `src: mesh_tree` (3,360). FoodAtlas diseases are attached to a
specialty by tree number (2,478 `disease` `part_of` `specialty` edges).

### How a MeSH grounding is verified

- Curated concepts: resolved through the UMLS UTS API, then adversarially verified, one agent per
  concept, each confirming the descriptor UI with a live UTS call (`GRAPH_STANDARDS.md`).
- Artifact types (2026-08-08): checked against the live NLM MeSH descriptor lookup with
  `match=exact`, audit trail `web/pipeline/groundings_verified.json`; then a concept-identity judge
  pass (2026-08-09) decided whether the descriptor is the same thing as the record type (see
  [Models and curriculum](models-and-curriculum.md)).
- Later domain additions record the lookup in `built_by`, with its date.
- In the SPARQL store, 3,373 of 3,377 panAtlas MeSH IRIs exist in NLM's MeSH RDF (2026-09-26).

## Wikipedia and Wikidata

| Field | Nodes | Meaning |
|---|---:|---|
| `wiki_title` | 161 | Wikipedia article title |
| `wp_url` | 211 | Article URL, with `?oldid=` when a revision is pinned |
| `wiki_oldid` | 51 | Pinned revision id |
| `canonical_id` `wikipedia:<…>` | 24 | Wikipedia as identity (non-MeSH nodes) |
| `grounding: wikipedia` | 154 | |

Wikipedia is a fallback identity only for genuinely non-medical nodes, and an overlay otherwise. The
general concept space, `web/general_concept_space.json` (`proposed` 153; `final.concepts` 120 with
`name`, `wikipedia_title`, `definition`, `domain`, `granularity` `top`/`mid`/`leaf`, `serves`,
`example_item`; plus `coverage_summary`, `gaps`), gives benchmark items in mathematics, science,
reading and similar areas a Wikipedia-grounded concept. `build_concept_remap.py` writes them as
`concept` nodes with `grounding: wikipedia`, `wiki_title`, `wp_url`, `general_domain` and
`granularity` (117 nodes at HEAD; 3 already existed).

The markdown fact pages record a pinned revision in frontmatter as
`wikipedia: {title, oldid, retrieved}`, and every claim seeded from Wikipedia carries the revision
in its provenance tag. Wikipedia text is evidence, never verification
([Knowledge layers](../concepts/layers.md)).

Wikidata is registered (`onto-wikidata`, stem `http://www.wikidata.org/entity/`), but no node in the
served graph carries a Wikidata QID. The bridge exists in the SPARQL store: 3,310 panAtlas concepts
reach 3,313 Wikidata entities through the OKN `identifier-mappings` graph (vault, 2026-09-26). See
[RDF vocabulary](rdf-vocabulary.md).

## FHIR and NACC

`web/fhir.json` roots the clinical instance layer in HL7 FHIR R4. Keys: `_note`, `root`
(`onto-fhir`), `resources` (13), `dataset_instantiates` (rules).

| Resource node | Group | Binds |
|---|---|---|
| `fhir-patient` | clinical | none |
| `fhir-condition` | clinical | SNOMED CT, ICD-10-CM, ICD-11 |
| `fhir-procedure` | clinical | SNOMED CT |
| `fhir-allergyintolerance` | clinical | SNOMED CT, RxNorm |
| `fhir-observation` | diagnostics | LOINC, SNOMED CT |
| `fhir-diagnosticreport` | diagnostics | LOINC |
| `fhir-specimen` | diagnostics | SNOMED CT |
| `fhir-imagingstudy` | imaging | none |
| `fhir-medicationrequest` | medications | RxNorm |
| `fhir-medication` | medications | RxNorm |
| `fhir-documentreference` | documents | LOINC |
| `fhir-composition` | documents | LOINC |
| `fhir-molecularsequence` | genomics | Gene Ontology |

Resource fields: `id`, `label`, `group`, `binds` (code-system ids), `desc`. In the graph each
becomes a `fhir` node (`layer: ontology`, `fhir_group`), with `binds` edges to the code systems.
`dataset_instantiates` rules (`match_modality` or `match_ids` → `resources`) give 36 `dataset`
`instantiates` → `fhir` edges: imaging datasets instantiate `ImagingStudy` and `DiagnosticReport`,
genomics datasets `MolecularSequence`, clinical-note datasets `DocumentReference` and `Composition`,
drug-label datasets `Medication`.

`web/nacc/` holds the NACC Digital Neuropathology Metadata schema (`openapi.yaml`, `schemas/`,
`codelists.json`, `data_dictionary.json`, `mappings/`, `slide_staining_matrix.json`). The
`onto-nacc` node records version `6.0.0-draft`, 92 variables, 39 codelists and five record types,
which are the five non-FHIR `fhir`-kind nodes: `nacc-case-level`, `nacc-slide-level`,
`nacc-pathology`, `nacc-non-pathology`, `nacc-qc-checklist`.

!!! note "Instance layer: model only"
    The graph holds the FHIR and NACC resource types and which datasets would instantiate them. It
    holds no FHIR instance records. Layer 2 of `GRAPH_STANDARDS.md` (FHIR RDF instances whose codings
    join the backbone) is designed, not built.

## Domains: `web/domains.json`

The navigational spine, broad to granular: the top-level fields of knowledge under `atlas-root`,
grounded to Wikipedia main-topic categories and, where medical, to a MeSH tree category. Medicine
(`domain-health`) is one of five domains today.

| Key | Content |
|---|---|
| `root` | `atlas-root` ("PanAtlas") |
| `domains` (5) | `id`, `label`, `wiki`, `mesh_cat`, `entries` (entry concept ids), `desc`: `domain-health` (Health & Medicine, MeSH C / N), `domain-food` (Food & Nutrition), `domain-lifesci` (Life Sciences & Chemistry, MeSH G / D), `domain-standards` (Data & Standards), `domain-general` (General Knowledge, non-medical) |
| `general_categories` (3) | `id`, `label`, `wiki`, `match` (keywords assigning datasets): `gen-physical`, `gen-computing`, `gen-society` |
| `ontology_backbone` | The 15 authority ids listed above |

Graph: `domain` (5), `gen-category` (3) and `atlas-root` (1) nodes in `layer: domain`; `domain`
`part_of` `atlas-root` (5), `gen-category` `part_of` `domain` (3), `dataset` `part_of`
`gen-category` (43).

## Food and nutrition vocabularies

| Source | In the graph | Fields |
|---|---|---|
| FoodAtlas KG v4.8 (Apache-2.0; 216,804 entities, 542,674 triplets, 161,655 evidence records per `foodatlas_summary.json`) | The `kg` node `dataset-foodatlas`; 3,170 `disease` nodes (3,160 MeSH-grounded, 10 with an OMIM upstream id and `grounding: none`); 1,582 `food` nodes (`foodon` 1,558, `fdc` 24) | `fa_n_chem`, `fa_n_food` / `fa_n_disease`, `fa_top_foods`, `fa_top_diseases`, `fa_top_chemicals` |
| FNDDS (USDA) | 172 `food-category` nodes, one per WWEIA category (`fndds-cat-<code>`) | `fndds_wweia_code`, `fndds_n_foods`, `fndds_n_resolved`, `fndds_sample_foods` |
| FoodOn, ChEBI, FDC | `authority` nodes; foods `structured_as` their vocabulary | |
| `nutrition.json` | 8 MeSH nutrition concepts (`concept-nutritional-sciences`, `concept-diet`, `concept-food`, …), 3 guideline documents (`doc-*`), 1 restricted system | |

`web/fndds_resolution.json` resolves FNDDS foods to FoodAtlas entities by name (Jaccard ≥ 0.5):
5,432 FNDDS foods, 1,379 resolved (25.4 %), across 172 WWEIA categories. Record fields:
`fndds_fdc_id`, `food_code`, `desc`, `wweia_code`, `wweia`, and when resolved `foodatlas_id`,
`foodatlas_name`, `jaccard`. These become 250 `food-category` `resolves_to` `food` edges
(`src: entity_resolution`).

## Internal vocabularies

These are controlled by panAtlas and documented on the pages that use them:

| Vocabulary | Size | Where |
|---|---:|---|
| Artifact types (`atype-*`) | 35 | [Models and curriculum](models-and-curriculum.md) |
| Registers (`register-*`) | 5 | [Models and curriculum](models-and-curriculum.md) |
| Testing types, evaluation domains, capabilities, capability groups | 21, 10, 35, 13 | [Benchmarks](benchmarks.md) |
| Benchmark ontology facets | 26 dimensions | [Benchmarks](benchmarks.md) |
| `eval_type` → modality | 7 | [Evaluation records](evaluation-records.md) |
| Fact predicates (`atlas/predicates.yaml`) | 9 fact types | [Knowledge layers](../concepts/layers.md) |

### Corpus cells to concepts

`web/cell2concept.json` (1,740 records) maps clusters of the training corpus to concepts. Fields:
`cell_id`, `topic_cluster`, `subtopic_cluster`, `count` (documents), `slug` (concept id, 50
distinct), `cos` (cosine to the concept anchor), `cell_domain` (for example `basic_science` 533,
`general` 498, `radiology` 113), `topic_summary`. This is the path by which corpus documents, and in
the first question mapping benchmark items, reach a concept. `web/concept_similarity.json` gives the
top related concepts by anchor cosine, written as `related` edges at 0.72 or above.

## UMLS

The UMLS Metathesaurus is a licensed vocabulary. In panAtlas it is internal and entitlement-gated:

- It is used as a lookup service through the UTS API under licence, to resolve MeSH groundings and
  obtain cross-codes. The cross-code fields listed above come from that lookup.
- The release files were acquired for the planned restricted store (phase P1 passed 2026-10-16,
  owner-only access). They are not loaded, and nothing from them is in the served graph.
- `PLAN-restricted-data-umls.md` designs per-user, per-project access with restriction levels read
  from the release itself; it is not built.
- This documentation contains no UMLS content.
