"""Medical publication policies for MedAutoScience."""

from .medical_publication_surface import (
    AMA_CSL_BASENAME,
    BLOCKED_RECOMMENDED_ACTION as SURFACE_BLOCKED_RECOMMENDED_ACTION,
    CLEAR_RECOMMENDED_ACTION as SURFACE_CLEAR_RECOMMENDED_ACTION,
)
from .data_asset_gate import (
    ADVISORY_RECOMMENDED_ACTION as DATA_ASSET_ADVISORY_RECOMMENDED_ACTION,
    BLOCKED_RECOMMENDED_ACTION as DATA_ASSET_BLOCKED_RECOMMENDED_ACTION,
    CLEAR_RECOMMENDED_ACTION as DATA_ASSET_CLEAR_RECOMMENDED_ACTION,
)
from .publication_gate import (
    BLOCKED_RECOMMENDED_ACTION as GATE_BLOCKED_RECOMMENDED_ACTION,
    CLEAR_RECOMMENDED_ACTION as GATE_CLEAR_RECOMMENDED_ACTION,
)
from .research_route_bias import (
    DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID,
    ResearchRouteBiasPolicy,
    get_policy,
    render_policy_block,
)
from .study_archetypes import (
    DEFAULT_STUDY_ARCHETYPE_IDS,
    StudyArchetype,
    get_archetype,
    render_archetype_block,
    resolve_archetypes,
)

__all__ = [
    "AMA_CSL_BASENAME",
    "DATA_ASSET_ADVISORY_RECOMMENDED_ACTION",
    "DATA_ASSET_BLOCKED_RECOMMENDED_ACTION",
    "DATA_ASSET_CLEAR_RECOMMENDED_ACTION",
    "DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID",
    "DEFAULT_STUDY_ARCHETYPE_IDS",
    "GATE_BLOCKED_RECOMMENDED_ACTION",
    "GATE_CLEAR_RECOMMENDED_ACTION",
    "ResearchRouteBiasPolicy",
    "StudyArchetype",
    "SURFACE_BLOCKED_RECOMMENDED_ACTION",
    "SURFACE_CLEAR_RECOMMENDED_ACTION",
    "get_archetype",
    "get_policy",
    "render_archetype_block",
    "render_policy_block",
    "resolve_archetypes",
]
