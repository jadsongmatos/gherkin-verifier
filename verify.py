#!/usr/bin/env python3
"""
Gherkin Formal Verifier — CLI

Verifica contradições lógicas em especificações Gherkin (.feature)
usando técnicas de verificação formal (SAT/SMT, lógica de primeira ordem,
análise de grafos).

Uso:
  python verify.py features/01_contraditorias.feature
  python verify.py features/                          # todos os .feature
  python verify.py features/ --json                   # saída JSON
  python verify.py features/ --md                     # relatório completo em Markdown
  python verify.py features/ --verbose                # detalhes extras

Tipos de contradições verificadas:
  1. Contraditórias (A ∧ ¬A)
  2. Contrárias (universais incompatíveis)
  3. Subcontrárias (particulares)
  4. Privativas (aptidão + carência)
  5. Relativas (correlatos assimétricos)
  6. Autonegação (autodestruição de fundamentos)
  7. Modais (necessidade vs impossibilidade)
  8. Suplência (ambiguidade de termos)
  9. Contrassenso formal (Widersinn)
  10. Contradição performativa
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gherkin_verifier.engine import verify_file, format_report
from gherkin_verifier.domain import VerificationReport


def collect_feature_files(path: str) -> list[Path]:
    """Coleta arquivos .feature de um caminho (arquivo ou diretório)."""
    p = Path(path)
    if p.is_file() and p.suffix == ".feature":
        return [p]
    if p.is_dir():
        return sorted(p.rglob("*.feature"))
    print(
        f"Erro: '{path}' não é um arquivo .feature nem um diretório.", file=sys.stderr
    )
    sys.exit(1)


def report_to_dict(report: VerificationReport) -> dict:
    """Converte um relatório para dict serializável em JSON."""
    return {
        "feature_file": report.feature_file,
        "total_scenarios": report.total_scenarios,
        "total_propositions": report.total_propositions,
        "contradiction_count": len(report.contradictions),
        "critical_count": report.critical_count,
        "warning_count": report.warning_count,
        "contradictions": [
            {
                "type": c.contradiction_type,
                "severity": c.severity,
                "description": c.description,
                "details": c.details,
                "source_locations": c.source_locations,
            }
            for c in report.contradictions
        ],
    }


def report_to_markdown(report: VerificationReport) -> str:
    """Converte um relatório para Markdown completo (sem headers de '=')."""
    lines = []
    lines.append(f"## Arquivo: `{report.feature_file}`")
    lines.append("")
    lines.append(f"- Cenários: {report.total_scenarios}")
    lines.append(f"- Proposições: {report.total_propositions}")
    lines.append(f"- Contradições: {len(report.contradictions)}")
    lines.append(f"- Críticas: {report.critical_count}")
    lines.append(f"- Avisos: {report.warning_count}")
    lines.append(
        f"- Resultado: {'INCONSISTENTE' if report.has_contradictions else 'CONSISTENTE'}"
    )

    if not report.contradictions:
        lines.append("")
        lines.append("Sem contradições detectadas.")
        return "\n".join(lines)

    lines.append("")
    lines.append("### Contradições")
    lines.append("")

    for i, c in enumerate(report.contradictions, 1):
        lines.append(f"#### {i}. {c.contradiction_type}")
        lines.append(f"- Severidade: `{c.severity}`")
        lines.append(f"- Descrição: {c.description}")

        if c.source_locations:
            lines.append("- Localização:")
            for loc in c.source_locations:
                lines.append(f"  - `{loc}`")

        if c.details:
            lines.append("- Detalhes:")
            for key, value in c.details.items():
                lines.append(f"  - {key}: `{value}`")

        lines.append("")

    return "\n".join(lines).rstrip()


def main():
    parser = argparse.ArgumentParser(
        description="Verificador Formal de Contradições Lógicas em Gherkin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "path",
        help="Arquivo .feature ou diretório contendo arquivos .feature",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Saída em formato JSON",
    )
    parser.add_argument(
        "--md",
        action="store_true",
        help="Relatório completo em Markdown (sem cabeçalhos com '=')",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Mostrar proposições extraídas e detalhes extras",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Mostrar apenas o resumo (sem detalhes de cada contradição)",
    )

    args = parser.parse_args()
    files = collect_feature_files(args.path)

    if not files:
        print("Nenhum arquivo .feature encontrado.", file=sys.stderr)
        sys.exit(1)

    all_reports = []
    total_contradictions = 0
    total_critical = 0

    for f in files:
        try:
            report = verify_file(f)
            all_reports.append(report)
            total_contradictions += len(report.contradictions)
            total_critical += report.critical_count
        except Exception as e:
            print(f"Erro ao verificar {f}: {e}", file=sys.stderr)
            continue

    if args.json:
        output = {
            "total_files": len(all_reports),
            "total_contradictions": total_contradictions,
            "total_critical": total_critical,
            "reports": [report_to_dict(r) for r in all_reports],
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    elif args.md:
        print("# Relatório de Verificação Formal")
        print("")
        print(f"- Arquivos verificados: {len(all_reports)}")
        print(f"- Total de contradições: {total_contradictions}")
        print(f"- Contradições críticas: {total_critical}")
        print("")
        for i, report in enumerate(all_reports, 1):
            if i > 1:
                print("\n---\n")
            print(report_to_markdown(report))
    elif args.summary:
        print(f"\n{'=' * 72}")
        print(f"  RESUMO DA VERIFICAÇÃO FORMAL")
        print(f"{'=' * 72}")
        print(f"  Arquivos verificados: {len(all_reports)}")
        print(f"  Total de contradições: {total_contradictions}")
        print(f"  Contradições críticas: {total_critical}")
        print(f"{'=' * 72}")
        for r in all_reports:
            status = "INCONSISTENTE" if r.has_contradictions else "OK"
            icon = "X" if r.has_contradictions else "V"
            print(
                f"  [{icon}] {r.feature_file}: {len(r.contradictions)} contradição(ões) — {status}"
            )
        print(f"{'=' * 72}\n")
    else:
        for report in all_reports:
            print(format_report(report))
            if args.verbose:
                from gherkin_verifier.extractor import extract_all
                from gherkin_verifier.parser import parse_feature_file

                feature = parse_feature_file(report.feature_file)
                extracted = extract_all(feature)
                print("\n  Proposições extraídas:")
                for p in extracted["propositions"]:
                    print(f"    {p.logical_form}")
                    print(f"      Step: {p.source_step}")
                    print(f"      Cenário: {p.source_scenario}")
                    print()
            print()

    # Exit code: 1 se houver contradições críticas
    sys.exit(1 if total_critical > 0 else 0)


if __name__ == "__main__":
    main()
