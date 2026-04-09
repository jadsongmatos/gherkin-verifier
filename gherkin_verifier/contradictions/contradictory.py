"""
Tipo 1: Contradições Contraditórias (A ∧ ¬A)

A oposição mais radical: entre um termo e sua negação absoluta.
Não admite meio-termo. SAT(A ∧ ¬A) → insatisfatível.

Verifica se existem proposições que afirmam e negam o mesmo predicado
sobre o mesmo sujeito e objeto simultaneamente.

Importante: proposições de cenários diferentes só são contraditórias
se compartilham o mesmo contexto (Given/preconditions). Cenários com
precondições distintas representam ramos condicionais, não contradições.
"""

from __future__ import annotations

from sympy import And as SAnd
from sympy import Not as SNot
from z3 import Bool, Implies as Z3Implies, Not, Solver, unsat

from ..domain import ContradictionResult, Proposition
from ..symbolic import (
    conjunction,
    implication,
    is_unsat,
    literal_for_proposition,
    symbol_for_key,
)


# Cache de contexto por cenário, preenchido pelo engine antes de chamar os checkers
_scenario_context_cache: dict[str, set[str]] = {}


def set_scenario_contexts(contexts: dict[str, set[str]]):
    """
    Define o cache de contexto dos cenários, usando os steps raw do parser.

    Deve ser chamado pelo engine antes de executar as verificações.
    contexts: {scenario_name: {step_text_normalizado, ...}} para Given+When steps.
    """
    global _scenario_context_cache
    _scenario_context_cache = contexts


def _get_scenario_context(props: list[Proposition], scenario: str) -> set[str]:
    """
    Retorna a assinatura de contexto de um cenário.

    Usa o cache preenchido pelo engine (que tem acesso aos steps raw).
    Fallback para proposições se o cache não estiver disponível.
    """
    if scenario in _scenario_context_cache:
        return _scenario_context_cache[scenario]

    # Fallback: usar proposições
    context_keys = set()
    for p in props:
        if p.source_scenario == scenario:
            step = p.source_step.lower()
            if any(kw in step for kw in ["dado", "given", "que o", "que a"]):
                context_keys.add(f"{p.key}:{'neg' if p.negated else 'pos'}")
    return context_keys


def _scenarios_share_context(
    all_props: list[Proposition],
    scenario_a: str,
    scenario_b: str,
) -> bool:
    """
    Verifica se dois cenários compartilham o mesmo contexto (precondições).

    Se o contexto é diferente (ex: "credenciais válidas" vs "credenciais inválidas"),
    não há contradição — são ramos condicionais legítimos.
    """
    ctx_a = _get_scenario_context(all_props, scenario_a)
    ctx_b = _get_scenario_context(all_props, scenario_b)

    # Se um dos cenários não tem contexto explícito, considerar potencialmente contraditório
    if not ctx_a or not ctx_b:
        return True

    # Contextos idênticos → potencial contradição
    # Contextos diferentes → ramos condicionais, sem contradição
    return ctx_a == ctx_b


def check_contradictory(propositions: list[Proposition]) -> list[ContradictionResult]:
    """
    Verifica contradições do tipo A ∧ ¬A entre proposições.

    Para cada par de proposições com a mesma chave (sujeito|predicado|objeto),
    verifica se uma afirma e outra nega, considerando o contexto dos cenários.
    """
    results = []

    # Agrupar por chave canônica
    by_key: dict[str, list[Proposition]] = {}
    for p in propositions:
        by_key.setdefault(p.key, []).append(p)

    for key, props in by_key.items():
        affirmatives = [p for p in props if not p.negated]
        negatives = [p for p in props if p.negated]

        if not affirmatives or not negatives:
            continue

        for aff in affirmatives:
            for neg in negatives:
                # Mesmo cenário → contradição direta (sempre)
                same_scenario = aff.source_scenario == neg.source_scenario

                # Cenários diferentes → só contraditório se contexto é o mesmo
                if not same_scenario:
                    if not _scenarios_share_context(
                        propositions, aff.source_scenario, neg.source_scenario
                    ):
                        continue

                # Verificação via Z3
                solver = Solver()
                var = Bool(f"prop_{key}")
                solver.add(var)
                solver.add(Not(var))

                # Pré-check simbólico com SymPy
                symbolic_var = symbol_for_key(key)
                symbolic_expr = SAnd(symbolic_var, SNot(symbolic_var))
                sympy_unsat = is_unsat(symbolic_expr)

                if sympy_unsat and solver.check() == unsat:
                    results.append(
                        ContradictionResult(
                            contradiction_type="Contraditória (A ∧ ¬A)",
                            severity="critical",
                            description=(
                                f"Contradição direta: '{aff.source_step}' "
                                f"contradiz '{neg.source_step}'"
                            ),
                            propositions=[aff, neg],
                            details={
                                "key": key,
                                "formal": f"{key} ∧ ¬{key} = ⊥",
                                "sympy_formula": str(symbolic_expr),
                                "sympy_result": "unsat",
                                "z3_result": "unsat",
                                "same_scenario": same_scenario,
                                "scenario_a": aff.source_scenario,
                                "scenario_b": neg.source_scenario,
                            },
                            source_locations=[
                                f"{aff.source_file}:{aff.source_line} ({aff.source_scenario})",
                                f"{neg.source_file}:{neg.source_line} ({neg.source_scenario})",
                            ],
                        )
                    )

    return results


def check_contradictory_with_rules(
    propositions: list[Proposition],
    implication_rules: list[tuple[str, str]],
) -> list[ContradictionResult]:
    """
    Verifica contradições considerando regras de implicação.

    Exemplo: Se "Caixa → permissões de Gerente" e "Gerente → acesso"
    e "Caixa → ¬acesso", então há contradição indireta.

    implication_rules: lista de (antecedente_key, consequente_key)
    """
    results = []
    solver = Solver()

    symbolic_literals = [literal_for_proposition(p) for p in propositions]
    symbolic_rules = [implication(ant, cons) for ant, cons in implication_rules]
    symbolic_expr = conjunction(symbolic_literals + symbolic_rules)
    sympy_unsat = is_unsat(symbolic_expr)

    vars_map: dict[str, Bool] = {}
    for p in propositions:
        if p.key not in vars_map:
            vars_map[p.key] = Bool(f"p_{p.key}")

    for p in propositions:
        var = vars_map[p.key]
        if p.negated:
            solver.add(Not(var))
        else:
            solver.add(var)

    for ant_key, cons_key in implication_rules:
        if ant_key in vars_map and cons_key in vars_map:
            solver.add(Z3Implies(vars_map[ant_key], vars_map[cons_key]))

    if sympy_unsat and solver.check() == unsat:
        results.append(
            ContradictionResult(
                contradiction_type="Contraditória Indireta (via implicação)",
                severity="critical",
                description=(
                    "Contradição indireta detectada: o conjunto de regras e "
                    "proposições é insatisfatível."
                ),
                propositions=propositions,
                details={
                    "rules_count": len(implication_rules),
                    "props_count": len(propositions),
                    "sympy_formula": str(symbolic_expr),
                    "sympy_result": "unsat",
                    "z3_result": "unsat",
                },
            )
        )

    return results
