# Deterministic Acoustic Reasoning

## Scientific boundary

The deterministic chain is:

`analysis -> observation -> reasoning -> action`

- An analysis is a technical result calculated from measurements.
- An observation is a descriptive synthesis of established analysis facts.
- A reasoning is an explicit chain from structured premises to a bounded
  conclusion.
- An action is an intervention or experiment and remains outside PR-055.

PR-055 consumes PR-054 observation objects in memory. It never reads REW files,
reconstructs an analysis, creates a hypothesis, proposes an action, changes a
campaign or uses an LLM.

## Initial rule set

The first rule is
`EXPLAIN_EXISTING_HYPOTHESIS_FROM_OBSERVATIONS_V1`. It may explain only one of
the four hypothesis identifiers already defined by AcousticBrain. A fixed map
links each existing hypothesis to relevant PR-054 observations. The output
keeps observation premises, the existing hypothesis premise, optional causal
and longitudinal premises, the applied rule, inference step, evidence on both
sides, limitations and upstream source ids.

One observation or an observation without confidence yields
`INSUFFICIENT_EVIDENCE`. Explicit observation conflicts, a contradictory causal
outcome or conflicting longitudinal evidence yield `CONTRADICTORY_EVIDENCE`.
An inconclusive causal result or existing inconclusive hypothesis yields
`NON_DISCRIMINATED`. Otherwise the rule projects the existing hypothesis status
as `SUPPORTED`, `PARTIALLY_SUPPORTED` or `CONTRADICTED`; it does not strengthen
or replace that status.

Confidence is the minimum of the confidence already exposed by the existing
hypothesis and available source observations. This deliberately conservative,
replaceable rule is not the general evidence weighting planned for PR-057.

## Determinism and CLI

Rules and hypothesis mappings use explicit tuple order. Evidence is deduplicated
without sets, inference steps reference stable premise ids, and identical input
objects produce identical objects and report bytes.

```bash
python main.py --measurements-root /path/to/campaign --reasoning
```

`--reasoning` synthesizes PR-054 observations internally and prints a dedicated
reasoning report. `--observations` alone and the historical CLI without either
option are unchanged. All modes are read-only.
