# Campaign Reference Qualification Contract

## Role and separation

The qualification chain is deliberately split into five immutable concepts:

`observed experiment -> user declaration -> calculated qualification ->`
`PR-051 reference admissibility -> campaign plan`.

The JSON declaration does not modify the experiment manifest or its historical
declaration. A syntactically `VALID` declaration may still calculate as
`BLOCKED`. Only a calculated `QUALIFIED` result can contribute explicit
configuration facts to PR-051, which remains the final authority.

## JSON version 1

The CLI accepts a selected UTF-8 JSON file through
`--campaign-reference-qualification`. There is no default path, automatic
discovery or active example. Every field except `notes` is explicit:

- qualification, experiment, protocol and optional campaign-instance identity;
- the `REFERENCE` role;
- a configuration assertion for each controlled variable;
- asserted required measurements;
- declaration source and version.

Each configuration assertion is `KNOWN`, `UNKNOWN` or `NOT_APPLICABLE`.
Absence and `UNKNOWN` never become `KNOWN`. The standard-library loader preserves
the declaration and never corrects names, chooses an experiment, infers a
protocol, changes the current directory or writes a file.

## Scientific qualification

`QUALIFIED` requires all of the following:

- the exact requested experiment exists and is `READY`;
- actual `LEFT`, `RIGHT` and `STEREO` measurements are available;
- its historical experiment declaration is not `UNKNOWN`;
- its local comparison is `COMPARABLE`;
- protocol id and version match the PR-050 protocol;
- campaign-instance identity and requested reference match PR-052;
- the role is `REFERENCE`;
- every protocol-controlled variable is explicitly asserted `KNOWN`;
- asserted measurements match the protocol and observed channels;
- no assertion contradicts an existing historical fact;
- the declaration source is explicit.

A `KNOWN` assertion can complete a configuration fact that was not represented
in the historical declaration, but it is cross-checked against every available
descriptor, channel, declaration, comparison, protocol and instance fact. It
never overwrites history. An `UNKNOWN` or `NOT_APPLICABLE` assertion against an
existing historical fact produces a contradiction.

The qualification does not demonstrate acoustic causality. Its causality remains
`NOT_ESTABLISHED`.

## Blocking reasons

The calculated qualification exposes precise reasons including:

- `CAMPAIGN_REFERENCE_DECLARATION_UNAVAILABLE`;
- `CAMPAIGN_REFERENCE_DECLARATION_INVALID`;
- `CAMPAIGN_REFERENCE_EXPERIMENT_NOT_FOUND`;
- `CAMPAIGN_REFERENCE_EXPERIMENT_NOT_READY`;
- `CAMPAIGN_REFERENCE_MEASUREMENTS_INCOMPLETE`;
- `CAMPAIGN_REFERENCE_DECLARATION_UNKNOWN`;
- `CAMPAIGN_REFERENCE_CONFIGURATION_INCOMPLETE`;
- `CAMPAIGN_REFERENCE_HISTORICAL_CONTRADICTION`;
- `CAMPAIGN_REFERENCE_PROTOCOL_MISMATCH`;
- `CAMPAIGN_REFERENCE_INSTANCE_MISMATCH`;
- `CAMPAIGN_REFERENCE_COMPARABILITY_UNAVAILABLE`.

PR-051 continues to expose the global plan reason
`CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE`. The qualification section explains
the precise cause. No alternative reference is selected.

## Read-only and extensibility guarantees

Qualification only reads the selected JSON and observed campaign structures.
It creates no experiment identity, directory, manifest or measurement and does
not update the qualification, campaign instance or personal campaign.

Additional protocols can reuse the declaration and qualification models by
providing their existing explicit protocol contract. The qualification engine
contains no active experiment id or protocol id default.

The file at
`docs/examples/campaign-reference-qualification.example.json` is documentation
only. Its `exp-007` and protocol values are illustrative and never loaded
automatically.
