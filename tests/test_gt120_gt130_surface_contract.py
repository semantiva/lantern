from __future__ import annotations

from pathlib import Path

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
AUTHORING_CONTRACTS = PRODUCT_ROOT / "lantern/authoring_contracts"
ADMIN_PROCEDURES = PRODUCT_ROOT / "lantern/administration_procedures"
TEMPLATES = PRODUCT_ROOT / "lantern/templates"


def test_no_lantern_change_index_pseudo_path_in_shipped_guides() -> None:
    """AC-1: no runtime-shipped guide, procedure, or template uses Lantern/change/INDEX.md."""
    offending_files: list[str] = []
    for search_root in (AUTHORING_CONTRACTS, ADMIN_PROCEDURES, TEMPLATES):
        for path in search_root.rglob("*.md"):
            if "Lantern/change/INDEX.md" in path.read_text(encoding="utf-8"):
                offending_files.append(str(path.relative_to(PRODUCT_ROOT)))
    assert offending_files == [], (
        "Lantern/change/INDEX.md pseudo-path found in runtime-shipped files: "
        + str(offending_files)
    )


def test_no_lantern_path_semantics_note_in_ev_templates() -> None:
    """AC-2: Lantern/... path-semantics disclaimer must not appear in GT-120/GT-130 EV templates."""
    ev_gt120 = (TEMPLATES / "EV_TEMPLATE__GT120_SELECTION_REPORT.md").read_text(encoding="utf-8")
    ev_gt130 = (TEMPLATES / "EV_TEMPLATE__GT130_VERIFICATION_REPORT.md").read_text(encoding="utf-8")
    disclaimer_fragment = "Lantern/... path in this document is a logical governed-workspace path"
    assert disclaimer_fragment not in ev_gt120, "GT-120 EV template still contains Lantern/... path-semantics disclaimer"
    assert disclaimer_fragment not in ev_gt130, "GT-130 EV template still contains Lantern/... path-semantics disclaimer"


def test_no_lantern_ci_selection_guide_pseudo_path_in_gt120_surface() -> None:
    """AC-2: Lantern/change_increment_selection_guide pseudo-path must not appear in GT-120 procedure or EV template."""
    gt120_proc = (ADMIN_PROCEDURES / "GT-120__CI_SELECTION_ADMINISTRATION_v0.2.1.md").read_text(encoding="utf-8")
    ev_gt120 = (TEMPLATES / "EV_TEMPLATE__GT120_SELECTION_REPORT.md").read_text(encoding="utf-8")
    pseudo_path = "Lantern/change_increment_selection_guide"
    assert pseudo_path not in gt120_proc, "Lantern/change_increment_selection_guide pseudo-path found in GT-120 procedure"
    assert pseudo_path not in ev_gt120, "Lantern/change_increment_selection_guide pseudo-path found in GT-120 EV template"


def test_agents_template_uses_generic_workspace_language() -> None:
    """AC-3: AGENTS template must use generic governed-product governance language, not Lantern-specific."""
    agents_template = (TEMPLATES / "TEMPLATE__PRODUCT_REPO_AGENTS.md").read_text(encoding="utf-8")
    agents_file = (PRODUCT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    lantern_specific = "companion Lantern governance workspace"
    generic_phrase = "companion governed product governance workspace"
    assert lantern_specific not in agents_template, (
        "TEMPLATE__PRODUCT_REPO_AGENTS.md still contains Lantern-specific companion workspace language"
    )
    assert generic_phrase in agents_template, (
        "TEMPLATE__PRODUCT_REPO_AGENTS.md does not contain the generic governed-product governance workspace phrase"
    )
    assert lantern_specific not in agents_file, (
        "AGENTS.md managed block still contains Lantern-specific companion workspace language"
    )


def test_readme_uses_package_install_for_grammar() -> None:
    """AC-4: README must not instruct sibling-source Grammar install."""
    readme = (PRODUCT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "pip install -e ../lantern-grammar" not in readme, (
        "README still instructs sibling-source Lantern Grammar install"
    )


def test_conftest_has_no_sibling_grammar_probe() -> None:
    """AC-5: conftest.py must not probe sibling filesystem paths for lantern-grammar/src."""
    conftest = (PRODUCT_ROOT / "tests/conftest.py").read_text(encoding="utf-8")
    assert "_CANDIDATE_GRAMMAR_PATHS" not in conftest, (
        "conftest.py still defines _CANDIDATE_GRAMMAR_PATHS sibling-probe list"
    )
    assert 'lantern-grammar' not in conftest, (
        "conftest.py still references lantern-grammar sibling path"
    )
