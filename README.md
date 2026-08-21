# AcousticBrain

AcousticBrain is a deterministic acoustic-analysis engine driven by measurement
campaigns. Its analysis pipeline produces structured results; presenters and
CLI reporters expose those results without changing the underlying scientific
rules.

The primary product goal is to help a user place left and right loudspeakers
through reversible, measurement-guided experiments. The authoritative scope
and development gate are defined in
[`docs/PRODUCT_TARGET.md`](docs/PRODUCT_TARGET.md).

The deterministic workflow is separate from the optional LLM Advisor. The
Advisor can explain validated report objects, but it is disabled by default and
is not a source of scientific authority.

AI-assisted contributions must follow the repository workflow defined in
[`AGENTS.md`](AGENTS.md).

The frozen presentation-only contract for a non-specialist experiment view is
documented in
[`docs/EXPERIMENT_USER_VIEW_CONTRACT.md`](docs/EXPERIMENT_USER_VIEW_CONTRACT.md).
It defines a four-block view of intent, user action, observed result and
scientific boundary without adding analysis or recommendation logic.

## Quick start

AcousticBrain requires Python 3.10 or newer. Verify the interpreter before
creating the environment:

```bash
python3 --version
```

Continue only if it reports Python 3.10 or later. Then create and activate an
environment with that compatible interpreter, and install the project
dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The runtime requirements contain only the dependencies needed by the
deterministic V1 engine. To develop AcousticBrain or run its tests, also
install the separate development requirements:

```bash
python -m pip install -r requirements-dev.txt
```

Analyze the versioned example campaign:

```bash
python main.py --measurements-root measurements
```

This is the public placement homepage: it says whether the existing evidence
supports one reversible loudspeaker test now, why, and the one public next
step. It only presents established report objects; it does not move a speaker,
declare an experiment, or claim acoustic causality. Use `--full-assessment`
for the detailed technical report.

Running `python main.py` without a measurement path uses the same historical
default directory:

```bash
python main.py
```

To analyze a campaign outside the repository:

```bash
python main.py --measurements-root /path/to/my-campaign
```

The selected path must exist and be a directory. AcousticBrain's discovery
logic determines which experiments and channels are available. Personal
measurements and real campaigns should remain outside the repository and must
not be committed to Git.

Use the CLI help to inspect the available options:

```bash
python main.py --help
```

## Deterministic result exposure

The CLI exposes the existing deterministic workflow at several levels:

| Output | CLI option | Exposes |
| --- | --- | --- |
| Loudspeaker-placement homepage | no option | The one existing placement action or the one existing verification step needed before a move |
| Acoustic observations | `--observations` | Descriptive observations projected from existing analyses |
| Deterministic acoustic reasoning | `--reasoning` | Premises, inference steps, conclusions, contradictions and limitations |
| Deterministic corrective actions | `--actions` | Declarative actions, applicability, parameters and blocking conditions |
| Deterministic evidence weighting | `--weighting` | Independent evidence dimensions without a global score |
| Next recommended experiment | `--evidence-acquisition` | One selected READY acquisition plan, or why none can be recommended |
| Technical analysis readiness | `--analysis-readiness` | Existing experiment and analysis-family readiness decisions |
| Assessment summary | `--assessment-summary` | A concise projection of the main existing report objects |
| Full assessment | `--full-assessment` | The five detailed deterministic reports in workflow order |
| Experiment user view | `--experiment-view EXPERIMENT_ID` | Four-block read-only view of one exact experiment |
| Evidence-plan user view | `--evidence-plan-view PLAN_ID` | Plain-language blockers and the only safe next action |
| Evidence-plan overview | `--evidence-plan-overview` | Every plan and its safe action, without ranking |
| Guided global status | `--guided-status` | Current workflow state, blocker and exactly one safe next action |
| Evidence-plan completion | `--complete-evidence-plan INPUT_JSON` | One exact audited derivation from a BLOCKED plan |

These options select different presentations of established deterministic
objects. They do not introduce a separate acoustic analysis.

Print the concise view of one exact experiment:

```bash
python main.py --measurements-root measurements --experiment-view exp-007
```

The view preserves the existing outcome and causal status verbatim. Missing
historical contract information is displayed as unavailable and is never
reconstructed.

Explain one exact evidence plan without changing or completing it:

```bash
python main.py \
  --measurements-root measurements \
  --evidence-plan-view EXACT_PLAN_ID
```

When scientific compatibility is not established, this view says that no safe
user action is available. It never asks the user to attest compatibility.
For a `READY` plan, the same view displays the complete declared preparation
checklist and asks only for prerequisite verification before declaration.
The implemented structured confirmation boundary is frozen in
[`docs/EVIDENCE_PLAN_PREPARATION_CONFIRMATION_CONTRACT.md`](docs/EVIDENCE_PLAN_PREPARATION_CONFIRMATION_CONTRACT.md).

List every plan before choosing one to inspect:

```bash
python main.py \
  --measurements-root measurements \
  --evidence-plan-overview
```

The overview is ordered by stable plan id and does not select or recommend a
plan. A separate French label identifies the acoustic subject and operation;
the original contractual objective remains visible and unchanged.

Show the current workflow state without changing it:

```bash
python main.py \
  --measurements-root measurements \
  --guided-status
```

### Complete guided preparation and declaration path

Use `--guided-status` first, then choose one exact `PLAN_ID` displayed by that
read-only view. Choose an explicit preparation registry path and generate the
preparation draft in a new output file:

```bash
python main.py \
  --measurements-root MEASUREMENTS_ROOT \
  --generate-evidence-plan-preparation PLAN_ID \
  --evidence-plan-preparation-registry PREPARATION_REGISTRY_JSON \
  --evidence-plan-preparation-output PREPARATION_DRAFT_JSON
```

The draft contains the deterministic `CONFIRMATION_ID` to retain; do not invent
or substitute one. After supplying the required preparation decisions in the
structured input file, preview it without writing, then confirm it explicitly
in the same chosen registry:

```bash
python main.py \
  --measurements-root MEASUREMENTS_ROOT \
  --preview-evidence-plan-preparation PREPARATION_INPUT_JSON \
  --evidence-plan-preparation-registry PREPARATION_REGISTRY_JSON

python main.py \
  --measurements-root MEASUREMENTS_ROOT \
  --confirm-evidence-plan-preparation PREPARATION_INPUT_JSON \
  --evidence-plan-preparation-registry PREPARATION_REGISTRY_JSON

python main.py \
  --measurements-root MEASUREMENTS_ROOT \
  --evidence-plan-preparation-view CONFIRMATION_ID \
  --evidence-plan-preparation-registry PREPARATION_REGISTRY_JSON
```

For a `CHANNEL_ISOLATION` plan, generate the two operational worksheets into
explicitly chosen new files. Complete them from observed information, then
review those exact files against the source preparation draft:

```bash
python main.py \
  --measurements-root MEASUREMENTS_ROOT \
  --generate-channel-isolation-records PLAN_ID \
  --microphone-position-output MICROPHONE_RECORD_JSON \
  --acquisition-settings-output ACQUISITION_SETTINGS_JSON

python main.py \
  --measurements-root MEASUREMENTS_ROOT \
  --review-channel-isolation-documentation PLAN_ID \
  --microphone-position-record MICROPHONE_RECORD_JSON \
  --acquisition-settings-record ACQUISITION_SETTINGS_JSON \
  --channel-isolation-source-preparation PREPARATION_DRAFT_JSON
```

Before declaration, choose one existing `REFERENCE_EXPERIMENT_ID` and one new
`NEW_EXPERIMENT_ID`. Check readiness with the exact plan, confirmation,
registry, reference, and new identifier; then reuse those same values for the
separate explicit declaration:

```bash
python main.py \
  --measurements-root MEASUREMENTS_ROOT \
  --channel-isolation-declaration-readiness PLAN_ID \
  --channel-isolation-preparation CONFIRMATION_ID \
  --evidence-plan-preparation-registry PREPARATION_REGISTRY_JSON \
  --channel-isolation-reference REFERENCE_EXPERIMENT_ID \
  --channel-isolation-experiment NEW_EXPERIMENT_ID

python main.py \
  --measurements-root MEASUREMENTS_ROOT \
  --declare-evidence-plan-experiment NEW_EXPERIMENT_ID \
  --evidence-plan-id PLAN_ID \
  --evidence-plan-reference REFERENCE_EXPERIMENT_ID \
  --evidence-plan-declaration-preparation-registry PREPARATION_REGISTRY_JSON \
  --evidence-plan-declaration-preparation CONFIRMATION_ID
```

Generation does not choose a plan, confirmation does not choose a reference,
and readiness does not create an experiment. Draft and worksheet generation,
confirmation, and declaration are separate explicit writes to their named
targets. The final declaration creates only the experiment declaration; it does
not execute the experiment or acquire measurements.

To include explicit preparation state, provide its registry rather than
letting AcousticBrain discover one by convention:

```bash
python main.py \
  --measurements-root measurements \
  --guided-status \
  --guided-preparation-registry state/evidence-plan-preparations.json
```

If several preparations target the recommended plan, the view lists their
identifiers without selecting one. Resolve one explicitly by adding:

```bash
--guided-preparation EXACT_CONFIRMATION_ID
```

The view reuses the plan already recommended by the deterministic report. It
never ranks plans again, chooses between several preparation declarations,
changes a prerequisite, declares an experiment or executes a measurement.

For an exactly selected incomplete `CHANNEL_ISOLATION` preparation, include
both explicit operational worksheets to distinguish missing documentation from
documentation that is complete but still awaits a separate user declaration:

```bash
python main.py \
  --measurements-root measurements \
  --guided-status \
  --guided-preparation-registry state/evidence-plan-preparations.json \
  --guided-preparation EXACT_CONFIRMATION_ID \
  --microphone-position-record microphone-position.json \
  --acquisition-settings-record acquisition-settings.json
```

The files are never discovered automatically, and their completeness never
confirms a prerequisite. The extension contract is frozen in
[`docs/GUIDED_GLOBAL_STATUS_OPERATIONAL_DOCUMENTATION_CONTRACT.md`](docs/GUIDED_GLOBAL_STATUS_OPERATIONAL_DOCUMENTATION_CONTRACT.md).

After an exact preparation is user-confirmed, qualify explicit declaration
identifiers in the same read-only view:

```bash
python main.py \
  --measurements-root measurements \
  --guided-status \
  --guided-preparation-registry state/evidence-plan-preparations.json \
  --guided-preparation EXACT_CONFIRMATION_ID \
  --channel-isolation-reference EXISTING_EXPERIMENT_ID \
  --channel-isolation-experiment NEW_EXPERIMENT_ID
```

On success, the view prints the existing separate declaration command. It does
not create the experiment directory or manifest. The extension contract is
frozen in
[`docs/GUIDED_GLOBAL_STATUS_DECLARATION_READINESS_CONTRACT.md`](docs/GUIDED_GLOBAL_STATUS_DECLARATION_READINESS_CONTRACT.md).

### Guided CHANNEL_ISOLATION worksheet revision

Generated operational worksheets now print one neutral question and one
limitation for every field. Fill one or more explicit values into two new
files without editing their JSON structure manually:

```bash
python main.py \
  --measurements-root measurements \
  --revise-channel-isolation-records EXACT_PLAN_ID \
  --microphone-position-record microphone-source.json \
  --acquisition-settings-record settings-source.json \
  --operational-field 'microphone_position.reference_geometry=EXPLICIT USER TEXT' \
  --microphone-position-output microphone-revised.json \
  --acquisition-settings-output settings-revised.json
```

Unassigned markers remain explicit and the output lists the questions still
unanswered. The command never overwrites either source, guesses a value,
confirms a prerequisite, declares an experiment or executes a measurement.

### Individual deterministic reports

Print acoustic observations:

```bash
python main.py --measurements-root measurements --observations
```

Observations describe established analysis facts, confidence, evidence,
limitations and provenance. They do not contain recommendations or corrective
actions. See
[`docs/DETERMINISTIC_ACOUSTIC_OBSERVATIONS.md`](docs/DETERMINISTIC_ACOUSTIC_OBSERVATIONS.md).

Print deterministic reasoning:

```bash
python main.py --measurements-root measurements --reasoning
```

The reasoning report exposes structured premises, inference steps,
conclusions, contradictions, limitations and provenance. See
[`docs/DETERMINISTIC_ACOUSTIC_REASONING.md`](docs/DETERMINISTIC_ACOUSTIC_REASONING.md).

Print declarative corrective actions:

```bash
python main.py --measurements-root measurements --actions
```

The action report exposes applicability, source reasoning, known and missing
parameters, contradictions and limitations. It does not execute a correction
or invent geometry or settings. See
[`docs/DETERMINISTIC_CORRECTIVE_ACTIONS.md`](docs/DETERMINISTIC_CORRECTIVE_ACTIONS.md).

Print multidimensional evidence weighting:

```bash
python main.py --measurements-root measurements --weighting
```

Evidence strength, source consistency, discriminative power, parameter
completeness and action applicability remain independent. The report creates no
evidence, decision or global score. See
[`docs/DETERMINISTIC_EVIDENCE_WEIGHTING.md`](docs/DETERMINISTIC_EVIDENCE_WEIGHTING.md).

Print the next recommended experiment for acquiring missing evidence:

```bash
python main.py \
  --measurements-root measurements \
  --evidence-acquisition
```

The report selects one `READY` plan by priority, then lowest estimated effort,
then stable plan id. It distinguishes a recommendation, proposed plans that are
not ready, plans that are all blocked, and the absence of any produced plan.
The report projects protocols explicitly linked by the source corrective
action, lists required inputs, and states when their availability has not been
verified. Missing protocol or measurement parameters remain missing and are
never inferred. These are diagnostic acquisition plans, not acoustic
corrections; a plan does not make a corrective action applicable by itself. See
[`docs/DETERMINISTIC_EVIDENCE_ACQUISITION.md`](docs/DETERMINISTIC_EVIDENCE_ACQUISITION.md).

### Technical analysis readiness

```bash
python main.py \
  --measurements-root measurements \
  --analysis-readiness
```

This report presents discovered experiments and the existing readiness decision
for each analysis family, including existing blocking and reservation codes.
Readiness is technical: it does not establish scientific validity, and
`BLOCKED` does not mean that the current pipeline skipped computation.

### Assessment summary

```bash
python main.py \
  --measurements-root measurements \
  --assessment-summary
```

The assessment summary consolidates existing projected report content into a
shorter user-facing view:

- measurement status;
- technical analysis readiness;
- main acoustic observations;
- applicable actions;
- blocked actions;
- Evidence Acquisition Plans;
- an explicit technical notice.

It uses the finalized `Report` produced by the deterministic workflow. It does
not add a score, scientific conclusion, action or experiment.

### Full assessment

```bash
python main.py \
  --measurements-root measurements \
  --full-assessment
```

The full assessment delegates to the five detailed reporters in this order:

1. acoustic observations;
2. deterministic acoustic reasoning;
3. deterministic corrective actions;
4. deterministic evidence weighting;
5. evidence acquisition plans.

It exposes the existing cascade through one command and does not run a
different scientific workflow.

To write that exact full rendering to a new UTF-8 text file:

```bash
python main.py \
  --measurements-root measurements \
  --full-assessment \
  --full-assessment-output assessment.txt
```

`--full-assessment-output` requires `--full-assessment`. The command refuses to
overwrite an existing path and writes the same bytes to stdout and the output
file.

## Multi-experiment campaigns

A measurement root may contain a baseline and versioned experiments. The
standard CLI path discovers the available experiments and performs the existing
comparison workflow when applicable; there is no separate comparison option.

The active repository campaign contains only `measurements/baseline`. The
historical `baseline → exp-001 → exp-002` campaign used by integration tests is
isolated under `tests/fixtures/campaigns/historical_reference`. The following
command exposes the final diagnostic plans for a supplied multi-experiment
campaign:

```bash
python main.py \
  --measurements-root measurements \
  --evidence-acquisition
```

The same final campaign state can be viewed concisely with
`--assessment-summary` or in detail with `--full-assessment`.

## Accept an eligible positioning proposal

When the deterministic report exposes a currently eligible loudspeaker
positioning proposal, the user may explicitly accept its exact identifier and
declare the intended experiment through the public CLI:

```bash
python main.py \
  --measurements-root /path/to/my-campaign \
  --accept-positioning-proposal EXACT_PROPOSAL_ID \
  --positioning-experiment-id exp-007 \
  --positioning-reference exp-006 \
  --positioning-declaration-note "Accepted reversible positioning test."
```

The command recalculates eligibility and rejects an unknown or stale proposal.
On success it creates only the existing controlled-experiment declaration for
the explicitly supplied experiment and reference. Accepting the proposal does
not move a loudspeaker, run an acquisition or experiment, interpret a result,
or establish causality. The physical change and measurements remain separate
user actions.

## Explicit campaign declarations

To provide an explicit, versioned multi-position campaign instance:

```bash
python main.py \
  --measurements-root /path/to/my-campaign \
  --listening-position-campaign /path/to/listening-position-campaign.json
```

The JSON file is read only. AcousticBrain validates its protocol, positions,
offsets, relations, measurements, controlled variables and requested existing
reference before producing a campaign plan. It never creates an experiment or
fills in missing geometry. The file in
[`docs/examples/listening-position-campaign.example.json`](docs/examples/listening-position-campaign.example.json)
is an editable illustration and is never activated automatically.

To qualify the exact existing experiment requested by that campaign:

```bash
python main.py \
  --measurements-root /path/to/my-campaign \
  --listening-position-campaign /path/to/listening-position-campaign.json \
  --campaign-reference-qualification /path/to/reference-qualification.json
```

The qualification is cross-checked against the observed experiment, its real
channels, historical declaration, local comparison, protocol and campaign
instance. It never replaces the requested experiment or rewrites historical
facts. The example at
[`docs/examples/campaign-reference-qualification.example.json`](docs/examples/campaign-reference-qualification.example.json)
is documentation only and is never loaded automatically.

## Optional LLM Advisor

The Advisor is an optional, read-only consumer of deterministic report objects:

```bash
python main.py \
  --measurements-root measurements \
  --advisor \
  --advisor-provider mock \
  --question "Why is this action blocked?"
```

The deterministic Mock provider works without network access. Ollama and OpenAI
are explicit provider choices and may use their configured endpoints. Provider
responses are validated before normal rendering. The Advisor does not create or
modify scientific knowledge. See
[`docs/OPTIONAL_LLM_ADVISOR.md`](docs/OPTIONAL_LLM_ADVISOR.md).

Ollama is not required to install, import or run AcousticBrain's deterministic
engine. The V1 Ollama Advisor uses its explicitly configured HTTP endpoint and
does not require the Python `ollama` package. The legacy `AcousticAssistant`
integration loads that package only when an LLM answer is explicitly requested;
install it separately with `python -m pip install ollama` if that legacy
integration is needed.

## Scientific governance

The documented outputs expose results produced by existing deterministic
rules. CLI reporters and the optional Advisor do not add, replace or bypass
those rules. Scientific conclusions, contradictions, limitations and missing
evidence remain under the authority of the deterministic core.

The frozen product contract for the deterministic V1 `EXPLORATORY` mode is
documented in
[`docs/EXPLORATORY_V1_CONTRACT.md`](docs/EXPLORATORY_V1_CONTRACT.md).
It defines bounded reversible tests, explicit user feasibility decisions and
non-causal result semantics.

Analyze an explicit proposal without modifying measurements or decisions:

```bash
python main.py \
  --measurements-root measurements \
  --exploratory \
  --exploratory-proposal /path/to/exploratory-proposal.json \
  --exploratory-decisions /path/to/exploratory-decisions.json
```

The proposal document must provide structured action parameters and exact
reference provenance. Free-form notes are never parsed to reconstruct missing
parameters. A documented shape is available in
[`docs/EXPLORATORY_V1_PROPOSAL_INPUT.example.json`](docs/EXPLORATORY_V1_PROPOSAL_INPUT.example.json).

Record the answer with a separate explicit command, using the identifiers
printed by the read-only analysis:

```bash
python main.py \
  --record-exploratory-feasibility FEASIBLE \
  --exploratory-decisions /path/to/exploratory-decisions.json \
  --exploratory-proposal-id PROPOSAL_ID \
  --exploratory-reference-scope-id REFERENCE_SCOPE_ID
```

Once the same analysis reports `EXPLORATORY_READY`, an existing acquisition
directory can be declared explicitly with
`--declare-exploratory-experiment EXPERIMENT_ID`. This writes declaration
metadata to its manifest; it never executes an acquisition or modifies a
measurement file.

## Complete one blocked evidence-acquisition plan

Completion requires an explicit structured input and a dedicated registry. For
a protocol reference, also provide the existing validated campaign instance
that declares that exact protocol:

```bash
python main.py \
  --measurements-root measurements \
  --listening-position-campaign campaign-instance.json \
  --complete-evidence-plan completion-input.json \
  --evidence-plan-completion-registry state/evidence-plan-completions.json
```

Minimal input:

```json
{
  "schema_version": 1,
  "completion_input_id": "completion-input-001",
  "source_plan_id": "EXACT_BLOCKED_PLAN_ID",
  "reference_kind": "PROTOCOL",
  "reference_id": "EXACT_COMPATIBLE_PROTOCOL_ID",
  "declaration_source": "completion-input.json"
}
```

The command succeeds only when the source, reference and existing structured
compatibility authority resolve exactly. It records `REFERENCE_RESOLVED`,
`REFERENCE_COMPATIBLE` and `DERIVED_PLAN_READY` atomically. It does not modify
the source plan, measurements, manifests or protocol declaration, and it does
not declare or execute an experiment.

## Preserve an evidence-acquisition plan contract

A `READY` evidence-acquisition plan can be declared as an experiment without
losing its objective, variables, prerequisites, expected observations,
criteria, limitations or provenance:

```bash
python main.py \
  --measurements-root measurements \
  --declare-evidence-plan-experiment exp-XXX \
  --evidence-plan-id PLAN_ID \
  --evidence-plan-reference baseline
```

For a `READY` plan created by evidence-plan completion, provide its dedicated
registry explicitly; the same declaration service and manifest contract are
used:

```bash
python main.py \
  --measurements-root measurements \
  --evidence-plan-completion-registry state/evidence-plan-completions.json \
  --declare-evidence-plan-experiment exp-XXX \
  --evidence-plan-id DERIVED_EVIDENCE_ACQUISITION_ID \
  --evidence-plan-reference baseline
```

This extends the existing plan → declaration → comparison pipeline; it does not
introduce a parallel engine. See
[`docs/EVIDENCE_ACQUISITION_PLAN_CONTRACT_PRESERVATION.md`](docs/EVIDENCE_ACQUISITION_PLAN_CONTRACT_PRESERVATION.md).

For a `CHANNEL_ISOLATION` plan that passed the explicit preparation preflight,
preserve that preparation and the specialized declared acquisition structure:

```bash
python main.py \
  --measurements-root measurements \
  --declare-evidence-plan-experiment exp-XXX \
  --evidence-plan-id PLAN_ID \
  --evidence-plan-reference baseline \
  --evidence-plan-declaration-preparation-registry state/evidence-plan-preparations.json \
  --evidence-plan-declaration-preparation CONFIRMATION_ID
```

The preflight runs before the target directory is created. This declaration
still performs no acquisition. See
[`docs/CHANNEL_ISOLATION_QUALIFIED_DECLARATION_CONTRACT.md`](docs/CHANNEL_ISOLATION_QUALIFIED_DECLARATION_CONTRACT.md).

After that qualified declaration, inspect the acquisition stage without
inferring execution from the new directory or manifest:

```bash
python main.py \
  --measurements-root measurements \
  --guided-status \
  --guided-preparation-registry state/evidence-plan-preparations.json \
  --guided-preparation CONFIRMATION_ID \
  --guided-declared-experiment exp-XXX
```

Without `--guided-declared-experiment`, the same guided view lists any
experiments carrying the exact selected preparation and asks for an explicit
identifier. It never selects by recency, lifecycle state, or because only one
candidate exists.

The view preserves `ACQUISITION_PENDING`, `ACQUISITION_INCOMPLETE` and
`COMPARISON_UNAVAILABLE` exactly. The last state means only that the declared
specialized acquisition is complete and no unique local comparison is
available. When a unique comparable local comparison already exists, the same
view preserves `RESULT_INCONCLUSIVE` or `RESULT_AVAILABLE` and its exact
observed outcome. The view performs no measurement, creates no comparison and
derives no verdict. See
[`docs/GUIDED_DECLARED_CHANNEL_ISOLATION_CONTRACT.md`](docs/GUIDED_DECLARED_CHANNEL_ISOLATION_CONTRACT.md).

`ADDITIONAL_OBSERVATION` plans keep pre-acquisition inputs disjoint from the
evidence they are intended to acquire. The corrected SBIR plan uses a versioned
V2 identity so historical contracts are never rewritten. See
[`docs/ADDITIONAL_OBSERVATION_PLAN_CONTRACT.md`](docs/ADDITIONAL_OBSERVATION_PLAN_CONTRACT.md).
Its user view keeps execution unavailable until an exact SBIR protocol instance
declares the speaker, surface, geometry candidate, displacement and reference.
The frozen structured-input contract for that recorded instance is documented in
[`docs/SBIR_PROTOCOL_INSTANCE_INPUT_CONTRACT.md`](docs/SBIR_PROTOCOL_INSTANCE_INPUT_CONTRACT.md).

List the exact structured sources first, without selecting or recommending one:

```bash
python main.py \
  --measurements-root MEASUREMENTS_ROOT \
  --sbir-protocol-instance-sources
```

After independently preparing `INPUT_JSON`, preview its exact source resolution
and compatibility, record it through a separate explicit action, then view the
persisted snapshot by its exact `INSTANCE_ID`:

```bash
python main.py \
  --measurements-root MEASUREMENTS_ROOT \
  --preview-sbir-protocol-instance INPUT_JSON \
  --sbir-protocol-instance-registry REGISTRY_JSON

python main.py \
  --measurements-root MEASUREMENTS_ROOT \
  --record-sbir-protocol-instance INPUT_JSON \
  --sbir-protocol-instance-registry REGISTRY_JSON

python main.py \
  --measurements-root MEASUREMENTS_ROOT \
  --sbir-protocol-instance-view INSTANCE_ID \
  --sbir-protocol-instance-registry REGISTRY_JSON
```

Preview is read-only. Record persists only the validated protocol-instance
snapshot: record is not an experiment declaration, experiment execution, or
causal conclusion. View rereads only that recorded snapshot and does not
reinterpret the current measurement corpus.

The explicit contract for declaring the missing room geometry is frozen in
[`docs/SBIR_ROOM_GEOMETRY_DECLARATION_CONTRACT.md`](docs/SBIR_ROOM_GEOMETRY_DECLARATION_CONTRACT.md).

Show the exact measurements and quality declarations required without
inventing or recording coordinates:

```bash
python main.py \
  --measurements-root measurements \
  --sbir-room-geometry-guide
```

Once a canonical input JSON has been independently measured and prepared,
preview it first and record it only with the separate explicit command:

```bash
python main.py --measurements-root measurements \
  --preview-sbir-room-geometry room-geometry.json
python main.py --measurements-root measurements \
  --declare-sbir-room-geometry room-geometry.json
```

## Tests

Run the complete test suite:

```bash
pytest
```

Run the CLI-focused tests:

```bash
pytest tests/test_main_cli.py \
  tests/test_full_assessment_console.py \
  tests/test_full_assessment_text_export.py \
  tests/test_analysis_readiness_report.py \
  tests/test_assessment_summary_report.py
```
