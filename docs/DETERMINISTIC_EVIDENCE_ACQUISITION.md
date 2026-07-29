# Deterministic Evidence Acquisition Planner

> An Evidence Acquisition Plan recommends how to acquire evidence. It is not
> an acoustic correction and does not make any action applicable by itself.

The planner is the read-only deterministic layer between Evidence Weighting
and the Optional Advisor. It consumes existing reasoning, corrective actions,
weights and explicit blocking factors. It never reads raw measurements,
changes an upstream object, resolves a contradiction or calls a language
model.

## Contract

`EvidenceAcquisitionPlan` is immutable and has stable provenance to one
reasoning, corrective action and evidence weight, plus one or more existing
blocking-factor ids. It explicitly carries its objective, test type,
instructions, inputs, variables, measurements, expected observations, success
and failure criteria, evidence targets, priority, effort, status and limits.

Collections preserve planner order and stable JSON uses sorted keys and compact
separators. Empty instructions, success criteria, evidence targets or blocking
factor references are invalid.

## Test taxonomy

- `REPEAT_MEASUREMENT`
- `CHANNEL_ISOLATION`
- `CONTROLLED_SPEAKER_DISPLACEMENT`
- `CONTROLLED_MICROPHONE_DISPLACEMENT`
- `GEOMETRY_ACQUISITION`
- `PROTOCOL_EXECUTION`
- `ADDITIONAL_OBSERVATION`
- `COMPARATIVE_MEASUREMENT`
- `PARAMETER_COMPLETION`

A controlled speaker displacement is an experiment only. The model requires
the language to say that it is temporary, protocol-defined and followed by a
return to the initial position. No permanent placement or guaranteed
improvement is permitted.

## Deterministic rules

| Existing condition | Generated acquisition |
| --- | --- |
| Stereo `CONTRADICTORY_EVIDENCE` | Isolate left/right channels and repeat at the identical documented microphone position. |
| Modal contradiction plus `INSUFFICIENT_DISCRIMINATION` | One comparative plan across independent speakers and protocol-defined microphone positions. |
| `MISSING_PARAMETERS:compatible_protocol_or_plan_id` | Parameter-completion plan, `BLOCKED` until an explicit compatible reference exists. |
| `MISSING_PARAMETERS:additional_supporting_observation` | Additional deterministic observation linked to the existing hypothesis. |
| SBIR observation gap plus geometry limitation | Separate geometry acquisition with declared coordinates and units. |

Protocol and geometry values are never invented. Exact displacement distances
must come from an explicit protocol or configurable parameter.

## Priority and status

Priority is categorical, never numerical:

1. `CRITICAL`: a blocked corrective action already has `HIGH` evidence;
2. `HIGH`: a scientific contradiction otherwise remains;
3. `MEDIUM`: an indispensable parameter is missing;
4. `LOW`: remaining supported acquisition work.

Effort is `LOW`, `MEDIUM` or `HIGH`. Status is `PROPOSED`, `READY` or
`BLOCKED`. A comparative modal plan is blocked while its compatible protocol
and protocol-defined positions are absent. Geometry acquisition can be ready
because its purpose is precisely to document those parameters.

`READY` means that the planner has produced a sufficiently defined acquisition
plan. `EvidenceAcquisitionPlan` does not contain evidence that every named
`required_input` is currently available. The user projection therefore lists
those inputs and marks their availability as unverified before execution; it
does not reinterpret their names as proof that they are satisfied.

## CLI

```bash
python main.py \
  --measurements-root /path/to/campaign \
  --evidence-acquisition
```

The report recommends exactly one `READY` plan. Selection is deterministic:
highest priority, then lowest estimated effort, then lexicographically smallest
stable `plan_id`. The id is only a technical final tie-breaker and is not a
scientific preference.

The scientific justification explains what uncertainty the experiment tests
from the associated structured reasoning. A separate selection rationale
explains why this `READY` plan ranked first. The report also displays required
inputs, procedure, controlled and independent variables, measurements, expected
observations, success and failure criteria, and limitations.

Protocol ids come only from `compatible_protocol_ids` on the corrective action
referenced by the plan's exact `corrective_action_id`. Multiple ids are
displayed in stable lexical order. No text parsing, approximate matching or
protocol invention is performed.

The visible result has four distinct states:

- `RECOMMENDED_EXPERIMENT`: one `READY` plan is presented as the next experiment;
- `PLANS_PROPOSED_BUT_NOT_READY`: at least one plan is `PROPOSED`, but none is
  `READY`; any coexisting blocked plans remain identified as blocked;
- `ALL_PLANS_BLOCKED`: plans exist, but no experiment is recommended and their
  required inputs and limitations explain the next prerequisite;
- `NO_PLANS`: the analysis produced no evidence acquisition plan.

The report performs no write to the campaign.

## Optional Advisor

Plans enter Advisor context only when `--evidence-acquisition` is explicitly
combined with `--advisor`. The historical Advisor context is otherwise
unchanged. Plans are known immutable context objects; the provider may cite and
rephrase them but cannot invent or modify them.

French Mock example:

```text
Question: Quels tests faut-il effectuer ensuite ?
Answer: Les prochains plans déterministes d’acquisition de preuves sont :
EVIDENCE_ACQUISITION_ASYMMETRIC_SPEAKER_ROOM_INTERACTION_REASONING_RESOLVE_CONTRADICTION; ...
Ils servent uniquement à acquérir des preuves et ne rendent aucune action
corrective bloquée applicable.
Validation: VALID
```

English Mock example:

```text
Question: Which tests should be performed next?
Answer: The next deterministic evidence acquisition plans are:
EVIDENCE_ACQUISITION_ASYMMETRIC_SPEAKER_ROOM_INTERACTION_REASONING_RESOLVE_CONTRADICTION; ...
They acquire evidence only and do not make a blocked corrective action applicable.
Validation: VALID
```

## Extension

Add a closed enum member only with a new explicit rule, model validation,
fixture and documentation. A rule must map existing factor ids to existing
object ids, declare all variables and criteria, and remain reproducible. It may
not infer a new scientific protocol or corrective recommendation.

## Scientific limits

Plans state what evidence could reduce a named uncertainty; they do not claim
that acquisition will resolve it. Future measurements still pass through Facts,
Analyses, Observations, Reasoning, Corrective Actions and Evidence Weighting.
Only those upstream deterministic layers can change the scientific state.
