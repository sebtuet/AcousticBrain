# AcousticBrain

AcousticBrain is a deterministic acoustic-analysis engine driven by measurement
campaigns. Its analysis pipeline produces structured results; presenters and
CLI reporters expose those results without changing the underlying scientific
rules.

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

Create and activate a virtual environment, then install the project
dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Analyze the versioned example campaign:

```bash
python main.py --measurements-root measurements
```

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
| Acoustic observations | `--observations` | Descriptive observations projected from existing analyses |
| Deterministic acoustic reasoning | `--reasoning` | Premises, inference steps, conclusions, contradictions and limitations |
| Deterministic corrective actions | `--actions` | Declarative actions, applicability, parameters and blocking conditions |
| Deterministic evidence weighting | `--weighting` | Independent evidence dimensions without a global score |
| Next recommended experiment | `--evidence-acquisition` | One selected READY acquisition plan, or why none can be recommended |
| Technical analysis readiness | `--analysis-readiness` | Existing experiment and analysis-family readiness decisions |
| Assessment summary | `--assessment-summary` | A concise projection of the main existing report objects |
| Full assessment | `--full-assessment` | The five detailed deterministic reports in workflow order |
| Experiment user view | `--experiment-view EXPERIMENT_ID` | Four-block read-only view of one exact experiment |
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

## Scientific governance

The documented outputs expose results produced by existing deterministic
rules. CLI reporters and the optional Advisor do not add, replace or bypass
those rules. Scientific conclusions, contradictions, limitations and missing
evidence remain under the authority of the deterministic core.

The frozen product contract for the future deterministic `EXPLORATORY` mode is
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
python -m acousticbrain.commands.declare_evidence_plan_experiment \
  measurements \
  --plan-id PLAN_ID \
  --experiment exp-XXX \
  --reference baseline
```

For a `READY` plan created by evidence-plan completion, provide its dedicated
registry explicitly; the same declaration service and manifest contract are
used:

```bash
python -m acousticbrain.commands.declare_evidence_plan_experiment \
  measurements \
  --completion-registry state/evidence-plan-completions.json \
  --plan-id DERIVED_EVIDENCE_ACQUISITION_ID \
  --experiment exp-XXX \
  --reference baseline
```

This extends the existing plan → declaration → comparison pipeline; it does not
introduce a parallel engine. See
[`docs/EVIDENCE_ACQUISITION_PLAN_CONTRACT_PRESERVATION.md`](docs/EVIDENCE_ACQUISITION_PLAN_CONTRACT_PRESERVATION.md).

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
