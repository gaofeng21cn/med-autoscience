from __future__ import annotations

from tests.display_schema_contract_cases.shared import (
    annotations,
    _shared_base,
    _registry_id_helpers,
    _input_schema_fixtures,
    importlib,
    Path,
    _CORE_PACK_ID,
    _full_id,
    lru_cache,
    SimpleNamespace,
    _INPUT_SCHEMAS,
    _CLASS_IDS,
    _display_class_by_id,
    _load_schema_contract_fixture,
)
from tests.display_schema_contract_cases.top_level_display_classes import (
    test_schema_contract_exposes_phase2_top_level_display_classes,
)
from tests.display_schema_contract_cases.input_shape_contracts import (
    annotations,
    test_schema_contract_tracks_current_clinical_and_publication_shapes,
    test_schema_contract_tracks_current_data_geometry_input_shapes,
    test_schema_contract_tracks_effect_and_explanation_input_shapes,
    test_schema_contract_tracks_matrix_and_omics_input_shapes,
)
from tests.display_schema_contract_cases.registered_display_surface_contracts import (
    test_schema_contract_covers_all_registered_display_surface_items,
    test_current_schema_contract_has_no_python_evidence_or_empty_evidence_schema,
    test_current_key_schema_contracts_remain_registered,
)
from tests.display_schema_contract_cases.shap_templates_and_docs_contracts import (
    test_current_shap_schema_contracts_are_registered,
    test_render_display_template_catalog_covers_current_registered_templates,
)
