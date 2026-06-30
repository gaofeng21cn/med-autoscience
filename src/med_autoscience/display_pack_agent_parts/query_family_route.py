from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import re
from typing import Any

from med_autoscience.medical_figure_family_catalog import MedicalFigureFamilyCatalog


_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class FigureFamilyQueryRoute:
    family_id: str
    family_title: str
    category_id: str
    template_seed_ids: tuple[str, ...]
    matched_terms: tuple[str, ...]
    score: int

    def as_request_patch(self) -> dict[str, Any]:
        return {
            "medical_figure_family_id": self.family_id,
            "medical_figure_family_title": self.family_title,
            "medical_figure_category_id": self.category_id,
            "medical_figure_template_seed_ids": list(self.template_seed_ids),
            "medical_figure_matched_terms": list(self.matched_terms),
        }


def _text(value: object) -> str:
    return str(value or "").strip()


def _normalized(value: str) -> str:
    return " ".join(_TOKEN_RE.findall(value.casefold()))


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(value.casefold()))


def _term_score(query: str, term: str) -> int:
    query_tokens = _tokens(query)
    term_tokens = _tokens(term)
    normalized_query = " ".join(query_tokens)
    normalized_term = " ".join(term_tokens)
    if not normalized_query or not normalized_term:
        return 0
    if normalized_query == normalized_term:
        return 100
    if normalized_query in normalized_term:
        return 90 + min(len(normalized_query), 20)
    if normalized_term in normalized_query:
        if len(term_tokens) == 1 and len(query_tokens) > 1:
            return 30 + min(len(normalized_term), 10)
        return 80 + min(len(normalized_term), 20)
    overlap = set(query_tokens) & set(term_tokens)
    return 20 * len(overlap) if overlap else 0


def _family_terms(family_id: str, family: Any) -> tuple[str, ...]:
    return (
        family_id,
        family.title,
        family.intent,
        *family.loose_match_terms,
        *family.canonical_variants,
        *family.template_seed_ids,
    )


def resolve_query_family_route(
    request: Mapping[str, Any],
    catalog: MedicalFigureFamilyCatalog,
) -> FigureFamilyQueryRoute | None:
    query = _text(request.get("query") or request.get("figure_goal") or request.get("claim_role"))
    if not query:
        return None
    normalized_query = _normalized(query)
    if "transportability" in normalized_query and any(
        token in normalized_query for token in ("governance", "calibration", "center", "deployment")
    ):
        family = catalog.families_by_id.get("external_validation_performance")
        if family is not None:
            matched_terms = tuple(
                term
                for term in (
                    "transportability governance",
                    "calibration governance",
                    "external validation",
                )
                if term in normalized_query
            )
            return FigureFamilyQueryRoute(
                family_id=family.family_id,
                family_title=family.title,
                category_id=family.category_id,
                template_seed_ids=family.template_seed_ids,
                matched_terms=matched_terms or ("transportability governance",),
                score=140,
            )

    routes: list[FigureFamilyQueryRoute] = []
    for family_id, family in catalog.families_by_id.items():
        scored_terms = [
            (score, term)
            for term in _family_terms(family_id, family)
            if (score := _term_score(query, term)) > 0
        ]
        if not scored_terms:
            continue
        scored_terms.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
        routes.append(
            FigureFamilyQueryRoute(
                family_id=family.family_id,
                family_title=family.title,
                category_id=family.category_id,
                template_seed_ids=family.template_seed_ids,
                matched_terms=tuple(term for _, term in scored_terms[:3]),
                score=scored_terms[0][0],
            )
        )
    if not routes:
        return None
    routes.sort(
        key=lambda route: (
            route.score,
            bool(route.template_seed_ids),
            len(route.template_seed_ids),
            route.family_id,
        ),
        reverse=True,
    )
    return routes[0]
