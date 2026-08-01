# Deterministic exploratory mode V1 contract

```text
contract_id = acousticbrain.exploratory.v1
version = 1
status = FROZEN
authority = PRODUCT_OPERATIONAL
scientific_authority = NONE
implementation_status = NOT_IMPLEMENTED
```

## Purpose and authority

This document is the normative product contract for AcousticBrain's
deterministic `EXPLORATORY` mode. It freezes the accepted V1 scope before
implementation. It does not claim that the current code already implements the
mode.

`EXPLORATORY` helps the user perform one bounded, reversible test when no
scientifically validated prescriptive protocol is available. It is a product
policy, not a scientific authority. Analyses and hypotheses remain under their
existing contracts.

The V1 promise is:

```text
analyze existing measurements
→ expose observations and hypotheses
→ select at most one deterministic exploratory test
→ request confirmation that the exact action is feasible
→ compare reference and intervention measurements
→ report the observed outcome without establishing causality
```

## Frozen knowledge boundary

The user-facing result must always distinguish:

- a scientifically validated protocol, when one exists;
- an `EXPLORATORY` proposal;
- descriptive analysis with no executable proposal.

Every exploratory proposal and result carries:

```text
mode = EXPLORATORY
causality_status = NOT_ESTABLISHED
universal_optimum = NOT_CLAIMED
```

An exploratory proposal does not confirm a hypothesis, identify an exclusive
cause, guarantee an improvement, prescribe a permanent correction, or prove
that a tested configuration is globally optimal.

## Relation to existing contracts

This contract orchestrates existing specialized objects; it does not alter
their scientific meaning. The first vertical slice reuses:

- `GeneratedAcousticExperiment` for the deterministic exploratory candidate;
- the generic experiment declaration for the user-declared intervention;
- the automatic experiment comparison for the empirical acoustic outcome.

The exact first-slice chain is:

```text
GeneratedAcousticExperiment
→ feasibility decision
→ generic experiment declaration
→ automatic experiment comparison
```

Its source contracts are
`DETERMINISTIC_ACOUSTIC_HYPOTHESIS_EXPERIMENT_GENERATION_CONTRACT.md`,
`EXPERIMENT_DECLARATION_CONTRACT.md` and
`AUTOMATIC_EXPERIMENT_COMPARISON_CONTRACT.md`.

The PR-036 to PR-039 controlled-reflection workflow remains a parallel,
descriptive chain with `eligibility_impact = NONE` and
`recommendation_impact = NONE`. This V1 contract neither mutates that chain nor
turns one of its observations into scientific validation.

Feasibility is also separate from experiment declaration. `FEASIBLE` does not
mean `PLANNED` or `EXECUTED`, and `EXECUTED` does not establish a result.

## Proposal admission

V1 presents no more than one proposal at a time. A proposal is admissible only
when it contains:

- a stable `proposal_id` and rule version;
- the exact reference experiment or configuration;
- one unambiguous target and action;
- exactly one intentionally modified semantic variable;
- every relevant controlled variable;
- every required measurement, including separate LEFT, RIGHT and STEREO
  measurements when the existing experiment family requires them;
- an explicit reversible return to the reference state;
- the observable facts used by the comparison;
- limitations and field-level provenance.

Every target, direction, amplitude, position, material or other action
parameter must come unchanged from one of these sources:

1. existing structured data;
2. an explicit, versioned exploratory product policy;
3. an explicit user declaration.

Missing values remain missing. Free text, collection order, an LLM response or
an acoustic hypothesis must not be converted implicitly into an action
parameter.

Candidate selection uses only an explicit, versioned total order. Its final
stable identifier tie-breaker is technical and never represents a scientific
preference. When no exact reversible candidate satisfies this contract,
AcousticBrain reports `NO_ACTION_AVAILABLE`.

## Feasibility decision

An admissible proposal is not executable until the user answers the exact
feasibility question. The V1 states are:

```text
FEASIBILITY_REQUIRED
EXPLORATORY_READY
USER_INFEASIBLE
NO_ACTION_AVAILABLE
```

The analysis command remains read-only. It presents the question; a separate
explicit command or API operation records `FEASIBLE` or `INFEASIBLE`.
AcousticBrain never infers the answer.

A feasibility decision is scoped to:

- the exact `proposal_id`;
- a stable `reference_scope_id` derived from the exact reference experiment,
  its content fingerprint and its structured configuration declaration;
- the proposal rule version.

An `INFEASIBLE` decision prevents the same proposal from being asked again in
that scope. It is not generalized to another distance, direction, target or
configuration. An optional user note is preserved but never parsed into a
broader constraint. A changed reference content or configuration fingerprint
requires a new decision and returns the proposal to `FEASIBILITY_REQUIRED`.
No clock or random value participates in `reference_scope_id`.

A stored `FEASIBLE` decision in the exact same scope yields
`EXPLORATORY_READY` without asking the same question again. It remains a
feasibility statement, not an execution statement, and applies until explicit
revocation or until the exact intervention is declared and therefore no longer
eligible as a new proposal.

After refusal, AcousticBrain selects the next already admissible candidate
using the same deterministic order. It does not invent a smaller or different
variant. If no candidate remains, it reports `NO_ACTION_AVAILABLE`.

## Execution and comparison

`EXPLORATORY_READY` authorizes only the declared acquisition. It does not
execute an experiment automatically. The resulting declaration preserves the
proposal identifier, reference configuration, target, direction or treatment,
action parameters, modified and controlled variables, required measurements
and provenance.

The comparison consumes only the observable facts declared by the proposal.
It uses the existing deterministic automatic-comparison contract and its
explicit threshold codes, without adding or changing a threshold, and projects
exactly one user-level acoustic outcome:

```text
IMPROVED
DEGRADED
UNCHANGED
MIXED
INCONCLUSIVE
```

These are empirical outcomes for the declared facts, not causal conclusions.
`MIXED` must remain `MIXED`; AcousticBrain does not collapse competing changes
into a hidden global score. `INCONCLUSIVE` must remain explicit.

Specialized reflection statuses such as `CHANGE_OBSERVED` remain lower-level
technical facts with their existing `recommendation_impact = NONE`. They do not
replace or overrule the user-level `MIXED` outcome.

A configuration may be called the best **observed** configuration only for an
explicitly declared objective, only among configurations actually measured,
and only when:

- the comparison is valid for every objective fact;
- no objective fact is degraded;
- reference stability has been established by the same deterministic
  comparison contract and explicit threshold codes.

When a declared return-to-reference control is not `UNCHANGED`, reference
stability is not established. AcousticBrain may describe the differences but
must not select a robust winner from that sequence.

The next step is deterministic:

- `DEGRADED`: return to the declared reference state;
- `UNCHANGED`: return, then consider the next admissible candidate;
- `MIXED` or `INCONCLUSIVE`: state that no preference is established, return,
  then consider another candidate only if one already exists;
- `IMPROVED`: report a better observed result for the declared objective only
  when the validity and stability conditions above hold; otherwise preserve
  `IMPROVED`, report that reference stability is not established, and select
  no robust winner.

No result changes a hypothesis to confirmed and no result authorizes a
permanent physical change automatically.

## First real acceptance case

The first V1 vertical slice is limited to
`DOMINANT_EARLY_REFLECTION_INTERACTION` and the historical
`baseline → exp-007` intervention from `AcousticBrain-measurements-real`.
That corpus remains outside the repository.

This case is a replay of the decision immediately before `exp-007`, followed
by consumption of its existing measurements. Because the intervention was
already executed and produced `MIXED`, the current campaign must not recommend
repeating it merely to validate the new mode.

The feasibility question is:

> Can you temporarily place the same mattress used for `exp-007` at the same
> location in front of the left lateral first-reflection area, without changing
> any controlled variable listed by the proposal, including listening
> position, loudspeaker positions, orientation and assignment, microphone
> position, measurement level, cabling, room configuration and REW settings,
> and then remove it to return to the reference state?

This fixed acceptance wording is derived only from the historical user
declaration and its structured controls. The structured target remains
`LEFT_FIRST_REFLECTION_AREA`; the mattress and its historical placement remain
free-form operator provenance. Runtime code must not parse that note into
material properties, geometry or a generic masking rule.

The established replay result is:

```text
comparison = baseline → exp-007
acoustic_outcome = MIXED
causality_status = NOT_ESTABLISHED
```

V1 must therefore preserve `MIXED`, recommend neither the treatment nor a
permanent change, and establish no reflection cause. This case validates the
workflow and user interaction; it creates no scientific rule.

## Acceptance criteria

V1 is complete only when automated tests demonstrate:

1. stable selection independent of Python collection order, clocks or random
   values;
2. no more than one pending proposal;
3. no proposal when an exact action or reversible return is missing;
4. `FEASIBILITY_REQUIRED` before any executable status;
5. idempotent persistence of `FEASIBLE` and `INFEASIBLE`;
6. no repeated question for the same refused proposal and scope;
7. a stored `FEASIBLE` decision yields `EXPLORATORY_READY` in the same scope;
8. a stored decision is never reused when `reference_scope_id` changes;
9. no generalization of a refusal;
10. exact preservation of proposal parameters in the experiment declaration;
11. comparison restricted to the proposal's declared observable facts;
12. stable `IMPROVED`, `DEGRADED`, `UNCHANGED`, `MIXED` and `INCONCLUSIVE`
    outcomes;
13. no winner when reference stability is not established;
14. `NOT_ESTABLISHED` causality through proposal, declaration, comparison and
    report;
15. an already executed identical `MIXED` intervention is not proposed again;
16. no modification of measurement files during analysis or decision.

A separate local, read-only validation against
`AcousticBrain-measurements-real` must demonstrate that the historical
`baseline → exp-007` replay remains `MIXED`. The private real-measurement corpus
is not a CI dependency and must not be committed.

## Explicitly outside V1

V1 does not introduce:

- an LLM-generated runtime action;
- adaptive learning that silently changes rules;
- automatic generalization of physical constraints;
- a universal protocol registry or execution framework;
- SBIR or modal causal validation;
- automatic permanent movement or treatment;
- a universal best-position claim;
- new acoustic metrics, thresholds or scientific rules;
- parsing of notes to reconstruct missing structured parameters.

Implementation must reuse `GeneratedAcousticExperiment`, the generic
experiment declaration and the automatic experiment comparison. The PR-036 to
PR-039 specialized reflection chain remains unchanged. Expanding this semantic
scope requires an explicit product decision and a new contract version. It
must not occur silently in an implementation pull request.

Adding another hypothesis family, action family or real acceptance case is
outside this frozen V1 scope and requires an explicit product decision and a
new contract version.
