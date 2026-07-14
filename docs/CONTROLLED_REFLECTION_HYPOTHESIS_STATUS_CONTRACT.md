# Controlled reflection hypothesis observation status contract

## Scope

PR-039 derives a cautious observation-support status from exactly one PR-038
comparison. The target is the PR-035 candidate carried by the PR-036 proposal;
it is never a surface attribution or a causal mechanism.

The pure dependency contract is:

```text
update(PR-036 proposal, PR-037 declaration, zero or one PR-038 comparison)
```

The engine does not load measurements, rebuild events, execute experiments,
aggregate comparisons, call an LLM, or mutate any input.

## Status vocabulary

- `NOT_ASSESSABLE`: comparison absent, invalidly typed, incoherently linked, or
  `NOT_COMPARABLE`;
- `INCONCLUSIVE`: PR-038 is inconclusive or its observed change does not include
  a directional change of the targeted event level;
- `NOT_SUPPORTED_BY_OBSERVATION`: no planned observable changed, or the targeted
  event level did not decrease after intervention;
- `SUPPORTED_BY_OBSERVATION`: the targeted event relative level explicitly
  decreased after intervention;
- `UNCHANGED`: reserved in the closed persistence vocabulary; the single-input
  transition engine does not use it to hide missing or ambiguous evidence.

`SUPPORTED_BY_OBSERVATION` describes only agreement between one observation and
the outcome anticipated by the controlled protocol. It does not prove that the
candidate, surface, mask, or material caused the change.

## Deterministic transition rules

```text
NOT_COMPARABLE       -> NOT_ASSESSABLE
INCONCLUSIVE         -> INCONCLUSIVE
NO_OBSERVABLE_CHANGE -> NOT_SUPPORTED_BY_OBSERVATION
CHANGE_OBSERVED with target level decrease -> SUPPORTED_BY_OBSERVATION
CHANGE_OBSERVED with target level increase -> NOT_SUPPORTED_BY_OBSERVATION
CHANGE_OBSERVED without directional target level change -> INCONCLUSIVE
absent or incoherent input -> NOT_ASSESSABLE
```

No significance threshold, multi-experiment vote, implicit pairing, or hidden
aggregation is introduced.

## Provenance separation

The persisted output stores disjoint fields for:

- measured fact codes from PR-038 differences;
- comparison result codes;
- transition rule codes;
- status provenance codes;
- descriptive justification codes.

Identifiers are deterministic:

```text
reflection_hypothesis_status_update.<comparison_id>
```

When comparison input is absent, the declaration identifier replaces the
comparison identifier so the `NOT_ASSESSABLE` result remains stable.

## Persistence and traceability

The JSON registry uses schema version 1, stable ordering, atomic replacement,
and idempotent saving. Loading into a project is explicit.

Traceability preserves:

```text
candidate -> proposal -> declaration -> comparison -> observation status update
```

No hypothesis-causality, action, recommendation, ranking, eligibility, or
recommended-candidate link is added.

## Absolute boundaries

Every output enforces:

```text
causality_status = NOT_ESTABLISHED
recommendation_impact = NONE
ranking_impact = NONE
eligibility_impact = NONE
```

PR-039 does not change acoustic scores, PR-035 ordering, recommendations,
experiment eligibility, upstream reasoning, or any file under `measurements/`.
