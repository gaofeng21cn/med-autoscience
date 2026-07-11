from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from med_autoscience.medical_figure_composition_recipes import (
    CompositionRecipe,
    parse_composition_recipes,
    validate_composition_recipe_refs,
)
from med_autoscience.medical_figure_family_recipes import (
    StarterRecipe,
    derive_starter_recipes,
    validate_family_recipe_refs,
    validate_starter_recipes,
)


_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_ROOT = _REPO_ROOT / "contracts" / "medical-figure-family-catalog"


@dataclass(frozen=True)
class StyleProfile:
    profile_id: str
    purpose: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class PaletteToken:
    token_id: str
    use_for: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class QualityGate:
    gate_id: str
    checks: tuple[str, ...]
    payload: dict[str, Any]


@dataclass(frozen=True)
class ExternalSource:
    source_id: str
    source_type: str
    url: str
    observed_date: str
    adopted_pattern: str


@dataclass(frozen=True)
class FigureFamily:
    family_id: str
    category_id: str
    title: str
    intent: str
    canonical_variants: tuple[str, ...]
    data_roles: tuple[str, ...]
    starter_recipe_refs: tuple[str, ...]
    style_tokens: tuple[str, ...]
    palette_tokens: tuple[str, ...]
    qa_gate_ids: tuple[str, ...]
    loose_match_terms: tuple[str, ...]
    external_refs: tuple[str, ...]
    template_seed_ids: tuple[str, ...]
    ai_adaptation_notes: str


@dataclass(frozen=True)
class FigureFamilyCategory:
    category_id: str
    title: str
    families: tuple[FigureFamily, ...]


@dataclass(frozen=True)
class MedicalFigureFamilyCatalog:
    schema_version: int
    catalog_id: str
    owner: str
    purpose: str
    machine_boundary: str
    source_module: str
    ai_adaptation_policy: dict[str, Any]
    style_profiles: tuple[StyleProfile, ...]
    palette_tokens: tuple[PaletteToken, ...]
    qa_gates: tuple[QualityGate, ...]
    external_sources: tuple[ExternalSource, ...]
    starter_recipe_policy: dict[str, Any]
    starter_recipes: tuple[StarterRecipe, ...]
    composition_recipe_policy: dict[str, Any]
    composition_recipes: tuple[CompositionRecipe, ...]
    categories: tuple[FigureFamilyCategory, ...]
    families_by_id: dict[str, FigureFamily]
    categories_by_id: dict[str, FigureFamilyCategory]
    starter_recipes_by_id: dict[str, StarterRecipe]
    composition_recipes_by_id: dict[str, CompositionRecipe]
    loose_terms_by_family_id: dict[str, tuple[str, ...]]

    @property
    def family_count(self) -> int:
        return len(self.families_by_id)

    def family(self, family_id: str) -> FigureFamily:
        try:
            return self.families_by_id[family_id]
        except KeyError as exc:
            raise ValueError(f"unknown medical figure family `{family_id}`") from exc

    def families_matching(self, query: str) -> tuple[FigureFamily, ...]:
        normalized_query = query.strip().casefold()
        if not normalized_query:
            return ()
        matches: list[FigureFamily] = []
        for family_id, terms in self.loose_terms_by_family_id.items():
            if any(term in normalized_query or normalized_query in term for term in terms):
                matches.append(self.families_by_id[family_id])
        return tuple(matches)


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _expect_int(payload: dict[str, Any], key: str, *, context: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{context}.{key} must be an integer")
    return value


def _expect_str(payload: dict[str, Any], key: str, *, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value.strip()


def _expect_bool(payload: dict[str, Any], key: str, *, context: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{context}.{key} must be a bool")
    return value


def _expect_str_tuple(payload: dict[str, Any], key: str, *, context: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{context}.{key} must be a list of strings")
    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{context}.{key}[{index}] must be a non-empty string")
        normalized.append(item.strip())
    return tuple(normalized)


def _expect_object_list(payload: dict[str, Any], key: str, *, context: str) -> tuple[dict[str, Any], ...]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{context}.{key} must be a list")
    objects: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"{context}.{key}[{index}] must be an object")
        objects.append(dict(item))
    return tuple(objects)


def _resolve_catalog_ref(catalog_root: Path, ref: str, *, context: str) -> Path:
    ref_path = Path(ref)
    if ref_path.is_absolute():
        raise ValueError(f"{context} must be relative to the catalog root")
    resolved = (catalog_root / ref_path).resolve()
    try:
        resolved.relative_to(catalog_root.resolve())
    except ValueError as exc:
        raise ValueError(f"{context} must stay inside the catalog root") from exc
    if not resolved.is_file():
        raise ValueError(f"{context} points to missing file `{ref}`")
    return resolved


def _parse_style_profiles(payload: dict[str, Any]) -> tuple[StyleProfile, ...]:
    profiles: list[StyleProfile] = []
    seen: set[str] = set()
    for index, item in enumerate(_expect_object_list(payload, "style_profiles", context="style_profiles")):
        context = f"style_profiles[{index}]"
        profile_id = _expect_str(item, "profile_id", context=context)
        if profile_id in seen:
            raise ValueError(f"duplicate style profile `{profile_id}`")
        seen.add(profile_id)
        profiles.append(
            StyleProfile(
                profile_id=profile_id,
                purpose=_expect_str(item, "purpose", context=context),
                payload=item,
            )
        )
    return tuple(profiles)


def _parse_palette_tokens(payload: dict[str, Any]) -> tuple[PaletteToken, ...]:
    tokens: list[PaletteToken] = []
    seen: set[str] = set()
    for index, item in enumerate(_expect_object_list(payload, "palette_tokens", context="palette_tokens")):
        context = f"palette_tokens[{index}]"
        token_id = _expect_str(item, "token_id", context=context)
        if token_id in seen:
            raise ValueError(f"duplicate palette token `{token_id}`")
        seen.add(token_id)
        tokens.append(
            PaletteToken(
                token_id=token_id,
                use_for=_expect_str(item, "use_for", context=context),
                payload=item,
            )
        )
    return tuple(tokens)


def _parse_quality_gates(payload: dict[str, Any]) -> tuple[QualityGate, ...]:
    gates: list[QualityGate] = []
    seen: set[str] = set()
    for index, item in enumerate(_expect_object_list(payload, "qa_gates", context="qa_gates")):
        context = f"qa_gates[{index}]"
        gate_id = _expect_str(item, "gate_id", context=context)
        if gate_id in seen:
            raise ValueError(f"duplicate QA gate `{gate_id}`")
        seen.add(gate_id)
        gates.append(
            QualityGate(
                gate_id=gate_id,
                checks=_expect_str_tuple(item, "checks", context=context),
                payload=item,
            )
        )
    return tuple(gates)


def _parse_external_sources(payload: dict[str, Any]) -> tuple[ExternalSource, ...]:
    sources: list[ExternalSource] = []
    seen: set[str] = set()
    for index, item in enumerate(_expect_object_list(payload, "external_sources", context="external_sources")):
        context = f"external_sources[{index}]"
        source_id = _expect_str(item, "source_id", context=context)
        if source_id in seen:
            raise ValueError(f"duplicate external source `{source_id}`")
        seen.add(source_id)
        sources.append(
            ExternalSource(
                source_id=source_id,
                source_type=_expect_str(item, "source_type", context=context),
                url=_expect_str(item, "url", context=context),
                observed_date=_expect_str(item, "observed_date", context=context),
                adopted_pattern=_expect_str(item, "adopted_pattern", context=context),
            )
        )
    return tuple(sources)


def _parse_family(
    item: dict[str, Any],
    *,
    expected_category_id: str,
    policy_id: str,
    context: str,
) -> tuple[FigureFamily, tuple[StarterRecipe, ...]]:
    family_id = _expect_str(item, "family_id", context=context)
    category_id = _expect_str(item, "category_id", context=context)
    if category_id != expected_category_id:
        raise ValueError(f"{context}.category_id must equal `{expected_category_id}`")
    overrides = _expect_object_list(item, "starter_recipe_overrides", context=context)
    if not overrides:
        raise ValueError(f"{context}.starter_recipe_overrides must be non-empty")
    recipe_ids = tuple(
        _expect_str(override, "recipe_id", context=f"{context}.starter_recipe_overrides[{index}]")
        for index, override in enumerate(overrides)
    )
    if len(recipe_ids) != len(set(recipe_ids)):
        raise ValueError(f"{context}.starter_recipe_overrides has duplicate recipe_id values")
    family = FigureFamily(
        family_id=family_id,
        category_id=category_id,
        title=_expect_str(item, "title", context=context),
        intent=_expect_str(item, "intent", context=context),
        canonical_variants=_expect_str_tuple(item, "canonical_variants", context=context),
        data_roles=_expect_str_tuple(item, "data_roles", context=context),
        starter_recipe_refs=recipe_ids,
        style_tokens=_expect_str_tuple(item, "style_tokens", context=context),
        palette_tokens=_expect_str_tuple(item, "palette_tokens", context=context),
        qa_gate_ids=_expect_str_tuple(item, "qa_gate_ids", context=context),
        loose_match_terms=_expect_str_tuple(item, "loose_match_terms", context=context),
        external_refs=_expect_str_tuple(item, "external_refs", context=context),
        template_seed_ids=_expect_str_tuple(item, "template_seed_ids", context=context),
        ai_adaptation_notes=_expect_str(item, "ai_adaptation_notes", context=context),
    )
    return family, derive_starter_recipes(
        overrides,
        family=family,
        policy_id=policy_id,
        context=f"{context}.starter_recipe_overrides",
        expect_str=_expect_str,
        expect_str_tuple=_expect_str_tuple,
    )


def _parse_category(
    path: Path,
    *,
    policy_id: str,
) -> tuple[FigureFamilyCategory, tuple[StarterRecipe, ...]]:
    payload = _read_json_object(path)
    category_id = _expect_str(payload, "category_id", context=path.name)
    parsed_families = tuple(
        _parse_family(
            item,
            expected_category_id=category_id,
            policy_id=policy_id,
            context=f"{path.name}.families[{index}]",
        )
        for index, item in enumerate(_expect_object_list(payload, "families", context=path.name))
    )
    families = tuple(family for family, _ in parsed_families)
    if not families:
        raise ValueError(f"{path.name}.families must be non-empty")
    return (
        FigureFamilyCategory(
            category_id=category_id,
            title=_expect_str(payload, "title", context=path.name),
            families=families,
        ),
        tuple(recipe for _, recipes in parsed_families for recipe in recipes),
    )


def _load_ref_payload(catalog_root: Path, index: dict[str, Any], key: str) -> dict[str, Any]:
    ref = _expect_str(index, key, context="index")
    return _read_json_object(_resolve_catalog_ref(catalog_root, ref, context=f"index.{key}"))


def load_medical_figure_family_catalog(
    catalog_root: Path = DEFAULT_CATALOG_ROOT,
) -> MedicalFigureFamilyCatalog:
    normalized_root = Path(catalog_root).expanduser().resolve()
    index_path = normalized_root / "index.json"
    index = _read_json_object(index_path)
    schema_version = _expect_int(index, "schema_version", context="index")
    if schema_version != 1:
        raise ValueError("medical figure family catalog schema_version must equal 1")

    ai_adaptation_payload = _load_ref_payload(normalized_root, index, "ai_adaptation_policy_ref")
    ai_adaptation_policy = dict(ai_adaptation_payload.get("ai_adaptation_policy") or {})
    if not ai_adaptation_policy:
        raise ValueError("ai_adaptation_policy must be present")
    _expect_bool(
        ai_adaptation_policy,
        "starter_templates_are_floor_not_ceiling",
        context="ai_adaptation_policy",
    )
    _expect_bool(ai_adaptation_policy, "loose_matching_default", context="ai_adaptation_policy")
    _expect_str_tuple(ai_adaptation_policy, "ai_may_change", context="ai_adaptation_policy")
    _expect_str_tuple(ai_adaptation_policy, "ai_must_preserve", context="ai_adaptation_policy")

    style_profiles = _parse_style_profiles(_load_ref_payload(normalized_root, index, "style_profiles_ref"))
    palette_tokens = _parse_palette_tokens(_load_ref_payload(normalized_root, index, "palette_tokens_ref"))
    qa_gates = _parse_quality_gates(_load_ref_payload(normalized_root, index, "qa_gates_ref"))
    external_sources = _parse_external_sources(_load_ref_payload(normalized_root, index, "external_sources_ref"))
    starter_policy_payload = _load_ref_payload(normalized_root, index, "starter_recipe_policy_ref")
    starter_recipe_policy = dict(starter_policy_payload.get("starter_recipe_policy") or {})
    if not starter_recipe_policy:
        raise ValueError("starter_recipe_policy must be present")
    starter_policy_id = _expect_str(starter_recipe_policy, "policy_id", context="starter_recipe_policy")
    _expect_bool(
        starter_recipe_policy,
        "starter_recipe_is_floor_not_ceiling",
        context="starter_recipe_policy",
    )
    _expect_str_tuple(starter_recipe_policy, "required_request_refs", context="starter_recipe_policy")
    _expect_str_tuple(starter_recipe_policy, "default_ai_may_change", context="starter_recipe_policy")
    _expect_str_tuple(starter_recipe_policy, "default_ai_must_preserve", context="starter_recipe_policy")
    _expect_str_tuple(starter_recipe_policy, "required_output_refs", context="starter_recipe_policy")
    _expect_str_tuple(starter_recipe_policy, "quality_gate_route", context="starter_recipe_policy")

    category_refs = _expect_str_tuple(index, "category_refs", context="index")
    parsed_categories = tuple(
        _parse_category(
            _resolve_catalog_ref(normalized_root, ref, context=f"index.category_refs[{ref_index}]"),
            policy_id=starter_policy_id,
        )
        for ref_index, ref in enumerate(category_refs)
    )
    categories = tuple(category for category, _ in parsed_categories)
    starter_recipes = tuple(recipe for _, recipes in parsed_categories for recipe in recipes)
    starter_recipes_by_id = validate_starter_recipes(
        starter_recipes,
        style_profile_ids={item.profile_id for item in style_profiles},
        palette_token_ids={item.token_id for item in palette_tokens},
        qa_gate_ids={item.gate_id for item in qa_gates},
        policy_id=starter_policy_id,
    )
    categories_by_id: dict[str, FigureFamilyCategory] = {}
    for category in categories:
        if category.category_id in categories_by_id:
            raise ValueError(f"duplicate medical figure category `{category.category_id}`")
        categories_by_id[category.category_id] = category

    families_by_id = validate_family_recipe_refs(
        categories,
        style_profile_ids={item.profile_id for item in style_profiles},
        palette_token_ids={item.token_id for item in palette_tokens},
        qa_gate_ids={item.gate_id for item in qa_gates},
        external_source_ids={item.source_id for item in external_sources},
        starter_recipes_by_id=starter_recipes_by_id,
    )
    composition_policy_payload = _load_ref_payload(normalized_root, index, "composition_recipe_policy_ref")
    composition_policy = dict(composition_policy_payload.get("composition_recipe_policy") or {})
    _expect_str(composition_policy, "policy_id", context="composition_recipe_policy")
    _expect_bool(
        composition_policy,
        "composition_recipes_are_floor_not_ceiling",
        context="composition_recipe_policy",
    )
    _expect_str_tuple(composition_policy, "default_ai_may_change", context="composition_recipe_policy")
    _expect_str_tuple(composition_policy, "default_ai_must_preserve", context="composition_recipe_policy")
    _expect_str_tuple(composition_policy, "forbidden_authority", context="composition_recipe_policy")
    composition_recipe_refs = _expect_str_tuple(index, "composition_recipe_refs", context="index")
    composition_recipes = tuple(
        recipe
        for ref_index, ref in enumerate(composition_recipe_refs)
        for recipe in parse_composition_recipes(
            _resolve_catalog_ref(normalized_root, ref, context=f"index.composition_recipe_refs[{ref_index}]"),
            read_json_object=_read_json_object,
            expect_str=lambda payload, key: _expect_str(payload, key, context="composition_recipe"),
            expect_bool=lambda payload, key: _expect_bool(payload, key, context="composition_recipe"),
            expect_str_tuple=lambda payload, key: _expect_str_tuple(payload, key, context="composition_recipe"),
            expect_object_list=lambda payload, key: _expect_object_list(payload, key, context="composition_recipe"),
        )
    )
    composition_recipes_by_id = validate_composition_recipe_refs(
        composition_recipes,
        family_ids=set(families_by_id),
        starter_recipe_ids=set(starter_recipes_by_id),
        style_profile_ids={item.profile_id for item in style_profiles},
        palette_token_ids={item.token_id for item in palette_tokens},
        qa_gate_ids={item.gate_id for item in qa_gates},
    )
    loose_terms_by_family_id = {
        family_id: tuple(term.casefold() for term in family.loose_match_terms)
        for family_id, family in families_by_id.items()
    }

    return MedicalFigureFamilyCatalog(
        schema_version=schema_version,
        catalog_id=_expect_str(index, "catalog_id", context="index"),
        owner=_expect_str(index, "owner", context="index"),
        purpose=_expect_str(index, "purpose", context="index"),
        machine_boundary=_expect_str(index, "machine_boundary", context="index"),
        source_module=_expect_str(index, "source_module", context="index"),
        ai_adaptation_policy=ai_adaptation_policy,
        style_profiles=style_profiles,
        palette_tokens=palette_tokens,
        qa_gates=qa_gates,
        external_sources=external_sources,
        starter_recipe_policy=starter_recipe_policy,
        starter_recipes=starter_recipes,
        composition_recipe_policy=composition_policy,
        composition_recipes=composition_recipes,
        categories=categories,
        families_by_id=families_by_id,
        categories_by_id=categories_by_id,
        starter_recipes_by_id=starter_recipes_by_id,
        composition_recipes_by_id=composition_recipes_by_id,
        loose_terms_by_family_id=loose_terms_by_family_id,
    )
