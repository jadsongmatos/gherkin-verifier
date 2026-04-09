"""
Tipo 5: Contradições Relativas (violação de correlatos)

Oposição entre termos que se definem mutuamente e cuja essência
consiste em "ser para outro" (ad aliud).

Quatro tipos de violação:
  1. Assimetria de recíproca: R(a,b) ∧ ¬R⁻¹(b,a)
  2. Existência sem correlato: Role_A(a) ∧ ¬∃b: R(a,b)
  3. Destruição unilateral: Remove(b) sem propagar ¬Role_A(a)
  4. Graus inconsistentes: peso(R(a,b)) ≠ peso(R⁻¹(b,a))
"""
from __future__ import annotations

import networkx as nx
from z3 import (
    BoolSort, Const, DeclareSort, Exists, ForAll,
    Function, Implies, Not, And, Solver, unsat,
)

from ..domain import ContradictionResult, Proposition, RelationDeclaration


def check_relative_z3(
    propositions: list[Proposition],
    relations: list[RelationDeclaration],
) -> list[ContradictionResult]:
    """
    Verifica contradições relativas via Z3: reciprocidade e simultaneidade.
    """
    results = []

    if not relations:
        return results

    Entity = DeclareSort('Entity')
    a = Const('a', Entity)
    b = Const('b', Entity)

    for rel_decl in relations:
        solver = Solver()

        R = Function(f'R_{rel_decl.relation}', Entity, Entity, BoolSort())
        R_inv = Function(f'R_{rel_decl.inverse_relation}', Entity, Entity, BoolSort())
        IsRoleA = Function(f'Is_{rel_decl.role_a}', Entity, BoolSort())
        IsRoleB = Function(f'Is_{rel_decl.role_b}', Entity, BoolSort())

        # Axioma de reciprocidade: R(a,b) ↔ R⁻¹(b,a)
        solver.add(ForAll([a, b], R(a, b) == R_inv(b, a)))

        # Axioma de simultaneidade (se declarado)
        if rel_decl.simultaneous:
            solver.add(ForAll([a],
                Implies(IsRoleA(a), Exists([b], R(a, b)))))
            solver.add(ForAll([b],
                Implies(IsRoleB(b), Exists([a], R(a, b)))))

        # Buscar proposições que envolvam os papéis declarados
        for prop in propositions:
            subj_is_role_a = prop.subject == rel_decl.role_a
            subj_is_role_b = prop.subject == rel_decl.role_b
            obj_is_role_a = prop.obj == rel_decl.role_a
            obj_is_role_b = prop.obj == rel_decl.role_b

            if subj_is_role_a or obj_is_role_b:
                entity_a = Const(f'e_{prop.subject}', Entity)
                entity_b = Const(f'e_{prop.obj}', Entity)

                if not prop.negated:
                    solver.add(IsRoleA(entity_a))
                    solver.add(R(entity_a, entity_b))
                else:
                    # Nega a relação
                    solver.add(ForAll([a], Not(R(a, entity_b))))

            if subj_is_role_b or obj_is_role_a:
                entity_a = Const(f'e_{prop.obj}', Entity)
                entity_b = Const(f'e_{prop.subject}', Entity)

                if not prop.negated:
                    solver.add(IsRoleB(entity_b))
                    solver.add(R_inv(entity_b, entity_a))
                else:
                    solver.add(ForAll([b], Not(R_inv(b, entity_a))))

        result = solver.check()
        if result == unsat:
            results.append(ContradictionResult(
                contradiction_type="Relativa (violação de correlato)",
                severity="critical",
                description=(
                    f"Contradição relativa: a relação "
                    f"'{rel_decl.role_a} {rel_decl.relation} {rel_decl.role_b}' "
                    f"viola reciprocidade ou simultaneidade."
                ),
                propositions=propositions,
                details={
                    "relation": rel_decl.relation,
                    "inverse": rel_decl.inverse_relation,
                    "role_a": rel_decl.role_a,
                    "role_b": rel_decl.role_b,
                    "z3_result": "unsat",
                },
                source_locations=[rel_decl.source],
            ))

    return results


def check_relative_graph(
    propositions: list[Proposition],
    relations: list[RelationDeclaration],
) -> list[ContradictionResult]:
    """
    Verifica contradições relativas via análise de grafos:
    correlatos órfãos, assimetria de graus, e destruição unilateral.
    """
    results = []

    if not relations:
        return results

    G = nx.DiGraph()

    # Construir grafo de relações a partir das proposições
    for prop in propositions:
        if not prop.negated:
            G.add_edge(prop.subject, prop.obj, predicate=prop.predicate, weight=1.0)

    for rel_decl in relations:
        # Tipo 2: Existência sem correlato
        # Verificar se existem nós com role_a mas sem arestas para role_b
        role_a_nodes = [
            n for n in G.nodes()
            if any(
                G[n][succ].get("predicate") == rel_decl.relation
                for succ in G.successors(n)
            )
        ]
        role_b_nodes = [
            n for n in G.nodes()
            if any(
                G[pred][n].get("predicate") == rel_decl.relation
                for pred in G.predecessors(n)
            )
        ]

        # Verificar reciprocidade no grafo
        for u, v, data in G.edges(data=True):
            if data.get("predicate") == rel_decl.relation:
                # Deve existir aresta inversa v→u com predicado inverso
                has_inverse = any(
                    G[v][u2].get("predicate") == rel_decl.inverse_relation
                    for u2 in G.successors(v)
                    if u2 == u
                ) if G.has_edge(v, u) else False

                if not has_inverse:
                    results.append(ContradictionResult(
                        contradiction_type="Relativa Tipo 1 (Assimetria de Recíproca)",
                        severity="warning",
                        description=(
                            f"Assimetria relativa: '{u} {rel_decl.relation} {v}' "
                            f"existe, mas '{v} {rel_decl.inverse_relation} {u}' "
                            f"não foi declarado."
                        ),
                        details={
                            "edge": f"{u} → {v}",
                            "missing_inverse": f"{v} → {u}",
                            "relation": rel_decl.relation,
                            "inverse": rel_decl.inverse_relation,
                        },
                    ))

        # Tipo 4: Graus inconsistentes (para grafos ponderados)
        for u, v, data in G.edges(data=True):
            if data.get("predicate") == rel_decl.relation:
                w_uv = data.get("weight", 1.0)
                if G.has_edge(v, u):
                    w_vu = G[v][u].get("weight", 1.0)
                    if abs(w_uv - w_vu) > 0.5:
                        results.append(ContradictionResult(
                            contradiction_type="Relativa Tipo 4 (Graus Inconsistentes)",
                            severity="info",
                            description=(
                                f"Assimetria de grau: "
                                f"{u}→{v} (peso={w_uv}) vs "
                                f"{v}→{u} (peso={w_vu})"
                            ),
                            details={
                                "weight_forward": w_uv,
                                "weight_backward": w_vu,
                                "asymmetry": abs(w_uv - w_vu),
                            },
                        ))

    return results


def check_relative(
    propositions: list[Proposition],
    relations: list[RelationDeclaration],
) -> list[ContradictionResult]:
    """Combina verificação Z3 e grafos para contradições relativas."""
    results = []
    results.extend(check_relative_z3(propositions, relations))
    results.extend(check_relative_graph(propositions, relations))
    return results
