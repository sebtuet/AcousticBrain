# Experiment user view contract

```text
contract_id = acousticbrain.experiment_user_view.v1
version = 1
status = FROZEN
authority = PRESENTATION_ONLY
scientific_authority = NONE
implementation_status = IMPLEMENTED
```

## Purpose

The experiment user view is a concise, non-specialist projection of one
existing experiment and its preserved scientific context. It answers four
questions in a fixed order:

1. What was this experiment intended to test?
2. What must the user do, if anything?
3. What was actually observed?
4. What may and may not be concluded?

The view consumes established report objects. It does not create an analysis,
select a plan, interpret free text, change a status, rank outcomes, or add a
scientific conclusion.

## Architectural position

```text
EvidenceAcquisitionPlan
→ preserved plan contract
→ ExperimentDeclaration
→ ExperimentDescriptor
→ automatic comparison
→ experiment user view
```

The view does not replace `DecisionFirst`, `OneMinuteExecutiveSummary`,
`AssessmentSummary`, detailed comparison reports, or specialized execution
validators. Those projections retain their contracts. V1 provides a stable
experiment-centered navigation surface over their existing source objects.

## Identity and scope

One view describes exactly one `experiment_id`. It carries:

- the exact experiment identifier;
- its declared reference experiment, when available;
- its source `plan_id` and preserved contract mode, when available;
- its source protocol and hypothesis identifiers, when declared;
- the exact comparison identifier used for the displayed result.

The view never silently combines different experiments, local and cumulative
comparisons, or several equally applicable plans. V1 uses the local comparison
whose `after_experiment_id` exactly matches the viewed experiment. Zero or
multiple matching local comparisons produce an explicit unavailable state.

## Required four-block hierarchy

### 1. Intent

Display, in order:

1. the preserved plan objective;
2. the declared modified variable or variables;
3. controlled variables;
4. expected observations;
5. plan limitations.

The preserved `EvidenceAcquisitionPlanContract` is authoritative when present.
The generic `ExperimentDeclaration` supplies declared reference, modified and
controlled variables. A mismatch between both sources is displayed as a
contract inconsistency; neither source overwrites the other.

When no preserved plan contract exists, the view says that the original plan
intent is unavailable. It may still display the experiment declaration, but
must not reconstruct an objective from a note, filename, hypothesis label or
comparison result.

### 2. User action

The view projects exactly one action state:

```text
NO_USER_ACTION
DECLARE_EXPERIMENT_CONTRACT
COMPLETE_REQUIRED_ACQUISITION
RESOLVE_PLAN_CONTRACT_MISMATCH
RESTORE_COMPARABILITY
REVIEW_OBSERVED_RESULT
```

The projection order is normative:

1. missing declaration → `DECLARE_EXPERIMENT_CONTRACT`;
2. missing or divergent preserved contract for a referenced plan →
   `RESOLVE_PLAN_CONTRACT_MISMATCH`;
3. incomplete experiment or incomplete specialized coverage →
   `COMPLETE_REQUIRED_ACQUISITION`;
4. non-comparable or ambiguous comparison → `RESTORE_COMPARABILITY`;
5. comparable observed result → `REVIEW_OBSERVED_RESULT`;
6. otherwise → `NO_USER_ACTION`.

The action text may list only already-declared missing requirements or existing
unblock steps. It cannot invent a position, channel, repetition, setting,
threshold, material, direction, amplitude or protocol.

### 3. Observed result

Display only an existing automatic local-comparison outcome:

```text
IMPROVED
DEGRADED
UNCHANGED
MIXED
INCONCLUSIVE
NOT_COMPARABLE
NOT_AVAILABLE
```

`MIXED` remains `MIXED`. No global score, majority vote or favorable wording
may collapse competing changes. Facts improved, degraded, changed, unchanged
or unavailable remain separate collections and retain their source codes and
threshold codes.

Expected observations belong to the intent block. They are never presented as
observed unless the existing comparison or specialized result evaluator
actually produced the corresponding fact.

### 4. Scientific boundary

Every view displays:

```text
causality_status = NOT_ESTABLISHED
```

unless a future source object under an explicit scientific contract carries a
different authorized status. Presentation code cannot promote it.

The boundary block distinguishes:

- what the local comparison establishes in its measured scope;
- missing or unavailable measurements;
- contract, execution and comparability limitations;
- whether reference stability was established;
- whether any scientific protocol is formally associated.

An `IMPROVED` outcome means only that the declared measured objective improved
under the comparison contract. It does not prove a cause, a permanent remedy,
an optimum, or a generally applicable recommendation.

## User-view lifecycle states

The top-level state is one of:

```text
CONTRACT_MISSING
CONTRACT_INCONSISTENT
ACQUISITION_PENDING
ACQUISITION_INCOMPLETE
COMPARISON_UNAVAILABLE
RESULT_INCONCLUSIVE
RESULT_AVAILABLE
```

It is derived with this total order:

1. required declaration or plan contract absent → `CONTRACT_MISSING`;
2. plan identity or preserved fields inconsistent → `CONTRACT_INCONSISTENT`;
3. declared experiment has no acquired files → `ACQUISITION_PENDING`;
4. experiment state or specialized plan coverage incomplete →
   `ACQUISITION_INCOMPLETE`;
5. no unique comparable local comparison → `COMPARISON_UNAVAILABLE`;
6. outcome `INCONCLUSIVE` or `MIXED` → `RESULT_INCONCLUSIVE`;
7. outcome `IMPROVED`, `DEGRADED` or `UNCHANGED` → `RESULT_AVAILABLE`.

`MIXED` is grouped under `RESULT_INCONCLUSIVE` only at lifecycle level; the
observed result must still display the exact word `MIXED`.

## Language rules

### Required qualities

User-facing text must be:

- short and concrete;
- explicit about the object being described;
- explicit about missing information;
- scoped to the measured experiment;
- traceable to source identifiers.

### Forbidden claims

Without an authorized scientific source, the view must not say or imply:

- “cause confirmed”;
- “optimal position” or “best configuration”;
- “permanent correction”;
- “guaranteed improvement”;
- “the treatment works”;
- “the hypothesis is proven”;
- that an expected observation was observed;
- that `READY` means executed, successful or scientifically validated.

## Relationship to `READY`

The word `READY` is never displayed without its object:

- `plan READY` means the plan is structurally ready for its declared next step;
- `EXPLORATORY_READY` means feasibility was explicitly accepted;
- experiment `READY` means required files for discovery are present;
- none of these means successful, prescriptive or causally validated.

The view uses user-facing lifecycle states instead of presenting a bare
`READY` label.

## Normative examples

### Declared plan, acquisition not yet present

```text
State: ACQUISITION_PENDING
Intent: Compare left and right channels under the preserved isolation plan.
Your next step: Capture the separately declared LEFT and RIGHT measurements.
Observed result: NOT_AVAILABLE
Conclusion: No result exists yet; causality is not established.
```

### Comparable mixed intervention

```text
State: RESULT_INCONCLUSIVE
Intent: Test the declared temporary intervention against baseline.
Your next step: Review the observed result and return to the reference state.
Observed result: MIXED
Conclusion: Some declared facts improved and others degraded. No preference or
cause is established.
```

### Historical manifest without preserved plan contract

```text
State: CONTRACT_MISSING
Intent: Original plan intent unavailable; declared variables remain visible.
Your next step: Do not reconstruct or overwrite the historical contract.
Observed result: Display the existing comparison separately when available.
Conclusion: Historical observations remain valid in their existing scope; the
missing original intent is explicit.
```

## Acceptance criteria

V1 implementation is complete only when automated tests demonstrate:

1. exactly one view per requested `experiment_id`;
2. output independent of collection order;
3. no merge of local and cumulative comparisons;
4. complete plan intent projected unchanged when preserved;
5. historical manifests remain readable without synthetic intent;
6. declaration/contract mismatch remains explicit;
7. exactly one user-action state;
8. no action parameter invented from free text;
9. every acoustic outcome preserved exactly;
10. expected and observed facts never conflated;
11. `MIXED` never collapsed;
12. bare `READY` never displayed;
13. causal status never promoted by presentation;
14. source experiment, plan, protocol, hypothesis and comparison identifiers
    retained when available;
15. existing detailed reports remain unchanged without the new explicit view;
16. no measurement, manifest or decision file modified during presentation.

## Explicitly outside V1

V1 does not add:

- a dashboard or graphical interface;
- a new analysis or recommendation engine;
- scientific protocol selection;
- prescriptive decisions;
- new thresholds or acoustic metrics;
- manifest editing;
- LLM-authored facts or actions;
- cross-experiment optimization or ranking.

Implementation should begin as one presenter and one explicit CLI projection.
Any graphical surface may consume that presenter later.
