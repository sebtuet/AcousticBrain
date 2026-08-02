# Channel isolation guided execution contract

```text
contract_id = acousticbrain.channel_isolation_guided_execution.v1
version = 1
status = FROZEN
authority = OPERATIONAL_GUIDANCE_ONLY
scientific_authority = NONE
implementation_status = NOT_IMPLEMENTED
```

## Purpose

This contract guides a user from one exact `READY` `CHANNEL_ISOLATION` plan
and one exact preparation declaration to an acquisition checklist. It does not
perform a measurement, verify physical conditions, create an experiment or
interpret a result.

```text
exact READY CHANNEL_ISOLATION plan
→ exact recorded preparation declaration
→ preparation qualification
→ read-only acquisition checklist
→ separate future experiment declaration
```

## Exact inputs

The operation requires an explicit `plan_id`, `confirmation_id`, preparation
registry and measurement root. The plan and confirmation must each resolve
uniquely. The confirmation must reference the exact plan and preserve its
current canonical fingerprint.

No plan or confirmation is selected by recency, filename, status, ranking or
similarity. A historical fingerprint mismatch is rejected before rendering.

## Preparation qualification

The view preserves three distinct states:

```text
PREPARATION_INCOMPLETE
PREPARATION_USER_CONFIRMED
PREPARATION_ALREADY_USED = NOT_TRACKED_IN_V1
```

`PREPARATION_USER_CONFIRMED` is available only when the persisted record
carries `ALL_PREREQUISITES_USER_CONFIRMED`. It remains an unverified user
assertion. Any `UNKNOWN` or `NOT_CONFIRMED` produces
`PREPARATION_INCOMPLETE` and no experiment-declaration action.

V1 never tracks or infers whether a preparation declaration was previously
used. It therefore never consumes, supersedes or locks a declaration.

## Checklist projection

The checklist copies only the exact plan contract:

- required inputs and their recorded statuses;
- independent variables to change;
- controlled variables to keep constant;
- measurements to capture;
- expected observations, labeled as expectations rather than results;
- ordered procedural instructions;
- success and failure criteria;
- scientific limitations.

For `CHANNEL_ISOLATION`, LEFT and RIGHT acquisitions and repetitions are shown
only because the existing coverage validator requires them. The checklist may
state the structured manifest declarations that a future executed experiment
will need, but it cannot claim those declarations are true.

No microphone position, gain, time window, filename, threshold, metric value
or acquisition setting is invented. Existing identifiers remain exact.

## Single user action

- incomplete preparation: review the unresolved prerequisite declarations;
- all prerequisites user-confirmed: separately declare an experiment from the
  exact plan contract;
- missing declaration authority: no safe execution action.

The view never starts software, creates directories, writes manifests or tells
the user that an experiment has already begun.

## Relationship to existing validators

After a future experiment exists, `ChannelIsolationPlanCoverageValidator`
remains the sole authority for declared structural coverage and
`ChannelIsolationPlanResultEvaluator` remains the sole authority for declared
criteria evaluation. This guided checklist does not duplicate either.

`PLAN_COVERAGE_COMPLETE` will continue to mean declared structural coverage,
not verified execution. Result criteria remain unavailable when the plan does
not carry structured scientific thresholds.

## Required view blocks

1. exact plan and preparation provenance;
2. preparation qualification;
3. acquisition checklist;
4. exactly one user action;
5. scientific boundary with `Causality status: NOT_ESTABLISHED`.

All blocks remain present when content is unavailable. Missing information is
displayed, never reconstructed.

## CLI boundary

The future operation requires:

```text
--channel-isolation-journey PLAN_ID
--channel-isolation-preparation CONFIRMATION_ID
--evidence-plan-preparation-registry PATH
--measurements-root PATH
```

It is read-only and cannot be combined with preparation generation, preview or
recording, plan completion, reporting, experiment views, exploratory, advisor
or execution modes.

## Acceptance criteria

Tests must demonstrate exact identity and fingerprint resolution, rejection of
non-`READY` and non-`CHANNEL_ISOLATION` plans, exact status preservation,
blocked action for `UNKNOWN` and `NOT_CONFIRMED`, separate user-confirmed
qualification, complete plan-derived checklist, required LEFT/RIGHT coverage
declarations, exactly one action, no scientific threshold inference, no
filesystem write and unchanged historical workflows.
