"""One function per CLI check. Paths follow the product plan (F0)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import jsonschema
import yaml

KNOWN_SCHEMA_VERSIONS = {"1"}
ID_RE = re.compile(r"\b(?:FEAT|SCOPE|REQ|US|UNIT)-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
KIND_RE = {
    "FEAT": re.compile(r"\bFEAT-[A-Z0-9]+(?:-[A-Z0-9]+)*\b"),
    "SCOPE": re.compile(r"\bSCOPE-[A-Z0-9]+(?:-[A-Z0-9]+)*\b"),
    "REQ": re.compile(r"\bREQ-[A-Z0-9]+(?:-[A-Z0-9]+)*\b"),
    "US": re.compile(r"\bUS-[A-Z0-9]+(?:-[A-Z0-9]+)*\b"),
    "UNIT": re.compile(r"\bUNIT-[A-Z0-9]+(?:-[A-Z0-9]+)*\b"),
}

NONE_DEPS = {"", "-", "—", "none", "n/a"}

INCLUDE_MARKERS = {
    "vision": ("vision-document.md", False),
    "technical_environment": ("technical-environment.md", False),
    "features": ("features.md", False),
    "scopes": ("scopes", True),
    "requirements": ("requirements.md", False),
    "user_stories": ("stories.md", False),
    "application_design": ("application-design.md", False),
    "units": ("unit-of-work.md", False),
    "construction_designs": ("construction", True),
    "build_and_test_summary": ("build-and-test-summary.md", False),
    "operations_summary": ("operations-summary.md", False),
    "rules_validation_report": ("rules-validation-report.md", False),
    "post_deployment_test_report": ("post-deployment-test-report.md", False),
}

DEFAULT_INCLUDE = list(INCLUDE_MARKERS)
DEFAULT_EXCLUDE = ["audit", "question_files", "raw_plans", "deployment_deploy_log"]

QUESTION_NAME_RE = re.compile(r"questions", re.I)
DEFAULT_HUMAN_TRIGGERS = [
    "persistent_data",
    "security",
    "public_contract",
    "external_integration",
    "risk_high_or_critical",
    "rework_limit_exceeded",
    "no_executable_check",
]
DEFAULT_LIMITS = {
    "max_rework_iterations_per_unit": 3,
    "token_budget_per_unit": 200000,
    "on_token_budget_exceeded": "pause_and_ask_human",
}
PLAN_NAME_RE = re.compile(r"(?:^|[-_])plan(?:s)?(?:[-_.]|$)|-plan\.md$", re.I)

SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "schema" / "aidlc.config.schema.json"
)

# Artifact paths from the product plan (sections 3 and 4.2).
FEATURES_PATH = Path("aidlc-docs/vision/features.md")
SCOPES_DIR = Path("aidlc-docs/vision/scopes")
REQUIREMENTS_PATH = Path("aidlc-docs/inception/requirements/requirements.md")
STORIES_PATH = Path("aidlc-docs/inception/user-stories/stories.md")
UNITS_PATH = Path("aidlc-docs/inception/application-design/unit-of-work.md")
UNITS_DAG_PATH = Path(
    "aidlc-docs/inception/application-design/unit-of-work-dependency.md"
)
STORY_MAP_PATH = Path(
    "aidlc-docs/inception/application-design/unit-of-work-story-map.md"
)
ASSUMPTIONS_PATH = Path("aidlc-docs/assumptions.md")
ASSUMPTION_ID_RE = re.compile(r"^A-\d{3,}$")
ASSUMPTION_REQUIRED_COLS = (
    "id",
    "stage",
    "blocking",
    "question",
    "assumption_or_answer",
    "status",
)
ASSUMPTION_BLOCKING = {"yes", "no"}
ASSUMPTION_STATUS = {"open", "answered", "stopped"}
CYCLE_ARTIFACT_GLOBS = [
    "aidlc-docs/inception/**/*.md",
    "aidlc-docs/construction/**/*.md",
    "aidlc-docs/operations/**/*.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _ids(kind: str, text: str) -> list[str]:
    found = KIND_RE[kind].findall(text)
    return list(dict.fromkeys(found))


def parse_markdown_tables(text: str) -> list[list[dict[str, str]]]:
    """Return each markdown pipe-table as a list of row dicts (headers lowercased)."""
    tables: list[list[dict[str, str]]] = []
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            if header is not None:
                tables.append(rows)
                header, rows = None, []
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells):
            continue
        if header is None:
            header = [c.lower() for c in cells]
            continue
        row = {header[i]: cells[i] if i < len(cells) else "" for i in range(len(header))}
        rows.append(row)
    if header is not None:
        tables.append(rows)
    return tables


def load_config(root: Path) -> tuple[dict | None, list[str]]:
    path = root / "aidlc.config.yaml"
    if not path.is_file():
        return None, [f"config: aidlc.config.yaml not found at {path}"]
    try:
        data = yaml.safe_load(_read(path))
    except yaml.YAMLError as exc:
        return None, [f"config: invalid YAML in aidlc.config.yaml: {exc}"]
    if not isinstance(data, dict):
        return None, ["config: aidlc.config.yaml must be a mapping"]
    version = data.get("schema_version")
    if version not in KNOWN_SCHEMA_VERSIONS:
        return None, [
            f"config: unknown schema_version {version!r}; supported: "
            + ", ".join(sorted(KNOWN_SCHEMA_VERSIONS))
        ]
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if schema_errors:
        messages = []
        for err in schema_errors:
            loc = ".".join(str(p) for p in err.path) or "(root)"
            messages.append(f"config: schema error at {loc}: {err.message}")
        return None, messages
    dv = data.get("design_validation")
    if not isinstance(dv, dict):
        dv = {}
        data["design_validation"] = dv
    dv.setdefault("mode", "hybrid")
    dv.setdefault("human_triggers", list(DEFAULT_HUMAN_TRIGGERS))
    dv.setdefault("separate_llm_reviewer", True)

    limits = data.get("limits")
    if not isinstance(limits, dict):
        limits = {}
        data["limits"] = limits
    for key, value in DEFAULT_LIMITS.items():
        limits.setdefault(key, value)

    units = data.get("units")
    if not isinstance(units, dict):
        units = {}
        data["units"] = units
    units.setdefault("max_stories_per_unit", 8)

    ops = data.get("operations")
    if not isinstance(ops, dict):
        ops = {}
        data["operations"] = ops
    docs = ops.get("docs")
    if not isinstance(docs, dict):
        docs = {}
        ops["docs"] = docs
    docs.setdefault("language", "en")
    return data, []


def check_config(root: Path) -> list[str]:
    _cfg, errors = load_config(root)
    return errors


def check_gate_policy(root: Path, check_id: str) -> tuple[str, list[str]]:
    """How to treat this check: blocking, advisory, or skipped.

    Missing ``gates.checks`` means every known check is blocking (run).
    A present list is a whitelist: omitted ids are skipped (disabled).
    Invalid config is always a blocking error so an unknown id cannot hide.
    """
    path = root / "aidlc.config.yaml"
    if not path.is_file():
        return "blocking", []
    _cfg, errors = load_config(root)
    if errors:
        return "blocking", errors
    listed = (_cfg.get("gates") or {}).get("checks")
    if not listed:
        return "blocking", []
    for item in listed:
        if item.get("id") == check_id:
            return str(item.get("severity") or "blocking"), []
    return "skipped", []


def _declared_units(root: Path) -> set[str]:
    units: set[str] = set()
    units_file = root / UNITS_PATH
    if units_file.is_file():
        units.update(_ids("UNIT", _read(units_file)))
        for table in parse_markdown_tables(_read(units_file)):
            for row in table:
                for key in ("id", "unit"):
                    if key in row:
                        units.update(_ids("UNIT", row[key]))
    return units


def _dependency_graph(root: Path) -> tuple[dict[str, set[str]], list[str]]:
    path = root / UNITS_DAG_PATH
    if not path.is_file():
        return {}, [f"units-dag: missing {UNITS_DAG_PATH}"]
    text = _read(path)
    tables = parse_markdown_tables(text)
    graph: dict[str, set[str]] = {}
    errors: list[str] = []
    used = False
    for table in tables:
        for row in table:
            unit_cell = row.get("unit") or row.get("id")
            deps_cell = row.get("depends_on")
            if deps_cell is None:
                deps_cell = row.get("depends on", "")
            if unit_cell is None:
                continue
            used = True
            unit_ids = _ids("UNIT", unit_cell)
            if len(unit_ids) != 1:
                errors.append(
                    f"units-dag: row unit cell must be one UNIT- id, got {unit_cell!r}"
                )
                continue
            unit = unit_ids[0]
            graph.setdefault(unit, set())
            dep_text = deps_cell.strip()
            if dep_text.lower() in NONE_DEPS:
                continue
            deps = _ids("UNIT", dep_text)
            if not deps and dep_text:
                # Comma-separated names that failed the ID convention.
                parts = [p.strip() for p in re.split(r"[,;]", dep_text) if p.strip()]
                if parts:
                    errors.append(
                        f"units-dag: undeclared dependency id(s) on {unit}: {dep_text!r}"
                    )
            graph[unit].update(deps)
    if not used:
        errors.append(
            "units-dag: no dependency table with columns 'unit' and 'depends_on'"
        )
    return graph, errors


def check_units_dag(root: Path) -> list[str]:
    declared = _declared_units(root)
    graph, errors = _dependency_graph(root)
    if errors and not graph:
        return errors
    nodes = set(graph)
    for unit, deps in graph.items():
        for dep in deps:
            if dep not in graph:
                errors.append(
                    f"units-dag: undeclared unit {dep} (dependency of {unit})"
                )
            nodes.add(dep)
    if declared:
        for unit in nodes:
            if unit not in declared:
                errors.append(f"units-dag: undeclared unit {unit} (missing from {UNITS_PATH})")
        for unit in declared:
            if unit not in graph:
                errors.append(f"units-dag: declared unit {unit} missing from dependency table")
    # Cycle detection (DFS).
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}
    cycle_found: list[str] = []

    def dfs(node: str, stack: list[str]) -> None:
        color[node] = GRAY
        stack.append(node)
        for nxt in sorted(graph.get(node, ())):
            if nxt not in color:
                continue
            if color[nxt] == GRAY:
                loop = stack[stack.index(nxt) :] + [nxt]
                cycle_found.append(" -> ".join(loop))
            elif color[nxt] == WHITE:
                dfs(nxt, stack)
        stack.pop()
        color[node] = BLACK

    for node in sorted(graph):
        if color[node] == WHITE:
            dfs(node, [])
    if cycle_found:
        errors.append("units-dag: cycle detected: " + "; ".join(cycle_found))
    return errors


def _heading_ids(kind: str, text: str) -> list[str]:
    ids: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            ids.extend(_ids(kind, line))
    return list(dict.fromkeys(ids))


def _section_ids(text: str, heading: str, kind: str) -> list[str]:
    """IDs under a markdown heading (exact heading text, any level)."""
    lines = text.splitlines()
    collecting = False
    chunk: list[str] = []
    heading_re = re.compile(r"^#{1,6}\s+" + re.escape(heading) + r"\s*$", re.I)
    for line in lines:
        if heading_re.match(line):
            collecting = True
            continue
        if collecting and re.match(r"^#{1,6}\s+", line):
            break
        if collecting:
            chunk.append(line)
    return _ids(kind, "\n".join(chunk))


CANONICAL_SCOPE_NAME = re.compile(r"^scope-\d+\.md$")
MDX_IDENT_RE = re.compile(r"(?<!\\)\{([A-Za-z_][A-Za-z0-9_]*)")
FENCE_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`]+`")


def _current_scope_path(root: Path) -> Path | None:
    """`scope.current_path` from aidlc.config.yaml when that file exists."""
    path = root / "aidlc.config.yaml"
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(_read(path))
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    current = (data.get("scope") or {}).get("current_path")
    if not current:
        return None
    extra = root / current
    return extra if extra.is_file() else None


def _scope_files(root: Path) -> list[Path]:
    """Current-cycle scope files.

    Prefer `scope.current_path`. Also collect `scope-*.md`. Files that share
    a SCOPE- id are one set (canonical `scope-<digits>.md` wins over an
    alias such as `scope-atual.md`). When current_path is set, other
    SCOPE- ids are historical and are not extra in-scope sets.
    """
    directory = root / SCOPES_DIR
    current = _current_scope_path(root)
    candidates: list[Path] = []
    if current is not None:
        candidates.append(current.resolve())
    if directory.is_dir():
        for path in sorted(directory.glob("scope-*.md")):
            resolved = path.resolve()
            if resolved not in candidates:
                candidates.append(resolved)

    current_id: str | None = None
    if current is not None:
        ids = _ids("SCOPE", _read(current))
        current_id = ids[0] if ids else None

    def sort_key(path: Path) -> tuple[int, int, str]:
        canonical = 0 if CANONICAL_SCOPE_NAME.match(path.name) else 1
        current_first = 0 if current is not None and path == current.resolve() else 1
        return (canonical, current_first, path.name)

    unique: list[Path] = []
    seen: set[str] = set()
    for path in sorted(candidates, key=sort_key):
        ids = _ids("SCOPE", _read(path))
        if current_id is not None and ids and ids[0] != current_id:
            continue
        key = ids[0] if ids else str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _mdx_unescaped_idents(text: str) -> list[str]:
    stripped = FENCE_RE.sub("", text)
    stripped = INLINE_CODE_RE.sub("", stripped)
    return MDX_IDENT_RE.findall(stripped)


SKIP_SITE_DIRS = frozenset({"node_modules", "build", ".docusaurus"})
ANSWER_LINE_RE = re.compile(r"^\s*\[Answer\]:", re.M)


def _iter_site_paths(site: Path, pattern: str = "*"):
    """Walk the docs-site tree, skipping install and build output."""
    for path in site.rglob(pattern):
        rel = path.relative_to(site).parts
        if any(part in SKIP_SITE_DIRS for part in rel):
            continue
        yield path


def _covers_map(text: str, item_kind: str, covers_kind: str) -> dict[str, set[str]]:
    """Map heading IDs of item_kind to IDs listed on Covers:/Requirement: lines."""
    mapping: dict[str, set[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("#"):
            found = _ids(item_kind, line)
            current = found[0] if found else None
            if current:
                mapping.setdefault(current, set())
            continue
        if current and re.match(
            r"^\s*(covers|requirement|requirements|feature|features)\s*:", line, re.I
        ):
            mapping[current].update(_ids(covers_kind, line))
    return mapping


def check_scope_in_vision(root: Path) -> list[str]:
    errors: list[str] = []
    features_file = root / FEATURES_PATH
    if not features_file.is_file():
        return [f"scope-in-vision: missing {FEATURES_PATH}"]
    feature_ids = set(_ids("FEAT", _read(features_file)))
    files = _scope_files(root)
    if not files:
        return [f"scope-in-vision: no scope-*.md files under {SCOPES_DIR}"]
    for path in files:
        text = _read(path)
        in_scope = _section_ids(text, "In scope", "FEAT")
        if not in_scope:
            in_scope = _section_ids(text, "Features", "FEAT")
        for feat in in_scope:
            if feat not in feature_ids:
                errors.append(
                    f"scope-in-vision: {feat} in {path.relative_to(root)} "
                    f"does not resolve in {FEATURES_PATH}"
                )
    return errors


def check_traceability(root: Path) -> list[str]:
    errors: list[str] = []
    scope_files = _scope_files(root)
    if not scope_files:
        return [f"traceability: no scope-*.md files under {SCOPES_DIR}"]

    in_scope: set[str] = set()
    out_scope: set[str] = set()
    for path in scope_files:
        text = _read(path)
        in_scope.update(_section_ids(text, "In scope", "FEAT"))
        out_scope.update(_section_ids(text, "Out of scope", "FEAT"))
        out_scope.update(_section_ids(text, "Out of scope", "REQ"))
        out_scope.update(_section_ids(text, "Out of scope", "US"))

    req_file = root / REQUIREMENTS_PATH
    if not req_file.is_file():
        return [f"traceability: missing {REQUIREMENTS_PATH}"]
    req_text = _read(req_file)
    req_ids = _heading_ids("REQ", req_text) or _ids("REQ", req_text)
    req_covers = _covers_map(req_text, "REQ", "FEAT")

    covered_features: set[str] = set()
    for req, feats in req_covers.items():
        covered_features.update(feats)
    if not covered_features:
        # Fallback: any FEAT mentioned in a requirement body.
        covered_features.update(_ids("FEAT", req_text))

    for feat in sorted(in_scope):
        if feat not in covered_features:
            errors.append(f"traceability: in-scope {feat} has no requirement")

    stories_file = root / STORIES_PATH
    stories_exist = stories_file.is_file()
    if stories_exist and not _declared_units(root):
        errors.append(
            "traceability: stories exist but no UNIT record was produced; "
            "Units Generation must create at least one unit"
        )
    story_ids: list[str] = []
    story_covers: dict[str, set[str]] = {}
    if stories_exist:
        story_text = _read(stories_file)
        story_ids = _heading_ids("US", story_text) or _ids("US", story_text)
        story_covers = _covers_map(story_text, "US", "REQ")
        covered_reqs: set[str] = set()
        for _us, reqs in story_covers.items():
            covered_reqs.update(reqs)
        if not covered_reqs:
            covered_reqs.update(_ids("REQ", story_text))
        for req in req_ids:
            if req not in covered_reqs:
                errors.append(f"traceability: {req} has no story")

    map_file = root / STORY_MAP_PATH
    if map_file.is_file():
        map_text = _read(map_file)
        tables = parse_markdown_tables(map_text)
        assigned_stories: set[str] = set()
        units_with_stories: set[str] = set()
        stories_per_unit: Counter[str] = Counter()
        for table in tables:
            for row in table:
                story_cell = row.get("story") or row.get("stories") or ""
                unit_cell = row.get("unit") or row.get("units") or ""
                stories = _ids("US", story_cell)
                units = _ids("UNIT", unit_cell)
                assigned_stories.update(stories)
                if stories:
                    units_with_stories.update(units)
                    for unit in units:
                        stories_per_unit[unit] += len(stories)
        if stories_exist:
            for us in story_ids:
                if us not in assigned_stories:
                    errors.append(f"traceability: {us} is not mapped to a unit")
        graph, _dag_errors = _dependency_graph(root)
        declared = set(graph) | _declared_units(root)
        for unit in declared:
            if stories_exist and unit not in units_with_stories:
                errors.append(f"traceability: {unit} has no stories")
        cfg, _cfg_errors = load_config(root)
        max_stories = 8
        if cfg is not None:
            max_stories = int((cfg.get("units") or {}).get("max_stories_per_unit") or 8)
        for unit, n in stories_per_unit.items():
            if n > max_stories:
                errors.append(
                    f"traceability: {unit} has {n} stories; "
                    f"max_stories_per_unit is {max_stories}"
                )
    elif stories_exist:
        errors.append(f"traceability: missing {STORY_MAP_PATH}")

    # Out-of-scope IDs must not appear in cycle artifacts (inception/construction/operations).
    banned = out_scope - in_scope
    if banned:
        for rel in CYCLE_ARTIFACT_GLOBS:
            for path in root.glob(rel):
                if SCOPES_DIR.as_posix() in path.as_posix():
                    continue
                text = _read(path)
                found = set(ID_RE.findall(text))
                hits = sorted(banned & found)
                if hits:
                    errors.append(
                        "traceability: out-of-scope "
                        + ", ".join(hits)
                        + f" appears in {path.relative_to(root)}"
                    )
    return errors


def check_export(root: Path) -> list[str]:
    cfg, errors = load_config(root)
    if errors:
        return errors
    assert cfg is not None
    ops = cfg.get("operations") or {}
    site_rel = ops.get("docusaurus_path") or "docs-site"
    site = root / site_rel
    if not site.is_dir():
        return [f"export: docs-site folder missing: {site_rel}"]
    include = ops.get("include") or DEFAULT_INCLUDE
    exclude = ops.get("exclude") or DEFAULT_EXCLUDE

    site_files = list(_iter_site_paths(site))
    names = {p.name for p in site_files}
    for key in include:
        marker = INCLUDE_MARKERS.get(key)
        if not marker:
            errors.append(f"export: unknown include key {key!r}")
            continue
        name, is_dir = marker
        if name not in names:
            errors.append(f"export: included source {key!r} missing ({name})")

    md_files = [p for p in site_files if p.suffix == ".md"]
    for key in exclude:
        if key == "audit" and "audit.md" in names:
            errors.append("export: excluded audit.md is present in the docs-site folder")
        elif key == "deployment_deploy_log" and "deployment-deploy.md" in names:
            errors.append(
                "export: excluded deployment-deploy.md is present in the docs-site folder"
            )
        elif key == "question_files":
            hits = [
                str(p.relative_to(root))
                for p in md_files
                if QUESTION_NAME_RE.search(p.name)
            ]
            if hits:
                errors.append("export: excluded question files present: " + ", ".join(hits))
        elif key == "raw_plans":
            hits = [
                str(p.relative_to(root))
                for p in md_files
                if PLAN_NAME_RE.search(p.name) or "plans" in p.relative_to(site).parts
            ]
            if hits:
                errors.append("export: excluded raw plans present: " + ", ".join(hits))

    for md in sorted(md_files):
        text = _read(md)
        rel = md.relative_to(root)
        idents = _mdx_unescaped_idents(text)
        if idents:
            errors.append(
                f"export: unescaped MDX identifier {idents[0]!r} in {rel} "
                r"(escape braces like \{id\} or wrap in backticks)"
            )
        if ANSWER_LINE_RE.search(text):
            errors.append(
                f"export: unescaped [Answer]: line in {rel} "
                r"(rewrite as \[Answer\]: or wrap so it is not a link reference)"
            )
    errors.extend(_prove_docusaurus_build(site, ops))
    return errors


def _prove_docusaurus_build(site: Path, ops: dict) -> list[str]:
    """Run ``npm run build`` when the site has a package.json, or when asked."""
    prove = ops.get("prove_build")
    pkg = site / "package.json"
    has_pkg = pkg.is_file()
    if prove is False:
        return []
    if prove is None and not has_pkg:
        return []
    site_name = site.name
    if prove is True and not has_pkg:
        return [f"export: prove_build is true but {site_name}/package.json is missing"]
    npm = shutil.which("npm")
    node = shutil.which("node")
    if not npm or not node:
        return [
            "export: Docusaurus build required "
            "(operations.prove_build or docs-site/package.json) "
            "but node/npm is not available"
        ]
    try:
        proc = subprocess.run(
            [npm, "run", "build"],
            cwd=site,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return ["export: npm run build timed out"]
    if proc.returncode == 0:
        return []
    detail = (proc.stderr or proc.stdout or "").strip().splitlines()
    tail = "\n".join(detail[-5:]) if detail else ""
    extra = f"\n{tail}" if tail else ""
    return [f"export: npm run build failed (exit {proc.returncode}){extra}"]


def check_assumptions(root: Path) -> list[str]:
    """Table format plus no unresolved blocking rows (`common/assumptions.md`)."""
    path = root / ASSUMPTIONS_PATH
    if not path.is_file():
        return [f"assumptions: missing {ASSUMPTIONS_PATH}"]
    text = _read(path)
    tables = parse_markdown_tables(text)
    errors: list[str] = []
    seen: dict[str, int] = {}
    for table in tables:
        if not table:
            continue
        missing_cols = [
            col for col in ASSUMPTION_REQUIRED_COLS if col not in table[0]
        ]
        if missing_cols:
            errors.append(
                "assumptions: table missing required columns: "
                + ", ".join(missing_cols)
            )
            continue
        for row in table:
            aid = row.get("id", "").strip()
            if not aid:
                errors.append("assumptions: row with empty id")
                continue
            if not ASSUMPTION_ID_RE.fullmatch(aid):
                errors.append(
                    f"assumptions: {aid} is not an A- plus at least three digits id"
                )
            if aid in seen:
                errors.append(f"assumptions: duplicate id {aid}")
            seen[aid] = seen.get(aid, 0) + 1
            for col in ("stage", "question", "assumption_or_answer"):
                if not row.get(col, "").strip():
                    errors.append(f"assumptions: {aid} has empty {col}")
            blocking = row.get("blocking", "").strip().lower()
            if blocking not in ASSUMPTION_BLOCKING:
                errors.append(
                    f"assumptions: {aid} blocking must be yes or no, got {blocking!r}"
                )
            status = row.get("status", "").strip().lower()
            if status not in ASSUMPTION_STATUS:
                errors.append(
                    f"assumptions: {aid} status must be open, answered, or stopped, "
                    f"got {status!r}"
                )
            if blocking == "yes" and status != "answered":
                errors.append(
                    f"assumptions: open blocking question {aid} (status {status})"
                )
    return errors


def check_stories(root: Path) -> list[str]:
    """Format + min/max acceptance criteria from config.stories (F3)."""
    cfg, cfg_errors = load_config(root)
    stories_cfg: dict = {}
    if cfg is not None:
        stories_cfg = cfg.get("stories") or {}
    elif cfg_errors and "not found" not in cfg_errors[0]:
        return cfg_errors
    min_ac = int(stories_cfg.get("min_acceptance_criteria") or 2)
    max_ac = int((stories_cfg.get("max_size") or {}).get("max_acceptance_criteria") or 5)
    fmt = str(stories_cfg.get("format") or "")
    invest = bool(stories_cfg.get("invest_required", True))
    path = root / STORIES_PATH
    if not path.is_file():
        return []
    text = _read(path)
    blocks = re.split(r"(?=^#{1,6}\s+US-)", text, flags=re.M)
    errors: list[str] = []
    found = 0
    for block in blocks:
        ids = _heading_ids("US", block) or _ids("US", block.splitlines()[0] if block else "")
        if not ids:
            continue
        us = ids[0]
        found += 1
        ac_count = _acceptance_criteria_count(block)
        if ac_count < min_ac:
            errors.append(
                f"stories: {us} has {ac_count} acceptance criteria; min is {min_ac}"
            )
        if ac_count > max_ac:
            errors.append(
                f"stories: {us} has {ac_count} acceptance criteria; max is {max_ac}"
            )
        if "as_a" in fmt.lower() or invest:
            lowered = block.lower()
            if "as a" not in lowered or "i want" not in lowered:
                errors.append(
                    f"stories: {us} must use As a / I want (format {fmt!r})"
                )
    if found == 0:
        errors.append(f"stories: no US- headings in {STORIES_PATH}")
    return errors


_SCENARIO_RE = re.compile(r"^\s*(?:#{1,6}\s+)?scenario(?:\s|:)", re.I)
_GIVEN_RE = re.compile(r"^\s*(?:[-*] )?(?:\*\*)?given\b", re.I)
_AC_HEADING_RE = re.compile(r"^#{1,6}\s+.*acceptance", re.I)
_AC_BOLD_RE = re.compile(r"^\s*\*\*acceptance criteria", re.I)
_LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+\S")
_GHERKIN_RE = re.compile(
    r"^\s*(?:[-*] )?(?:\*\*)?(?:given|when|then|and|but)\b", re.I
)


def _acceptance_criteria_count(block: str) -> int:
    """Count scenarios (criteria), not every Given/When/Then line."""
    lines = block.splitlines()
    n_scenario = sum(1 for line in lines if _SCENARIO_RE.match(line))
    if n_scenario:
        return n_scenario
    n_given = sum(1 for line in lines if _GIVEN_RE.match(line))
    if n_given:
        return n_given
    in_ac = False
    n = 0
    for line in lines:
        if _AC_HEADING_RE.match(line) or _AC_BOLD_RE.match(line):
            in_ac = True
            continue
        if in_ac and re.match(r"^#{1,6}\s+", line):
            in_ac = False
        if in_ac and _LIST_ITEM_RE.match(line) and not _GHERKIN_RE.match(line):
            n += 1
    return n
