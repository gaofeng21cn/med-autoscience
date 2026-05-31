from __future__ import annotations

import importlib

from .test_study_delivery_sync_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_study_delivery_sync_facade_exposes_publication_profile_helpers() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")

    assert module.normalize_publication_profile(" general_medical_journal ") == "general_medical_journal"
    assert module.is_supported_publication_profile("general_medical_journal") is True


from .test_study_delivery_sync_cases.delivery_sync_cases import *  # noqa: F403,F401
from .test_study_delivery_sync_cases.stale_submission_delivery_cases import *  # noqa: F403,F401
from .test_study_delivery_sync_cases.clean_migration_guard_cases import *  # noqa: F403,F401
from .test_study_delivery_sync_cases.v2_layout_and_legacy_cases import *  # noqa: F403,F401
