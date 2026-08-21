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
`--guided-status`. It does not select a new plan or derive a new blocker.

The homepage must not calculate or change eligibility, select a direction,
create a proposal, write a manifest or registry, execute a measurement,
recommend a permanent correction, or establish causality. `--full-assessment`
remains the detailed technical presentation.
