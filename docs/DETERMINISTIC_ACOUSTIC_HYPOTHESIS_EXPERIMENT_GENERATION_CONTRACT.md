# Deterministic acoustic hypothesis and experiment generation contract

## Purpose

`AcousticHypothesisExperimentGenerator` is an exploratory, deterministic layer. It reads existing AcousticBrain analyses and proposes testable hypotheses and reversible experiments. It does not parse or recalculate REW data, validate a cause, alter an acoustic score, or replace comparison and causal-discrimination services.

Every generated hypothesis and experiment carries `causality_status = NOT_ESTABLISHED`. A generated test describes information that could be learned; it never promises an acoustic improvement.

## Separation from validation

Generation answers: “What simple test could distinguish the remaining explanations?” Validation remains the responsibility of structured experiment declarations, controlled-variable checks, comparisons, causal discrimination, and longitudinal learning. A `SUPPORTING` expected observation is a future test outcome, not a confirmed cause.

## Supported hypotheses

Only these existing reasoning hypotheses are projected:

- `SBIR_PLACEMENT_INTERACTION`;
- `DOMINANT_EARLY_REFLECTION_INTERACTION`;
- `ASYMMETRIC_SPEAKER_ROOM_INTERACTION`;
- `MODAL_BASS_PERSISTENCE`.

Existing reasoning statuses are conservatively projected as `PLAUSIBLE`, `WEAKLY_PLAUSIBLE`, `INSUFFICIENT_EVIDENCE`, or `CONTRADICTED`. A related prior `MIXED` temporary-treatment result can only weaken a reflection hypothesis. It cannot refute or confirm it.

## Supported experiments

The model enumerates the PR-048 allow-list:

- longitudinal moves for left, right, or both speakers, forward or backward;
- left, right, or both toe-in increase/decrease;
- temporary absorption at left/right first-reflection, front-wall, or rear-listening areas;
- listening-position forward/backward or multi-point measurements.

The first implementation emits only the subset for which explicit rules exist. It emits no toe-in proposal. Causal speaker and signal-chain swaps remain outside this generator because they are not in the PR-048 experiment allow-list and are already handled by causal protocols.

## Generation rules

### SBIR

A concrete move requires an existing geometry-to-dip correlation, a known speaker, a front-wall relationship, and an exploitable measured dip. The movement amplitude is copied without transformation only from the source hypothesis verification-action parameter `proposed_displacement_m`. If that positive structured parameter is absent, the candidate has `step_distance_m = None`, is blocked by `STRUCTURED_STEP_DISTANCE_UNAVAILABLE`, and cannot become the main recommendation. The generator has no `0.05 m` or `0.10 m` fallback.

An expected frequency region is emitted only when the correlated geometry candidate provides `frequency_uncertainty_hz`; its bounds are the measured frequency plus or minus that source uncertainty. Without it, `expected_frequency_regions` is empty. The generator applies no implicit absolute or percentage window.

### Dominant early reflection

A temporary treatment requires an accepted material-aware geometry candidate that resolves to exactly one supported room surface. The expected effect is a localized ETC-event change, possibly accompanied by local D/R or clarity changes. Floor, ceiling, unknown surfaces, and unlocalized massive treatment are refused. An expected time region is emitted only when the associated geometry path provides `uncertainty_ms`; its bounds are the theoretical delay plus or minus that source uncertainty. Without it, `expected_time_regions` is empty and no default timing window is created.

### Speaker/room asymmetry

The hypothesis remains visible when supported by existing reasoning. Completed causal discrimination is recorded as uncertainty context and never triggers a repeated swap. A localized one-sided reflection test may explicitly serve both reflection and asymmetry hypotheses; this multi-purpose relation is identified by `MULTI_PURPOSE_ASYMMETRY_TEST`. Without a safe localized or directional rule, the hypothesis is retained without an invented experiment.

### Modal persistence

A multi-position listening-area candidate is generated only when the projected modal hypothesis is `PLAUSIBLE` or `WEAKLY_PLAUSIBLE`, a targeted modal-density band or exploitable bass-decay band exists, and that test has not already been executed. `INSUFFICIENT_EVIDENCE` and `CONTRADICTED` modal hypotheses are ineligible even when bands are present. No speaker displacement is generated from modal evidence alone.

Direct executability additionally requires an explicitly supplied, structurally complete `ListeningPositionSamplingProtocol`. The generator consumes that protocol without reconstructing positions from discovered experiments or manifests. Position codes, roles, longitudinal/lateral/vertical offsets, parents, reference, acquisition order, LEFT/RIGHT/STEREO requirements, controlled variables, version, comparability rule and completion conditions are projected unchanged. The dedicated scientific contract is `LISTENING_POSITION_SAMPLING_PROTOCOL_CONTRACT.md`.

If no complete structured geometry exists, the candidate remains visible with no positions or offsets and is blocked by `MULTI_POSITION_SAMPLING_GEOMETRY_UNAVAILABLE`. It cannot be the main experiment.

## Refusal rules

Generation refuses or omits a concrete experiment when any required relation is absent, including:

- no reasoning analysis or no supported/contextual evidence;
- no correlated SBIR speaker, surface, or safe longitudinal direction;
- no accepted and representable reflection surface;
- a toe-in change without a dedicated directional rule;
- a floor/ceiling or multi-surface treatment outside the allow-list;
- a prior identical experiment;
- a prior identical inconclusive or `MIXED` experiment without new structural information;
- an already discriminated causal swap;
- a proposal that would modify more than one variable;
- a modal hypothesis with insufficient or contradicted evidence, or without a targeted measured band;
- a multi-position candidate without a complete source-declared sampling geometry;
- missing LEFT, RIGHT, or STEREO measurements.

Room geometry can represent front/rear/left/right walls, floor, ceiling, openings, speakers, listening positions, orientations, materials, covering zones, furniture, and treatments. Mere representability is not evidence: absent positioned speakers or surface correlations still blocks generation.

## Deterministic ranking

Candidate information value uses rule `PR048_DETERMINISTIC_INFORMATION_RANKING_V1`:

- 35 points for a structured candidate;
- 15 for being unblocked;
- 10 for high reversibility, otherwise 5;
- 10 for easy difficulty, otherwise 5;
- 5 per explicit expected outcome, capped at 20;
- 10 for a structured frequency or time region.

Scores are capped at 100. A blocked candidate receives no 15-point unblocked contribution. Ties are resolved by experiment-type code and candidate ID. This is a deterministic utility ordering, not a probability and not a pseudo-Bayesian confidence. At most five hypotheses and five experiments are returned; at most one eligible experiment is recommended.

## Deduplication

Experiment declarations and declared change codes are normalized to the supported experiment types. Exact type/target/distance duplicates are collapsed. Existing left/right temporary reflection absorption, multi-position measurements, and longitudinal moves are not repeated. Related local comparisons with outcome `MIXED` weaken the reflection hypothesis and do not authorize retrying the same treatment.

If one experiment tests two hypotheses, it is stored once and its explicit multi-purpose rationale is shared by both hypothesis records.

## Expected observations

Every emitted experiment includes four testable outcome classes:

- `SUPPORTING`;
- `CONTRADICTING`;
- `NEUTRAL`;
- `INCONCLUSIVE`.

SBIR expectations concern a localized frequency shift. Reflection expectations concern a localized ETC event and related local temporal metrics. Modal expectations concern spatial variation of low-frequency response and decay. Frequency/time regions are emitted only when already structured by source analyses.

## Controlled variables and measurements

Exactly one semantic variable is modified. The remaining relevant acquisition, room, signal-chain, placement, and orientation variables are listed as controlled according to the experiment family. Every experiment requires separate LEFT, RIGHT, and STEREO measurements. Availability is verified against the structured measurement-set quality channels, or against the project's loaded impulse responses when set-quality facts are unavailable. Each absent channel adds `REQUIRED_MEASUREMENT_UNAVAILABLE:<CHANNEL>` to `blocking_reasons`.

A blocked candidate remains visible to explain which otherwise structured experiment cannot yet be executed. It is not eligible and is never selected as `recommended_candidate_id`. Blocking does not establish, contradict, or otherwise mutate the source hypothesis, its causal state, acoustic scores, recommendations, causal-discrimination analysis, or longitudinal learning state.

The historical `ExperimentPlanningEngine` consumes the final generated-candidate eligibility. It also makes `protocol.verify_speaker_room_asymmetry.v1` ineligible when the matching causal analysis is `DISCRIMINATED`, has no remaining discrimination and recommends no next protocol. Such a candidate remains available in planning traceability with `CAUSAL_DISCRIMINATION_COMPLETED`, but cannot be recommended again.

## Reporting and export

The report exposes a structured `acoustic_hypothesis_experiment_generation` object with `to_dict()`. The console distinguishes “hypothèse exploratoire”, “candidat expérimental” and “expérience principale”. A candidate is never marked principal merely because it is informative. When none is directly executable, the report says “Aucune expérience principale directement exécutable” and lists the structured missing data. Historical planning remains visible as traceability and does not create a second main-action label.

## Limitations and LLM role

The generator cannot recover missing geometry, identify an uncorrelated surface, choose toe-in direction, infer a useful movement magnitude, or interpret a user note as a scientific association. It may therefore return a plausible hypothesis with no safe concrete experiment.

An LLM may be used as a second opinion to explain alternatives or ask for missing data. It must not create geometry, directions, distances, source associations, causal statuses, or validation results, and its suggestions must remain outside deterministic scientific state until explicitly declared and measured.

## Examples

- Correlated 160 Hz front-wall SBIR event for the left speaker with a structured `proposed_displacement_m = 0.12`: reuse exactly `0.12 m`, expect a localized frequency shift, keep `NOT_ESTABLISHED`.
- The same SBIR relation without `proposed_displacement_m`: expose a blocked candidate with no distance and no main recommendation.
- Dominant ETC path matched to the right wall: propose one reversible right first-reflection mask, expect a localized ETC change, make no global-improvement claim.
- Sparse 20–50 Hz modal band with no source-declared position schema: retain a blocked multi-position candidate and request the sampling geometry without inventing offsets.
- Missing positioned speakers and no accepted reflection surface: retain suitable hypotheses and state that no safe concrete experiment can be generated.
