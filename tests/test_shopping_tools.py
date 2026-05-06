"""Tests for Mealie v3 shopping-list payload handling."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.shopping import (  # noqa: E402
    _normalize_item_payload,
    _normalize_recipe_options,
)


def test_simple_shopping_item_payload_maps_name_to_display_and_list_id():
    assert _normalize_item_payload(
        {
            "name": "mléko",
            "quantity": 2,
            "unit_id": "unit-id",
            "food_id": "food-id",
        },
        list_id="list-id",
    ) == {
        "display": "mléko",
        "quantity": 2,
        "shoppingListId": "list-id",
        "unitId": "unit-id",
        "foodId": "food-id",
    }


def test_native_shopping_item_payload_passes_through_current_mealie_fields():
    assert _normalize_item_payload(
        {
            "shoppingListId": "list-id",
            "display": "mléko",
            "checked": False,
            "recipeReferences": [{"recipeId": "recipe-id"}],
            "extras": {"source": "test"},
        }
    ) == {
        "shoppingListId": "list-id",
        "display": "mléko",
        "checked": False,
        "recipeReferences": [{"recipeId": "recipe-id"}],
        "extras": {"source": "test"},
    }


def test_recipe_option_payload_accepts_snake_case_aliases():
    assert _normalize_recipe_options(
        {
            "recipe_increment_quantity": 2,
            "recipe_ingredients": [{"display": "těstoviny"}],
        }
    ) == {
        "recipeIncrementQuantity": 2,
        "recipeIngredients": [{"display": "těstoviny"}],
    }
