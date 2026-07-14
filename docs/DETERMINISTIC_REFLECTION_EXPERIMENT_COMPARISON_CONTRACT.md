# Deterministic baseline/intervention reflection comparison contract

## Scope

PR-038 compares explicit observations associated with the baseline and
intervention measurement references of one PR-037 declaration. It describes a
numerical difference. It does not interpret why that difference exists.

The dependency contract is:

```text
compare(
    PR-036 proposal,
    PR-037 declaration,
    explicit baseline observations,
    explicit intervention observations,
)
```

The engine has no hidden repository or measurement access and never rebuilds
ETC events from raw impulse responses.

## Temporal target and observables

The temporal target is exactly the PR-036 `observed_event_id`, exposed as the
comparison `temporal_window_code`. PR-038 neither widens nor relocates it.
Only observable codes already listed by PR-036 may be compared.

Each input observation identifies its measurement reference, temporal target,
observable code, numeric value, unit, and provenance. Baseline and intervention
provenance remain separate on every output difference.

Schema version 1 compares exactly one declared measurement reference per
condition. A declaration containing several references remains persisted but
is `NOT_COMPARABLE` until a future contract defines an explicit pairing rule;
PR-038 never pairs measurements by position or order implicitly.

## Status semantics

- `NOT_COMPARABLE`: execution, references, temporal target, or observations do
  not satisfy the explicit comparison contract;
- `INCONCLUSIVE`: comparable observations exist but coverage is partial or
  units differ;
- `NO_OBSERVABLE_CHANGE`: every planned observable is present with identical
  baseline and intervention values;
- `CHANGE_OBSERVED`: every planned observable is present and at least one exact
  numerical difference is non-zero.

No perceptual, uncertainty, or significance threshold is invented. A later
contract may introduce such a threshold only with explicit scientific rules.

## Persistence and ordering

Comparison identifiers are deterministic:

```text
reflection_experiment_comparison.<experiment_declaration_id>
```

The JSON registry is schema version 1. Comparisons and differences are sorted
by stable identifiers. Saving is atomic and idempotent; loading is explicit.

## Scientific boundaries

All comparisons impose:

```text
causality_status = NOT_ESTABLISHED
ranking_impact = NONE
recommendation_impact = NONE
eligibility_impact = NONE
```

PR-038 cannot confirm or refute an acoustic hypothesis, attribute a change to
a surface, modify a score or rank, change eligibility, create a recommendation,
or establish causality. Hypothesis interpretation remains outside this layer.

Traceability records only:

```text
proposal -> declaration -> comparison
```

It adds no hypothesis, recommended-candidate, action, or decision link.
