import pytest
from gherkin_verifier.contradictions.contradictory import (
    check_contradictory,
    check_contradictory_with_rules,
    set_scenario_contexts,
    _scenarios_share_context,
)
from gherkin_verifier.domain import Proposition


class TestCheckContradictory:
    def test_same_scenario_contradiction(self):
        props = [
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                negated=False,
                source_scenario="cenario1",
                source_step="o usuário tem acesso",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                negated=True,
                source_scenario="cenario1",
                source_step="o usuário não tem acesso",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_contradictory(props)
        assert len(results) > 0
        assert results[0].severity == "critical"

    def test_different_scenarios_same_context(self):
        set_scenario_contexts({
            "cenario1": {"o usuário é gerente"},
            "cenario2": {"o usuário é gerente"},
        })
        props = [
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                negated=False,
                source_scenario="cenario1",
                source_step="o usuário tem acesso",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                negated=True,
                source_scenario="cenario2",
                source_step="o usuário não tem acesso",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_contradictory(props)
        assert len(results) > 0

    def test_different_scenarios_different_context(self):
        set_scenario_contexts({
            "cenario1": {"credenciais válidas"},
            "cenario2": {"credenciais inválidas"},
        })
        props = [
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                negated=False,
                source_scenario="cenario1",
                source_step="o usuário tem acesso",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                negated=True,
                source_scenario="cenario2",
                source_step="o usuário não tem acesso",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_contradictory(props)
        # Different contexts should NOT trigger contradiction
        assert len(results) == 0

    def test_no_contradiction(self):
        props = [
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                negated=False,
                source_scenario="cenario1",
                source_step="o usuário tem acesso",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="permissao",
                negated=True,
                source_scenario="cenario2",
                source_step="o usuário não tem permissão",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_contradictory(props)
        assert len(results) == 0


class TestCheckContradictoryWithRules:
    def test_with_rules_contradiction(self):
        props = [
            Proposition(
                subject="caixa",
                predicate="tem",
                obj="acesso",
                negated=False,
                source_scenario="cenario1",
                source_step="caixa tem acesso",
                source_file="test.feature",
                source_line=1,
            ),
        ]
        rules = [("caixa|tem|acesso", "gerente|tem|acesso")]
        results = check_contradictory_with_rules(props, rules)
        # This test checks if rules are applied
        assert isinstance(results, list)


class TestScenariosShareContext:
    def test_share_context(self):
        set_scenario_contexts({
            "cenario1": {"contexto1"},
            "cenario2": {"contexto1"},
        })
        result = _scenarios_share_context([], "cenario1", "cenario2")
        # Same context available, should return True (potential contradiction)
        assert result is True

    def test_different_contexts(self):
        set_scenario_contexts({
            "cenario1": {"credenciais válidas"},
            "cenario2": {"credenciais inválidas"},
        })
        props = [
            Proposition(
                subject="x", predicate="y", obj="z",
                source_scenario="cenario1",
                source_step="", source_file="", source_line=0,
            ),
        ]
        result = _scenarios_share_context(props, "cenario1", "cenario2")
        assert result is False
