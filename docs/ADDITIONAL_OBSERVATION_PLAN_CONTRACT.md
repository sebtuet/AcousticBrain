# Additional-observation evidence plan contract

```text
contract_id = acousticbrain.additional_observation_plan.v2
version = 2
status = FROZEN
scientific_authority = NONE
implementation_status = IMPLEMENTED_AT_PLANNING_BOUNDARY_ONLY
```

## Purpose

Prevent an `ADDITIONAL_OBSERVATION` plan from requiring, before acquisition,
the same observation that the plan exists to acquire.

```text
pre-acquisition inputs
∩
resulting evidence targets
= empty set
```

This invariant is specific to `ADDITIONAL_OBSERVATION`. Parameter-completion
plans may legitimately produce a validated version of an input they were
created to resolve and are outside this contract.

## Versioned identity

The former generated SBIR plan used:

```text
..._ACQUIRE_SUPPORTING_OBSERVATION
```

and declared `additional_supporting_observation` as both a required input and a
resulting evidence target. That historical identity is not rewritten. The
corrected current plan uses:

```text
..._ACQUIRE_SUPPORTING_OBSERVATION_V2
```

with no pre-acquisition input invented and with
`additional_supporting_observation` preserved only as a resulting evidence
target. Historical manifests and preparation records keep their original plan
identity and fingerprint; they are never migrated silently.

## Scientific and execution boundary

V2 corrects only the planning contract. It does not define an SBIR acquisition
protocol, verify geometry, declare or execute an experiment, compare results,
or establish hypothesis support or causality.

A future guided execution path must preserve this plan contract and introduce
its own explicit acquisition and comparison contract before any measurement is
claimed as evidence.

## User-view execution boundary

The plan may be `READY` while execution remains unavailable. In V2, `READY`
means only that the non-circular planning contract is complete. It does not
resolve an instance of `protocol.temporary_move_speaker.v1`.

Until existing structured sources provide all of the following, the user view
must expose no declaration or execution action:

- one speaker identifier;
- one surface identifier;
- one geometry-candidate identifier;
- one finite, non-zero declared displacement;
- an exact reference experiment identifier.

The view displays
`ESTABLISH_COMPATIBLE_SBIR_PROTOCOL_INSTANCE` and delegates this scientific
work to a structured source or acoustic expert. It never derives these values
from prose, geometry alone, a plan status, or an acoustic hypothesis.
