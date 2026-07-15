# Explicit experiment declaration contract

## Purpose

An experiment may explicitly declare whether it is a controlled intervention,
a measurement repeat, or unknown. The declaration documents user knowledge; it
does not judge the acoustic result, measurement error, or repeatability.

## Manifest schema

`manifest.json` may contain this versioned block:

```json
{
  "experiment_declaration": {
    "schema_version": 1,
    "experiment_kind": "MEASUREMENT_REPEAT",
    "reference_experiment_code": "exp-005",
    "modified_variables": ["MEASUREMENT_ACQUISITION"],
    "controlled_variables": [
      "LISTENING_POSITION",
      "LOUDSPEAKER_POSITION",
      "MEASUREMENT_LEVEL",
      "MICROPHONE_POSITION",
      "REW_MEASUREMENT_PARAMETERS",
      "ROOM_CONFIGURATION"
    ],
    "user_note": "Répétition à configuration inchangée.",
    "field_provenance": {
      "controlled_variables": "USER_CLI",
      "experiment_kind": "USER_CLI",
      "modified_variables": "USER_CLI",
      "reference_experiment_code": "USER_CLI",
      "user_note": "USER_CLI"
    }
  }
}
```

Allowed kinds are `CONTROLLED_INTERVENTION`, `MEASUREMENT_REPEAT`, and
`UNKNOWN`. A historical manifest without the block is read as `UNKNOWN` and is
not rewritten merely to add that default.

For `MEASUREMENT_REPEAT`, the only modified variable is
`MEASUREMENT_ACQUISITION`. Every other controlled variable must be explicitly
listed; AcousticBrain does not infer controls from the kind alone. Modified and
controlled variables are disjoint, normalized into deterministic sorted lists,
and retain field-by-field provenance.

## CLI

The real `exp-006` declaration can be written without editing measurement files:

```text
python -m acousticbrain.commands.declare_experiment measurements \
  exp-006 \
  --kind MEASUREMENT_REPEAT \
  --reference exp-005 \
  --note "Même position d’écoute, mêmes enceintes, configuration inchangée."
```

When repeat variables are omitted, this command explicitly writes the repeat
defaults shown above. Advanced callers may repeat `--controlled-variable` and
`--modified-variable` to provide their own explicit declaration.

Persistence reuses `MeasurementRepository.save_manifest`: serialization is
sorted, writes use a temporary file followed by atomic replacement, and an
identical manifest is not rewritten.

## Scientific limits

The declaration is propagated to the existing comparison and report
projections. It does not change deltas, acoustic outcomes, hypothesis outcomes,
scores, rankings, diagnostics, or recommendations. In particular:

- different values in a repeat are not automatically measurement errors;
- an unchanged configuration does not prove satisfactory repeatability;
- no undeclared variable is presented as controlled;
- differences are not attributed to a placement change;
- causal status remains `NOT_ESTABLISHED`.
