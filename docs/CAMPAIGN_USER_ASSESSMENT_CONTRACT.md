# Campaign user assessment contract

```text
contract_id = acousticbrain.campaign_user_assessment.v1
version = 1
status = ACTIVE
authority = EXISTING_V1_REPORT_PROJECTION_ONLY
scientific_authority = NONE
llm_authority = NONE
```

## Purpose

`CampaignUserAssessment` is the concise human-facing projection of an already
calculated V1 `Report`:

```text
V1 Report
→ CampaignUserAssessmentPresenter
→ immutable presented model
→ HumanReadableAssessmentRenderer
→ console
```

The presenter does not call analysis engines, recalculate observations or
reasonings, change action applicability, reweight evidence, or select an
evidence plan. It reuses the exact `recommended_plan` already exposed by the
V1 evidence-acquisition report. No plan is shown as recommended when that
source value is absent.

## Closed projection

The immutable assessment contains:

- experiment and analysis-family measurement status;
- every deterministic reasoning in its stable V1 order;
- a second, non-destructive view of unresolved or contradictory reasonings;
- existing actions separated by their exact applicability;
- the existing selected evidence plan, if any;
- its exact required inputs and prerequisite-availability state;
- scientific boundaries and source-object provenance.

The projection does not choose a main finding. It defines no global score,
severity scale, cross-finding importance hierarchy, acoustic diagnosis,
treatment, placement, expected benefit or causal conclusion.

The next-step projection also copies the existing action objective and the
selected V1 plan's procedure, controlled variables, variables under test and
measurements. These fields are copied exactly and receive no new scientific
interpretation.

## Human-readable rendering

The console uses one closed, testable English vocabulary to translate existing
semantic states. It does not translate measurements, infer an acoustic cause,
or generate free-form advice. English is retained because it is the current
language of this public view and its immediate V1 source text; this contract
does not introduce a general localization system.

The main rendering is organized as:

1. `Campaign`;
2. `What the measurements show`;
3. `What remains uncertain`;
4. `What you can do now`;
5. `Recommended next measurement`;
6. `Before you start`;
7. `What AcousticBrain cannot conclude yet`;
8. `Technical references`.

Technical IDs, enum values, contract codes and expert commands are confined to
the final references section. They remain in the immutable model and detailed
V1 views. Finding order remains the stable V1 order; the renderer creates no
severity or importance ranking.

## Stable semantic states

`SUPPORTED` is rendered as meaning that the available observations support an existing
hypothesis under the applicable deterministic V1 rules. It does not establish
the hypothesis as an acoustic cause.

An evidence-plan `READY` value is rendered as a defined plan for its current
planning state, immediately qualified as not meaning ready to execute. It does
not mean declared, executed, acquired or causally validated.

An action `APPLICABLE` value permits a human statement only that a controlled
verification is currently available. It does not establish physical safety,
expected benefit, improvement or execution authorization.

`CONDITIONALLY_APPLICABLE`, every `BLOCKED_BY_*` state and `NOT_SUPPORTED`
remain outside that section. `ALREADY_TESTED` and `NO_ACTION_REQUIRED` retain
their exact values and are never converted into recommendations.

## Provenance and detail boundary

Finding objects preserve reasoning IDs, observation IDs, supporting and
contradicting evidence, limitations, excluded conclusions and upstream source
IDs. Action objects preserve their reasoning, observation and upstream source
IDs. The next step preserves its plan, evidence-weight, action and reasoning
IDs.

The default console output intentionally does not print every evidence value
and does not use technical identifiers as its primary message.
The complete audit information remains available through `--full-assessment`,
`--reasoning`, `--actions` and `--evidence-plan-view PLAN_ID`.

## Scientific and mutation boundary

The view is read-only. It does not write measurements, manifests, registries,
campaigns or experiments. It does not declare or execute an experiment and it
does not authorize a physical change.

The deterministic output states, when applicable:

- observation does not establish cause;
- `SUPPORTED` does not establish causality;
- `READY` does not establish execution readiness;
- `APPLICABLE` does not establish benefit or physical safety;
- a recommended plan has not been executed;
- prerequisite availability has not been independently verified;
- no physical change is authorized and no improvement is predicted;
- causality remains `NOT_ESTABLISHED`.

No LLM participates in projection, selection, wording, ranking or diagnosis.

## Public CLI

```bash
python main.py \
  --measurements-root PATH \
  --user-assessment
```

The mode is exclusive with concurrent report, guided, mutation, exploratory
and advisor modes. Existing expert and compatibility views remain unchanged.
