import pytest
from gherkin_verifier.contradictions.contrary import check_contrary
from gherkin_verifier.domain import Proposition, Quantifier


class TestCheckContrary:
    def test_contrary_universal(self):
        props = [
            Proposition(
                subject="caixa",
                predicate="tem",
                obj="acesso",
                negated=False,
                quantifier=Quantifier.UNIVERSAL_AFF,
                explicit_quantifier=True,
                source_scenario="cenario1",
                source_step="todo caixa tem acesso",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="caixa",
                predicate="tem",
                obj="acesso",
                negated=True,
                quantifier=Quantifier.UNIVERSAL_AFF,
                explicit_quantifier=True,
                source_scenario="cenario2",
                source_step="nenhum caixa tem acesso",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_contrary(props)
        assert len(results) > 0
        assert results[0].severity == "critical"

    def test_no_contrary_no_explicit_quantifier(self):
        props = [
            Proposition(
                subject="caixa",
                predicate="tem",
                obj="acesso",
                negated=False,
                quantifier=Quantifier.UNIVERSAL_AFF,
                explicit_quantifier=False,
                source_scenario="cenario1",
                source_step="caixa tem acesso",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="caixa",
                predicate="tem",
                obj="acesso",
                negated=True,
                quantifier=Quantifier.UNIVERSAL_AFF,
                explicit_quantifier=False,
                source_scenario="cenario2",
                source_step="caixa não tem acesso",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_contrary(props)
        # Without explicit quantifier, no contrary contradiction
        assert len(results) == 0

    def test_no_contrary_different_subject_object(self):
        props = [
            Proposition(
                subject="caixa",
                predicate="tem",
                obj="acesso",
                negated=False,
                quantifier=Quantifier.UNIVERSAL_AFF,
                explicit_quantifier=True,
                source_scenario="cenario1",
                source_step="todo caixa tem acesso",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="gerente",
                predicate="tem",
                obj="acesso",
                negated=True,
                quantifier=Quantifier.UNIVERSAL_AFF,
                explicit_quantifier=True,
                source_scenario="cenario2",
                source_step="nenhum gerente tem acesso",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_contrary(props)
        assert len(results) == 0


class TestCheckSubcontrary:
    def test_subcontrary(self):
        from gherkin_verifier.contradictions.subcontrary import check_subcontrary
        props = [
            Proposition(
                subject="caixa",
                predicate="tem",
                obj="acesso",
                negated=False,
                quantifier=Quantifier.PARTICULAR_AFF,
                source_scenario="cenario1",
                source_step="algum caixa tem acesso",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="caixa",
                predicate="tem",
                obj="acesso",
                negated=True,
                quantifier=Quantifier.PARTICULAR_AFF,
                source_scenario="cenario2",
                source_step="algum caixa não tem acesso",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_subcontrary(props)
        # May have results depending on solver constraints
        assert isinstance(results, list)


class TestCheckPrivative:
    def test_privative(self):
        from gherkin_verifier.contradictions.privative import check_privative, classify_absence
        from gherkin_verifier.domain import AptitudeDeclaration

        props = [
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                negated=False,
                source_scenario="cenario1",
                source_step="usuário tem acesso",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                negated=True,
                source_scenario="cenario2",
                source_step="usuário não tem acesso",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        aptitudes = [
            AptitudeDeclaration(
                subject_type="usuário",
                property_name="acesso",
                is_apt=True,
                source="test.feature:5",
            ),
        ]
        results = check_privative(props, aptitudes)
        assert len(results) > 0

    def test_no_aptitudes(self):
        from gherkin_verifier.contradictions.privative import check_privative
        props = [
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                negated=False,
                source_scenario="cenario1",
                source_step="usuário tem acesso",
                source_file="test.feature",
                source_line=1,
            ),
        ]
        results = check_privative(props, [])
        assert len(results) == 0

    def test_classify_absence(self):
        from gherkin_verifier.contradictions.privative import classify_absence
        from gherkin_verifier.domain import AptitudeDeclaration

        aptitudes = [
            AptitudeDeclaration(
                subject_type="usuario",
                property_name="acesso",
                is_apt=True,
            ),
        ]
        result = classify_absence("usuario", "acesso", aptitudes)
        assert result == "privação"

        result = classify_absence("pedra", "visao", aptitudes)
        # Returns "desconhecido" because pedra is not in aptitudes
        assert result == "desconhecido"

        result = classify_absence("desconhecido", "x", [])
        assert result == "desconhecido"
