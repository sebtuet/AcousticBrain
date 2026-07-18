# AcousticBrain

AcousticBrain analyzes the campaign stored in the historical default directory:

```bash
python main.py
```

This is equivalent to:

```bash
python main.py --measurements-root measurements
```

To analyze a personal campaign outside the repository, pass its directory explicitly:

```bash
python main.py --measurements-root /path/to/my-campaign
```

The selected directory must exist and be a directory. AcousticBrain's existing discovery logic remains responsible for deciding whether it contains a valid campaign.

The CLI prints the resolved measurement root as a technical header. It is not added to the acoustic report model and does not affect scientific results.

Keep the Git fixtures in `./measurements`. Personal measurement files and real campaigns should remain outside the repository and must not be committed to Git.

To provide an explicit, versioned multi-position campaign instance:

```bash
python main.py \
  --measurements-root /path/to/my-campaign \
  --listening-position-campaign /path/to/listening-position-campaign.json
```

The JSON file is read only. AcousticBrain validates its protocol, positions,
offsets, relations, measurements, controlled variables and requested existing
reference before producing a campaign plan. It never creates an experiment or
fills in missing geometry. The file in
`docs/examples/listening-position-campaign.example.json` is an editable
illustration only and is never activated automatically.

To qualify the exact existing experiment requested by a multi-position
campaign instance, provide a second explicit JSON declaration:

```bash
python main.py \
  --measurements-root /path/to/my-campaign \
  --listening-position-campaign /path/to/listening-position-campaign.json \
  --campaign-reference-qualification /path/to/reference-qualification.json
```

The qualification is cross-checked against the observed experiment, its real
channels, historical declaration, local comparison, protocol and campaign
instance. It never replaces the requested experiment or rewrites historical
facts. The example at
`docs/examples/campaign-reference-qualification.example.json` is documentation
only and is never loaded automatically.

To print the opt-in deterministic observation report:

```bash
python main.py --measurements-root /path/to/my-campaign --observations
```

This dedicated report copies established analysis facts, confidence and
provenance into immutable descriptive observations. It contains no
recommendation, corrective action, hypothesis or experiment. Without the
option, the historical report is unchanged. See
`docs/DETERMINISTIC_ACOUSTIC_OBSERVATIONS.md` for the contract.

To explain existing deterministic hypothesis statuses from PR-054 observations:

```bash
python main.py --measurements-root /path/to/my-campaign --reasoning
```

The dedicated report exposes structured premises, inference steps, conclusions,
contradictions, limitations and provenance. It creates no new hypothesis,
recommendation, action or experiment. See
`docs/DETERMINISTIC_ACOUSTIC_REASONING.md` for the scientific contract.

To project sufficiently established reasoning into declarative corrective or
discrimination actions:

```bash
python main.py --measurements-root /path/to/my-campaign --actions
```

The report exposes applicability, priority, source reasoning and observations,
existing compatible contracts, known and missing parameters, contradictions
and limitations. It executes nothing and invents no geometry or setting. See
`docs/DETERMINISTIC_CORRECTIVE_ACTIONS.md` for the contract.

To qualify the robustness of existing evidence without producing a global
score:

```bash
python main.py --measurements-root /path/to/my-campaign --weighting
```

The dedicated report keeps evidence strength, source consistency,
discriminative power, parameter completeness and action applicability
independent. It creates no evidence or decision and does not alter upstream
objects. See `docs/DETERMINISTIC_EVIDENCE_WEIGHTING.md` for the contract.

To ask the optional, non-authoritative advisor to explain those deterministic
objects offline:

```bash
python main.py \
  --measurements-root /path/to/my-campaign \
  --advisor \
  --advisor-provider mock \
  --question "Why is this action blocked?"
```

The advisor is disabled by default and never creates scientific knowledge. Its
context, provider adapters and strict post-response validation are documented
in `docs/OPTIONAL_LLM_ADVISOR.md`.
