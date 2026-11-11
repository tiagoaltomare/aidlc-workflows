from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from aidlc_validate.cli import CHECK_FNS, main
from aidlc_validate.checks import SCHEMA_PATH, load_config

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _run(check: str, root: Path) -> tuple[int, str, str]:
    from io import StringIO
    import sys

    stdout, stderr = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = stdout, stderr
        rc = main([check, "--root", str(root)])
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return rc, stdout.getvalue(), stderr.getvalue()


def test_valid_config_passes():
    rc, out, err = _run("config", FIXTURES / "valid")
    assert rc == 0, err
    assert "config: pass" in out


def test_example_yaml_validates(tmp_path: Path):
    repo = Path(__file__).resolve().parents[3]
    example = repo / "docs" / "aidlc.config.example.yaml"
    (tmp_path / "aidlc.config.yaml").write_text(
        example.read_text(encoding="utf-8"), encoding="utf-8"
    )
    rc, out, err = _run("config", tmp_path)
    assert rc == 0, err
    assert "pass" in out


def test_invalid_config_refused():
    rc, _out, err = _run("config", FIXTURES / "invalid_config")
    assert rc == 1
    assert "schema error" in err or "invalid" in err.lower()


def test_unknown_schema_version_refused():
    rc, _out, err = _run("config", FIXTURES / "unknown_schema")
    assert rc == 1
    assert "unknown schema_version" in err


def test_valid_units_dag_passes():
    rc, out, err = _run("units-dag", FIXTURES / "valid")
    assert rc == 0, err
    assert "units-dag: pass" in out


def test_cyclic_dag_fails():
    rc, _out, err = _run("units-dag", FIXTURES / "cyclic_dag")
    assert rc == 1
    assert "cycle" in err.lower()


def test_undeclared_unit_fails():
    rc, _out, err = _run("units-dag", FIXTURES / "undeclared_unit")
    assert rc == 1
    assert "undeclared" in err.lower()


def test_valid_traceability_passes():
    rc, out, err = _run("traceability", FIXTURES / "valid")
    assert rc == 0, err
    assert "traceability: pass" in out


def test_out_of_scope_in_stories_fails():
    rc, _out, err = _run("traceability", FIXTURES / "out_of_scope_in_stories")
    assert rc == 1
    assert "out-of-scope" in err.lower()


def test_valid_scope_in_vision_passes():
    rc, out, err = _run("scope-in-vision", FIXTURES / "valid")
    assert rc == 0, err
    assert "scope-in-vision: pass" in out


def test_in_scope_feature_missing_from_features_fails():
    rc, _out, err = _run("scope-in-vision", FIXTURES / "missing_feature")
    assert rc == 1
    assert "does not resolve" in err
    assert "FEAT-999" in err


def test_valid_export_passes():
    rc, out, err = _run("export", FIXTURES / "valid")
    assert rc == 0, err
    assert "export: pass" in out


def test_audit_md_in_export_fails():
    rc, _out, err = _run("export", FIXTURES / "export_with_audit")
    assert rc == 1
    assert "audit.md" in err


def test_stories_valid_passes():
    rc, out, err = _run("stories", FIXTURES / "valid")
    assert rc == 0, err
    assert "stories: pass" in out


def test_stories_too_few_ac_fails():
    rc, _out, err = _run("stories", FIXTURES / "too_few_ac")
    assert rc == 1
    assert "min is 2" in err


def _copy_valid(tmp_path: Path) -> Path:
    dest = tmp_path / "repo"
    shutil.copytree(FIXTURES / "valid", dest)
    return dest


def _update_config(repo: Path, **updates: object) -> None:
    path = repo / "aidlc.config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(data.get(key), dict):
            merged = dict(data[key])
            merged.update(value)
            data[key] = merged
        else:
            data[key] = value
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_scope_atual_alias_only_passes(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    scopes = repo / "aidlc-docs" / "vision" / "scopes"
    canonical = scopes / "scope-001.md"
    alias = scopes / "scope-atual.md"
    alias.write_text(canonical.read_text(encoding="utf-8"), encoding="utf-8")
    canonical.unlink()
    cfg = (repo / "aidlc.config.yaml").read_text(encoding="utf-8")
    (repo / "aidlc.config.yaml").write_text(
        cfg.replace(
            "aidlc-docs/vision/scopes/scope-001.md",
            "aidlc-docs/vision/scopes/scope-atual.md",
        ),
        encoding="utf-8",
    )
    rc, out, err = _run("scope-in-vision", repo)
    assert rc == 0, err
    assert "scope-in-vision: pass" in out
    rc, out, err = _run("traceability", repo)
    assert rc == 0, err


def test_scope_alias_and_canonical_count_once(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    scopes = repo / "aidlc-docs" / "vision" / "scopes"
    canonical = scopes / "scope-001.md"
    (scopes / "scope-atual.md").write_text(
        canonical.read_text(encoding="utf-8"), encoding="utf-8"
    )
    cfg = (repo / "aidlc.config.yaml").read_text(encoding="utf-8")
    (repo / "aidlc.config.yaml").write_text(
        cfg.replace(
            "aidlc-docs/vision/scopes/scope-001.md",
            "aidlc-docs/vision/scopes/scope-atual.md",
        ),
        encoding="utf-8",
    )
    rc, out, err = _run("scope-in-vision", repo)
    assert rc == 0, err
    assert "pass" in out
    rc, _out, err = _run("traceability", repo)
    assert rc == 0, err


def test_stories_without_units_fail_traceability(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    design = repo / "aidlc-docs" / "inception" / "application-design"
    for name in (
        "unit-of-work.md",
        "unit-of-work-dependency.md",
        "unit-of-work-story-map.md",
    ):
        (design / name).unlink()
    rc, _out, err = _run("traceability", repo)
    assert rc == 1
    assert "no UNIT record" in err


def test_export_unescaped_mdx_braces_fail(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    features = repo / "docs-site" / "docs" / "features.md"
    features.write_text(
        "# Features\n\nBook {id} is a field.\n", encoding="utf-8"
    )
    rc, _out, err = _run("export", repo)
    assert rc == 1
    assert "unescaped MDX identifier" in err
    assert "id" in err


def test_export_escaped_mdx_braces_pass(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    features = repo / "docs-site" / "docs" / "features.md"
    features.write_text(
        "# Features\n\nBook \\{id\\} is a field.\n\nAlso `{id}` in code.\n",
        encoding="utf-8",
    )
    rc, out, err = _run("export", repo)
    assert rc == 0, err
    assert "export: pass" in out


def test_export_unescaped_answer_line_fails():
    rc, _out, err = _run("export", FIXTURES / "export_unescaped_answer")
    assert rc == 1
    assert "unescaped [Answer]:" in err


def test_export_escaped_answer_line_passes(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    stories = repo / "docs-site" / "docs" / "stories.md"
    stories.write_text(
        "# Stories\n\n\\[Answer\\]: A\n",
        encoding="utf-8",
    )
    rc, out, err = _run("export", repo)
    assert rc == 0, err
    assert "export: pass" in out


def test_export_skips_node_modules_build_docusaurus():
    rc, out, err = _run("export", FIXTURES / "export_site_junk")
    assert rc == 0, err
    assert "export: pass" in out


def test_assumptions_valid_passes():
    rc, out, err = _run("assumptions", FIXTURES / "valid")
    assert rc == 0, err
    assert "assumptions: pass" in out


def test_assumptions_empty_table_passes(tmp_path: Path):
    (tmp_path / "aidlc-docs").mkdir()
    (tmp_path / "aidlc-docs" / "assumptions.md").write_text(
        "# Assumptions\n\n| id | stage | blocking | question | assumption_or_answer | status |\n"
        "| --- | ----- | -------- | -------- | -------------------- | ------ |\n",
        encoding="utf-8",
    )
    rc, out, err = _run("assumptions", tmp_path)
    assert rc == 0, err
    assert "assumptions: pass" in out


def test_assumptions_missing_fails():
    rc, _out, err = _run("assumptions", FIXTURES / "assumptions_missing")
    assert rc == 1
    assert "missing" in err
    assert "assumptions.md" in err


def test_assumptions_open_blocking_fails():
    rc, _out, err = _run("assumptions", FIXTURES / "assumptions_open_blocking")
    assert rc == 1
    assert "open blocking question A-001" in err


def test_assumptions_stopped_blocking_fails(tmp_path: Path):
    (tmp_path / "aidlc-docs").mkdir()
    (tmp_path / "aidlc-docs" / "assumptions.md").write_text(
        "# Assumptions\n\n"
        "| id | stage | blocking | question | assumption_or_answer | status |\n"
        "| --- | ----- | -------- | -------- | -------------------- | ------ |\n"
        "| A-001 | requirements | yes | Opt in? | waiting | stopped |\n",
        encoding="utf-8",
    )
    rc, _out, err = _run("assumptions", tmp_path)
    assert rc == 1
    assert "open blocking question A-001" in err
    assert "stopped" in err


def test_assumptions_bad_format_fails():
    rc, _out, err = _run("assumptions", FIXTURES / "assumptions_bad_format")
    assert rc == 1
    assert "missing required columns" in err


def test_schema_check_ids_match_cli():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    enum = schema["properties"]["gates"]["properties"]["checks"]["items"]["properties"][
        "id"
    ]["enum"]
    assert set(enum) == set(CHECK_FNS)


def test_unknown_check_id_fails_config(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    _update_config(
        repo,
        gates={"checks": [{"id": "nope", "severity": "blocking"}]},
    )
    rc, _out, err = _run("config", repo)
    assert rc == 1
    assert "schema error" in err
    assert "nope" in err
    rc, _out, err = _run("stories", repo)
    assert rc == 1
    assert "nope" in err


def test_omitted_check_is_skipped(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    stories = repo / "aidlc-docs" / "inception" / "user-stories" / "stories.md"
    stories.write_text(
        "# Stories\n\n### US-001 Checkout a book\n"
        "As a member, I want to check out a book so that I can read it.\n",
        encoding="utf-8",
    )
    _update_config(
        repo,
        gates={"checks": [{"id": "config", "severity": "blocking"}]},
    )
    rc, out, err = _run("stories", repo)
    assert rc == 0, err
    assert "stories: skipped" in out
    rc, _out, err = _run("stories", FIXTURES / "too_few_ac")
    assert rc == 1


def test_advisory_check_exits_zero_with_findings(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    shutil.copytree(FIXTURES / "too_few_ac" / "aidlc-docs", repo / "aidlc-docs", dirs_exist_ok=True)
    _update_config(
        repo,
        gates={"checks": [{"id": "stories", "severity": "advisory"}]},
    )
    rc, out, err = _run("stories", repo)
    assert rc == 0
    assert "min is 2" in err
    assert "stories: advisory" in out


def test_max_acceptance_criteria_from_config(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    _update_config(repo, stories={"min_acceptance_criteria": 1, "max_size": {"max_acceptance_criteria": 1}})
    rc, _out, err = _run("stories", repo)
    assert rc == 1
    assert "max is 1" in err


def test_stories_count_scenarios_not_gherkin_lines(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    stories = repo / "aidlc-docs" / "inception" / "user-stories" / "stories.md"
    stories.write_text(
        "# Stories\n\n"
        "### US-001 Checkout a book\n"
        "As a member, I want to check out a book so that I can read it.\n"
        "Requirement: REQ-001\n\n"
        "**Acceptance Criteria:**\n\n"
        "Scenario: happy path\n"
        "- Given I am a registered member\n"
        "- When I checkout an available book\n"
        "- Then the loan is created\n\n"
        "Scenario: already on loan\n"
        "- Given the book is already on loan\n"
        "- When I checkout that book\n"
        "- Then I see it is unavailable\n",
        encoding="utf-8",
    )
    _update_config(
        repo,
        stories={"min_acceptance_criteria": 2, "max_size": {"max_acceptance_criteria": 5}},
    )
    rc, out, err = _run("stories", repo)
    assert rc == 0, err
    assert "stories: pass" in out


def test_max_stories_per_unit_from_config(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    story_map = (
        repo / "aidlc-docs" / "inception" / "application-design" / "unit-of-work-story-map.md"
    )
    story_map.write_text(
        "# Story map\n\n"
        "| story  | unit     |\n"
        "| ------ | -------- |\n"
        "| US-001 | UNIT-001 |\n"
        "| US-002 | UNIT-001 |\n"
        "| US-002 | UNIT-002 |\n",
        encoding="utf-8",
    )
    _update_config(repo, units={"max_stories_per_unit": 1, "parallelism": "sequential"})
    rc, _out, err = _run("traceability", repo)
    assert rc == 1
    assert "UNIT-001 has 2 stories" in err
    assert "max_stories_per_unit is 1" in err


def test_load_config_applies_design_validation_and_limits_defaults(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    cfg, errors = load_config(repo)
    assert errors == []
    assert cfg is not None
    assert cfg["design_validation"]["mode"] == "hybrid"
    assert cfg["limits"]["max_rework_iterations_per_unit"] == 3
    assert cfg["units"]["max_stories_per_unit"] == 8


def test_export_questions_filename_fails_gate_filename_passes(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    docs = repo / "docs-site" / "docs"
    (docs / "construction").mkdir(exist_ok=True)
    (docs / "construction" / "design-validation-gate.md").write_text(
        "# Design validation gate\n\nEscalate?\n", encoding="utf-8"
    )
    rc, out, err = _run("export", repo)
    assert rc == 0, err
    assert "export: pass" in out
    (docs / "design-questions.md").write_text("# Questions\n", encoding="utf-8")
    rc, _out, err = _run("export", repo)
    assert rc == 1
    assert "question files" in err
    assert "design-questions.md" in err


def _write_stub_package_json(site: Path, exit_code: int) -> None:
    (site / "package.json").write_text(
        json.dumps({"scripts": {"build": f"node -e \"process.exit({exit_code})\""}}),
        encoding="utf-8",
    )


@pytest.mark.skipif(
    not shutil.which("npm") or not shutil.which("node"),
    reason="npm/node required to prove Docusaurus build",
)
def test_export_prove_build_runs_npm_when_package_json_present(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    _write_stub_package_json(repo / "docs-site", 0)
    rc, out, err = _run("export", repo)
    assert rc == 0, err
    assert "export: pass" in out
    _write_stub_package_json(repo / "docs-site", 1)
    rc, _out, err = _run("export", repo)
    assert rc == 1
    assert "npm run build failed" in err


def test_export_prove_build_flag_true_without_package_json_fails(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    _update_config(repo, operations={"prove_build": True, "docusaurus_path": "docs-site"})
    rc, _out, err = _run("export", repo)
    assert rc == 1
    assert "prove_build is true" in err
    assert "package.json" in err


def test_export_prove_build_false_skips_failing_script(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    _write_stub_package_json(repo / "docs-site", 1)
    _update_config(repo, operations={"prove_build": False, "docusaurus_path": "docs-site"})
    rc, out, err = _run("export", repo)
    assert rc == 0, err
    assert "export: pass" in out


def test_export_docusaurus_path_escape_fails(tmp_path: Path):
    repo = _copy_valid(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "package.json").write_text(
        json.dumps({"scripts": {"build": 'node -e "process.exit(0)"'}}),
        encoding="utf-8",
    )
    _update_config(
        repo, operations={"docusaurus_path": "../outside", "prove_build": True}
    )
    rc, _out, err = _run("export", repo)
    assert rc == 1
    assert "escapes project root" in err
    assert "../outside" in err

    link = repo / "docs-site-link"
    link.symlink_to(outside)
    _update_config(
        repo, operations={"docusaurus_path": "docs-site-link", "prove_build": True}
    )
    rc, _out, err = _run("export", repo)
    assert rc == 1
    assert "escapes project root" in err
    assert "docs-site-link" in err


def test_assumptions_duplicate_id_fails(tmp_path: Path):
    (tmp_path / "aidlc-docs").mkdir()
    (tmp_path / "aidlc-docs" / "assumptions.md").write_text(
        "# Assumptions\n\n"
        "| id | stage | blocking | question | assumption_or_answer | status |\n"
        "| --- | ----- | -------- | -------- | -------------------- | ------ |\n"
        "| A-001 | requirements | no | Q1 | Assumed X | open |\n"
        "| A-001 | stories | no | Q2 | Assumed Y | open |\n",
        encoding="utf-8",
    )
    rc, _out, err = _run("assumptions", tmp_path)
    assert rc == 1
    assert "duplicate id A-001" in err
