"""
Tipo 2: Contradições Contrárias (A vs E no Quadrado Lógico)

Duas proposições universais que não podem ser ambas verdadeiras,
mas podem ser ambas falsas.

Verificação:
  SAT(A ∧ B) → insatisfatível (não podem coexistir)
  SAT(¬A ∧ ¬B) → satisfatível (existe meio-termo)

Exemplo: "Todo caixa tem acesso" vs "Nenhum caixa tem acesso"
"""

from __future__ import annotations

from sympy import And as SAnd
from sympy import Not as SNot
from z3 import Bool, Not, And, Solver, sat, unsat

from ..domain import ContradictionResult, Proposition, Quantifier
from ..symbolic import is_sat, is_unsat, symbol_for_key


def check_contrary(propositions: list[Proposition]) -> list[ContradictionResult]:
    """
    Verifica contradições contrárias entre proposições universais.

    Busca pares onde:
    - Mesmo sujeito e objeto
    - Uma é Universal Afirmativa (A) e outra é Universal Negativa (E)

    Nota: Contrárias são verificadas sem considerar contexto de cenário,
    pois representam conflitos de política universal ("Todo X é P" vs
    "Nenhum X é P") que não podem coexistir independentemente da
    precondição que os motivou.
    """
    results = []

    by_subject_obj: dict[tuple[str, str], list[Proposition]] = {}
    for p in propositions:
        key = (p.subject, p.obj)
        by_subject_obj.setdefault(key, []).append(p)

    for (subj, obj), props in by_subject_obj.items():
        universals_aff = [
            p
            for p in props
            if p.quantifier == Quantifier.UNIVERSAL_AFF and not p.negated
        ]
        universals_neg = [
            p
            for p in props
            if p.quantifier == Quantifier.UNIVERSAL_NEG
            or (p.quantifier == Quantifier.UNIVERSAL_AFF and p.negated)
        ]

        if not universals_aff or not universals_neg:
            continue

        for a_prop in universals_aff:
            for e_prop in universals_neg:
                # Cross-scenario contrárias only fire when at least one
                # proposition has an explicit quantifier ("todo", "nenhum")
                if a_prop.source_scenario != e_prop.source_scenario:
                    if not (a_prop.explicit_quantifier or e_prop.explicit_quantifier):
                        continue

                # Test 1: SAT(A ∧ E) must be unsatisfiable
                s1 = Solver()
                var_a = Bool(f"A_{a_prop.key}")
                s1.add(var_a)
                s1.add(Not(var_a))
                test1_unsat = s1.check() == unsat

                symbol_a = symbol_for_key(a_prop.key)
                sympy_test1_expr = SAnd(symbol_a, SNot(symbol_a))
                sympy_test1_unsat = is_unsat(sympy_test1_expr)

                # Test 2: SAT(¬A ∧ ¬E) must be satisfiable (middle term exists)
                s2 = Solver()
                var_a2 = Bool(f"A2_{a_prop.key}")
                var_e2 = Bool(f"E2_{e_prop.key}")
                s2.add(Not(var_a2))
                s2.add(Not(var_e2))
                test2_sat = s2.check() == sat

                sympy_a2 = symbol_for_key(f"A2_{a_prop.key}")
                sympy_e2 = symbol_for_key(f"E2_{e_prop.key}")
                sympy_test2_expr = SAnd(SNot(sympy_a2), SNot(sympy_e2))
                sympy_test2_sat = is_sat(sympy_test2_expr)

                if test1_unsat and test2_sat and sympy_test1_unsat and sympy_test2_sat:
                    results.append(
                        ContradictionResult(
                            contradiction_type="Contrária (A vs E)",
                            severity="critical",
                            description=(
                                f"Oposição contrária: '{a_prop.source_step}' "
                                f"e '{e_prop.source_step}' não podem ser "
                                f"ambas verdadeiras (mas ambas podem ser falsas)."
                            ),
                            propositions=[a_prop, e_prop],
                            details={
                                "subject": subj,
                                "object": obj,
                                "test_both_true": "insatisfatível",
                                "test_both_false": "satisfatível (meio-termo existe)",
                                "sympy_test_both_true": str(sympy_test1_expr),
                                "sympy_test_both_true_result": "unsat",
                                "sympy_test_both_false": str(sympy_test2_expr),
                                "sympy_test_both_false_result": "sat",
                                "formal": (
                                    f"∀{subj}: P({subj},{obj}) ∧ "
                                    f"∀{subj}: ¬P({subj},{obj}) = ⊥"
                                ),
                            },
                            source_locations=[
                                f"{a_prop.source_file}:{a_prop.source_line}",
                                f"{e_prop.source_file}:{e_prop.source_line}",
                            ],
                        )
                    )

    return results
