from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedAnalysisReadiness:
    family: str
    status: str
    blocking_issue_codes: tuple[str, ...] = ()
    reservation_issue_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class PresentedAnalysisReadinessReport:
    analyses: tuple[PresentedAnalysisReadiness, ...]


class AnalysisReadinessPresenter:
    """Projects existing technical readiness decisions without interpreting them."""

    def present(self, context):
        readiness = getattr(context, "measurement_readiness_analysis", None)
        if readiness is None:
            return None
        return PresentedAnalysisReadinessReport(
            analyses=tuple(
                PresentedAnalysisReadiness(
                    family=item.family.value,
                    status=item.status.value,
                    blocking_issue_codes=tuple(
                        issue.code.value for issue in item.blocking_issues
                    ),
                    reservation_issue_codes=tuple(
                        issue.code.value for issue in item.non_blocking_issues
                    ),
                )
                for item in readiness.analyses
            )
        )
