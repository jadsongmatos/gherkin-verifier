"""
Parser de arquivos .feature Gherkin.

Usa a biblioteca gherkin-official para parsing e extrai a estrutura
de Features, Scenarios, Steps, e Tags.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from gherkin.parser import Parser as GherkinParser
from gherkin.token_scanner import TokenScanner


@dataclass
class ParsedStep:
    keyword: str       # Given, When, Then, And, But
    text: str          # texto do step
    line: int = 0

    @property
    def effective_keyword(self) -> str:
        """Resolve And/But para o keyword efetivo anterior."""
        return self._effective or self.keyword

    def set_effective_keyword(self, kw: str):
        self._effective = kw

    def __post_init__(self):
        self._effective = None


@dataclass
class ParsedScenario:
    name: str
    tags: list[str] = field(default_factory=list)
    steps: list[ParsedStep] = field(default_factory=list)
    line: int = 0
    description: str = ""


@dataclass
class ParsedRule:
    name: str
    scenarios: list[ParsedScenario] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ParsedFeature:
    name: str
    file_path: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    background_steps: list[ParsedStep] = field(default_factory=list)
    scenarios: list[ParsedScenario] = field(default_factory=list)
    rules: list[ParsedRule] = field(default_factory=list)


def _extract_tags(node: dict) -> list[str]:
    return [t["name"].lstrip("@") for t in node.get("tags", [])]


def _extract_steps(node: dict) -> list[ParsedStep]:
    steps = []
    last_keyword = "Given"
    for s in node.get("steps", []):
        kw = s["keyword"].strip()
        step = ParsedStep(
            keyword=kw,
            text=s["text"].strip(),
            line=s["location"]["line"],
        )
        if kw in ("And", "But", "*"):
            step.set_effective_keyword(last_keyword)
        else:
            last_keyword = kw
        steps.append(step)
    return steps


def parse_feature_file(file_path: str | Path) -> ParsedFeature:
    """Faz parsing de um arquivo .feature e retorna a estrutura."""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    return parse_feature_string(content, str(path))


def parse_feature_string(content: str, source: str = "<string>") -> ParsedFeature:
    """Faz parsing de uma string Gherkin."""
    parser = GherkinParser()
    scanner = TokenScanner(content)
    gherkin_doc = parser.parse(scanner)

    feature_node = gherkin_doc.get("feature")
    if not feature_node:
        return ParsedFeature(name="", file_path=source)

    parsed = ParsedFeature(
        name=feature_node.get("name", ""),
        file_path=source,
        description=feature_node.get("description", "").strip(),
        tags=_extract_tags(feature_node),
    )

    for child in feature_node.get("children", []):
        # Background
        if "background" in child:
            bg = child["background"]
            parsed.background_steps = _extract_steps(bg)

        # Scenario / Scenario Outline
        if "scenario" in child:
            sc = child["scenario"]
            parsed_sc = ParsedScenario(
                name=sc.get("name", ""),
                tags=_extract_tags(sc),
                steps=_extract_steps(sc),
                line=sc["location"]["line"],
                description=sc.get("description", "").strip(),
            )
            parsed.scenarios.append(parsed_sc)

        # Rule
        if "rule" in child:
            rule_node = child["rule"]
            parsed_rule = ParsedRule(
                name=rule_node.get("name", ""),
                tags=_extract_tags(rule_node),
                description=rule_node.get("description", "").strip(),
            )
            for rule_child in rule_node.get("children", []):
                if "scenario" in rule_child:
                    sc = rule_child["scenario"]
                    parsed_sc = ParsedScenario(
                        name=sc.get("name", ""),
                        tags=_extract_tags(sc),
                        steps=_extract_steps(sc),
                        line=sc["location"]["line"],
                        description=sc.get("description", "").strip(),
                    )
                    parsed_rule.scenarios.append(parsed_sc)
            parsed.rules.append(parsed_rule)

    return parsed
