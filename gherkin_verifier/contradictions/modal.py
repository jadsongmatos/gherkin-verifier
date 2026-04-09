"""
Tipo 7: Contradições Modais (Necessário vs Possível vs Impossível)

Referem-se ao modo como o predicado se atribui ao sujeito.

Relações modais:
  Necessário(P) → ¬Possível(¬P)
  Impossível(P) → ¬Possível(P)
  Possível(P) → ¬Impossível(P)

Contradição modal: afirmar que algo é Necessário e Possível-que-não-seja,
ou que é Impossível e ao mesmo tempo Real.
"""

from __future__ import annotations

from sympy import And as SAnd
from sympy import Implies as SImplies
from sympy import Not as SNot
from sympy import Symbol
from z3 import Bool, Implies as Z3Implies, Not as Z3Not, Solver, unsat

from ..domain import ContradictionResult, Modality, Proposition
from ..symbolic import is_unsat, symbol_for_key


# Tabela de incompatibilidade modal
_MODAL_CONFLICTS: list[tuple[Modality, Modality, str]] = [
    (
        Modality.NECESSARY,
        Modality.IMPOSSIBLE,
        "Algo não pode ser simultaneamente necessário e impossível",
    ),
    (
        Modality.NECESSARY,
        Modality.POSSIBLE,
        "Se algo é necessário, não é meramente possível (é mais que possível)",
    ),
    (
        Modality.IMPOSSIBLE,
        Modality.POSSIBLE,
        "Algo não pode ser simultaneamente impossível e possível",
    ),
]


def check_modal(propositions: list[Proposition]) -> list[ContradictionResult]:
    """
    Verifica contradições modais entre proposições.

    Busca pares com mesma chave (sujeito|predicado|objeto) mas
    modalidades incompatíveis.
    """
    results = []

    # Agrupar por chave
    by_key: dict[str, list[Proposition]] = {}
    for p in propositions:
        if p.modality != Modality.CONTINGENT:
            by_key.setdefault(p.key, []).append(p)

    for key, props in by_key.items():
        modalities_present = {p.modality for p in props}

        for m1, m2, description in _MODAL_CONFLICTS:
            if m1 in modalities_present and m2 in modalities_present:
                p1 = next(p for p in props if p.modality == m1)
                p2 = next(p for p in props if p.modality == m2)

                # Verificação formal com Z3
                solver = Solver()
                necessary = Bool(f"necessary_{key}")
                possible = Bool(f"possible_{key}")
                impossible = Bool(f"impossible_{key}")

                sym_necessary = Symbol(f"necessary_{key.replace('|', '_')}")
                sym_possible = Symbol(f"possible_{key.replace('|', '_')}")
                sym_impossible = Symbol(f"impossible_{key.replace('|', '_')}")

                # Axiomas modais
                solver.add(Z3Implies(necessary, Z3Not(impossible)))
                solver.add(Z3Implies(impossible, Z3Not(possible)))
                solver.add(Z3Implies(possible, Z3Not(impossible)))
                solver.add(Z3Implies(necessary, possible))

                sympy_axioms = SAnd(
                    SImplies(sym_necessary, SNot(sym_impossible)),
                    SImplies(sym_impossible, SNot(sym_possible)),
                    SImplies(sym_possible, SNot(sym_impossible)),
                    SImplies(sym_necessary, sym_possible),
                )
                sympy_assertions = []

                # Asserções do cenário
                if m1 == Modality.NECESSARY or m2 == Modality.NECESSARY:
                    solver.add(necessary)
                    sympy_assertions.append(sym_necessary)
                if m1 == Modality.IMPOSSIBLE or m2 == Modality.IMPOSSIBLE:
                    solver.add(impossible)
                    sympy_assertions.append(sym_impossible)
                if m1 == Modality.POSSIBLE or m2 == Modality.POSSIBLE:
                    solver.add(possible)
                    sympy_assertions.append(sym_possible)

                sympy_expr = SAnd(sympy_axioms, *sympy_assertions)
                sympy_unsat = is_unsat(sympy_expr)

                if sympy_unsat and solver.check() == unsat:
                    results.append(
                        ContradictionResult(
                            contradiction_type="Modal (incompatibilidade de modalidades)",
                            severity="critical",
                            description=(
                                f"Contradição modal: {description}. "
                                f"'{p1.source_step}' ({m1.name}) vs "
                                f"'{p2.source_step}' ({m2.name})"
                            ),
                            propositions=[p1, p2],
                            details={
                                "key": key,
                                "modality_1": m1.name,
                                "modality_2": m2.name,
                                "formal": f"{m1.name}({key}) ∧ {m2.name}({key}) → ⊥",
                                "sympy_formula": str(sympy_expr),
                                "sympy_result": "unsat",
                                "z3_result": "unsat",
                            },
                            source_locations=[
                                f"{p1.source_file}:{p1.source_line}",
                                f"{p2.source_file}:{p2.source_line}",
                            ],
                        )
                    )

    return results


def check_modal_negation_conflict(
    propositions: list[Proposition],
) -> list[ContradictionResult]:
    """
    Verifica conflito entre modalidade e negação.

    Exemplo: "O usuário deve ter acesso" (NECESSARY) +
             "O usuário não tem acesso" (negado) → contradição
    """
    results = []

    by_key: dict[str, list[Proposition]] = {}
    for p in propositions:
        by_key.setdefault(p.key, []).append(p)

    for key, props in by_key.items():
        necessary_positive = [
            p for p in props if p.modality == Modality.NECESSARY and not p.negated
        ]
        contingent_negative = [
            p
            for p in props
            if p.negated and p.modality in (Modality.CONTINGENT, Modality.IMPOSSIBLE)
        ]

        for nec in necessary_positive:
            for neg in contingent_negative:
                sym_necessary = Symbol(f"necessary_{key.replace('|', '_')}")
                sym_prop = symbol_for_key(key)
                sympy_expr = SAnd(
                    SImplies(sym_necessary, sym_prop), sym_necessary, SNot(sym_prop)
                )

                if not is_unsat(sympy_expr):
                    continue

                results.append(
                    ContradictionResult(
                        contradiction_type="Modal (necessidade violada)",
                        severity="critical",
                        description=(
                            f"Contradição modal: '{nec.source_step}' declara "
                            f"necessidade, mas '{neg.source_step}' nega a "
                            f"propriedade."
                        ),
                        propositions=[nec, neg],
                        details={
                            "key": key,
                            "formal": f"□P ∧ ¬P → ⊥",
                            "sympy_formula": str(sympy_expr),
                            "sympy_result": "unsat",
                        },
                        source_locations=[
                            f"{nec.source_file}:{nec.source_line}",
                            f"{neg.source_file}:{neg.source_line}",
                        ],
                    )
                )

    return results
