# Causal protocol step declaration contract

## Purpose and scope

`experiment_declaration` and `causal_protocol_step` describe two different user
declarations.

- `experiment_declaration` records the general experimental intervention: its
  reference, modified variables, controlled variables, and optional user note.
- `causal_protocol_step` records that one named step of a supported causal
  protocol was executed, together with its declared variables and any causal
  observations explicitly qualified by the user.

Declaring an executed step does not declare its result. An empty
`observation_codes` list means that the step was executed but its causal
observation has not yet been qualified. AcousticBrain must not infer an
observation from measurements, variable names, or the selected step.

## Supported protocol and steps

This declaration boundary supports only
`VERIFY_SPEAKER_ROOM_ASYMMETRY`:

| Step | Index | Required changed variables | Required controlled variables |
| --- | ---: | --- | --- |
| `STEP_0_BASELINE` | 0 | none | `MEASUREMENT_LEVEL`, `ROOM_CONFIGURATION` |
| `STEP_1_LEFT_RIGHT_REMEASUREMENT` | 1 | `MEASUREMENT_ACQUISITION` | `LOUDSPEAKER_ASSIGNMENT`, `MICROPHONE_POSITION`, `ROOM_SIDE`, `SIGNAL_CHAIN_ASSIGNMENT` |
| `STEP_2_SPEAKER_SWAP` | 2 | `LOUDSPEAKER_ASSIGNMENT` | `ROOM_SIDE`, `SIGNAL_CHAIN_ASSIGNMENT` |
| `STEP_3_SIGNAL_CHAIN_SWAP` | 3 | `SIGNAL_CHAIN_ASSIGNMENT` | `LOUDSPEAKER_ASSIGNMENT`, `ROOM_SIDE` |

Changed, controlled, and unknown variables must be pairwise disjoint. Additional
variables may be declared when they remain consistent with the general
experiment declaration.

## Explicit observations

Zero or more observations may be supplied. Every code must be known by the
existing discrimination rules and belong to the declared step. Unknown codes
and codes belonging to another step are rejected.

- `STEP_0_BASELINE`: `ANOMALY_NOT_REPRODUCIBLE`.
- `STEP_1_LEFT_RIGHT_REMEASUREMENT`:
  `LEFT_RIGHT_DIFFERENCE_REPRODUCIBLE`,
  `CHANNEL_SPECIFIC_PATTERN_CHANGED`, `CHANNEL_SPECIFIC_PATTERN_STABLE`, or
  `ANOMALY_NOT_REPRODUCIBLE`.
- `STEP_2_SPEAKER_SWAP`:
  `ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER`,
  `ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SPEAKER_SWAP`, or
  `ANOMALY_NOT_REPRODUCIBLE`.
- `STEP_3_SIGNAL_CHAIN_SWAP`:
  `ANOMALY_MOVED_WITH_SWAPPED_SIGNAL_CHAIN`,
  `ANOMALY_REMAINED_WITH_LOUDSPEAKER_AFTER_SIGNAL_CHAIN_SWAP`,
  `ANOMALY_REMAINED_WITH_LOUDSPEAKER_OR_ROOM_SIDE_AFTER_SIGNAL_CHAIN_SWAP`,
  `ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SIGNAL_CHAIN_SWAP`, or
  `ANOMALY_NOT_REPRODUCIBLE`.

The command treats the supplied observations as the complete desired set. A
later invocation replaces the previous set; there is no implicit merge. Thus,
invoking the command without `--observation` explicitly stores an empty list.
Repeating the same command produces byte-identical JSON and does not rewrite
the manifest.

The optional `--note` is an explicit update to the existing
`experiment_declaration.user_note`; it is never added to the causal step model.
It therefore requires an existing experiment declaration.

## Coherence with the experiment declaration

When a non-`UNKNOWN` `experiment_declaration` exists:

- causal changed variables must exactly match `modified_variables`;
- every causal controlled variable must already be declared controlled;
- a causal unknown variable must not be declared modified or controlled.

An inconsistency is rejected. The service never changes the experiment kind,
reference, or declared variables. Apart from an explicitly supplied `--note`,
the general experiment declaration is preserved byte-for-byte as JSON data.

## Persistence guarantees

The service requires an existing `READY` manifest. It preserves all unrelated
keys, including `comparison`, `files`, and `content_hash`. It uses the existing
manifest repository's deterministic, atomic, and idempotent save operation. No
WAV, TXT, MDAT, or other measurement file is opened for writing.

## Impact on causal discrimination

An accepted step is part of the completed protocol history. Without an explicit
observation:

- no trajectory receives support or counter-evidence from that step;
- no discrimination is resolved by that step;
- the result remains `INCONCLUSIVE`;
- the engine waits for qualification of the missing observation instead of
  recommending a later discriminating step;
- the report states that the causal observation is not yet qualified and the
  causal conclusion is not established.

No trajectory can be confirmed by this declaration service. The causal status
remains `NOT_ESTABLISHED` in the decision and longitudinal layers until their
existing evidence contracts are satisfied.

`causal_protocol_step` does not associate the automatic source comparison with
the protocol or hypothesis. That association still requires the comparison's
explicit `protocol_id` and `hypothesis_code` contract. Inferring it from the
step alone would requalify a generic intervention as hypothesis evidence, so
this declaration boundary deliberately leaves
`SOURCE_COMPARISON_UNAVAILABLE` visible when the source metadata is absent.

## Example: controlled loudspeaker swap

For an `exp-005` whose general declaration modifies
`LOUDSPEAKER_ASSIGNMENT` relative to `exp-004`, a declaration of
`STEP_2_SPEAKER_SWAP` is coherent when at least `ROOM_SIDE` and
`SIGNAL_CHAIN_ASSIGNMENT` are controlled. With no observation, the generated
manifest contains:

```json
"causal_protocol_step": {
  "changed_variable_codes": ["LOUDSPEAKER_ASSIGNMENT"],
  "controlled_variable_codes": ["ROOM_SIDE", "SIGNAL_CHAIN_ASSIGNMENT"],
  "observation_codes": [],
  "protocol_code": "VERIFY_SPEAKER_ROOM_ASYMMETRY",
  "step_code": "STEP_2_SPEAKER_SWAP",
  "step_index": 2,
  "unknown_variable_codes": []
}
```

This contract complements the PR-043 experiment declaration boundary, the
PR-045 longitudinal learning boundary, and
`CAUSAL_DISCRIMINATION_CONTRACT.md`. It does not change their eligibility,
scoring, hypothesis, or causal inference rules.
