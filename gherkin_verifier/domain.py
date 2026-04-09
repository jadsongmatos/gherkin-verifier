"""
Modelo de domínio: proposições lógicas extraídas de Gherkin.

Cada cenário Gherkin é decomposto em proposições atômicas com metadados
que permitem a verificação formal por diferentes engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class Quantifier(Enum):
    """Quantificador lógico do juízo."""

    UNIVERSAL_AFF = auto()  # A: Todo S é P
    UNIVERSAL_NEG = auto()  # E: Nenhum S é P
    PARTICULAR_AFF = auto()  # I: Algum S é P
    PARTICULAR_NEG = auto()  # O: Algum S não é P


class Modality(Enum):
    """Modalidade do juízo."""

    NECESSARY = auto()  # deve ser / é obrigatório
    POSSIBLE = auto()  # pode ser / é permitido
    IMPOSSIBLE = auto()  # não pode ser / é proibido
    CONTINGENT = auto()  # pode ou não ser


@dataclass
class Proposition:
    """
    Proposição lógica extraída de um step Gherkin.

    Exemplo: "Given o usuário é Gerente" →
        subject='usuário', predicate='é', obj='Gerente', negated=False
    """

    subject: str
    predicate: str
    obj: str
    negated: bool = False
    quantifier: Quantifier = Quantifier.UNIVERSAL_AFF
    explicit_quantifier: bool = (
        False  # True se "todo"/"nenhum" etc. foi encontrado no texto
    )
    modality: Modality = Modality.CONTINGENT
    source_step: str = ""
    source_scenario: str = ""
    source_file: str = ""
    source_line: int = 0

    @property
    def key(self) -> str:
        """Chave canônica para comparação."""
        return f"{self.subject}|{self.predicate}|{self.obj}"

    @property
    def logical_form(self) -> str:
        neg = "¬" if self.negated else ""
        q = {
            Quantifier.UNIVERSAL_AFF: "∀",
            Quantifier.UNIVERSAL_NEG: "∀¬",
            Quantifier.PARTICULAR_AFF: "∃",
            Quantifier.PARTICULAR_NEG: "∃¬",
        }[self.quantifier]
        return f"{q}{self.subject}: {neg}{self.predicate}({self.subject}, {self.obj})"

    def contradicts(self, other: Proposition) -> bool:
        """Verifica contradição direta (mesma chave, negação oposta)."""
        return self.key == other.key and self.negated != other.negated

    def __repr__(self) -> str:
        neg = "NOT " if self.negated else ""
        return f"Prop({neg}{self.subject}.{self.predicate}={self.obj})"


@dataclass
class AptitudeDeclaration:
    """
    Declaração de aptidão ontológica — usada para contradições privativas.

    Exemplo: "Todo usuário autenticado é apto a receber permissões"
    """

    subject_type: str
    property_name: str
    is_apt: bool = True
    source: str = ""


@dataclass
class RelationDeclaration:
    """
    Declaração de relação correlativa — usada para contradições relativas.

    Exemplo: "gerente controla subordinado" ↔ "subordinado é controlado por gerente"
    """

    role_a: str
    role_b: str
    relation: str
    inverse_relation: str
    simultaneous: bool = True
    source: str = ""


@dataclass
class PresuppositionDeclaration:
    """
    Declaração de pressuposição — usada para autonegação.

    Uma proposição que pressupõe certas condições para ser formulada
    mas que nega essas mesmas condições em seu conteúdo.
    """

    proposition_id: str
    content: str
    presupposes: set[str] = field(default_factory=set)
    negates: set[str] = field(default_factory=set)
    source: str = ""

    @property
    def self_negated_foundations(self) -> set[str]:
        return self.presupposes & self.negates

    @property
    def is_self_negating(self) -> bool:
        return len(self.self_negated_foundations) > 0


@dataclass
class ContradictionResult:
    """Resultado de uma verificação de contradição."""

    contradiction_type: str
    severity: str  # "critical", "warning", "info"
    description: str
    propositions: list[Proposition] = field(default_factory=list)
    details: dict = field(default_factory=dict)
    source_locations: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"[{self.severity.upper()}] {self.contradiction_type}: {self.description}"
        )


@dataclass
class VerificationReport:
    """Relatório completo de verificação."""

    feature_file: str
    total_scenarios: int = 0
    total_propositions: int = 0
    contradictions: list[ContradictionResult] = field(default_factory=list)
    # Dados de pré-checagens simbólicas (SymPy) para acelerar o pipeline
    precheck: dict = field(default_factory=dict)

    @property
    def has_contradictions(self) -> bool:
        return len(self.contradictions) > 0

    @property
    def critical_count(self) -> int:
        return sum(1 for c in self.contradictions if c.severity == "critical")

    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.contradictions if c.severity == "warning")
