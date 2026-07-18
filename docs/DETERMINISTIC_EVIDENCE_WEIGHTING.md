# Deterministic Evidence Weighting

## Scientific boundary

```text
Observation
    ↓
Reasoning
    ↓
Corrective Action
    ↓
Evidence Weight
```

PR-057 qualifies objects that already exist. It creates no analysis,
observation, reasoning, action, hypothesis, experiment, evidence, protocol or
decision. The source objects remain authoritative and immutable.

There is deliberately no global score, average or probability. Collapsing the
dimensions would allow strong evidence to hide a contradiction, incomplete
discrimination or an unusable action. The output is therefore a vector with
independent categorical dimensions.

## Dimensions

- **Evidence Strength** qualifies the number of independent observation
  sources and their already-declared confidence. Individual frequency values
  are not counted as independent sources.
- **Source Consistency** reports whether upstream evidence contains explicit
  contradictions. It does not reduce evidence strength.
- **Discriminative Power** projects whether PR-055 has discriminated the
  conclusion. `NON_DISCRIMINATED`, `CONTRADICTORY_EVIDENCE` and
  `INSUFFICIENT_EVIDENCE` cap this dimension at `LOW`.
- **Parameter Completeness** reports known, derivable and required missing
  parameters from PR-056. Required missing parameters cap it at `LOW`.
- **Action Applicability** projects the PR-056 status. PR-057 neither authorizes
  nor blocks an action; PR-056 remains the authority.

Levels are `UNAVAILABLE`, `LOW`, `MEDIUM` and `HIGH`. They are categorical and
never converted into numbers.

## Blocking factors and ceilings

Blocking factors preserve explicit upstream state such as contradictory
evidence, missing parameters, insufficient discrimination, tested actions or
history blocks. They are separate from every other dimension.

Each cap is an immutable object with a stable id, rule id, affected dimension,
maximum level and justification. Structural validation rejects a dimension
above its cap, a missing factor for blocked applicability, a hidden
contradiction, or an upstream reference that cannot be resolved.

The initial rules are:

- `QUALIFY_EXISTING_EVIDENCE_VECTOR_V1` builds the independent vector from
  referenced objects only.
- `CAP_CONSISTENCY_ON_CONTRADICTION_V1` caps consistency at `LOW` while leaving
  strength independent.
- `CAP_POWER_WHEN_NOT_DISCRIMINATED_V1` caps discriminative power at `LOW`.
- `CAP_COMPLETENESS_ON_MISSING_PARAMETERS_V1` caps completeness at `LOW`.
- `PROJECT_EXISTING_ACTION_APPLICABILITY_V1` copies PR-056 applicability
  without changing it.

## Determinism and read-only operation

Equivalent inputs produce the same ids, order, dimensions, factors, ceilings
and report bytes. Deduplication is inherited from the upstream action layer;
PR-057 emits one vector per existing action in its stable order.

```bash
python main.py --measurements-root /path/to/campaign --weighting
```

The option composes observations, reasoning and actions in memory, then prints
only the weighting report. It performs no filesystem, campaign, measurement,
qualification, plan, action or longitudinal write.
