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
→ console renderer
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

## Stable semantic states

`SUPPORTED` means that the available observations support an existing
hypothesis under the applicable deterministic V1 rules. It does not establish
the hypothesis as an acoustic cause.

An evidence-plan `READY` value is rendered only as `Planning status: READY`.
It means that the planning contract contains the information required for its
current state. It does not mean ready to execute, declared, executed, acquired
or causally validated.

An action `APPLICABLE` value permits placement only in the section
`Currently applicable controlled actions`. It does not establish physical
safety, expected benefit, improvement or execution authorization.

`CONDITIONALLY_APPLICABLE`, every `BLOCKED_BY_*` state and `NOT_SUPPORTED`
remain outside that section. `ALREADY_TESTED` and `NO_ACTION_REQUIRED` retain
their exact values and are never converted into recommendations.

## Provenance and detail boundary

Finding objects preserve reasoning IDs, observation IDs, supporting and
contradicting evidence, limitations, excluded conclusions and upstream source
IDs. Action objects preserve their reasoning, observation and upstream source
IDs. The next step preserves its plan, evidence-weight, action and reasoning
IDs.

The default console output intentionally does not print every evidence value.
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
