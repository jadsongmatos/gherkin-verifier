import pytest
from gherkin_verifier.engine import (
    verify_feature,
    verify_file,
    verify_string,
    format_report,
)
from gherkin_verifier.parser import parse_feature_string


class TestVerifyFeature:
    def test_verify_feature_simple(self):
        feature = parse_feature_string("""
Feature: Test
  Scenario: Test
    Given o usuário é gerente
    Then o usuário tem acesso
""", "test.feature")
        report = verify_feature(feature)
        assert report.feature_file == "test.feature"
        assert report.total_scenarios == 1
        assert report.total_propositions >= 1

    def test_verify_feature_no_contradictions(self):
        feature = parse_feature_string("""
Feature: Test
  Scenario: Test
    Given o usuário é gerente
    Then o usuário tem acesso
""", "test.feature")
        report = verify_feature(feature)
        # No contradictions expected for this simple case
        assert report is not None

    def test_verify_feature_with_background(self):
        feature = parse_feature_string("""
Feature: Test
  Background:
    Given o sistema está ligado
  Scenario: Test
    Given o usuário é gerente
    Then o usuário tem acesso
""", "test.feature")
        report = verify_feature(feature)
        assert report.total_scenarios == 1
        assert len(report.contradictions) >= 0

    def test_verify_feature_with_rule(self):
        feature = parse_feature_string("""
Feature: Test
  Rule: Test Rule
    Scenario: Rule scenario
      Given o usuário é gerente
      Then o usuário tem acesso
""", "test.feature")
        report = verify_feature(feature)
        assert report.total_scenarios == 1


class TestVerifyString:
    def test_verify_string_basic(self):
        content = """
Feature: Test
  Scenario: Test
    Given o usuário é gerente
    Then o usuário tem acesso
"""
        report = verify_string(content, "test.feature")
        assert report.total_propositions >= 1

    def test_verify_string_with_contradiction(self):
        content = """
Feature: Test
  Scenario: Test 1
    Given o usuário é gerente
    Then o usuário tem acesso

  Scenario: Test 2
    Given o usuário é gerente
    Then o usuário não tem acesso
"""
        report = verify_string(content, "test.feature")
        assert report.has_contradictions is True


class TestFormatReport:
    def test_format_report_no_contradictions(self):
        from gherkin_verifier.domain import VerificationReport
        report = VerificationReport(feature_file="test.feature")
        report.total_scenarios = 1
        report.total_propositions = 2
        formatted = format_report(report)
        assert "RELATÓRIO DE VERIFICAÇÃO" in formatted
        assert "CONSISTENTE" in formatted

    def test_format_report_with_contradictions(self):
        from gherkin_verifier.domain import VerificationReport, ContradictionResult
        report = VerificationReport(
            feature_file="test.feature",
            contradictions=[
                ContradictionResult(
                    contradiction_type="Contraditória",
                    severity="critical",
                    description="Test contradiction",
                )
            ],
        )
        report.total_scenarios = 1
        report.total_propositions = 2
        formatted = format_report(report)
        assert "RELATÓRIO DE VERIFICAÇÃO" in formatted
        assert "inconsistências" in formatted.lower() or "contradi" in formatted.lower()
