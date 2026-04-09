import pytest
from gherkin_verifier.extractor import (
    extract_propositions_from_step,
    extract_aptitudes_from_tags,
    extract_relations_from_tags,
    extract_presuppositions_from_tags,
    extract_all,
    _detect_negation,
    _detect_quantifier,
    _detect_modality,
    _strip_negation,
    _extract_spo,
    _normalize_term,
    _parse_tag_args,
)
from gherkin_verifier.parser import ParsedStep, ParsedScenario, ParsedRule, ParsedFeature


class TestDetectNegation:
    def test_negation_with_nao(self):
        assert _detect_negation("o usuário não tem acesso") is True

    def test_negation_with_nao_tem(self):
        assert _detect_negation("o usuário não tem acesso") is True

    def test_negation_with_nao_e(self):
        assert _detect_negation("o usuário não é gerente") is True

    def test_negation_with_nenhum(self):
        assert _detect_negation("nenhum usuário tem acesso") is True

    def test_negation_english_cannot(self):
        assert _detect_negation("cannot access") is True

    def test_no_negation(self):
        assert _detect_negation("o usuário tem acesso") is False


class TestDetectQuantifier:
    def test_universal_affirmative(self):
        q, explicit = _detect_quantifier("todo usuário tem acesso", False)
        assert q.value == 1  # UNIVERSAL_AFF

    def test_universal_negative(self):
        q, explicit = _detect_quantifier("nenhum usuário tem acesso", True)
        assert q.value == 2  # UNIVERSAL_NEG

    def test_particular_affirmative(self):
        q, explicit = _detect_quantifier("algum usuário tem acesso", False)
        assert q.value == 3  # PARTICULAR_AFF

    def test_particular_negative(self):
        q, explicit = _detect_quantifier("algum usuário não tem acesso", True)
        assert q.value == 4  # PARTICULAR_NEG

    def test_explicit_true_when_quantifier_present(self):
        _, explicit = _detect_quantifier("todo usuário tem acesso", False)
        assert explicit is True


class TestDetectModality:
    def test_necessity_deve(self):
        assert _detect_modality("o usuário deve ter acesso") is not None

    def test_possibility_pode(self):
        m = _detect_modality("o usuário pode ter acesso")
        from gherkin_verifier.domain import Modality
        assert m == Modality.POSSIBLE

    def test_impossibility_nao_pode(self):
        m = _detect_modality("o usuário não pode ter acesso")
        from gherkin_verifier.domain import Modality
        assert m == Modality.IMPOSSIBLE

    def test_contingent_default(self):
        m = _detect_modality("o usuário tem acesso")
        from gherkin_verifier.domain import Modality
        assert m == Modality.CONTINGENT


class TestStripNegation:
    def test_strip_nao_tem(self):
        result = _strip_negation("o usuário não tem acesso")
        assert "não" not in result

    def test_strip_not(self):
        result = _strip_negation("user does not have access")
        assert "not" not in result


class TestExtractSPO:
    def test_extract_spo_pt_tem(self):
        result = _extract_spo("o usuário tem acesso")
        assert result is not None
        assert result[0] == "usuário"
        assert result[1] == "tem"
        assert result[2] == "acesso"

    def test_extract_spo_pt_e(self):
        result = _extract_spo("o usuário é gerente")
        assert result is not None
        assert result[0] == "usuário"
        # Extractor normalizes 'é' to 'tem' for consistency
        assert result[1] == "tem"
        assert result[2] == "gerente"

    def test_extract_spo_en_has(self):
        result = _extract_spo("the user has access")
        assert result is not None
        assert result[0] == "user"
        assert result[1] == "has"
        assert result[2] == "access"

    def test_extract_spo_no_match(self):
        result = _extract_spo("some random text")
        assert result is None


class TestNormalizeTerm:
    def test_normalize_with_article(self):
        assert _normalize_term("o usuário") == "usuário"

    def test_normalize_with_the(self):
        assert _normalize_term("the user") == "user"

    def test_normalize_spaces_to_underscore(self):
        assert _normalize_term("access to file") == "access_to_file"


class TestParseTagArgs:
    def test_parse_apt_tag(self):
        args = _parse_tag_args("apt-usuario-acesso", "apt")
        assert args == ["usuario", "acesso"]

    def test_parse_rel_tag(self):
        args = _parse_tag_args("rel-gerente-subordinado-controla-controlado_por", "rel")
        assert args == ["gerente", "subordinado", "controla", "controlado_por"]

    def test_parse_presupposes_tag(self):
        args = _parse_tag_args("presupposes-sessao_ativa", "presupposes")
        assert args == ["sessao_ativa"]


class TestExtractPropositionsFromStep:
    def test_extract_basic(self):
        step = ParsedStep(keyword="Given", text="o usuário é gerente")
        prop = extract_propositions_from_step(step, "test scenario", "test.feature")
        assert prop is not None
        assert prop.subject == "usuário"
        # Extractor normalizes 'é' to 'tem' for consistency
        assert prop.predicate == "tem"
        assert prop.obj == "gerente"

    def test_extract_with_negation(self):
        step = ParsedStep(keyword="Then", text="o usuário não tem acesso")
        prop = extract_propositions_from_step(step, "test", "test.feature")
        assert prop is not None
        assert prop.negated is True

    def test_extract_no_match(self):
        step = ParsedStep(keyword="Given", text="some random text")
        prop = extract_propositions_from_step(step, "test", "test.feature")
        assert prop is None


class TestExtractAptitudesFromTags:
    def test_extract_apt(self):
        scenario = ParsedScenario(
            name="test",
            tags=["apt-usuario-acesso"],
            steps=[],
        )
        aptitudes = extract_aptitudes_from_tags(scenario, "test.feature")
        assert len(aptitudes) == 1
        assert aptitudes[0].subject_type == "usuario"
        assert aptitudes[0].property_name == "acesso"

    def test_extract_no_apt(self):
        scenario = ParsedScenario(name="test", tags=["other"], steps=[])
        aptitudes = extract_aptitudes_from_tags(scenario, "test.feature")
        assert len(aptitudes) == 0


class TestExtractRelationsFromTags:
    def test_extract_rel(self):
        scenario = ParsedScenario(
            name="test",
            tags=["rel-gerente-subordinado-controla-controlado_por"],
            steps=[],
        )
        relations = extract_relations_from_tags(scenario, "test.feature")
        assert len(relations) == 1
        assert relations[0].role_a == "gerente"
        assert relations[0].role_b == "subordinado"

    def test_extract_no_rel(self):
        scenario = ParsedScenario(name="test", tags=["other"], steps=[])
        relations = extract_relations_from_tags(scenario, "test.feature")
        assert len(relations) == 0


class TestExtractPresuppositionsFromTags:
    def test_extract_presup(self):
        scenario = ParsedScenario(
            name="test",
            tags=["presupposes-sessao_ativa", "negates-sessao_ativa"],
            steps=[],
        )
        presup = extract_presuppositions_from_tags(scenario, "test.feature")
        assert len(presup) == 1
        assert "sessao_ativa" in presup[0].presupposes
        assert "sessao_ativa" in presup[0].negates

    def test_extract_no_presup(self):
        scenario = ParsedScenario(name="test", tags=["other"], steps=[])
        presup = extract_presuppositions_from_tags(scenario, "test.feature")
        assert len(presup) == 0


class TestExtractAll:
    def test_extract_all_basic(self):
        feature = ParsedFeature(
            name="Test",
            file_path="test.feature",
            scenarios=[
                ParsedScenario(
                    name="test scenario",
                    steps=[
                        ParsedStep(keyword="Given", text="o usuário é gerente"),
                        ParsedStep(keyword="Then", text="o usuário tem acesso"),
                    ],
                )
            ],
        )
        result = extract_all(feature)
        assert "propositions" in result
        assert len(result["propositions"]) >= 1

    def test_extract_all_with_background(self):
        feature = ParsedFeature(
            name="Test",
            file_path="test.feature",
            background_steps=[
                ParsedStep(keyword="Given", text="o sistema está ligado"),
            ],
            scenarios=[
                ParsedScenario(
                    name="test",
                    steps=[
                        ParsedStep(keyword="Given", text="o usuário é gerente"),
                    ],
                )
            ],
        )
        result = extract_all(feature)
        assert len(result["propositions"]) == 2  # background + scenario

    def test_extract_all_with_rules(self):
        feature = ParsedFeature(
            name="Test",
            file_path="test.feature",
            rules=[
                ParsedRule(
                    name="Test Rule",
                    scenarios=[
                        ParsedScenario(
                            name="rule scenario",
                            steps=[
                                ParsedStep(keyword="Given", text="o usuário é gerente"),
                            ],
                        )
                    ],
                )
            ],
        )
        result = extract_all(feature)
        assert len(result["propositions"]) == 1
