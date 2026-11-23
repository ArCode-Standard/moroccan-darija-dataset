# Regional Darija Data

This directory stores regional or locality-specific submissions separately from the national lexicon.

## Current resources

| Path | Content | Status |
|---|---|---|
| `north.json` | 122 initial entries about family and people, attributed to reported northern use | Contributor submission; pending review |

## Record rules

- A reported locality is a claim about where a form was reported, not proof that every speaker in that locality uses it.
- Do not call a term exclusive to a region unless comparative evidence supports that conclusion.
- Keep locality-level observations separate. Do not copy a region-wide list of localities onto every record unless the contributor explicitly reported that scope.
- Preserve original forms and variants; do not normalize away phonological or spelling differences.
- Keep unknown collection details and rights as `unknown`; do not fill them by inference.
- Every record remains `pending` until a human reviewer documents a linguistic decision.
- Do not include speaker names, phone numbers, precise home addresses, or private conversation content.

## Schema

Regional files should validate against [regional-lexicon.schema.json](../schemas/regional-lexicon.schema.json). The existing `north.json` is kept at its current path for compatibility.

## Future layout

When multiple independent datasets exist for a region, they may be separated into `<region>/entries.json`, `<region>/examples.json`, and `<region>/metadata.json`. Do not split the current file until migration tests and stable IDs are in place.
