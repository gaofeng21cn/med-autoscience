from __future__ import annotations

import os
from pathlib import Path


EXTERNAL_OWNER_SKILL_MAP = {
    "figure": "medical-research-figure",
    "write": "medical-research-write",
    "review": "medical-research-review",
}
EXTERNAL_OWNER_SKILL_IDS = frozenset(EXTERNAL_OWNER_SKILL_MAP)
MAS_SCHOLAR_SKILLS_REPO_ENV = "MAS_SCHOLAR_SKILLS_REPO"
MAS_SCHOLAR_SKILLS_REPO_NAME = "mas-scholar-skills"
REPO_ROOT = Path(__file__).resolve().parents[3]


def candidate_scholar_skills_repo_roots() -> list[Path]:
    roots: list[Path] = []
    env_value = str(os.environ.get(MAS_SCHOLAR_SKILLS_REPO_ENV) or "").strip()
    if env_value:
        roots.append(Path(env_value).expanduser())
    roots.extend(
        [
            REPO_ROOT.parent / MAS_SCHOLAR_SKILLS_REPO_NAME,
            REPO_ROOT.parent.parent / MAS_SCHOLAR_SKILLS_REPO_NAME,
        ]
    )
    deduped: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        resolved = root.resolve()
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            deduped.append(resolved)
    return deduped


def external_owner_skill_source_path(skill_id: str) -> Path | None:
    source_skill_id = EXTERNAL_OWNER_SKILL_MAP.get(skill_id)
    if source_skill_id is None:
        return None
    for repo_root in candidate_scholar_skills_repo_roots():
        candidate = repo_root / "skills" / source_skill_id / "SKILL.md"
        if candidate.exists():
            return candidate
    return None


def external_owner_skill_missing_message(skill_id: str) -> str:
    source_skill_id = EXTERNAL_OWNER_SKILL_MAP[skill_id]
    searched = ", ".join(str(path) for path in candidate_scholar_skills_repo_roots())
    return (
        f"External MAS Scholar Skills source missing for `{skill_id}` / `{source_skill_id}`. "
        f"Set {MAS_SCHOLAR_SKILLS_REPO_ENV} to the mas-scholar-skills repo or run "
        "`opl connect sync-skills --domain mas-scholar-skills --json` before MAS overlay bootstrap. "
        f"Searched: {searched}"
    )


def load_external_owner_skill_text(skill_id: str) -> str:
    source_path = external_owner_skill_source_path(skill_id)
    if source_path is None:
        raise FileNotFoundError(external_owner_skill_missing_message(skill_id))
    return source_path.read_text(encoding="utf-8")


def seed_external_owner_skill_from_source(
    *,
    skill_id: str,
    target_root: Path,
    skill_path: Path,
) -> None:
    if skill_id not in EXTERNAL_OWNER_SKILL_IDS or skill_path.exists():
        return
    source_path = external_owner_skill_source_path(skill_id)
    if source_path is None:
        return
    target_root.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
