import pytest
from gherkin_verifier.parser import (
    ParsedStep,
    ParsedScenario,
    ParsedRule,
    ParsedFeature,
    parse_feature_file,
    parse_feature_string,
)


class TestParsedStep:
    def test_effective_keyword_given(self):
        step = ParsedStep(keyword="Given", text="o usuário é gerente")
        assert step.effective_keyword == "Given"

    def test_effective_keyword_and(self):
        step = ParsedStep(keyword="And", text="o usuário tem acesso")
        step.set_effective_keyword("Given")
        assert step.effective_keyword == "Given"

    def test_effective_keyword_but(self):
        step = ParsedStep(keyword="But", text="não tem acesso")
        step.set_effective_keyword("Then")
        assert step.effective_keyword == "Then"

    def test_effective_keyword_default(self):
        step = ParsedStep(keyword="When", text="o usuário acessa")
        assert step.effective_keyword == "When"


class TestParsedScenario:
    def test_basic(self):
        scenario = ParsedScenario(
            name="Test scenario",
            tags=["tag1", "tag2"],
            steps=[],
            line=5,
            description="Test description",
        )
        assert scenario.name == "Test scenario"
        assert len(scenario.tags) == 2
        assert scenario.line == 5


class TestParsedRule:
    def test_basic(self):
        rule = ParsedRule(
            name="Test rule",
            scenarios=[],
            tags=["rule_tag"],
            description="Rule description",
        )
        assert rule.name == "Test rule"
        assert len(rule.tags) == 1


class TestParsedFeature:
    def test_basic(self):
        feature = ParsedFeature(
            name="Test Feature",
            file_path="test.feature",
            description="Feature description",
            tags=["feature_tag"],
            background_steps=[],
            scenarios=[],
            rules=[],
        )
        assert feature.name == "Test Feature"
        assert feature.file_path == "test.feature"
        assert len(feature.tags) == 1


class TestParseFeatureString:
    def test_parse_simple_feature(self):
        content = """
Feature: Test Feature
  Scenario: Test scenario
    Given o usuário é gerente
    Then o usuário tem acesso
"""
        feature = parse_feature_string(content, "test.feature")
        assert feature.name == "Test Feature"
        assert len(feature.scenarios) == 1
        assert feature.scenarios[0].name == "Test scenario"
        assert len(feature.scenarios[0].steps) == 2

    def test_parse_feature_with_background(self):
        content = """
Feature: Test Feature
  Background:
    Given o sistema está funcionando

  Scenario: Test scenario
    Given o usuário é gerente
    Then o usuário tem acesso
"""
        feature = parse_feature_string(content, "test.feature")
        assert len(feature.background_steps) == 1
        assert feature.background_steps[0].text == "o sistema está funcionando"

    def test_parse_feature_with_tags(self):
        content = """
@feature_tag
Feature: Test Feature
  @scenario_tag
  Scenario: Test scenario
    Given o usuário é gerente
    Then o usuário tem acesso
"""
        feature = parse_feature_string(content, "test.feature")
        assert "feature_tag" in feature.tags
        assert "scenario_tag" in feature.scenarios[0].tags

    def test_parse_feature_with_rule(self):
        content = """
Feature: Test Feature
  Rule: Test Rule
    Scenario: Rule scenario
      Given o usuário é gerente
      Then o usuário tem acesso
"""
        feature = parse_feature_string(content, "test.feature")
        assert len(feature.rules) == 1
        assert feature.rules[0].name == "Test Rule"
        assert len(feature.rules[0].scenarios) == 1

    def test_parse_feature_with_and_but_keywords(self):
        content = """
Feature: Test Feature
  Scenario: Test scenario
    Given o usuário é gerente
    And o usuário tem permissões
    But não tem acesso especial
    Then o usuário tem acesso
"""
        feature = parse_feature_string(content, "test.feature")
        steps = feature.scenarios[0].steps
        assert len(steps) == 4
        assert steps[1].effective_keyword == "Given"
        assert steps[2].effective_keyword == "Given"
        assert steps[3].effective_keyword == "Then"

    def test_parse_empty_feature(self):
        content = "Feature: Empty"
        feature = parse_feature_string(content, "test.feature")
        assert feature.name == "Empty"
        assert len(feature.scenarios) == 0

    def test_parse_feature_with_scenario_outline(self):
        content = """
Feature: Test Feature
  Scenario Outline: Test outline
    Given o usuário é <tipo>
    Then o usuário tem <acesso>

    Examples:
      | tipo     | acesso |
      | gerente  | total   |
      | caixa    | parcial |
"""
        feature = parse_feature_string(content, "test.feature")
        assert len(feature.scenarios) == 1
        assert feature.scenarios[0].name == "Test outline"


class TestParseFeatureFile:
    def test_parse_file(self, tmp_path):
        feature_file = tmp_path / "test.feature"
        feature_file.write_text("""
Feature: Test
  Scenario: Test
    Given o usuário é gerente
    Then o usuário tem acesso
""")
        feature = parse_feature_file(str(feature_file))
        assert feature.name == "Test"
        assert len(feature.scenarios) == 1

    def test_parse_nonexistent_file(self):
        with pytest.raises(Exception):
            parse_feature_file("/nonexistent/file.feature")
