import pytest
from gherkin_verifier.domain import (
    Proposition,
    Quantifier,
    Modality,
    AptitudeDeclaration,
    RelationDeclaration,
    PresuppositionDeclaration,
    ContradictionResult,
    VerificationReport,
)


class TestProposition:
    def test_key_property(self):
        prop = Proposition(
            subject="usuário",
            predicate="tem",
            obj="acesso",
        )
        assert prop.key == "usuário|tem|acesso"

    def test_logical_form_affirmative(self):
        prop = Proposition(
            subject="usuário",
            predicate="tem",
            obj="acesso",
            quantifier=Quantifier.UNIVERSAL_AFF,
        )
        assert "∀" in prop.logical_form
        assert "usuário" in prop.logical_form

    def test_logical_form_negated(self):
        prop = Proposition(
            subject="usuário",
            predicate="tem",
            obj="acesso",
            negated=True,
            quantifier=Quantifier.UNIVERSAL_AFF,
        )
        assert "¬" in prop.logical_form

    def test_logical_form_quantifiers(self):
        prop_aff = Proposition(
            subject="x", predicate="P", obj="y",
            quantifier=Quantifier.UNIVERSAL_AFF
        )
        assert "∀" in prop_aff.logical_form

        prop_neg = Proposition(
            subject="x", predicate="P", obj="y",
            quantifier=Quantifier.UNIVERSAL_NEG
        )
        assert "∀¬" in prop_neg.logical_form

        prop_part_aff = Proposition(
            subject="x", predicate="P", obj="y",
            quantifier=Quantifier.PARTICULAR_AFF
        )
        assert "∃" in prop_part_aff.logical_form

        prop_part_neg = Proposition(
            subject="x", predicate="P", obj="y",
            quantifier=Quantifier.PARTICULAR_NEG
        )
        assert "∃¬" in prop_part_neg.logical_form

    def test_contradicts_same_key_different_negation(self):
        prop_aff = Proposition(
            subject="usuário",
            predicate="tem",
            obj="acesso",
            negated=False,
        )
        prop_neg = Proposition(
            subject="usuário",
            predicate="tem",
            obj="acesso",
            negated=True,
        )
        assert prop_aff.contradicts(prop_neg) is True

    def test_contradicts_same_key_same_negation(self):
        prop1 = Proposition(
            subject="usuário",
            predicate="tem",
            obj="acesso",
            negated=False,
        )
        prop2 = Proposition(
            subject="usuário",
            predicate="tem",
            obj="acesso",
            negated=False,
        )
        assert prop1.contradicts(prop2) is False

    def test_contradicts_different_key(self):
        prop1 = Proposition(
            subject="usuário",
            predicate="tem",
            obj="acesso",
        )
        prop2 = Proposition(
            subject="usuário",
            predicate="tem",
            obj="permissao",
        )
        assert prop1.contradicts(prop2) is False

    def test_repr(self):
        prop = Proposition(
            subject="usuário",
            predicate="tem",
            obj="acesso",
            negated=False,
        )
        assert "Prop(" in repr(prop)
        assert "usuário.tem=acesso" in repr(prop)

    def test_repr_negated(self):
        prop = Proposition(
            subject="usuário",
            predicate="tem",
            obj="acesso",
            negated=True,
        )
        assert "NOT " in repr(prop)


class TestAptitudeDeclaration:
    def test_basic(self):
        apt = AptitudeDeclaration(
            subject_type="usuário_autenticado",
            property_name="acesso_relatorio",
            is_apt=True,
            source="test.feature:10",
        )
        assert apt.subject_type == "usuário_autenticado"
        assert apt.property_name == "acesso_relatorio"
        assert apt.is_apt is True

    def test_not_apt(self):
        apt = AptitudeDeclaration(
            subject_type="pedra",
            property_name="visão",
            is_apt=False,
        )
        assert apt.is_apt is False


class TestRelationDeclaration:
    def test_basic(self):
        rel = RelationDeclaration(
            role_a="gerente",
            role_b="subordinado",
            relation="controla",
            inverse_relation="controlado_por",
            simultaneous=True,
            source="test.feature:5",
        )
        assert rel.role_a == "gerente"
        assert rel.role_b == "subordinado"
        assert rel.relation == "controla"
        assert rel.inverse_relation == "controlado_por"


class TestPresuppositionDeclaration:
    def test_self_negated_foundations(self):
        presup = PresuppositionDeclaration(
            proposition_id="test:1",
            content="test scenario",
            presupposes={"sessao_ativa", "autenticacao"},
            negates={"sessao_ativa"},
            source="test.feature:5",
        )
        assert "sessao_ativa" in presup.self_negated_foundations

    def test_is_self_negating(self):
        presup = PresuppositionDeclaration(
            proposition_id="test:1",
            content="test scenario",
            presupposes={"sessao_ativa"},
            negates={"sessao_ativa"},
        )
        assert presup.is_self_negating is True

    def test_is_not_self_negating(self):
        presup = PresuppositionDeclaration(
            proposition_id="test:1",
            content="test scenario",
            presupposes={"sessao_ativa"},
            negates={"outra_coisa"},
        )
        assert presup.is_self_negating is False


class TestContradictionResult:
    def test_repr(self):
        result = ContradictionResult(
            contradiction_type="Contraditória",
            severity="critical",
            description="Test contradiction",
        )
        assert "[CRITICAL]" in repr(result)
        assert "Contraditória" in repr(result)


class TestVerificationReport:
    def test_has_contradictions_true(self):
        report = VerificationReport(
            feature_file="test.feature",
            contradictions=[
                ContradictionResult(
                    contradiction_type="Test",
                    severity="critical",
                    description="Test",
                )
            ],
        )
        assert report.has_contradictions is True

    def test_has_contradictions_false(self):
        report = VerificationReport(
            feature_file="test.feature",
            contradictions=[],
        )
        assert report.has_contradictions is False

    def test_critical_count(self):
        report = VerificationReport(
            feature_file="test.feature",
            contradictions=[
                ContradictionResult(contradiction_type="A", severity="critical", description=""),
                ContradictionResult(contradiction_type="B", severity="warning", description=""),
                ContradictionResult(contradiction_type="C", severity="critical", description=""),
            ],
        )
        assert report.critical_count == 2

    def test_warning_count(self):
        report = VerificationReport(
            feature_file="test.feature",
            contradictions=[
                ContradictionResult(contradiction_type="A", severity="critical", description=""),
                ContradictionResult(contradiction_type="B", severity="warning", description=""),
                ContradictionResult(contradiction_type="C", severity="info", description=""),
            ],
        )
        assert report.warning_count == 1
