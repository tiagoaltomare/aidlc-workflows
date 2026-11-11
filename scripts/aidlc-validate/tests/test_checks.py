from __future__ import annotations

from pathlib import Path

from aidlc_validate.cli import main

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
    import shutil

    dest = tmp_path / "repo"
    shutil.copytree(FIXTURES / "valid", dest)
    return dest


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
