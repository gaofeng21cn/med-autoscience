from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import tomllib

from med_autoscience.display_pack_contract import (
    DisplayPackManifest,
    DisplayTemplateManifest,
    load_display_pack_manifest,
    load_display_template_manifest,
)

_VALID_SOURCE_KINDS = frozenset(("local_dir", "git_repo", "python_package"))


@dataclass(frozen=True)
class DisplayPackSourceConfig:
    pack_id: str
    kind: str
    path: str | None
    package: str | None
    pack_subdir: str
    version: str | None
    declared_in: str
    config_path: Path
    resolved_source_root: Path
    resolved_root: Path


@dataclass(frozen=True)
class DisplayPackResolution:
    repo_config_path: Path
    paper_config_path: Path | None
    paper_config_present: bool
    inherit_repo_defaults: bool
    enabled_pack_ids: tuple[str, ...]
    source_configs: tuple[DisplayPackSourceConfig, ...]


@dataclass(frozen=True)
class LoadedDisplayPack:
    pack_root: Path
    pack_manifest: DisplayPackManifest
    source_config: DisplayPackSourceConfig


@dataclass(frozen=True)
class LoadedDisplayTemplate:
    pack_root: Path
    template_path: Path
    pack_manifest: DisplayPackManifest
    template_manifest: DisplayTemplateManifest
    source_config: DisplayPackSourceConfig


def _expect_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{key} must be non-empty")
    return normalized


def _optional_str(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{key} must be non-empty when provided")
    return normalized


def _expect_bool(payload: dict[str, object], key: str, *, default: bool) -> bool:
    value = payload.get(key)
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a bool")
    return value


def _optional_str_list(payload: dict[str, object], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list of strings")
    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{key}[{index}] must be a non-empty string")
        normalized.append(item.strip())
    return tuple(normalized)


def _dedupe_preserving_order(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for item in values:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return tuple(result)


def _load_toml_payload(path: Path) -> dict[str, object]:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a top-level object")
    return payload


def _expect_source_kind(payload: dict[str, object]) -> str:
    kind = _expect_str(payload, "kind")
    if kind not in _VALID_SOURCE_KINDS:
        raise ValueError(f"kind must be one of {sorted(_VALID_SOURCE_KINDS)!r}")
    return kind


def _normalize_pack_subdir(value: str | None) -> str:
    normalized = "." if value is None else value.strip()
    if not normalized:
        return "."
    subdir = Path(normalized)
    if subdir.is_absolute():
        raise ValueError("pack_subdir must be relative")
    return subdir.as_posix()


def _resolve_python_package_root(package_name: str) -> Path:
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        raise ValueError(f"python package `{package_name}` is not importable")
    if spec.submodule_search_locations:
        return Path(next(iter(spec.submodule_search_locations))).resolve()
    if spec.origin is not None:
        return Path(spec.origin).resolve().parent
    raise ValueError(f"python package `{package_name}` does not expose a filesystem location")


def _parse_source_configs(
    payload: dict[str, object],
    *,
    config_path: Path,
    anchor_root: Path,
    declared_in: str,
) -> dict[str, DisplayPackSourceConfig]:
    raw_sources = payload.get("sources")
    if raw_sources is None:
        return {}
    if not isinstance(raw_sources, list):
        raise ValueError("sources must be a list")

    sources_by_pack_id: dict[str, DisplayPackSourceConfig] = {}
    for index, raw_source in enumerate(raw_sources):
        if not isinstance(raw_source, dict):
            raise ValueError(f"sources[{index}] must be an object")
        pack_id = _expect_str(raw_source, "pack_id")
        if pack_id in sources_by_pack_id:
            raise ValueError(f"duplicate source for pack_id `{pack_id}`")
        kind = _expect_source_kind(raw_source)
        pack_subdir = _normalize_pack_subdir(_optional_str(raw_source, "pack_subdir"))
        raw_path: str | None = None
        package_name: str | None = None
        if kind == "local_dir":
            raw_path = _expect_str(raw_source, "path")
            if pack_subdir != ".":
                raise ValueError("local_dir sources must not set pack_subdir")
            resolved_source_root = (anchor_root / raw_path).expanduser().resolve()
            resolved_root = resolved_source_root
        elif kind == "git_repo":
            raw_path = _expect_str(raw_source, "path")
            resolved_source_root = (anchor_root / raw_path).expanduser().resolve()
            git_dir = resolved_source_root / ".git"
            if not git_dir.exists():
                raise ValueError(f"git_repo source `{raw_path}` must point to a git checkout root")
            resolved_root = (resolved_source_root / pack_subdir).resolve()
        else:
            package_name = _expect_str(raw_source, "package")
            resolved_source_root = _resolve_python_package_root(package_name)
            resolved_root = (resolved_source_root / pack_subdir).resolve()
        sources_by_pack_id[pack_id] = DisplayPackSourceConfig(
            pack_id=pack_id,
            kind=kind,
            path=raw_path,
            package=package_name,
            pack_subdir=pack_subdir,
            version=_optional_str(raw_source, "version"),
            declared_in=declared_in,
            config_path=config_path,
            resolved_source_root=resolved_source_root,
            resolved_root=resolved_root,
        )
    return sources_by_pack_id


def resolve_display_pack_selection(
    repo_root: Path,
    *,
    paper_root: Path | None = None,
) -> DisplayPackResolution:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    repo_config_path = normalized_repo_root / "config" / "display_packs.toml"
    repo_payload = _load_toml_payload(repo_config_path)

    enabled_pack_ids = _dedupe_preserving_order(_optional_str_list(repo_payload, "default_enabled_packs"))
    if not enabled_pack_ids:
        raise ValueError("default_enabled_packs must contain at least one pack")

    source_by_pack_id = _parse_source_configs(
        repo_payload,
        config_path=repo_config_path,
        anchor_root=normalized_repo_root,
        declared_in="repo",
    )

    normalized_paper_root = Path(paper_root).expanduser().resolve() if paper_root is not None else None
    paper_config_path = normalized_paper_root / "display_packs.toml" if normalized_paper_root is not None else None
    paper_config_present = bool(paper_config_path and paper_config_path.exists())
    inherit_repo_defaults = True

    if paper_config_present and paper_config_path is not None and normalized_paper_root is not None:
        paper_payload = _load_toml_payload(paper_config_path)
        inherit_repo_defaults = _expect_bool(paper_payload, "inherit_repo_defaults", default=True)
        if not inherit_repo_defaults:
            enabled_pack_ids = ()
        enabled_pack_ids = _dedupe_preserving_order(
            [*enabled_pack_ids, *_optional_str_list(paper_payload, "enabled_packs")]
        )
        disabled_packs = set(_optional_str_list(paper_payload, "disabled_packs"))
        enabled_pack_ids = tuple(item for item in enabled_pack_ids if item not in disabled_packs)

        paper_sources = _parse_source_configs(
            paper_payload,
            config_path=paper_config_path,
            anchor_root=normalized_paper_root,
            declared_in="paper",
        )
        source_by_pack_id.update(paper_sources)

    resolved_sources: list[DisplayPackSourceConfig] = []
    for pack_id in enabled_pack_ids:
        try:
            resolved_sources.append(source_by_pack_id[pack_id])
        except KeyError as exc:
            raise ValueError(f"enabled pack `{pack_id}` is missing from sources") from exc

    return DisplayPackResolution(
        repo_config_path=repo_config_path,
        paper_config_path=paper_config_path,
        paper_config_present=paper_config_present,
        inherit_repo_defaults=inherit_repo_defaults,
        enabled_pack_ids=tuple(enabled_pack_ids),
        source_configs=tuple(resolved_sources),
    )


def load_enabled_local_display_pack_records(
    repo_root: Path,
    *,
    paper_root: Path | None = None,
) -> list[LoadedDisplayPack]:
    resolution = resolve_display_pack_selection(repo_root, paper_root=paper_root)
    records: list[LoadedDisplayPack] = []

    for source_config in resolution.source_configs:
        manifest = load_display_pack_manifest(source_config.resolved_root / "display_pack.toml")
        if manifest.pack_id != source_config.pack_id:
            raise ValueError(
                f"pack_id mismatch: source={source_config.pack_id!r}, manifest={manifest.pack_id!r}"
            )
        if source_config.version is not None and manifest.version != source_config.version:
            raise ValueError(
                f"version mismatch for pack `{source_config.pack_id}`: "
                f"requested {source_config.version!r}, manifest {manifest.version!r}"
            )
        records.append(
            LoadedDisplayPack(
                pack_root=source_config.resolved_root,
                pack_manifest=manifest,
                source_config=source_config,
            )
        )
    return records


def load_enabled_local_display_packs(
    repo_root: Path,
    *,
    paper_root: Path | None = None,
) -> list[DisplayPackManifest]:
    return [
        item.pack_manifest for item in load_enabled_local_display_pack_records(repo_root, paper_root=paper_root)
    ]


def load_enabled_local_display_template_records(
    repo_root: Path,
    *,
    paper_root: Path | None = None,
) -> list[LoadedDisplayTemplate]:
    records: list[LoadedDisplayTemplate] = []
    for loaded_pack in load_enabled_local_display_pack_records(repo_root, paper_root=paper_root):
        template_paths = sorted((loaded_pack.pack_root / "templates").glob("*/template.toml"))
        for template_path in template_paths:
            records.append(
                LoadedDisplayTemplate(
                    pack_root=loaded_pack.pack_root,
                    template_path=template_path,
                    pack_manifest=loaded_pack.pack_manifest,
                    template_manifest=load_display_template_manifest(
                        template_path,
                        expected_pack_id=loaded_pack.pack_manifest.pack_id,
                    ),
                    source_config=loaded_pack.source_config,
                )
            )
    return records


def load_enabled_local_display_pack_templates(
    repo_root: Path,
    *,
    paper_root: Path | None = None,
) -> list[DisplayTemplateManifest]:
    return [
        item.template_manifest
        for item in load_enabled_local_display_template_records(repo_root, paper_root=paper_root)
    ]


def load_enabled_local_display_pack_template_records(
    repo_root: Path,
    *,
    paper_root: Path | None = None,
) -> list[LoadedDisplayTemplate]:
    return load_enabled_local_display_template_records(repo_root, paper_root=paper_root)
