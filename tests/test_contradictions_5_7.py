import pytest
from gherkin_verifier.contradictions.modal import check_modal, check_modal_negation_conflict
from gherkin_verifier.contradictions.relative import check_relative, check_relative_z3, check_relative_graph
from gherkin_verifier.contradictions.self_negation import (
    check_self_negation,
    check_self_negation_structural,
    check_self_negation_z3,
    _classify_self_negation,
)
from gherkin_verifier.domain import (
    Proposition,
    Modality,
    RelationDeclaration,
    PresuppositionDeclaration,
    AptitudeDeclaration,
)


class TestCheckModal:
    def test_modal_necessary_impossible(self):
        props = [
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                modality=Modality.NECESSARY,
                source_scenario="cenario1",
                source_step="o usuário deve ter acesso",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                modality=Modality.IMPOSSIBLE,
                source_scenario="cenario2",
                source_step="o usuário não pode ter acesso",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_modal(props)
        assert len(results) > 0
        assert results[0].severity == "critical"

    def test_modal_no_conflict(self):
        props = [
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                modality=Modality.POSSIBLE,
                source_scenario="cenario1",
                source_step="o usuário pode ter acesso",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                modality=Modality.CONTINGENT,
                source_scenario="cenario2",
                source_step="o usuário tem acesso",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_modal(props)
        assert len(results) == 0


class TestCheckModalNegationConflict:
    def test_modal_negation_conflict(self):
        props = [
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                modality=Modality.NECESSARY,
                negated=False,
                source_scenario="cenario1",
                source_step="o usuário deve ter acesso",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                modality=Modality.CONTINGENT,
                negated=True,
                source_scenario="cenario2",
                source_step="o usuário não tem acesso",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_modal_negation_conflict(props)
        assert len(results) > 0


class TestCheckRelative:
    def test_relative_with_relations(self):
        props = [
            Proposition(
                subject="gerente",
                predicate="controla",
                obj="subordinado",
                negated=False,
                source_scenario="cenario1",
                source_step="o gerente controla o subordinado",
                source_file="test.feature",
                source_line=1,
            ),
        ]
        relations = [
            RelationDeclaration(
                role_a="gerente",
                role_b="subordinado",
                relation="controla",
                inverse_relation="controlado_por",
                simultaneous=True,
                source="test.feature:5",
            ),
        ]
        results = check_relative(props, relations)
        assert isinstance(results, list)

    def test_relative_no_relations(self):
        props = [
            Proposition(
                subject="gerente",
                predicate="controla",
                obj="subordinado",
                negated=False,
                source_scenario="cenario1",
                source_step="o gerente controla o subordinado",
                source_file="test.feature",
                source_line=1,
            ),
        ]
        results = check_relative(props, [])
        assert len(results) == 0


class TestCheckSelfNegation:
    def test_self_negation_structural(self):
        presuppositions = [
            PresuppositionDeclaration(
                proposition_id="test:1",
                content="Test scenario",
                presupposes={"sessao_ativa"},
                negates={"sessao_ativa"},
                source="test.feature:5",
            ),
        ]
        results = check_self_negation_structural(presuppositions)
        assert len(results) > 0
        assert results[0].severity == "critical"

    def test_self_negation_z3(self):
        props = [
            Proposition(
                subject="sistema",
                predicate="está",
                obj="ativo",
                source_scenario="cenario1",
                source_step="Dado que o sistema está ativo",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="sistema",
                predicate="verifica",
                obj="autenticação",
                source_scenario="cenario1",
                source_step="Then o sistema verifica a autenticação",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_self_negation_z3(props)
        # May or may not have results depending on logic
        assert isinstance(results, list)

    def test_self_negation_no_presuppositions(self):
        props = [
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                source_scenario="cenario1",
                source_step="o usuário tem acesso",
                source_file="test.feature",
                source_line=1,
            ),
        ]
        results = check_self_negation(props, [])
        assert isinstance(results, list)


class TestClassifySelfNegation:
    def test_classify_performative(self):
        result = _classify_self_negation({"sessao_ativa"})
        assert result == "Performativa"

    def test_classify_epistemic(self):
        result = _classify_self_negation({"cognoscibilidade"})
        assert result == "Epistêmica"

    def test_classify_foundational(self):
        result = _classify_self_negation({"rule_engine_active"})
        assert result == "Fundacional"

    def test_classify_generic(self):
        result = _classify_self_negation({"unknown"})
        assert result == "Genérica"
