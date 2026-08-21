# Repeatability evaluation band contract

## Scope

`repeatability_contract.v1` applies only to the two explicitly labelled A/B
captures of a declared `CHANNEL_ISOLATION` experiment. It is a deterministic
numerical projection; it does not modify observations, reasoning, hypotheses,
actions, evidence weights, experiment manifests, or causal status.

## Default convention

| Field | Default |
| --- | --- |
| Contract identifier | `repeatability_contract.v1` |
| Evaluation band | 40–200 Hz, inclusive |
| Threshold | 3 dB, inclusive |

The 40 Hz lower bound is an operational convention for a typical domestic
measurement system. It makes the numerical comparison explicit where the
operator has chosen to evaluate repeatability; it is not a general acoustic
claim about every microphone, loudspeaker, room, or frequency below 40 Hz.
The upper bound confines this first contract to the bass band relevant to this
controlled channel-isolation workflow.

For each channel, the projection calculates the maximum absolute A/B SPL
difference inside the declared inclusive band. If both LEFT and RIGHT values
are at or below the threshold, the status is
`REPEATABILITY_ACCEPTABLE_IN_BAND`. If either is above it, the status is
`REPEATABILITY_UNCERTAIN`. If a value cannot be calculated, the status is
`NOT_EVALUABLE`.

The left/right-difference metric remains descriptive and is deliberately not a
criterion of this V1 contract.

## Scientific boundary

An acceptable numerical result does not prove physical stability of the
microphone, loudspeakers, listening position, or room. An unchanged-position
statement remains a user declaration and is not independently verified. The
projection always carries `Causality status: NOT_ESTABLISHED`.

It is intentionally not connected to any existing hypothesis, reasoning,
action, evidence weighting, experiment execution, or placement recommendation.
Such a connection requires a separately reviewed scientific contract and a
separate implementation.

## Revision

A change to the band, threshold, or decision rule must introduce a new
versioned contract identifier and preserve the identifier alongside any result.
The application exposes the contract as immutable configuration, so a caller
can evaluate an explicit alternative configuration without modifying the
calculation code. A revision must document its scope, inclusive/exclusive
boundaries, and the reason it does not reinterpret prior results.
