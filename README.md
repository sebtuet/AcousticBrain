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
