"""Tests for meal plan Pydantic models and validation."""

import pytest
from datetime import datetime, date, timedelta
from pydantic import ValidationError

from src.tools.meal_plans import (
    MealType,
    MealPlanFilters,
    MealPlanEntry,
    MealPlanRule,
    RandomMealPlanEntry,
    _meal_plan_entry_to_api_data,
    _meal_plan_rule_to_api_data,
    _meal_plan_update_to_api_data,
    _normalize_meal_plan_entry,
    _normalize_meal_plan_filters,
    _random_meal_plan_entry_to_api_data,
)


class TestMealPlanModels:
    """Test meal plan Pydantic models."""

    def test_meal_type_enum(self):
        """Test MealType enum values."""
        assert MealType.BREAKFAST.value == "breakfast"
        assert MealType.LUNCH.value == "lunch"
        assert MealType.DINNER.value == "dinner"
        assert MealType.SNACK.value == "snack"
        assert MealType.SIDE.value == "side"
        assert MealType.DRINK.value == "drink"
        assert MealType.DESSERT.value == "dessert"

    def test_meal_plan_filters_valid(self):
        """Test valid MealPlanFilters creation."""
        filters = MealPlanFilters(
            start_date="2024-01-01",
            end_date="2024-01-07",
            meal_type=MealType.DINNER,
            recipe_id="123e4567-e89b-12d3-a456-426614174000"
        )
        
        assert filters.start_date == "2024-01-01"
        assert filters.end_date == "2024-01-07"
        assert filters.meal_type == MealType.DINNER
        assert filters.recipe_id == "123e4567-e89b-12d3-a456-426614174000"

    def test_meal_plan_filters_invalid_date(self):
        """Test MealPlanFilters with invalid date format."""
        with pytest.raises(ValidationError) as exc_info:
            MealPlanFilters(start_date="2024/01/01")
        
        assert "Date must be in YYYY-MM-DD format" in str(exc_info.value)

    def test_meal_plan_filters_invalid_date_range(self):
        """Test MealPlanFilters with end_date before start_date."""
        with pytest.raises(ValidationError) as exc_info:
            MealPlanFilters(
                start_date="2024-01-07",
                end_date="2024-01-01"
            )
        
        assert "end_date must be after start_date" in str(exc_info.value)

    def test_meal_plan_entry_valid(self):
        """Test valid MealPlanEntry creation."""
        entry = MealPlanEntry(
            date="2024-01-01",
            meal_type=MealType.BREAKFAST,
            recipe_id="123e4567-e89b-12d3-a456-426614174000",
            title="Scrambled Eggs",
            text="Delicious breakfast"
        )
        
        assert entry.date == "2024-01-01"
        assert entry.meal_type == MealType.BREAKFAST
        assert entry.recipe_id == "123e4567-e89b-12d3-a456-426614174000"
        assert entry.title == "Scrambled Eggs"

    def test_meal_plan_entry_with_title_only(self):
        """Test MealPlanEntry with title but no recipe_id."""
        entry = MealPlanEntry(
            date="2024-01-01",
            meal_type=MealType.LUNCH,
            title="Custom Lunch"
        )
        
        assert entry.date == "2024-01-01"
        assert entry.meal_type == MealType.LUNCH
        assert entry.recipe_id is None
        assert entry.title == "Custom Lunch"

    def test_meal_plan_entry_missing_title_and_recipe(self):
        """Test MealPlanEntry fails without title or recipe_id."""
        with pytest.raises(ValidationError) as exc_info:
            MealPlanEntry(
                date="2024-01-01",
                meal_type=MealType.DINNER
            )
        
        assert "Either title or recipe_id must be provided" in str(exc_info.value)

    def test_meal_plan_entry_invalid_date(self):
        """Test MealPlanEntry with invalid date format."""
        with pytest.raises(ValidationError) as exc_info:
            MealPlanEntry(
                date="01-01-2024",
                meal_type=MealType.BREAKFAST,
                title="Breakfast"
            )
        
        assert "Date must be in YYYY-MM-DD format" in str(exc_info.value)

    def test_meal_plan_entry_invalid_recipe_id(self):
        """Test MealPlanEntry with invalid recipe ID format."""
        with pytest.raises(ValidationError) as exc_info:
            MealPlanEntry(
                date="2024-01-01",
                meal_type=MealType.BREAKFAST,
                recipe_id="invalid-uuid"
            )
        
        assert "recipe_id must be a valid UUID" in str(exc_info.value)

    def test_meal_plan_filter_key_normalization(self):
        """Test meal plan filters accept Mealie API-style keys."""
        filters = _normalize_meal_plan_filters({
            "startDate": "2024-01-01",
            "endDate": "2024-01-07",
            "mealType": "dinner",
            "recipeId": "123e4567-e89b-12d3-a456-426614174000",
        })

        assert filters == {
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
            "meal_type": "dinner",
            "recipe_id": "123e4567-e89b-12d3-a456-426614174000",
        }

    def test_meal_plan_entry_key_normalization(self):
        """Test meal plan entries accept Mealie API-style keys."""
        entry = _normalize_meal_plan_entry({
            "date": "2024-01-01",
            "entryType": "dinner",
            "recipeId": "123e4567-e89b-12d3-a456-426614174000",
        })

        assert entry == {
            "date": "2024-01-01",
            "meal_type": "dinner",
            "recipe_id": "123e4567-e89b-12d3-a456-426614174000",
        }

    def test_meal_plan_entry_api_data_uses_empty_strings(self):
        """Test recipe-only meal plans send strings for optional text fields."""
        entry = MealPlanEntry(
            date="2024-01-01",
            meal_type=MealType.DINNER,
            recipe_id="123e4567-e89b-12d3-a456-426614174000",
        )

        assert _meal_plan_entry_to_api_data(entry) == {
            "date": "2024-01-01",
            "entryType": "dinner",
            "title": "",
            "text": "",
            "recipeId": "123e4567-e89b-12d3-a456-426614174000",
        }

    def test_random_meal_plan_entry_api_data(self):
        """Test random meal-plan entries use Mealie's current payload shape."""
        entry = RandomMealPlanEntry(date="2024-01-01", meal_type=MealType.LUNCH)

        assert _random_meal_plan_entry_to_api_data(entry) == {
            "date": "2024-01-01",
            "entryType": "lunch",
        }

    def test_meal_plan_rule_api_data(self):
        """Test meal-plan rules use Mealie's current payload shape."""
        rule = MealPlanRule(
            day="monday",
            entry_type="dinner",
            query_filter_string='{"recipeCategory":["saláty"]}',
        )

        assert _meal_plan_rule_to_api_data(rule) == {
            "day": "monday",
            "entryType": "dinner",
            "queryFilterString": '{"recipeCategory":["saláty"]}',
        }

    def test_meal_plan_update_api_data_preserves_required_identity_fields(self):
        """Test meal-plan updates include fields required by current Mealie."""
        current = {
            "id": 10,
            "groupId": "group-id",
            "userId": "user-id",
        }
        entry = MealPlanEntry(
            date="2024-01-01",
            meal_type=MealType.DINNER,
            title="Večeře",
        )

        assert _meal_plan_update_to_api_data(current, entry) == {
            "id": 10,
            "groupId": "group-id",
            "userId": "user-id",
            "date": "2024-01-01",
            "entryType": "dinner",
            "title": "Večeře",
            "text": "",
            "recipeId": None,
        }


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_meal_plan_filters_default_values(self):
        """Test MealPlanFilters with default values."""
        filters = MealPlanFilters()

        assert filters.start_date is None
        assert filters.end_date is None
        assert filters.meal_type is None
        assert filters.recipe_id is None

    def test_meal_plan_entry_edge_case_dates(self):
        """Test MealPlanEntry with edge case dates."""
        # Leap year date
        entry = MealPlanEntry(
            date="2024-02-29",  # Leap year
            meal_type=MealType.LUNCH,
            title="Leap Day Lunch"
        )
        assert entry.date == "2024-02-29"
        
        # End of year
        entry = MealPlanEntry(
            date="2024-12-31",
            meal_type=MealType.DINNER,
            title="New Year's Eve Dinner"
        )
        assert entry.date == "2024-12-31"
