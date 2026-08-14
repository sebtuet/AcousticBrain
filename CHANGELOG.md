# Changelog

## 1.0.1

Documentation-only clarification of the public terminology `_V2`, `READY`,
and `SUPPORTED`. No runtime, CLI, planning, eligibility, scientific rule,
persisted identifier, schema, protocol, manifest, registry, or contract
fingerprint changes in this release. See the user-facing terminology section
in [`README.md`](README.md).

## 1.0.0

AcousticBrain V1 provides a deterministic, contract-driven workflow for
inspecting and preparing acoustic measurement campaigns.

### Included in V1

- import and deterministic analysis of REW measurement campaigns, including
  frequency-response and impulse-response data;
- structured acoustic diagnostics, observations, reasoning, evidence
  weighting, traceability, and explicit limitations;
- room-mode, SBIR, temporal, spatial, measurement-quality, and readiness
  analyses where their required inputs are available;
- public guided workflows through `main.py`, including global status and
  read-only views of experiments and evidence plans;
- deterministic evidence plans, explicit preparation confirmation, operational
  worksheet review, readiness checks, and qualified declarations;
- the `CHANNEL_ISOLATION` workflow with explicit documentation and result
  boundaries;
- deterministic loudspeaker-positioning proposals and explicit acceptance of
  a currently eligible proposal;
- explicit preview, recording, and snapshot-only re-reading of compatible SBIR
  protocol instances;
- explicit experiment, preparation, feasibility, geometry, and protocol-input
  declarations where exposed by their V1 contracts;
- strict separation between the deterministic scientific engine and the
  optional read-only LLM Advisor; Ollama is optional and is not a deterministic
  runtime dependency;
- a reproducible source installation path with separated runtime and
  development dependencies and an explicit Python 3.10-or-newer requirement;
- a centralized public V1 CLI through `main.py`; technical contract adapters
  remain internal;
- comprehensive automated tests, deterministic serialization checks,
  idempotence checks, read-only guarantees, and scientific non-inference
  guards.

### Scientific boundaries

V1 does not automatically provide or perform:

- causal conclusions when causality is not established by the applicable
  evidence contract;
- physical execution of experiments or measurement acquisition;
- physical loudspeaker movement;
- Bayesian optimization;
- machine learning;
- `PRESCRIPTIVE` operation;
- three-dimensional reconstruction.

Declarations, proposals, compatibility decisions, and recorded snapshots do
not by themselves constitute measured evidence, execution, or causality.
