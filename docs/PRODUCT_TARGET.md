# AcousticBrain product target

```text
status = FROZEN_FOR_V1_PRODUCT_DIRECTION
authority = PRODUCT_SCOPE
scientific_authority = NONE
```

## Product promise

AcousticBrain helps a person place their left and right loudspeakers through
reversible, measurement-guided experiments.

It must answer, in human language:

1. what the current measurements allow or do not allow about placement;
2. whether a speaker move is currently justified as a controlled test;
3. when it is justified, which speaker, direction and distance the existing
   deterministic proposal specifies, and how to verify it;
4. when it is not justified, the one missing piece of evidence that prevents a
   placement test.

The target is not a general scientific laboratory interface. Scientific
contracts, manifests, registries and reports exist to make this user journey
reliable; they are not the primary product experience.

## Primary user journey

```text
REW measurements
→ placement status in plain language
→ either no move is justified, or one reversible measured move is proposed
→ explicit declaration of that controlled test
→ user performs the measurement
→ deterministic comparison
→ readable result: keep investigating, revert, or collect further evidence
```

Every visible movement remains an experiment. A proposed move is not a
permanent correction, a guaranteed improvement, an optimum, or an established
acoustic cause.

## Definition of a useful product

The placement product is useful when a non-specialist can complete the primary
journey without needing to understand internal identifiers, manifests,
registries, evidence-plan types or source-code commands.

At each state, the public interface must present:

- the current placement state;
- the reason for that state using only established facts;
- exactly one next safe action when one exists;
- a copyable public `main.py` command when a command is needed;
- the scientific limit that prevents a stronger conclusion.

## Product boundaries

AcousticBrain does not currently promise:

- a final or optimal speaker position;
- an automatic physical move;
- a causal explanation not established by the current contract;
- a treatment, EQ or room-correction recommendation outside a verified
  placement experiment;
- a second placement engine separate from the existing deterministic analysis,
  geometry, eligibility, proposal, declaration and comparison contracts.

## Development gate

Before a new feature or PR is started, it must answer all of the following:

1. Which step of the primary user journey does it make clearer, safer or
   executable?
2. Does it reuse an existing scientific authority rather than create a parallel
   workflow or recommendation path?
3. Can its user-facing outcome be demonstrated from `main.py`?

If the change cannot answer the first question, it is deferred. New analyses,
metrics, models, workflows or Advisor capabilities are not sufficient reasons
on their own to expand the product.

## Architectural rule

The human-facing placement experience may only project existing deterministic
outputs. It may not recalculate placement eligibility, generate a displacement,
select a candidate, relax uncertainty limits, write a manifest implicitly or
promote a measured association to causality.

This rule keeps the product focused while preserving the architecture already
built for repeatability and scientific restraint.
