# AWAL Data Pipeline — operational specification

## Purpose

Define a traceable path from a proposed Darija data item to a reviewed, rights-screened, versioned dataset export. The pipeline must preserve evidence and uncertainty; it must never manufacture source attribution, consent, or permission.

## Data lifecycle

`proposed → normalized → deduplicated → linguistically_reviewed → rights_reviewed → approved_for_export`

A record may instead move to `needs_correction`, `restricted`, `excluded`, or `on_hold`. These are explicit outcomes, not silent deletion. Linguistic approval does not imply rights approval, and rights approval does not imply linguistic correctness.

## Required record envelope

Every future corpus or lexical record should carry:

| Field | Purpose |
|---|---|
| `record_id` | Stable, unique identifier |
| `resource_type` | lexicon, corpus, parallel, instruction, evaluation, or speech |
| `source_id` | Foreign key into `data/sources/registry.json`; required for sourced material |
| `source_locator` | Stable locator such as URL + section, document page, dataset row, or contributor submission ID |
| `collection_method` | Manual contribution, licensed download, interview, transcription, etc. |
| `transformation` | Normalization, segmentation, translation, filtering, or other transformations |
| `permission_evidence` | Path/URL or controlled reference to the actual permission/consent evidence; never a bare assertion |
| `rights_review_status` | pending_verification, cleared, restricted, unknown, or excluded |
| `linguistic_review_status` | pending, reviewed, needs_correction, or rejected |
| `reviewer_id` | Pseudonymous reviewer identifier |
| `reviewed_at` | Timestamp for the decision |
| `split` | train, validation, test, or null until a benchmark split is defined |

The existing lexicon schema is retained for compatibility. These fields are a target envelope for pipeline resources; do not bulk-migrate old entries with invented values.

## Intake procedure

1. Register the source family in the source registry, including owner/author, canonical URL, license statement, permitted uses, restrictions, and verification notes when known.
2. Capture the exact source locator for every ingested item. A family-level homepage is not a record-level locator.
3. Store permission/consent evidence in a controlled location and reference it by stable identifier. Do not place private personal data or signed consent forms in a public repository.
4. Record the collection method and every transformation. Preserve the original text where lawful and necessary for audit.
5. Normalize encoding and whitespace without destroying original spelling, script, or regional variants.
6. Run exact and normalized duplicate detection. Flag possible duplicates for review; do not merge automatically.
7. Route linguistic and rights reviews independently.
8. Export only records whose intended use is explicitly cleared. Apply separate export policies for redistribution, model training, and commercial use.

## Rights decision matrix

| Rights status | Public redistribution | Model training | Action |
|---|---|---|---|
| cleared | Only if redistribution is cleared | Only if training is cleared | Export for the individually cleared purposes |
| restricted | No, unless restriction permits it | No, unless restriction permits it | Keep in restricted partition |
| pending_verification | No | No | Hold pending evidence |
| unknown | No | No | Hold; investigate source |
| excluded | No | No | Exclude from all release exports |

A `cleared` status must be supported by verifiable evidence and must specify the relevant use. Do not treat the single status field as a substitute for separate permission flags.

## Duplicate and contamination controls

- Keep exact-text hashes and normalized-text fingerprints separate.
- Normalization must be versioned and documented.
- Compare source IDs and locators to identify repeated extraction from the same source.
- Prevent overlap between benchmark test records and training/validation records.
- Do not use benchmark test data for synthetic generation, instruction tuning, or prompt construction.
- Mark synthetic records with generator, model/version, prompt-template version, generation date, and human review status.

## Review protocol

- Use stratified review samples across source families, categories, registers, and documented regions.
- Record the reviewer decision, timestamp, and concise rationale.
- Escalate disagreement instead of automatically accepting a majority label.
- Keep review history append-only where practical; corrections should preserve prior decisions.
- Never infer region, speaker identity, age, gender, or social group from wording alone.

## Release gates

A release partition is eligible only when:
- schema validation and unit tests pass;
- record IDs are stable and unique;
- source IDs and locators resolve;
- intended redistribution/training/commercial permissions are independently established;
- linguistic review status is explicit;
- duplicate and benchmark leakage checks have run;
- a machine-readable audit report accompanies the release.

CI success verifies only the checks that the workflow actually runs. It is not linguistic peer review or legal clearance.

## Immediate work queue

1. Review the 1,090 national lexicon records by source family, beginning with the 434 external-source records that lack source locators in the current audit.
2. Verify the rights basis for the 271 DODa, 126 Wattpad-derived, and 37 Peace Corps-classified entries; distinguish source material from project-authored transformations.
3. Define and document provenance for the 656 `original` entries; the label alone does not prove independent authorship.
4. Decide whether the 146 context examples can be retained, rewritten, or excluded based on their authorship and intended reuse.
5. Request contributor-level provenance and permission records for the 122 northern entries before any public training export.
6. After evidence is collected, update only verified records and regenerate the audit.

## Non-goals

This specification does not claim that the current repository already contains a complete corpus, a speech dataset, an instruction dataset, or a benchmark. Those resources require separate schemas, consent/rights procedures, and evaluation methodology.
