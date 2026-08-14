# Deterministic Corrective Actions

## Boundary

The deterministic chain is:

`analysis -> observation -> reasoning -> corrective action`

An action is a declarative proposal derived from a structured PR-055 reasoning.
It is not executed. PR-056 does not create an experiment, campaign, protocol,
plan, geometry, EQ setting or material purchase, and it does not use an LLM.

## Rules

`MAP_BOUNDED_REASONING_TO_DECLARATIVE_ACTION_V1` is the only initial rule.

- `SUPPORTED` may produce a controlled measurement only when an existing
  compatible protocol or plan is referenced; otherwise it is blocked.
- `PARTIALLY_SUPPORTED` and `NON_DISCRIMINATED` permit only conditional data
  collection or discrimination, never a strong correction.
- `CONTRADICTORY_EVIDENCE` produces a contradiction-blocked deferment.
- `INSUFFICIENT_EVIDENCE` produces only a missing-evidence deferment.
- `CONTRADICTED` preserves the current configuration and requires no action.

Compatibility is explicit: causal protocols apply only to the existing
asymmetry hypothesis, listening-position sampling contracts only to modal-bass
reasoning, and controlled-reflection proposals only to early-reflection
reasoning. SBIR receives no implicit contract.

Each action copies reasoning, observation and upstream analysis ids. Known
parameters contain identifiers from existing contracts only. Derivable,
required-but-missing, and forbidden-to-invent parameters are separate immutable
fields. Missing identifiers remain explicit; distances, angles, gains, Q values
and frequencies are never invented. Existing tested or invalidated action ids
change applicability to `ALREADY_TESTED` or `BLOCKED_BY_HISTORY`.

## Scientific rule review

| PR-055 conclusion | Permitted declaration | Blocking condition | Required parameter | Proportionality and history |
| --- | --- | --- | --- | --- |
| `SUPPORTED` | controlled evaluation | contradiction, or no compatible contract | existing protocol or ready plan id | remains a measurement declaration; tested/invalidated action ids override it |
| `PARTIALLY_SUPPORTED` | conditional measurement | no compatible contract | existing protocol or ready plan id | never promoted to a correction; history override applies |
| `NON_DISCRIMINATED` | discrimination measurement | no compatible contract | existing protocol or ready plan id | priority denotes prerequisite discrimination only; history override applies |
| `CONTRADICTORY_EVIDENCE` | defer action | contradiction is preserved as the block | none | does not choose between conflicting evidence |
| `INSUFFICIENT_EVIDENCE` | defer action | missing additional observation | additional structured observation | does not propose a direct correction |
| `CONTRADICTED` | preserve configuration | none | none | explicitly records that no correction is supported |

The stage accepts only target-compatible contracts already present in context.
A blocked campaign plan is not compatible: only a `READY` plan may supply its
identifier. The rule has no geometry, material, product, position, frequency,
gain, Q, or treatment value from which it could synthesize an implicit setting.

Equivalent action identity is based on type, target and referenced contracts.
Sources, justifications, contradictions and limitations are merged in stable
input order. Confidence is the minimum source-reasoning confidence and never
exceeds it. This is deliberately separate from PR-057 weighting.

## CLI and read-only guarantee

```bash
python main.py --measurements-root /path/to/campaign --actions
```

`--actions` composes observations and reasoning in memory, then prints only the
dedicated action report. Historical mode, `--observations` and `--reasoning`
remain unchanged. The engine produces objects only and performs no filesystem,
REW, audio, campaign, qualification, plan or longitudinal write.
