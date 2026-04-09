"""
Tipo 8: Contradições de Suplência (Suppositio)

Ocorre quando o significado de um termo muda no meio do raciocínio,
invalidando a identidade lógica — o sofisma dos quatro termos
(quaternio terminorum).

Detecção: pré-processamento semântico que identifica termos homônimos
usados com aceções diferentes em cenários distintos.
"""
from __future__ import annotations

from collections import defaultdict

from ..domain import ContradictionResult, Proposition


def _compute_term_context(prop: Proposition) -> tuple[str, str]:
    """
    Retorna o contexto semântico de um termo baseado nos co-ocorrentes.

    O "contexto" de um sujeito é definido pelo par (predicado, objeto).
    Se o mesmo sujeito aparece com predicados/objetos semanticamente
    incompatíveis, pode haver suplência.
    """
    return (prop.predicate, prop.obj)


def check_suppositio(propositions: list[Proposition]) -> list[ContradictionResult]:
    """
    Verifica contradições de suplência (ambiguidade de termos).

    Detecta quando o mesmo termo (sujeito) é usado com aceções
    diferentes que geram consequências contraditórias.

    Exemplo: "usuário" em um cenário refere-se a "usuário autenticado"
    e em outro a "usuário anônimo" — o termo médio muda de significado.
    """
    results = []

    # Agrupar por sujeito e rastrear contextos por cenário
    subject_contexts: dict[str, dict[str, list[tuple[str, str]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    subject_props: dict[str, list[Proposition]] = defaultdict(list)

    for prop in propositions:
        ctx = _compute_term_context(prop)
        subject_contexts[prop.subject][prop.source_scenario].append(ctx)
        subject_props[prop.subject].append(prop)

    for subject, scenario_contexts in subject_contexts.items():
        if len(scenario_contexts) < 2:
            continue

        # Verificar se o sujeito tem predicados contraditórios em cenários diferentes
        all_contexts = []
        for scenario, contexts in scenario_contexts.items():
            all_contexts.append((scenario, set(contexts)))

        for i, (sc_a, ctx_a) in enumerate(all_contexts):
            for sc_b, ctx_b in all_contexts[i+1:]:
                # Procurar predicados idênticos com objetos conflitantes
                preds_a = {pred for pred, _ in ctx_a}
                preds_b = {pred for pred, _ in ctx_b}
                shared_preds = preds_a & preds_b

                for pred in shared_preds:
                    objs_a = {obj for p, obj in ctx_a if p == pred}
                    objs_b = {obj for p, obj in ctx_b if p == pred}

                    if objs_a != objs_b and objs_a and objs_b:
                        # Verificar se alguma prop é negada e outra não
                        props_a = [
                            p for p in subject_props[subject]
                            if p.source_scenario == sc_a and p.predicate == pred
                        ]
                        props_b = [
                            p for p in subject_props[subject]
                            if p.source_scenario == sc_b and p.predicate == pred
                        ]

                        neg_a = any(p.negated for p in props_a)
                        neg_b = any(p.negated for p in props_b)
                        pos_a = any(not p.negated for p in props_a)
                        pos_b = any(not p.negated for p in props_b)

                        if (neg_a and pos_b) or (neg_b and pos_a):
                            all_involved = props_a + props_b
                            results.append(ContradictionResult(
                                contradiction_type="Suplência (quaternio terminorum)",
                                severity="warning",
                                description=(
                                    f"Possível suplência: o termo '{subject}' "
                                    f"é usado com aceções diferentes nos cenários "
                                    f"'{sc_a}' e '{sc_b}'. O predicado '{pred}' "
                                    f"produz resultados opostos."
                                ),
                                propositions=all_involved,
                                details={
                                    "subject": subject,
                                    "predicate": pred,
                                    "scenario_a": sc_a,
                                    "scenario_b": sc_b,
                                    "objects_a": list(objs_a),
                                    "objects_b": list(objs_b),
                                    "explanation": (
                                        "O mesmo termo pode estar sendo usado com "
                                        "significados diferentes (equivocidade), "
                                        "invalidando o raciocínio como um sofisma "
                                        "dos quatro termos."
                                    ),
                                },
                                source_locations=[
                                    f"{p.source_file}:{p.source_line}" for p in all_involved
                                ],
                            ))

    return results
