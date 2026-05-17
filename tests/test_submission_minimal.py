from __future__ import annotations

import pytest

from tests.submission_minimal_cases.package_core_and_authority import *
from tests.submission_minimal_cases.clean_migration_guard import *
from tests.submission_minimal_cases.frontiers_profile_and_sync import *
from tests.submission_minimal_cases.source_markdown_and_materialized_refs import *
from tests.submission_minimal_cases.v2_layout_and_legacy_cases import *

pytestmark = pytest.mark.submission_heavy
