# Evidence-acquisition plan contract preservation

This contract preserves the complete reason for an experiment from an existing
`EvidenceAcquisitionPlan` into the executed experiment's manifest. It extends
the established chain and does not create another planning or exploratory
engine:

```text
EvidenceAcquisitionPlan
→ ExperimentDeclaration
→ execution
→ automatic comparison
```

Only a uniquely resolved `READY` plan may be declared. The declaration reuses
the plan's independent and controlled variables, requires an explicit reference
experiment, and stores an immutable snapshot containing:

- plan identity and upstream reasoning/action/weight provenance;
- objective and test type;
- prerequisites and instructions;
- independent and controlled variables;
- required measurements and expected observations;
- success and failure criteria;
- evidence targets, limitations, priority and effort;
- explicit mode (`EXPLORATORY` in the current contract).

`PRESCRIPTIVE` is represented as a future semantic value but is rejected until
a separate scientific contract authorizes it. Free text is never parsed to
complete a plan, and a different contract cannot overwrite an existing
experiment contract.

Contract preservation and execution conformity are separate decisions. A
complete snapshot proves why the experiment was declared; it does not prove
that every acquisition was performed or that a comparison is valid. Existing
specialized coverage and result validators retain that authority.

Declare a currently `READY` plan with:

```bash
python -m acousticbrain.commands.declare_evidence_plan_experiment \
  /path/to/measurements \
  --plan-id PLAN_ID \
  --experiment exp-XXX \
  --reference baseline
```

The command analyzes the campaign read-only to resolve the plan, then performs
one explicit manifest declaration. Measurement files are never modified.
