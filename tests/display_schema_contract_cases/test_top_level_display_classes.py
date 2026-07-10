from .shared import (
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

def test_schema_contract_exposes_phase2_top_level_display_classes() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    classes = module.list_display_schema_classes()

    assert {item.class_id for item in classes} == {
        "prediction_performance",
        "clinical_utility",
        "time_to_event",
        "data_geometry",
        "matrix_pattern",
        "effect_estimate",
        "model_explanation",
        "model_audit",
        "generalizability",
        "publication_shells_and_tables",
    }
