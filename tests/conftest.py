from __future__ import annotations

import pytest

from tests.authority_record_fixtures._paper import PaperMissionFixtures
from tests.authority_record_fixtures._primitives import PrimitiveAuthorityFixtures
from tests.authority_record_fixtures._revision import RevisionFixtures
from tests.authority_record_fixtures.surface_constants import (
    ANALYSIS_ROLES,
    AUTHORITY_ROLE_BY_LANE,
    FIRST_DRAFT_QUALITY_ROLES,
    FIRST_DRAFT_ROLE_BY_REF_FIELD,
    LANES_BY_SCOPE,
    LEGACY_FIRST_DRAFT_ROLE_BY_REF_FIELD,
    MANUSCRIPT_ROLES,
    PUBLICATION_ROLES,
    REVIEWER_RESPONSE_ROLE_BY_REF_FIELD,
    ROLES_BY_SCOPE,
    SCHOLAR_V2_FIRST_DRAFT_ROLE_BY_REF_FIELD,
    SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL,
    SELECTED_BUILD_ROLE_BY_REF_FIELD,
)

__all__ = [
    "ANALYSIS_ROLES",
    "AUTHORITY_ROLE_BY_LANE",
    "FIRST_DRAFT_QUALITY_ROLES",
    "FIRST_DRAFT_ROLE_BY_REF_FIELD",
    "LANES_BY_SCOPE",
    "LEGACY_FIRST_DRAFT_ROLE_BY_REF_FIELD",
    "MANUSCRIPT_ROLES",
    "PUBLICATION_ROLES",
    "REVIEWER_RESPONSE_ROLE_BY_REF_FIELD",
    "ROLES_BY_SCOPE",
    "SCHOLAR_V2_FIRST_DRAFT_ROLE_BY_REF_FIELD",
    "SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL",
    "SELECTED_BUILD_ROLE_BY_REF_FIELD",
    "AuthorityRecordFactory",
    "authority_records",
]


class AuthorityRecordFactory(RevisionFixtures, PaperMissionFixtures):
    authority_epoch = PrimitiveAuthorityFixtures.authority_epoch
    generation_id = PrimitiveAuthorityFixtures.generation_id


@pytest.fixture
def authority_records() -> AuthorityRecordFactory:
    return AuthorityRecordFactory()
