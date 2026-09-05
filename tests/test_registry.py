from backend.tools.registry import build_default_registry


def test_schemas_for_llm_filters_by_domain():
    registry = build_default_registry()
    all_schemas = registry.schemas_for_llm()
    vision_schemas = registry.schemas_for_llm(domains={"vision"})

    assert len(vision_schemas) < len(all_schemas)
    assert any(s["function"]["name"] == "describe_screen" for s in vision_schemas)
    assert not any(s["function"]["name"] == "open_application" for s in vision_schemas)
