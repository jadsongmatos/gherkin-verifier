"""
Tipo 9: Contrassenso Formal (Widersinn)

Uma teoria que, em seu conteúdo, nega as condições necessárias para
a existência de qualquer verdade ou teoria (Husserl).

No contexto de software: regras que negam o próprio motor de regras,
permissões que revogam a capacidade de conceder permissões, etc.

Tipo 10: Contradição Performativa

O ato de dizer algo desmente o conteúdo do que é dito.
No contexto de software: um cenário que testa funcionalidade X
enquanto seus preconditions desabilitam X.
"""
from __future__ import annotations

import re

from z3 import Bool, Not, Implies, And, Solver, unsat

from ..domain import ContradictionResult, Proposition


# Padrões que indicam ações destrutivas sobre componentes do sistema.
# Requerem a co-ocorrência de um VERBO DESTRUTIVO + um ALVO do sistema.
_DESTRUCTIVE_VERBS = [
    r"desabilit\w*", r"desativ\w*", r"deslig\w*", r"remov\w*", r"delet\w*",
    r"destru\w*", r"encerr\w*", r"par\w+\s+o\b",
    r"disable\w*", r"deactivate\w*", r"turn\w*\s*off", r"remove\w*",
    r"delete\w*", r"destroy\w*", r"shut\w*\s*down", r"stop\w*",
]

_SYSTEM_TARGETS = {
    # PT-BR
    "regra": "sistema_de_regras", "política": "sistema_de_regras",
    "permiss": "sistema_de_regras", "autoriza": "sistema_de_regras",
    "validaç": "sistema_de_regras", "validação": "sistema_de_regras",
    "sistema de validação": "sistema_de_regras",
    "sistema": "sistema", "serviço": "sistema", "servidor": "sistema",
    "motor": "sistema", "engine": "sistema",
    "log": "observabilidade", "auditoria": "observabilidade",
    "monitoramento": "observabilidade",
    "autenticação": "autenticacao", "sessão": "autenticacao",
    # EN
    "rule": "rule_system", "policy": "rule_system",
    "permission": "rule_system", "authorization": "rule_system",
    "validation": "rule_system",
    "system": "system", "service": "system", "server": "system",
    "logging": "observability", "audit": "observability",
    "authentication": "authentication", "session": "authentication",
}

# Padrões de ações que usam o sistema que está sendo negado
_USAGE_PATTERNS = [
    (r"verific|valid|chec|confirm|garanti", "validacao"),
    (r"acess|entr|naveg|abr", "acesso"),
    (r"cri|gera|produz|emiti", "criacao"),
    (r"consult|busc|pesquis|filtr", "consulta"),
]


def _detect_meta_operation(text: str) -> list[str]:
    """
    Detecta se um step realiza uma meta-operação destrutiva sobre o sistema.

    Requer co-ocorrência de verbo destrutivo + alvo do sistema.
    "não tem acesso ao sistema" NÃO é uma meta-operação.
    "desabilita o sistema de validação" É uma meta-operação.
    """
    text_lower = text.lower()

    # Verificar se há um verbo destrutivo no texto
    has_destructive_verb = any(
        re.search(v, text_lower) for v in _DESTRUCTIVE_VERBS
    )
    if not has_destructive_verb:
        return []

    # Verificar quais alvos do sistema são mencionados
    ops = []
    for target_pattern, label in _SYSTEM_TARGETS.items():
        if target_pattern in text_lower:
            ops.append(label)
    return ops


def _detect_system_usage(text: str) -> list[str]:
    """Detecta se um step depende do sistema para funcionar."""
    text_lower = text.lower()
    usages = []
    for pattern, label in _USAGE_PATTERNS:
        if re.search(pattern, text_lower):
            usages.append(label)
    return usages


def check_countersense(propositions: list[Proposition]) -> list[ContradictionResult]:
    """
    Verifica contrassenso formal: cenários que desabilitam os sistemas
    dos quais dependem.
    """
    results = []

    # Agrupar por cenário
    by_scenario: dict[str, list[Proposition]] = {}
    for p in propositions:
        by_scenario.setdefault(p.source_scenario, []).append(p)

    for scenario, props in by_scenario.items():
        # Detectar meta-operações destrutivas e usos do sistema
        destructive_ops: dict[str, list[Proposition]] = {}
        system_usages: dict[str, list[Proposition]] = {}

        for prop in props:
            # Detectar ações destrutivas sobre o sistema
            # (requer verbo destrutivo + alvo — não mera negação)
            meta_ops = _detect_meta_operation(prop.source_step)
            for op in meta_ops:
                destructive_ops.setdefault(op, []).append(prop)

            # Detectar uso/dependência do sistema
            usages = _detect_system_usage(prop.source_step)
            for usage in usages:
                system_usages.setdefault(usage, []).append(prop)

        # Cruzar: se uma meta-operação destrói algo que outro step usa
        _META_TO_USAGE = {
            "sistema_de_regras": ["validacao", "acesso"],
            "rule_system": ["validacao", "acesso"],
            "sistema": ["validacao", "acesso", "criacao", "consulta"],
            "system": ["validacao", "acesso", "criacao", "consulta"],
            "observabilidade": ["consulta"],
            "observability": ["consulta"],
            "autenticacao": ["acesso"],
            "authentication": ["acesso"],
            "desabilita": ["validacao", "acesso", "criacao", "consulta"],
            "disables": ["validacao", "acesso", "criacao", "consulta"],
        }

        for destroyed_system, destroy_props in destructive_ops.items():
            dependent_usages = _META_TO_USAGE.get(destroyed_system, [])
            for usage in dependent_usages:
                if usage in system_usages:
                    usage_props = system_usages[usage]
                    results.append(ContradictionResult(
                        contradiction_type="Contrassenso Formal (Widersinn)",
                        severity="critical",
                        description=(
                            f"Contrassenso no cenário '{scenario}': "
                            f"o sistema '{destroyed_system}' é desabilitado/destruído, "
                            f"mas o cenário depende dele para '{usage}'."
                        ),
                        propositions=destroy_props + usage_props,
                        details={
                            "scenario": scenario,
                            "destroyed_system": destroyed_system,
                            "dependent_usage": usage,
                            "explanation": (
                                "Como uma teoria que nega as condições de "
                                "possibilidade de qualquer teoria (Husserl), "
                                "este cenário destrói o que ele mesmo requer."
                            ),
                        },
                        source_locations=[
                            f"{p.source_file}:{p.source_line}"
                            for p in destroy_props + usage_props
                        ],
                    ))

    return results


def check_performative(propositions: list[Proposition]) -> list[ContradictionResult]:
    """
    Verifica contradição performativa: o ato de executar o cenário
    contradiz o que ele afirma.

    Exemplo: cenário que testa "sistema offline" enquanto depende de
    conectividade para rodar o teste.
    """
    results = []

    by_scenario: dict[str, list[Proposition]] = {}
    for p in propositions:
        by_scenario.setdefault(p.source_scenario, []).append(p)

    for scenario, props in by_scenario.items():
        # Detectar afirmações sobre o estado do próprio sistema de teste
        system_state_claims = []
        test_dependencies = []

        for prop in props:
            text_lower = prop.source_step.lower()
            # Afirmações de que algo está desligado/indisponível
            if any(w in text_lower for w in [
                "offline", "indisponível", "fora do ar", "desligado",
                "unavailable", "down", "disconnected", "desconectado",
            ]):
                system_state_claims.append(prop)

            # Dependências implícitas (ações que requerem o sistema)
            if any(w in text_lower for w in [
                "acessa", "navega", "clica", "envia", "submete",
                "access", "navigate", "click", "send", "submit",
                "consulta", "busca", "filtra",
            ]):
                test_dependencies.append(prop)

        if system_state_claims and test_dependencies:
            results.append(ContradictionResult(
                contradiction_type="Contradição Performativa",
                severity="warning",
                description=(
                    f"Contradição performativa no cenário '{scenario}': "
                    f"afirma que o sistema está indisponível, mas executa "
                    f"ações que dependem da disponibilidade."
                ),
                propositions=system_state_claims + test_dependencies,
                details={
                    "scenario": scenario,
                    "state_claims": [p.source_step for p in system_state_claims],
                    "dependencies": [p.source_step for p in test_dependencies],
                },
                source_locations=[
                    f"{p.source_file}:{p.source_line}"
                    for p in system_state_claims + test_dependencies
                ],
            ))

    return results
