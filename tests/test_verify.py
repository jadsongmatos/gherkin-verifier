import pytest
import sys
import json
from io import StringIO
from pathlib import Path
from verify import (
    collect_feature_files,
    report_to_dict,
    main,
)


class TestCollectFeatureFiles:
    def test_collect_single_file(self, tmp_path):
        feature_file = tmp_path / "test.feature"
        feature_file.write_text("Feature: Test")
        
        result = collect_feature_files(str(feature_file))
        assert len(result) == 1
        assert result[0].name == "test.feature"

    def test_collect_directory(self, tmp_path):
        (tmp_path / "test1.feature").write_text("Feature: Test1")
        (tmp_path / "test2.feature").write_text("Feature: Test2")
        
        result = collect_feature_files(str(tmp_path))
        assert len(result) == 2

    def test_collect_invalid_path(self, tmp_path):
        with pytest.raises(SystemExit):
            collect_feature_files(str(tmp_path / "nonexistent"))

    def test_collect_non_feature_file(self, tmp_path):
        text_file = tmp_path / "test.txt"
        text_file.write_text("Feature: Test")
        
        with pytest.raises(SystemExit):
            collect_feature_files(str(text_file))


class TestReportToDict:
    def test_basic_conversion(self):
        from gherkin_verifier.domain import VerificationReport, ContradictionResult
        
        report = VerificationReport(
            feature_file="test.feature",
            total_scenarios=2,
            total_propositions=4,
            contradictions=[
                ContradictionResult(
                    contradiction_type="Contraditória",
                    severity="critical",
                    description="Test contradiction",
                    details={"key": "test"},
                    source_locations=["test.feature:1"],
                )
            ]
        )
        
        result = report_to_dict(report)
        
        assert result["feature_file"] == "test.feature"
        assert result["total_scenarios"] == 2
        assert result["total_propositions"] == 4
        assert result["contradiction_count"] == 1
        assert result["critical_count"] == 1
        assert result["warning_count"] == 0
        assert len(result["contradictions"]) == 1


class TestMain:
    def test_main_invalid_path(self, capsys):
        old_argv = sys.argv
        sys.argv = ["verify.py", "/nonexistent/path"]
        
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        finally:
            sys.argv = old_argv

    def test_main_no_files(self, tmp_path, capsys):
        old_argv = sys.argv
        sys.argv = ["verify.py", str(tmp_path)]
        
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        finally:
            sys.argv = old_argv

    def test_main_json_output(self, tmp_path, capsys):
        feature_file = tmp_path / "test.feature"
        feature_file.write_text("""
Feature: Test
  Scenario: Test
    Given o usuário é gerente
    Then o usuário tem acesso
""")
        
        old_argv = sys.argv
        sys.argv = ["verify.py", str(feature_file), "--json"]
        
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert "total_files" in output
        finally:
            sys.argv = old_argv

    def test_main_summary_output(self, tmp_path, capsys):
        feature_file = tmp_path / "test.feature"
        feature_file.write_text("""
Feature: Test
  Scenario: Test
    Given o usuário é gerente
    Then o usuário tem acesso
""")
        
        old_argv = sys.argv
        sys.argv = ["verify.py", str(feature_file), "--summary"]
        
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "RESUMO" in captured.out or "resumo" in captured.out.lower()
        finally:
            sys.argv = old_argv

    def test_main_verbose_output(self, tmp_path, capsys):
        feature_file = tmp_path / "test.feature"
        feature_file.write_text("""
Feature: Test
  Scenario: Test
    Given o usuário é gerente
    Then o usuário tem acesso
""")
        
        old_argv = sys.argv
        sys.argv = ["verify.py", str(feature_file), "--verbose"]
        
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "RELATÓRIO" in captured.out or "Proposições" in captured.out
        finally:
            sys.argv = old_argv
