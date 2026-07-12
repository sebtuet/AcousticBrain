class DiagnosticsStage:
    """
    Exécute tous les diagnostics
    et les ajoute au rapport.
    """

    def __init__(self, diagnostics):

        self.diagnostics = diagnostics

    def run(self, context, report):

        families = {
            "BassDiagnostic": "FREQUENCY",
            "RoomModeDiagnostic": "FREQUENCY",
            "DipDiagnostic": "FREQUENCY",
            "StereoDiagnostic": "FREQUENCY",
            "SBIRDiagnostic": "FREQUENCY",
            "ModalDensityDiagnostic": "FREQUENCY",
            "RT60Diagnostic": "RT60",
            "ETCDiagnostic": "ETC",
            "ClarityDiagnostic": "CLARITY",
            "SpatialDiagnostic": "SPATIAL",
            "DirectReverberantDiagnostic": "DIRECT_REVERBERANT",
            "BassDecayDiagnostic": "BASS_DECAY",
        }
        readiness = {
            item.family.value: item
            for item in getattr(
                context.measurement_readiness_analysis,
                "analyses",
                (),
            )
        }

        for diagnostic in self.diagnostics:
            result = diagnostic.analyze(context)
            family = families.get(type(diagnostic).__name__)
            decision = readiness.get(family)
            if decision is not None:
                result.analysis_family = family
                result.readiness_status = decision.status.value
                if decision.status.value == "BLOCKED":
                    result.provisional = True
                    result.validity = "Validité technique non garantie"
                elif decision.status.value == "AVAILABLE_WITH_RESERVATIONS":
                    result.validity = "Validité technique avec réserves"
                else:
                    result.validity = "Validité technique établie"
            report.add(result)
