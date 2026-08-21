# Default speaker-placement homepage contract

`python main.py --measurements-root PATH` is the public placement homepage.
It is a read-only projection of objects already created by the deterministic
analysis pipeline.

The homepage answers, in this order:

1. whether one reversible loudspeaker test is currently available;
2. why that state follows from the existing positioning presentation;
3. one public next step.

If an existing positioning proposal is available, the homepage may display its
existing target, direction, amplitude and identifier. It may show the explicit
public declaration command with placeholders for values that the user must
still choose. Displaying that command neither declares nor executes an
experiment.

If no single move is available, the homepage may point to the existing
deterministically selected READY evidence-acquisition plan through
`--start-placement`. This public command asks for explicit user declarations
of existing prerequisites and persists them only after an explicit confirmation
in the dedicated campaign-local preparation registry. It does not select a new
plan or derive a new blocker.

For the existing CHANNEL_ISOLATION journey, once preparation is explicitly
confirmed, the command lists the existing measurement directories for the user
to choose a starting measurement and proposes an unused human-readable test
name. It runs the existing declaration preflight and declares the test only
after a second explicit confirmation. It never chooses the reference itself.

The homepage must not calculate or change eligibility, select a direction,
create a proposal, write a manifest or registry, execute a measurement,
recommend a permanent correction, or establish causality. `--full-assessment`
remains the detailed technical presentation.
