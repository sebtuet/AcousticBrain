from dataclasses import fields

from acousticbrain.models import GlobalAnalysis, GlobalCorrelation, GlobalDomainAnalysis


def test_global_contract_contains_no_diagnostic_or_rendering_text():
    global_fields = {field.name for field in fields(GlobalAnalysis)}
    domain_fields = {field.name for field in fields(GlobalDomainAnalysis)}
    correlation_fields = {field.name for field in fields(GlobalCorrelation)}

    forbidden = {"diagnostic", "diagnostics", "title", "message", "description"}
    assert global_fields.isdisjoint(forbidden)
    assert domain_fields.isdisjoint(forbidden)
    assert correlation_fields.isdisjoint(forbidden)
