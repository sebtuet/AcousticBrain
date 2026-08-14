# Deterministic Acoustic Observations

## Scope

PR-054 introduces an opt-in, read-only synthesis layer:

`measurements -> deterministic analyses -> deterministic observations`

An analysis exposes calculated technical facts. An observation copies a set of
those established facts into a stable, traceable descriptive record. Reasoning
may later relate observations to explanations, and a later action layer may
propose interventions. PR-054 implements neither reasoning nor actions.

The observation layer does not create recommendations, corrective actions,
hypotheses, experiments, protocols or campaign plans. It does not use an LLM.

## Contract

Each immutable observation contains a stable id, extensible category, title,
description, confidence copied from its source analysis when available,
supporting evidence, contradicting evidence, limitations and source-analysis
identifiers. Every collection is a tuple.

The synthesizer evaluates a fixed rule order and creates an observation only
when the corresponding calculated facts exist. It does not invent missing
confidence: `UNAVAILABLE` is reported when a source analysis exposes none.
Numeric facts use stable formatting, inputs are never mutated, and identical
analyses produce identical observations in identical order.

The first rules cover measurement-quality facts, low-frequency decay, RT60,
ETC reflection-event counts, C80 clarity and stereo peak distribution. Their
outputs remain descriptive and retain contradictory or limiting source facts.

## CLI and read-only guarantee

Use the dedicated report explicitly:

```bash
python main.py --measurements-root /path/to/campaign --observations
```

The dedicated report prints observations and provenance only. Without
`--observations`, the historical CLI call and report are strictly unchanged.
The option never writes to a campaign, measurement, REW result, experiment or
declaration.
