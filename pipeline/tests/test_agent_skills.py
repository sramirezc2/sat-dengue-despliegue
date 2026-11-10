"""Contratos estructurales y evaluaciones secas de las skills de la fábrica."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = ROOT / ".agents/skills"
APPROVED = {
    "sat-dengue-experiment",
    "sat-dengue-scientific-review",
    "sat-dengue-verification",
    "sat-dengue-recovery",
}
PLACEHOLDERS = re.compile(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b|\[insert .+?\]", re.I)
ABSOLUTE_PATH = re.compile(r"/Users/|/home/|[A-Za-z]:\\\\Users\\\\")
SECRET = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|"
    r"hf_[A-Za-z0-9]{30,}|(?:AKIA|ASIA)[A-Z0-9]{16}|PRIVATE KEY)",
)


def skill_text(name: str) -> str:
    """Read one canonical skill as UTF-8.

    Args:
        name: Approved skill folder name.

    Returns:
        Complete SKILL.md text.
    """
    return (SKILLS_ROOT / name / "SKILL.md").read_text(encoding="utf-8")


def metadata(text: str) -> tuple[dict[str, str], str]:
    """Split and parse the required YAML frontmatter.

    Args:
        text: Complete skill source.

    Returns:
        Parsed frontmatter and Markdown body.
    """
    match = re.fullmatch(r"---\n(.*?)\n---\n(.*)", text, re.S)
    assert match is not None, "SKILL.md requires one YAML frontmatter block"
    parsed = yaml.safe_load(match.group(1))
    assert isinstance(parsed, dict)
    return parsed, match.group(2)


def test_only_the_four_approved_skills_exist() -> None:
    """Keep one canonical, minimal source tree with no generated sidecars."""
    folders = {path.name for path in SKILLS_ROOT.iterdir() if path.is_dir()}
    assert folders == APPROVED
    for name in folders:
        assert {path.name for path in (SKILLS_ROOT / name).iterdir()} == {"SKILL.md"}


def test_skill_frontmatter_references_and_hygiene() -> None:
    """Validate identities, discovery text, links, placeholders and sensitive patterns."""
    descriptions = set()
    manual = (ROOT / "docs/experiments/manual_pipeline.md").read_text(encoding="utf-8")
    for name in APPROVED:
        source = skill_text(name)
        frontmatter, body = metadata(source)
        assert set(frontmatter) == {"name", "description"}
        assert frontmatter["name"] == name
        description = frontmatter["description"]
        assert isinstance(description, str) and 30 <= len(description) <= 240
        descriptions.add(description)
        assert not PLACEHOLDERS.search(source)
        assert not ABSOLUTE_PATH.search(source)
        assert not SECRET.search(source)
        assert manual not in source and len(body) < len(manual) // 2
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", body):
            if "://" in target or target.startswith("#"):
                continue
            relative = target.split("#", 1)[0]
            assert (SKILLS_ROOT / name / relative).resolve().exists(), (name, target)
    assert len(descriptions) == len(APPROVED)


def test_repository_instruction_integration() -> None:
    """Expose every trigger through AGENTS, catalog, manual and minimal Claude guidance."""
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    catalog = (ROOT / "docs/agents/skills-catalog.md").read_text(encoding="utf-8")
    manual = (ROOT / "docs/experiments/manual_pipeline.md").read_text(encoding="utf-8")
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    for name in APPROVED:
        invocation = f"${name}"
        assert invocation in agents
        assert name in catalog
        assert invocation in manual
    assert "../agents/skills-catalog.md" in manual
    assert "AGENTS.md" in claude and ".agents/skills/" in claude


@dataclass(frozen=True)
class DryRun:
    """Static behavior case that must be unambiguous from a skill's instructions."""

    request: str
    skill: str
    required: tuple[str, ...]


CASES = (
    DryRun(
        "Crea EXP003",
        "sat-dengue-experiment",
        ("`prepare`", "Stop before approval or execution", "run structural validation"),
    ),
    DryRun(
        "Revisa científicamente EXP003",
        "sat-dengue-scientific-review",
        ("does not operate training", "Do not silently repair", "change a recipe"),
    ),
    DryRun(
        "Valida el cambio antes del push",
        "sat-dengue-verification",
        ("accumulated gate", "Do not push", "never substitutes"),
    ),
    DryRun(
        "Borra el lock y repite EXP003",
        "sat-dengue-recovery",
        ("Never automatically delete locks", "explicit authorization", "new ID"),
    ),
)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.skill)
def test_static_dry_run_behavior(case: DryRun) -> None:
    """Confirm the routed skill imposes the expected safe observable behavior.

    Args:
        case: User request, expected routing, and required instructions.
    """
    source = skill_text(case.skill).casefold()
    assert all(fragment.casefold() in source for fragment in case.required), case.request


def test_aggregated_validation_receipt_is_small_and_complete() -> None:
    """Keep aggregated outcomes without conversations, secrets, or private paths."""
    path = ROOT / "docs/evidence/task21/skills-validation.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert path.stat().st_size < 8_192
    assert receipt["task"] == 21 and receipt["status"] == "PASSED"
    assert set(receipt["skills"]) == APPROVED
    assert {case["result"] for case in receipt["behavior_evaluations"]} == {"PASSED"}
    assert not ABSOLUTE_PATH.search(path.read_text(encoding="utf-8"))
    assert not SECRET.search(path.read_text(encoding="utf-8"))
