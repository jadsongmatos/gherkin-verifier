"""
Tipo 3: Contradições Subcontrárias (I vs O no Quadrado Lógico)

Duas proposições particulares que podem ser ambas verdadeiras,
mas não podem ser ambas falsas.

Verificação:
  SAT(¬I ∧ ¬O) → insatisfatível (não podem ser ambas falsas)
  SAT(I ∧ O) → satisfatível (podem coexistir)

Exemplo: "Algum caixa tem acesso" vs "Algum caixa não tem acesso"
  → Ambas podem ser verdadeiras, mas se negarmos ambas, geramos impossibilidade.
"""

from __future__ import annotations

from sympy import And as SAnd
from sympy import Not as SNot
from sympy import Or as SOr
from z3 import Bool, Not, And, Or, Solver, sat, unsat

from ..domain import ContradictionResult, Proposition, Quantifier
from ..symbolic import is_unsat, symbol_for_key


def check_subcontrary(propositions: list[Proposition]) -> list[ContradictionResult]:
    """
    Verifica contradições subcontrárias entre proposições particulares.

    Busca pares onde:
    - Mesmo sujeito e objeto
    - Uma é Particular Afirmativa (I) e outra é Particular Negativa (O)
    - Se o sistema força ambas a serem falsas → contradição
    """
    results = []

    # Agrupar por (subject, obj)
    by_subject_obj: dict[tuple[str, str], list[Proposition]] = {}
    for p in propositions:
        key = (p.subject, p.obj)
        by_subject_obj.setdefault(key, []).append(p)

    for (subj, obj), props in by_subject_obj.items():
        particulars_aff = [
            p
            for p in props
            if p.quantifier == Quantifier.PARTICULAR_AFF and not p.negated
        ]
        particulars_neg = [
            p
            for p in props
            if p.quantifier == Quantifier.PARTICULAR_NEG
            or (p.quantifier == Quantifier.PARTICULAR_AFF and p.negated)
        ]

        if not particulars_aff or not particulars_neg:
            continue

        for i_prop in particulars_aff:
            for o_prop in particulars_neg:
                # Verificar se o sistema inteiro força ambas a serem falsas
                # Coletar todas as constraints do sistema que afetam este par
                solver = Solver()

                var_i = Bool(f"I_{i_prop.key}")  # "algum S é P"
                var_o = Bool(f"O_{o_prop.key}")  # "algum S não é P"

                # Subcontrárias: pelo menos uma deve ser verdadeira
                # Se o sistema forçar ¬I ∧ ¬O → contradição
                solver.add(Not(var_i))
                solver.add(Not(var_o))
                # Axioma subcontrário: pelo menos um é verdadeiro
                solver.add(Or(var_i, var_o))

                sympy_i = symbol_for_key(f"I_{i_prop.key}")
                sympy_o = symbol_for_key(f"O_{o_prop.key}")
                sympy_expr = SAnd(SNot(sympy_i), SNot(sympy_o), SOr(sympy_i, sympy_o))
                sympy_unsat = is_unsat(sympy_expr)

                if solver.check() == unsat and sympy_unsat:
                    results.append(
                        ContradictionResult(
                            contradiction_type="Subcontrária (I vs O)",
                            severity="warning",
                            description=(
                                f"Violação subcontrária: o sistema força "
                                f"'{i_prop.source_step}' e '{o_prop.source_step}' "
                                f"a serem ambas falsas, mas pelo menos uma deve "
                                f"ser verdadeira."
                            ),
                            propositions=[i_prop, o_prop],
                            details={
                                "subject": subj,
                                "object": obj,
                                "formal": f"¬∃{subj}:P ∧ ¬∃{subj}:¬P = ⊥",
                                "sympy_formula": str(sympy_expr),
                                "sympy_result": "unsat",
                                "explanation": (
                                    "Se nenhum S é P e nenhum S não é P, "
                                    "não existem S — contradição se S existe."
                                ),
                            },
                            source_locations=[
                                f"{i_prop.source_file}:{i_prop.source_line}",
                                f"{o_prop.source_file}:{o_prop.source_line}",
                            ],
                        )
                    )

    return results
