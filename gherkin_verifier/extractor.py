"""
Extrator de proposições lógicas a partir de steps Gherkin.

Converte linguagem natural semi-estruturada (Given/When/Then) em
proposições lógicas formais para verificação.

Suporta duas abordagens:
1. Pattern-matching em português e inglês sobre padrões comuns
2. Anotações via tags Gherkin (@apt, @rel, @presupposes, etc.)
"""
from __future__ import annotations

import re
from typing import Optional

from .domain import (
    AptitudeDeclaration,
    Modality,
    PresuppositionDeclaration,
    Proposition,
    Quantifier,
    RelationDeclaration,
)
from .parser import ParsedFeature, ParsedScenario, ParsedStep


# ── Padrões de extração (PT-BR e EN) ────────────────────────────

# Negação
_NEG_PATTERNS = [
    r"\bnão\b", r"\bnão tem\b", r"\bnão pode\b", r"\bnão é\b",
    r"\bnão possui\b", r"\bnão deve\b", r"\bnem\b",
    r"\bnenhum\b", r"\bnenhuma\b",  # "nenhum X" = universal negativo
    r"\bnot\b", r"\bcannot\b", r"\bcan't\b", r"\bdoes not\b",
    r"\bdon't\b", r"\bshould not\b", r"\bshouldn't\b",
    r"\bnever\b", r"\bnone\b", r"\bno\b access",
]

# Quantificadores
_UNIVERSAL_PATTERNS = [
    r"\btodo\b", r"\btoda\b", r"\btodos\b", r"\btodas\b",
    r"\bnenhum\b", r"\bnenhuma\b", r"\bsempre\b",
    r"\ball\b", r"\bevery\b", r"\bnone\b", r"\bno\b", r"\balways\b", r"\bnever\b",
]
_PARTICULAR_PATTERNS = [
    r"\balgum\b", r"\balguma\b", r"\balguns\b", r"\balgumas\b",
    r"\bsome\b", r"\bany\b", r"\bcertain\b",
]

# Modalidade
_NECESSITY_PATTERNS = [
    r"\bdeve\b", r"\bdevem\b", r"\bobrigatório\b", r"\bobrigatoriamente\b",
    r"\bmust\b", r"\bshall\b", r"\brequired\b", r"\bmandatory\b",
]
_POSSIBILITY_PATTERNS = [
    r"\bpode\b", r"\bpodem\b", r"\bpermitido\b", r"\bopcional\b",
    r"\bcan\b", r"\bmay\b", r"\ballowed\b", r"\boptional\b",
]
_IMPOSSIBILITY_PATTERNS = [
    r"\bnão pode\b", r"\bnão podem\b", r"\bproibido\b", r"\bimpossível\b",
    r"\bcannot\b", r"\bcan't\b", r"\bforbidden\b", r"\bimpossible\b",
    r"\bprohibited\b",
]

# Prefixos opcionais (artigos e quantificadores) para extração de sujeito
_PT_PREFIX = r"(?:que\s+)?(?:o|a|os|as|todo|toda|todos|todas|nenhum|nenhuma|algum|alguma|algums|algumas)?\s*"
_EN_PREFIX = r"(?:the|all|every|no|some|any)?\s*"

# Extração de sujeito-predicado-objeto
_SPO_PATTERNS_PT = [
    # "SUJEITO tem/possui OBJETO"
    _PT_PREFIX + r"(\w[\w\s]*?)\s+(?:tem|possui|têm|possuem)\s+(?:acesso\s+(?:a|à|ao))?\s*([\w\s]+)",
    # "SUJEITO é/está OBJETO"
    _PT_PREFIX + r"(\w[\w\s]*?)\s+(?:é|está|são|estão)\s+([\w\s]+)",
    # "SUJEITO PREDICADO OBJETO" genérico — verbos de ação
    r"(\w[\w\s]*?)\s+(controla|gerencia|pertence|depende|autoriza|bloqueia|supervisiona)\s+(?:o|a|os|as)?\s*([\w\s]+)",
    # "SUJEITO deve/pode/não pode VERBO OBJETO"
    _PT_PREFIX + r"(\w[\w\s]*?)\s+(?:deve|pode|não pode|não deve)\s+(\w+)\s+(?:o|a|os|as)?\s*([\w\s]+)",
    # "SUJEITO VERBO o/a OBJETO" — verbos de ação genéricos
    _PT_PREFIX + r"(\w[\w\s]*?)\s+(gera|gerar|desabilita|desabilitar|verifica|verificar|acessa|acessar|navega|consulta)\s+(?:o|a|os|as)?\s*([\w\s]+)",
]

_SPO_PATTERNS_EN = [
    _EN_PREFIX + r"(\w[\w\s]*?)\s+(?:has|have)\s+(?:access\s+to\s+)?([\w\s]+)",
    _EN_PREFIX + r"(\w[\w\s]*?)\s+(?:is|are)\s+([\w\s]+)",
    r"(\w[\w\s]*?)\s+(controls|manages|belongs|depends|authorizes|blocks|supervises)\s+(?:the\s+)?([\w\s]+)",
]

# Tags especiais para anotação ontológica (formato: @prefix-arg1-arg2-...)
_TAG_APT = "apt"           # @apt-usuario-permissao
_TAG_REL = "rel"           # @rel-gerente-subordinado-controla-controlado_por
_TAG_PRESUP = "presupposes"  # @presupposes-autenticacao-sessao_ativa
_TAG_NEGATES = "negates"     # @negates-sessao_ativa


def _match_any(text: str, patterns: list[str]) -> bool:
    """Verifica se algum padrão regex faz match no texto."""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


def _detect_negation(text: str) -> bool:
    return _match_any(text, _NEG_PATTERNS)


def _detect_quantifier(text: str, negated: bool) -> tuple[Quantifier, bool]:
    """Retorna (quantifier, explicit) onde explicit=True se o texto contém quantificador."""
    is_universal = _match_any(text, _UNIVERSAL_PATTERNS)
    is_particular = _match_any(text, _PARTICULAR_PATTERNS)
    explicit = is_universal or is_particular

    if is_universal and negated:
        return Quantifier.UNIVERSAL_NEG, explicit
    if is_universal:
        return Quantifier.UNIVERSAL_AFF, explicit
    if is_particular and negated:
        return Quantifier.PARTICULAR_NEG, explicit
    if is_particular:
        return Quantifier.PARTICULAR_AFF, explicit
    # Default: universal afirmativa (implícita)
    return Quantifier.UNIVERSAL_AFF, False


def _detect_modality(text: str) -> Modality:
    if _match_any(text, _IMPOSSIBILITY_PATTERNS):
        return Modality.IMPOSSIBLE
    if _match_any(text, _NECESSITY_PATTERNS):
        return Modality.NECESSARY
    if _match_any(text, _POSSIBILITY_PATTERNS):
        return Modality.POSSIBLE
    return Modality.CONTINGENT


def _strip_negation(text: str) -> str:
    """Remove marcadores de negação do texto para extração limpa de SPO."""
    cleaned = text
    # Remover negações compostas primeiro (ordem importa)
    for neg in [
        "não tem", "não possui", "não pode", "não é", "não está",
        "não deve", "não são", "não estão",
        "does not have", "does not", "do not", "cannot", "can't",
        "should not", "shouldn't", "is not", "are not",
    ]:
        cleaned = re.sub(re.escape(neg), lambda m: m.group().split()[-1], cleaned, flags=re.IGNORECASE)
    # Remover "não" isolado restante
    cleaned = re.sub(r'\bnão\b\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bnot\b\s*', '', cleaned, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', cleaned).strip()


def _extract_spo(text: str) -> Optional[tuple[str, str, str]]:
    """Extrai sujeito, predicado, objeto do texto do step."""
    # Primeiro tenta com o texto original
    text_clean = text.strip().rstrip(".")
    # Também tenta com texto sem negação (para evitar que "não" polua o sujeito)
    text_no_neg = _strip_negation(text_clean)

    for attempt_text in [text_no_neg, text_clean]:
        # Tenta padrões PT-BR
        for pattern in _SPO_PATTERNS_PT:
            m = re.search(pattern, attempt_text, re.IGNORECASE)
            if m:
                groups = m.groups()
                if len(groups) == 2:
                    return (groups[0].strip(), "tem", groups[1].strip())
                elif len(groups) == 3:
                    return (groups[0].strip(), groups[1].strip(), groups[2].strip())

        # Tenta padrões EN
        for pattern in _SPO_PATTERNS_EN:
            m = re.search(pattern, attempt_text, re.IGNORECASE)
            if m:
                groups = m.groups()
                if len(groups) == 2:
                    return (groups[0].strip(), "has", groups[1].strip())
                elif len(groups) == 3:
                    return (groups[0].strip(), groups[1].strip(), groups[2].strip())

    return None


def _normalize_term(term: str) -> str:
    """Normaliza um termo removendo artigos e padronizando."""
    term = term.strip().lower()
    for prefix in ["o ", "a ", "os ", "as ", "um ", "uma ", "the ", "a ", "an "]:
        if term.startswith(prefix):
            term = term[len(prefix):]
    return term.strip().replace(" ", "_")


def _parse_tag_args(tag: str, prefix: str) -> list[str]:
    """Extrai argumentos de uma tag: @prefix-arg1-arg2 → [arg1, arg2]."""
    # Formato novo: dash-separated (compatível com Gherkin)
    if tag.startswith(f"{prefix}-"):
        rest = tag[len(prefix) + 1:]
        return [a.strip() for a in rest.split("-") if a.strip()]
    # Formato antigo: parentheses (para compatibilidade)
    m = re.match(rf"{prefix}\((.+)\)", tag)
    if m:
        return [a.strip() for a in m.group(1).split(",")]
    return []


def extract_propositions_from_step(
    step: ParsedStep,
    scenario_name: str,
    file_path: str,
) -> Optional[Proposition]:
    """Extrai uma proposição lógica de um step Gherkin."""
    spo = _extract_spo(step.text)
    if not spo:
        return None

    subject_raw, predicate_raw, obj_raw = spo
    negated = _detect_negation(step.text)
    quantifier, explicit_quantifier = _detect_quantifier(step.text, negated)
    modality = _detect_modality(step.text)

    return Proposition(
        subject=_normalize_term(subject_raw),
        predicate=_normalize_term(predicate_raw),
        obj=_normalize_term(obj_raw),
        negated=negated,
        quantifier=quantifier,
        explicit_quantifier=explicit_quantifier,
        modality=modality,
        source_step=step.text,
        source_scenario=scenario_name,
        source_file=file_path,
        source_line=step.line,
    )


def extract_aptitudes_from_tags(
    scenario: ParsedScenario,
    file_path: str,
) -> list[AptitudeDeclaration]:
    """Extrai declarações de aptidão de tags @apt(sujeito, propriedade)."""
    aptitudes = []
    for tag in scenario.tags:
        args = _parse_tag_args(tag, _TAG_APT)
        if len(args) >= 2:
            aptitudes.append(AptitudeDeclaration(
                subject_type=_normalize_term(args[0]),
                property_name=_normalize_term(args[1]),
                is_apt=True,
                source=f"{file_path}:{scenario.line}",
            ))
    return aptitudes


def extract_relations_from_tags(
    scenario: ParsedScenario,
    file_path: str,
) -> list[RelationDeclaration]:
    """Extrai declarações de relação de tags @rel(roleA, roleB, rel, inv_rel)."""
    relations = []
    for tag in scenario.tags:
        args = _parse_tag_args(tag, _TAG_REL)
        if len(args) >= 4:
            relations.append(RelationDeclaration(
                role_a=_normalize_term(args[0]),
                role_b=_normalize_term(args[1]),
                relation=_normalize_term(args[2]),
                inverse_relation=_normalize_term(args[3]),
                source=f"{file_path}:{scenario.line}",
            ))
    return relations


def extract_presuppositions_from_tags(
    scenario: ParsedScenario,
    file_path: str,
) -> list[PresuppositionDeclaration]:
    """Extrai pressuposições de tags @presupposes(...) e @negates(...)."""
    presup_args = set()
    neg_args = set()

    for tag in scenario.tags:
        p = _parse_tag_args(tag, _TAG_PRESUP)
        if p:
            presup_args.update(_normalize_term(a) for a in p)
        n = _parse_tag_args(tag, _TAG_NEGATES)
        if n:
            neg_args.update(_normalize_term(a) for a in n)

    if presup_args or neg_args:
        return [PresuppositionDeclaration(
            proposition_id=f"{file_path}:{scenario.name}",
            content=scenario.name,
            presupposes=presup_args,
            negates=neg_args,
            source=f"{file_path}:{scenario.line}",
        )]
    return []


def extract_all(feature: ParsedFeature) -> dict:
    """
    Extrai todas as estruturas lógicas de uma feature parseada.

    Retorna um dict com:
    - propositions: list[Proposition]
    - aptitudes: list[AptitudeDeclaration]
    - relations: list[RelationDeclaration]
    - presuppositions: list[PresuppositionDeclaration]
    """
    propositions = []
    aptitudes = []
    relations = []
    presuppositions = []

    # Proposições do background (aplicam-se a todos os cenários)
    bg_props = []
    for step in feature.background_steps:
        prop = extract_propositions_from_step(step, "__background__", feature.file_path)
        if prop:
            bg_props.append(prop)

    all_scenarios = list(feature.scenarios)
    for rule in feature.rules:
        all_scenarios.extend(rule.scenarios)

    for scenario in all_scenarios:
        # Proposições dos steps
        for step in scenario.steps:
            prop = extract_propositions_from_step(step, scenario.name, feature.file_path)
            if prop:
                propositions.append(prop)

        # Anotações ontológicas via tags
        aptitudes.extend(extract_aptitudes_from_tags(scenario, feature.file_path))
        relations.extend(extract_relations_from_tags(scenario, feature.file_path))
        presuppositions.extend(extract_presuppositions_from_tags(scenario, feature.file_path))

    # Inclui background props
    propositions = bg_props + propositions

    return {
        "propositions": propositions,
        "aptitudes": aptitudes,
        "relations": relations,
        "presuppositions": presuppositions,
    }
