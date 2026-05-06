"""Tests for Mealie ingredient/unit master-data payload handling."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.ingredients import (  # noqa: E402
    FoodUpdate,
    UnitCreate,
    UnitUpdate,
    _food_update_to_api_data,
    _merge_resource_update,
    _unit_create_to_api_data,
    _unit_update_to_api_data,
)


def test_unit_payload_preserves_czech_plural_and_alias_fields():
    unit = UnitUpdate(
        name="kilogram",
        pluralName="kilogramů",
        abbreviation="kg",
        pluralAbbreviation="kg",
        useAbbreviation=True,
        aliases=["kilo", {"name": "kila"}],
        standardQuantity=1,
        standardUnit="kilogram",
    )

    assert _unit_update_to_api_data(unit) == {
        "name": "kilogram",
        "pluralName": "kilogramů",
        "abbreviation": "kg",
        "pluralAbbreviation": "kg",
        "useAbbreviation": True,
        "aliases": [{"name": "kilo"}, {"name": "kila"}],
        "standardQuantity": 1,
        "standardUnit": "kilogram",
    }


def test_unit_create_accepts_snake_case_payload_names():
    unit = UnitCreate(
        name="gram",
        plural_name="gramů",
        abbreviation="g",
        use_abbreviation=True,
        standard_quantity=1,
        standard_unit="gram",
    )

    assert _unit_create_to_api_data(unit)["pluralName"] == "gramů"
    assert _unit_create_to_api_data(unit)["useAbbreviation"] is True
    assert _unit_create_to_api_data(unit)["standardQuantity"] == 1


def test_unit_create_does_not_force_mealie_defaults():
    unit = UnitCreate(name="lžíce")

    assert _unit_create_to_api_data(unit) == {"name": "lžíce"}


def test_food_payload_preserves_plural_and_aliases():
    food = FoodUpdate(
        name="Kuřecí prsa",
        pluralName="Kuřecí prsa",
        aliases=["kuřecích prsou", {"name": "kuřecího masa"}],
    )

    assert _food_update_to_api_data(food) == {
        "name": "Kuřecí prsa",
        "pluralName": "Kuřecí prsa",
        "aliases": [{"name": "kuřecích prsou"}, {"name": "kuřecího masa"}],
    }


def test_update_payload_merges_current_resource_before_put():
    current = {
        "name": "gram",
        "pluralName": "gramů",
        "abbreviation": "g",
        "pluralAbbreviation": "g",
        "useAbbreviation": True,
        "standardQuantity": 1,
        "standardUnit": "gram",
        "aliases": [{"name": "gramy"}],
    }
    updates = {"description": "Gram"}

    assert _merge_resource_update(
        current,
        updates,
        [
            "name",
            "pluralName",
            "description",
            "abbreviation",
            "pluralAbbreviation",
            "useAbbreviation",
            "aliases",
            "standardQuantity",
            "standardUnit",
        ],
    ) == {
        "name": "gram",
        "pluralName": "gramů",
        "description": "Gram",
        "abbreviation": "g",
        "pluralAbbreviation": "g",
        "useAbbreviation": True,
        "aliases": [{"name": "gramy"}],
        "standardQuantity": 1,
        "standardUnit": "gram",
    }


def test_food_update_payload_keeps_id_for_mealie_put():
    current = {
        "id": "food-id",
        "name": "Sůl",
        "pluralName": None,
        "description": "Kuchyňská sůl",
        "extras": {},
        "labelId": None,
        "aliases": [],
    }
    updates = {"pluralName": "soli"}

    assert _merge_resource_update(
        current,
        updates,
        ["id", "name", "pluralName", "description", "extras", "labelId", "aliases"],
    ) == {
        "id": "food-id",
        "name": "Sůl",
        "pluralName": "soli",
        "description": "Kuchyňská sůl",
        "extras": {},
        "labelId": None,
        "aliases": [],
    }
