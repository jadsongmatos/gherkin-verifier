import pytest
from gherkin_verifier.contradictions.suppositio import check_suppositio, _compute_term_context
from gherkin_verifier.contradictions.countersense import (
    check_countersense,
    check_performative,
    _detect_meta_operation,
    _detect_system_usage,
)
from gherkin_verifier.domain import Proposition


class TestCheckSuppositio:
    def test_suppositio_basic(self):
        props = [
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                negated=False,
                source_scenario="cenario1",
                source_step="Dado que o usuário está autenticado",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="acesso",
                negated=True,
                source_scenario="cenario2",
                source_step="Então o usuário não tem acesso",
                source_file="test.feature",
                source_line=2,
            ),
            Proposition(
                subject="usuário",
                predicate="tem",
                obj="permissao",
                negated=False,
                source_scenario="cenario2",
                source_step="Dado que o usuário é anônimo",
                source_file="test.feature",
                source_line=3,
            ),
        ]
        results = check_suppositio(props)
        assert isinstance(results, list)

    def test_no_suppositio_same_context(self):
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
                negated=False,
                source_scenario="cenario1",
                source_step="o usuário tem acesso",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_suppositio(props)
        assert len(results) == 0


class TestComputeTermContext:
    def test_basic(self):
        prop = Proposition(
            subject="usuário",
            predicate="tem",
            obj="acesso",
            source_scenario="test",
            source_step="test",
            source_file="test.feature",
            source_line=1,
        )
        ctx = _compute_term_context(prop)
        assert ctx == ("tem", "acesso")


class TestCheckCountersense:
    def test_countersense_widersinn(self):
        props = [
            Proposition(
                subject="sistema",
                predicate="desabilita",
                obj="validação",
                source_scenario="cenario1",
                source_step="Quando o administrador desabilita o sistema de validação",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="sistema",
                predicate="verifica",
                obj="permissão",
                source_scenario="cenario1",
                source_step="Then o sistema verifica a permissão do usuário",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_countersense(props)
        assert len(results) > 0

    def test_no_countersense(self):
        props = [
            Proposition(
                subject="usuário",
                predicate="acessa",
                obj="dashboard",
                source_scenario="cenario1",
                source_step="o usuário acessa o dashboard",
                source_file="test.feature",
                source_line=1,
            ),
        ]
        results = check_countersense(props)
        assert len(results) == 0


class TestDetectMetaOperation:
    def test_detect_disable_system(self):
        result = _detect_meta_operation("o administrador desabilita o sistema de validação")
        assert len(result) > 0
        assert "sistema_de_regras" in result

    def test_no_meta_operation(self):
        result = _detect_meta_operation("o usuário não tem acesso")
        assert len(result) == 0


class TestDetectSystemUsage:
    def test_detect_usage(self):
        result = _detect_system_usage("o usuário acessa o dashboard")
        assert "acesso" in result

    def test_no_usage(self):
        result = _detect_system_usage("o usuário é gerente")
        assert len(result) == 0


class TestCheckPerformative:
    def test_performative_contradiction(self):
        props = [
            Proposition(
                subject="sistema",
                predicate="está",
                obj="offline",
                source_scenario="cenario1",
                source_step="Dado que o sistema está offline",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="usuário",
                predicate="acessa",
                obj="dashboard",
                source_scenario="cenario1",
                source_step="When o usuário acessa o dashboard",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_performative(props)
        assert len(results) > 0
        assert results[0].severity == "warning"

    def test_no_performative(self):
        props = [
            Proposition(
                subject="sistema",
                predicate="está",
                obj="online",
                source_scenario="cenario1",
                source_step="Given o sistema está online",
                source_file="test.feature",
                source_line=1,
            ),
            Proposition(
                subject="usuário",
                predicate="acessa",
                obj="dashboard",
                source_scenario="cenario1",
                source_step="When o usuário acessa o dashboard",
                source_file="test.feature",
                source_line=2,
            ),
        ]
        results = check_performative(props)
        assert len(results) == 0
