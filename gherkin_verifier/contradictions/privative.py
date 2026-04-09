"""
Tipo 4: Contradições Privativas (Apt ∧ Has ∧ Priv)

Oposição entre uma perfeição (posse) e a carência dessa perfeição
(privação) em um sujeito que, por sua natureza, seria apto a possuí-la.

Modelo de três predicados:
  Apt(S, P)  → S é apto a possuir P
  Has(S, P)  → S efetivamente possui P
  Priv(S, P) → S é privado de P (derivado: Apt ∧ ¬Has)

Axiomas:
  1. Apt(s,p) ∧ ¬Has(s,p) → Priv(s,p)
  2. Has(s,p) ∧ Priv(s,p) → ⊥
  3. ¬Apt(s,p) → ¬Priv(s,p)   (pedra não é privada, é alheia)
"""
from __future__ import annotations

from z3 import (
    BoolSort, Const, DeclareSort, ForAll, Function,
    Implies, Not, And, Solver, unsat,
)

from ..domain import (
    AptitudeDeclaration,
    ContradictionResult,
    Proposition,
)


def check_privative(
    propositions: list[Proposition],
    aptitudes: list[AptitudeDeclaration],
) -> list[ContradictionResult]:
    """
    Verifica contradições privativas usando Z3 com lógica de primeira ordem.

    Detecta quando um sujeito apto está simultaneamente em posse e em
    privação da mesma propriedade.
    """
    results = []

    if not aptitudes:
        return results

    # Definir sorts
    Subject = DeclareSort('Subject')
    Property = DeclareSort('Property')

    # Funções
    Apt = Function('Apt', Subject, Property, BoolSort())
    Has = Function('Has', Subject, Property, BoolSort())
    Priv = Function('Priv', Subject, Property, BoolSort())

    s = Const('s', Subject)
    p = Const('p', Property)

    solver = Solver()

    # ── Axiomas estruturais ──────────────────────────────────────
    # Axioma 1: Privação = Aptidão sem Posse
    solver.add(ForAll([s, p],
        Implies(And(Apt(s, p), Not(Has(s, p))), Priv(s, p))))

    # Axioma 2: Contradição privativa é impossível
    solver.add(ForAll([s, p],
        Implies(And(Has(s, p), Priv(s, p)), False)))

    # Axioma 3: Sem aptidão não há privação
    solver.add(ForAll([s, p],
        Implies(Not(Apt(s, p)), Not(Priv(s, p)))))

    # ── Criar constantes para sujeitos e propriedades ────────────
    subject_consts: dict[str, Const] = {}
    property_consts: dict[str, Const] = {}

    def get_subject(name: str):
        if name not in subject_consts:
            subject_consts[name] = Const(f"subj_{name}", Subject)
        return subject_consts[name]

    def get_property(name: str):
        if name not in property_consts:
            property_consts[name] = Const(f"prop_{name}", Property)
        return property_consts[name]

    # ── Adicionar aptidões ───────────────────────────────────────
    for apt in aptitudes:
        subj = get_subject(apt.subject_type)
        prop = get_property(apt.property_name)
        if apt.is_apt:
            solver.add(Apt(subj, prop))
        else:
            solver.add(Not(Apt(subj, prop)))

    # ── Adicionar proposições como Has/¬Has ──────────────────────
    prop_groups: dict[tuple[str, str], list[Proposition]] = {}
    for proposition in propositions:
        key = (proposition.subject, proposition.obj)
        prop_groups.setdefault(key, []).append(proposition)

    for (subj_name, obj_name), props in prop_groups.items():
        subj = get_subject(subj_name)
        prop = get_property(obj_name)

        for proposition in props:
            if proposition.negated:
                solver.add(Not(Has(subj, prop)))
            else:
                solver.add(Has(subj, prop))

    # ── Verificar ────────────────────────────────────────────────
    result = solver.check()

    if result == unsat:
        # Encontrar quais pares sujeito-propriedade estão em conflito
        # Verificar incrementalmente
        for (subj_name, obj_name), props in prop_groups.items():
            has_positive = any(not p.negated for p in props)
            has_negative = any(p.negated for p in props)
            is_apt = any(
                a.subject_type == subj_name and a.property_name == obj_name
                for a in aptitudes
            )

            if is_apt and has_positive and has_negative:
                results.append(ContradictionResult(
                    contradiction_type="Privativa (Apt ∧ Has ∧ Priv)",
                    severity="critical",
                    description=(
                        f"Contradição privativa: '{subj_name}' é apto a "
                        f"possuir '{obj_name}', mas está simultaneamente "
                        f"em posse e em privação."
                    ),
                    propositions=props,
                    details={
                        "subject": subj_name,
                        "property": obj_name,
                        "is_apt": True,
                        "has_assertion": True,
                        "privation_assertion": True,
                        "formal": (
                            f"Apt({subj_name},{obj_name}) ∧ "
                            f"Has({subj_name},{obj_name}) ∧ "
                            f"¬Has({subj_name},{obj_name}) → ⊥"
                        ),
                        "z3_result": "unsat",
                    },
                    source_locations=[
                        f"{p.source_file}:{p.source_line}" for p in props
                    ],
                ))

        # Se nenhum par específico identificado, reportar geral
        if not results:
            results.append(ContradictionResult(
                contradiction_type="Privativa (Apt ∧ Has ∧ Priv)",
                severity="critical",
                description=(
                    "Contradição privativa detectada no conjunto de "
                    "regras e aptidões. O sistema é insatisfatível."
                ),
                propositions=propositions,
                details={"z3_result": "unsat"},
            ))

    return results


def classify_absence(
    subject: str,
    property_name: str,
    aptitudes: list[AptitudeDeclaration],
) -> str:
    """
    Classifica uma ausência como privação ou mera carência.

    Retorna:
    - "privação": sujeito é apto mas não possui (cego)
    - "carência": sujeito não é apto, ausência é natural (pedra sem visão)
    - "desconhecido": sem informação de aptidão
    """
    for apt in aptitudes:
        if apt.subject_type == subject and apt.property_name == property_name:
            return "privação" if apt.is_apt else "carência"
    return "desconhecido"
