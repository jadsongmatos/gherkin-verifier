"""
Utilitários de lógica simbólica (SymPy) para pré-verificação proposicional.

Esta camada é usada como etapa intermediária entre extração e solver SMT,
permitindo normalização/formatação de fórmulas e checks rápidos de SAT/UNSAT.
"""

from __future__ import annotations

import re

from sympy import And, Implies, Not, Symbol
from sympy.logic.boolalg import Boolean, true
from sympy.logic.inference import satisfiable

from .domain import Proposition


def _sanitize_symbol_name(name: str) -> str:
    """Normaliza nomes de símbolos para uso estável no SymPy."""
    normalized = re.sub(r"[^0-9a-zA-Z_]+", "_", name)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        return "p"
    if normalized[0].isdigit():
        return f"p_{normalized}"
    return normalized


def symbol_for_key(key: str) -> Symbol:
    """Cria símbolo canônico para uma chave lógica sujeito|predicado|objeto."""
    return Symbol(_sanitize_symbol_name(key))


def literal_for_proposition(proposition: Proposition) -> Boolean:
    """Converte uma proposição para literal simbólico."""
    symbol = symbol_for_key(proposition.key)
    return Not(symbol) if proposition.negated else symbol


def conjunction(expressions: list[Boolean]) -> Boolean:
    """Conjunção simbólica com identidade booleana para lista vazia."""
    if not expressions:
        return true
    return And(*expressions)


def implication(antecedent_key: str, consequent_key: str) -> Boolean:
    """Cria expressão simbólica de implicação entre duas chaves."""
    return Implies(symbol_for_key(antecedent_key), symbol_for_key(consequent_key))


def is_unsat(expression: Boolean) -> bool:
    """Retorna True se a expressão for insatisfatível."""
    return satisfiable(expression) is False


def is_sat(expression: Boolean) -> bool:
    """Retorna True se a expressão for satisfatível."""
    return satisfiable(expression) is not False


def precheck_propositions(propositions: list[Proposition]) -> dict:
    """Pré-check simbólico simples das proposições antes do SMT.

    Agrupa por chave (subject|predicate|object). Se houver pelo menos uma
    proposição positiva e uma negativa para a mesma chave, registra como
    potencial contradição, com contagens e algumas amostras de contexto.
    """
    from collections import defaultdict

    counts: dict[str, dict[str, object]] = defaultdict(
        lambda: {"pos": 0, "neg": 0, "samples": []}
    )
    for p in propositions:
        key = p.key
        rec = counts[key]
        if p.negated:
            rec["neg"] += 1
        else:
            rec["pos"] += 1
        rec["samples"].append((p.source_scenario, p.source_step))

    potential = []
    for key, rec in counts.items():
        if rec["pos"] > 0 and rec["neg"] > 0:
            samples = [f"{sc}: {step}" for sc, step in rec["samples"][:3]]
            potential.append(
                {
                    "key": key,
                    "pos": int(rec["pos"]),
                    "neg": int(rec["neg"]),
                    "samples": samples,
                }
            )

    return {
        "total_potentials": len(potential),
        "potential": potential,
    }
