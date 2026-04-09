"""
Engine principal de verificação — orquestra todos os engines de contradição.

Pipeline:
  .feature → Parser → Extrator → Expressões simbólicas (SymPy)
          → [10 Engines de Contradição] → Relatório
"""

from __future__ import annotations

from pathlib import Path

from .domain import ContradictionResult, VerificationReport
from .extractor import extract_all
from .parser import parse_feature_file, parse_feature_string, ParsedFeature

from .contradictions.contradictory import (
    check_contradictory,
    check_contradictory_with_rules,
    set_scenario_contexts,
)
from .contradictions.contrary import check_contrary
from .contradictions.subcontrary import check_subcontrary
from .contradictions.privative import check_privative
from .contradictions.relative import check_relative
from .contradictions.self_negation import check_self_negation
from .contradictions.modal import check_modal, check_modal_negation_conflict
from .contradictions.suppositio import check_suppositio
from .contradictions.countersense import check_countersense, check_performative
from .symbolic import precheck_propositions


def verify_feature(feature: ParsedFeature) -> VerificationReport:
    """
    Executa todas as verificações de contradição em uma feature parseada.

    Retorna um VerificationReport completo.
    """
    report = VerificationReport(
        feature_file=feature.file_path,
        total_scenarios=len(feature.scenarios)
        + sum(len(r.scenarios) for r in feature.rules),
    )

    # Extrair proposições e anotações ontológicas
    extracted = extract_all(feature)
    propositions = extracted["propositions"]
    aptitudes = extracted["aptitudes"]
    relations = extracted["relations"]
    presuppositions = extracted["presuppositions"]

    report.total_propositions = len(propositions)
    # Pré-checagens simbólicas (SymPy) para acelerar SMT
    report.precheck = precheck_propositions(propositions)

    # Construir cache de contexto dos cenários usando steps raw do parser.
    # Contexto = Given + When steps (texto normalizado) de cada cenário.
    # Isso permite distinguir cenários com precondições diferentes.
    scenario_contexts: dict[str, set[str]] = {}
    all_scenarios = list(feature.scenarios)
    for rule in feature.rules:
        all_scenarios.extend(rule.scenarios)
    for sc in all_scenarios:
        ctx = set()
        for step in sc.steps:
            kw = step.effective_keyword.lower()
            if kw in ("given", "dado", "quando", "when", "e", "and", "but", "mas", "*"):
                # Excluir Then/Então do contexto
                ctx.add(step.text.strip().lower())
            elif kw in ("then", "então", "entao"):
                pass  # Then é conclusão, não contexto
            else:
                ctx.add(step.text.strip().lower())
        # Remover steps Then que foram erroneamente incluídos
        scenario_contexts[sc.name] = ctx
    # Background steps também são parte do contexto de todos os cenários
    bg_text = {s.text.strip().lower() for s in feature.background_steps}
    for name in scenario_contexts:
        scenario_contexts[name] |= bg_text

    set_scenario_contexts(scenario_contexts)

    if not propositions:
        return report

    # ── 1. Contraditórias (A ∧ ¬A) ──────────────────────────────
    report.contradictions.extend(check_contradictory(propositions))

    # ── 2. Contrárias (A vs E) ───────────────────────────────────
    report.contradictions.extend(check_contrary(propositions))

    # ── 3. Subcontrárias (I vs O) ────────────────────────────────
    report.contradictions.extend(check_subcontrary(propositions))

    # ── 4. Privativas (Apt ∧ Has ∧ Priv) ────────────────────────
    report.contradictions.extend(check_privative(propositions, aptitudes))

    # ── 5. Relativas (violação de correlatos) ────────────────────
    report.contradictions.extend(check_relative(propositions, relations))

    # ── 6. Autonegação ───────────────────────────────────────────
    report.contradictions.extend(check_self_negation(propositions, presuppositions))

    # ── 7. Modais ────────────────────────────────────────────────
    report.contradictions.extend(check_modal(propositions))
    report.contradictions.extend(check_modal_negation_conflict(propositions))

    # ── 8. Suplência (ambiguidade de termos) ─────────────────────
    report.contradictions.extend(check_suppositio(propositions))

    # ── 9. Contrassenso Formal ───────────────────────────────────
    report.contradictions.extend(check_countersense(propositions))

    # ── 10. Contradição Performativa ─────────────────────────────
    report.contradictions.extend(check_performative(propositions))

    return report


def verify_file(file_path: str | Path) -> VerificationReport:
    """Verifica um arquivo .feature."""
    feature = parse_feature_file(file_path)
    return verify_feature(feature)


def verify_string(content: str, source: str = "<string>") -> VerificationReport:
    """Verifica uma string Gherkin."""
    feature = parse_feature_string(content, source)
    return verify_feature(feature)


def format_report(report: VerificationReport) -> str:
    """Formata o relatório de verificação para saída no terminal."""
    lines = []
    lines.append("=" * 72)
    lines.append("  RELATÓRIO DE VERIFICAÇÃO FORMAL — CONTRADIÇÕES LÓGICAS")
    lines.append("=" * 72)
    lines.append(f"  Arquivo:       {report.feature_file}")
    lines.append(f"  Cenários:      {report.total_scenarios}")
    lines.append(f"  Proposições:   {report.total_propositions}")
    lines.append(f"  Contradições:  {len(report.contradictions)}")
    lines.append(f"    Críticas:    {report.critical_count}")
    lines.append(f"    Avisos:      {report.warning_count}")
    lines.append("-" * 72)

    if not report.contradictions:
        lines.append("")
        lines.append("  [OK] Nenhuma contradição detectada.")
        lines.append("  O conjunto de especificações é formalmente consistente.")
        lines.append("")
    else:
        for i, c in enumerate(report.contradictions, 1):
            severity_icon = {
                "critical": "[CRITICAL]",
                "warning": "[WARNING] ",
                "info": "[INFO]    ",
            }.get(c.severity, "[?]")

            lines.append("")
            lines.append(f"  {severity_icon} #{i}: {c.contradiction_type}")
            lines.append(f"  {c.description}")

            if c.source_locations:
                lines.append(f"  Localização:")
                for loc in c.source_locations:
                    lines.append(f"    -> {loc}")

            if c.details:
                if "formal" in c.details:
                    lines.append(f"  Fórmula: {c.details['formal']}")
                if "z3_result" in c.details:
                    lines.append(f"  Z3: {c.details['z3_result']}")
                if "explanation" in c.details:
                    lines.append(f"  Nota: {c.details['explanation']}")

            lines.append(f"  {'─' * 68}")

    lines.append("")
    lines.append("=" * 72)

    if report.has_contradictions:
        lines.append(
            f"  RESULTADO: {len(report.contradictions)} contradição(ões) encontrada(s)"
        )
        lines.append("  O conjunto de especificações contém inconsistências lógicas.")
    else:
        lines.append("  RESULTADO: CONSISTENTE")

    lines.append("=" * 72)

    return "\n".join(lines)
