# Controlled reflection experiment declaration and persistence contract

## Scope

PR-037 records that a controlled reflection verification proposed by PR-036 is
planned, executed, invalid, or cancelled. It persists the declaration and
presents it in the report. It does not analyze the referenced measurements.

Every declaration references exactly one existing `proposal_id`. Its stable
identifier is derived without randomness or time:

`reflection_experiment_declaration.<proposal_id>`

## Declared knowledge

A declaration contains only:

- the PR-036 proposal identifier;
- the status `PLANNED`, `EXECUTED`, `INVALID`, or `CANCELLED`;
- the baseline and intervention condition codes inherited from PR-036;
- explicit measurement references for each condition;
- an explicit reason for `INVALID` and `CANCELLED`;
- field-level provenance.

`EXECUTED` means only that both conditions have at least one declared
measurement reference. It makes no statement about an acoustic difference or
the validity of a hypothesis.

## Provenance separation

System-derived identifiers, PR-036 condition data, operator declarations, and
measurement-manifest fields use separate provenance sources. Provenance is
required for every persisted field and is never synthesized from measurement
contents.

## Persistence

The JSON registry uses schema version 1. Declarations, measurement references,
and provenance entries are sorted by stable identifiers or field codes before
serialization. Saving is atomic and idempotent. Loading is explicit; a missing
registry yields an empty declaration set.

## Scientific boundaries

PR-037 performs no result comparison and exposes no result field. It cannot:

- confirm or refute a hypothesis;
- establish causality;
- modify acoustic scores, ranks, eligibility, or recommendations;
- recommend treatment;
- execute an experiment;
- mutate PR-036 or any upstream analysis;
- invoke an LLM in the scientific engine.

Traceability links a declaration to its source proposal only. That link carries
no acoustic fact, result evidence, hypothesis, protocol decision, ranking, or
recommendation.

## Report contract

The report displays identifiers, status, conditions, measurement references,
and provenance-preserving presentation data. It states explicitly:

- `Result interpretation: NONE`;
- `Causality: NOT_ESTABLISHED`;
- `Ranking impact: NONE`;
- `Recommendation impact: NONE`.
