"""
Tipo 6: Autonegação (presupposes ∩ negates ≠ ∅)

A contradição não está entre duas proposições externas, mas entre
uma proposição e as condições necessárias para que ela possa ser afirmada.

Três formas:
  Performativa:  Afirma(S, P) ∧ P → ¬Exists(S)
  Epistêmica:    Afirma(S, P) ∧ P → ¬Knowable(P)
  Fundacional:   T ∧ T → ¬Valid(LogicUsedBy(T))
"""
from __future__ import annotations

from z3 import Bool, Not, Implies, Solver, unsat

from ..domain import ContradictionResult, PresuppositionDeclaration, Proposition


def _classify_self_negation(destroyed_foundations: set[str]) -> str:
    """Classifica o tipo de autonegação baseado nos fundamentos destruídos."""
    performative_markers = {
        "subject_existence", "agent_existence", "user_existence",
        "autenticacao", "sessao_ativa", "authentication",
    }
    epistemic_markers = {
        "knowability", "cognoscibilidade", "observability",
        "readability", "visibility",
    }
    foundational_markers = {
        "logic_validity", "rule_engine_active", "system_active",
        "regra_ativa", "validacao_ativa", "authorization_system",
    }

    if destroyed_foundations & performative_markers:
        return "Performativa"
    if destroyed_foundations & epistemic_markers:
        return "Epistêmica"
    if destroyed_foundations & foundational_markers:
        return "Fundacional"
    return "Genérica"


def check_self_negation_structural(
    presuppositions: list[PresuppositionDeclaration],
) -> list[ContradictionResult]:
    """
    Verifica autonegação estrutural: presupposes ∩ negates ≠ ∅.

    Baseado no grafo de dependência de fundamentos.
    """
    results = []

    for presup in presuppositions:
        destroyed = presup.self_negated_foundations
        if destroyed:
            neg_type = _classify_self_negation(destroyed)
            results.append(ContradictionResult(
                contradiction_type=f"Autonegação {neg_type}",
                severity="critical",
                description=(
                    f"Autonegação detectada em '{presup.content}': "
                    f"a proposição destrói os fundamentos que ela mesma "
                    f"pressupõe: {destroyed}"
                ),
                details={
                    "proposition": presup.content,
                    "presupposes": list(presup.presupposes),
                    "negates": list(presup.negates),
                    "destroyed_foundations": list(destroyed),
                    "type": neg_type,
                },
                source_locations=[presup.source],
            ))

    return results


def check_self_negation_z3(
    propositions: list[Proposition],
) -> list[ContradictionResult]:
    """
    Verifica autonegação via reductio ad absurdum com Z3.

    Detecta quando o conjunto de proposições de um cenário
    cria condições que negam suas próprias premissas (Given nega Then,
    ou Then destrói Given).
    """
    results = []

    # Agrupar proposições por cenário
    by_scenario: dict[str, list[Proposition]] = {}
    for p in propositions:
        by_scenario.setdefault(p.source_scenario, []).append(p)

    for scenario_name, props in by_scenario.items():
        if len(props) < 2:
            continue

        # Separar premissas (Given) e conclusões (Then)
        # Given = condições de possibilidade
        # Then = o que se afirma
        givens = [p for p in props if "Given" in p.source_step or "Dado" in p.source_step
                  or p.source_step.startswith("Given") or p.source_step.startswith("Dado")]
        thens = [p for p in props if "Then" in p.source_step or "Então" in p.source_step
                 or p.source_step.startswith("Then") or p.source_step.startswith("Então")]

        if not givens and not thens:
            # Usar heurística: primeiros steps são premissas, últimos são conclusões
            mid = len(props) // 2
            givens = props[:mid] if mid > 0 else props[:1]
            thens = props[mid:] if mid > 0 else props[1:]

        if not givens or not thens:
            continue

        # Verificar se alguma conclusão contradiz alguma premissa
        solver = Solver()
        var_map: dict[str, Bool] = {}

        for p in givens:
            if p.key not in var_map:
                var_map[p.key] = Bool(f"g_{p.key}")
            var = var_map[p.key]
            solver.add(var if not p.negated else Not(var))

        for p in thens:
            if p.key not in var_map:
                var_map[p.key] = Bool(f"t_{p.key}")
            var = var_map[p.key]
            solver.add(var if not p.negated else Not(var))

        if solver.check() == unsat:
            results.append(ContradictionResult(
                contradiction_type="Autonegação (Then destrói Given)",
                severity="critical",
                description=(
                    f"Cenário '{scenario_name}': as conclusões (Then) "
                    f"negam as premissas (Given) que as fundamentam."
                ),
                propositions=props,
                details={
                    "scenario": scenario_name,
                    "givens": [p.source_step for p in givens],
                    "thens": [p.source_step for p in thens],
                    "z3_result": "unsat",
                },
                source_locations=[
                    f"{p.source_file}:{p.source_line}" for p in props
                ],
            ))

    return results


def check_self_negation(
    propositions: list[Proposition],
    presuppositions: list[PresuppositionDeclaration],
) -> list[ContradictionResult]:
    """Combina verificação estrutural e Z3 para autonegação."""
    results = []
    results.extend(check_self_negation_structural(presuppositions))
    results.extend(check_self_negation_z3(propositions))
    return results
