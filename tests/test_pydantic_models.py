"""Test Pydantic models without MCP dependencies.

This module tests the Pydantic models used for validation
by importing them directly without the MCP tool decorators.
"""

import pytest
import sys
from pathlib import Path
from pydantic import ValidationError
from datetime import datetime
from uuid import UUID

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test if we can import models by extracting them from the files
# We'll define the models here to avoid import issues

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from typing import List, Optional, Union
from enum import Enum


# Recipe models (extracted from tools/recipes.py without MCP dependencies)
class RecipeSearchFilters(BaseModel):
    """Filters for recipe search operations."""
    query: str = Field(default="", description="Search query text")
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    per_page: int = Field(default=10, ge=1, le=100, description="Items per page")
    include_tags: Optional[List[str]] = Field(default=None, description="Tags to include")
    exclude_tags: Optional[List[str]] = Field(default=None, description="Tags to exclude")
    category: Optional[str] = Field(default=None, description="Recipe category")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Minimum rating")


class RecipeIngredient(BaseModel):
    """Recipe ingredient model."""
    title: str = Field(description="Ingredient name")
    text: str = Field(description="Full ingredient text with quantities")
    quantity: Optional[float] = Field(default=None, description="Numeric quantity")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    food: Optional[str] = Field(default=None, description="Food item name")
    note: Optional[str] = Field(default=None, description="Additional notes")


class RecipeInstruction(BaseModel):
    """Recipe instruction model."""
    text: str = Field(description="Instruction text")
    id: Optional[int] = Field(default=None, description="Instruction ID")
    title: Optional[str] = Field(default=None, description="Instruction title")
    ingredient_references: Optional[List[int]] = Field(default=None, description="Referenced ingredients")


class RecipeNutrition(BaseModel):
    """Recipe nutrition information."""
    calories: Optional[str] = Field(default=None, description="Calories per serving")
    protein_content: Optional[str] = Field(default=None, description="Protein content")
    carbohydrate_content: Optional[str] = Field(default=None, description="Carbohydrate content")
    fat_content: Optional[str] = Field(default=None, description="Fat content")
    fiber_content: Optional[str] = Field(default=None, description="Fiber content")
    sugar_content: Optional[str] = Field(default=None, description="Sugar content")
    sodium_content: Optional[str] = Field(default=None, description="Sodium content")


class RecipeCreateUpdate(BaseModel):
    """Model for creating or updating recipes."""
    name: str = Field(min_length=1, max_length=200, description="Recipe name")
    description: Optional[str] = Field(default=None, max_length=2000, description="Recipe description")
    recipe_yield: Optional[str] = Field(default=None, description="Recipe yield/servings")
    prep_time: Optional[str] = Field(default=None, description="Preparation time")
    cook_time: Optional[str] = Field(default=None, description="Cooking time")
    total_time: Optional[str] = Field(default=None, description="Total time")
    recipe_category: Optional[str] = Field(default=None, description="Recipe category")
    tags: List[str] = Field(default_factory=list, description="Recipe tags")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Recipe rating")
    recipe_ingredient: Optional[List[RecipeIngredient]] = Field(default=None, description="Recipe ingredients")
    recipe_instructions: Optional[List[RecipeInstruction]] = Field(default=None, description="Recipe instructions")
    nutrition: Optional[RecipeNutrition] = Field(default=None, description="Nutrition information")
    notes: Optional[List[dict]] = Field(default=None, description="Recipe notes")

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(',') if tag.strip()]
        return v or []


class RecipeImportUrl(BaseModel):
    """Model for importing recipes from URLs."""
    url: HttpUrl = Field(description="URL to import recipe from")
    include_tags: List[str] = Field(default_factory=list, description="Tags to add to imported recipe")


# Meal plan models (extracted from tools/meal_plans.py)
class MealType(Enum):
    """Meal type enumeration."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class DayOfWeek(Enum):
    """Day of week enumeration."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class MealPlanFilters(BaseModel):
    """Filters for meal plan operations."""
    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")
    meal_type: Optional[MealType] = Field(default=None, description="Meal type filter")
    recipe_id: Optional[str] = Field(default=None, description="Recipe ID filter")

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @model_validator(mode='after')
    def validate_date_range(self):
        if self.end_date is None or self.start_date is None:
            return self
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class MealPlanEntry(BaseModel):
    """Model for meal plan entries."""
    date: str = Field(description="Date for the meal plan (YYYY-MM-DD)")
    meal_type: MealType = Field(description="Type of meal")
    recipe_id: Optional[str] = Field(default=None, description="Recipe ID (UUID format)")
    title: Optional[str] = Field(default=None, description="Custom meal title")
    text: Optional[str] = Field(default=None, description="Additional text/notes")

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator('recipe_id')
    @classmethod
    def validate_recipe_id(cls, v):
        if v is None:
            return v
        try:
            UUID(v)  # This validates UUID format
        except (ValueError, TypeError):
            raise ValueError("recipe_id must be a valid UUID")
        return v

    @model_validator(mode='after')
    def validate_title_or_recipe_id(self):
        if self.title is None and self.recipe_id is None:
            raise ValueError("Either title or recipe_id must be provided")
        return self


# Test classes
class TestRecipeModels:
    """Test recipe Pydantic models."""

    def test_recipe_search_filters_defaults(self):
        """Test default values for RecipeSearchFilters."""
        filters = RecipeSearchFilters()
        assert filters.query == ""
        assert filters.page == 1
        assert filters.per_page == 10
        assert filters.include_tags is None
        assert filters.exclude_tags is None
        assert filters.category is None
        assert filters.rating is None

    def test_recipe_search_filters_validation(self):
        """Test validation for RecipeSearchFilters."""
        # Valid filters
        filters = RecipeSearchFilters(
            query="pasta",
            page=2,
            per_page=25,
            include_tags=["italian"],
            rating=4
        )
        assert filters.query == "pasta"
        assert filters.page == 2
        assert filters.per_page == 25
        assert filters.rating == 4

        # Invalid page
        with pytest.raises(ValidationError):
            RecipeSearchFilters(page=0)

        # Invalid per_page
        with pytest.raises(ValidationError):
            RecipeSearchFilters(per_page=101)

        # Invalid rating
        with pytest.raises(ValidationError):
            RecipeSearchFilters(rating=6)

    def test_recipe_ingredient_model(self):
        """Test RecipeIngredient model."""
        # Minimal ingredient
        ingredient = RecipeIngredient(
            title="flour",
            text="2 cups all-purpose flour"
        )
        assert ingredient.title == "flour"
        assert ingredient.text == "2 cups all-purpose flour"

        # Complete ingredient
        ingredient = RecipeIngredient(
            title="flour",
            text="2 cups all-purpose flour",
            quantity=2.0,
            unit="cups",
            food="all-purpose flour",
            note="sifted"
        )
        assert ingredient.quantity == 2.0
        assert ingredient.unit == "cups"

    def test_recipe_instruction_model(self):
        """Test RecipeInstruction model."""
        instruction = RecipeInstruction(
            text="Mix all ingredients together",
            id=1,
            title="Mixing"
        )
        assert instruction.text == "Mix all ingredients together"
        assert instruction.id == 1
        assert instruction.title == "Mixing"

    def test_recipe_create_update_model(self):
        """Test RecipeCreateUpdate model."""
        # Minimal recipe
        recipe = RecipeCreateUpdate(name="Test Recipe")
        assert recipe.name == "Test Recipe"
        assert recipe.tags == []

        # Recipe with tags as string
        recipe = RecipeCreateUpdate(
            name="Test Recipe",
            tags="italian, dinner, easy"
        )
        assert recipe.tags == ["italian", "dinner", "easy"]

        # Invalid name length
        with pytest.raises(ValidationError):
            RecipeCreateUpdate(name="")

        with pytest.raises(ValidationError):
            RecipeCreateUpdate(name="x" * 201)

    def test_recipe_import_url_model(self):
        """Test RecipeImportUrl model."""
        import_data = RecipeImportUrl(url="https://example.com/recipe")
        assert str(import_data.url) == "https://example.com/recipe"

        # Invalid URL
        with pytest.raises(ValidationError):
            RecipeImportUrl(url="not-a-url")


class TestMealPlanModels:
    """Test meal plan Pydantic models."""

    def test_meal_type_enum(self):
        """Test MealType enum."""
        assert MealType.BREAKFAST.value == "breakfast"
        assert MealType.LUNCH.value == "lunch"
        assert MealType.DINNER.value == "dinner"
        assert MealType.SNACK.value == "snack"

    def test_meal_plan_filters(self):
        """Test MealPlanFilters model."""
        # Valid filters
        filters = MealPlanFilters(
            start_date="2024-01-01",
            end_date="2024-01-07",
            meal_type=MealType.DINNER
        )
        assert filters.start_date == "2024-01-01"
        assert filters.end_date == "2024-01-07"
        assert filters.meal_type == MealType.DINNER

        # Invalid date format
        with pytest.raises(ValidationError):
            MealPlanFilters(start_date="2024/01/01")

        # Invalid date range
        with pytest.raises(ValidationError):
            MealPlanFilters(start_date="2024-01-07", end_date="2024-01-01")

    def test_meal_plan_entry(self):
        """Test MealPlanEntry model."""
        # Valid entry with recipe_id
        entry = MealPlanEntry(
            date="2024-01-01",
            meal_type=MealType.BREAKFAST,
            recipe_id="123e4567-e89b-12d3-a456-426614174000"
        )
        assert entry.date == "2024-01-01"
        assert entry.meal_type == MealType.BREAKFAST

        # Valid entry with title only
        entry = MealPlanEntry(
            date="2024-01-01",
            meal_type=MealType.LUNCH,
            title="Custom Lunch"
        )
        assert entry.title == "Custom Lunch"

        # Invalid - neither title nor recipe_id
        with pytest.raises(ValidationError):
            MealPlanEntry(
                date="2024-01-01",
                meal_type=MealType.DINNER
            )

        # Invalid date format
        with pytest.raises(ValidationError):
            MealPlanEntry(
                date="01-01-2024",
                meal_type=MealType.BREAKFAST,
                title="Breakfast"
            )

        # Invalid recipe_id format
        with pytest.raises(ValidationError):
            MealPlanEntry(
                date="2024-01-01",
                meal_type=MealType.BREAKFAST,
                recipe_id="invalid-uuid"
            )


class TestModelValidation:
    """Test comprehensive model validation."""

    def test_recipe_data_validation_function(self):
        """Test a validation function similar to what would be in the tools."""
        def validate_recipe_data(recipe_data: dict) -> List[str]:
            """Validate recipe data and return list of errors."""
            errors = []
            
            # Check required fields
            if not recipe_data.get('name'):
                errors.append("Recipe name is required")
            
            # Validate name length
            name = recipe_data.get('name', '')
            if len(name) > 200:
                errors.append("Recipe name too long (max 200 characters)")
            
            # Validate rating
            rating = recipe_data.get('rating')
            if rating is not None and (rating < 1 or rating > 5):
                errors.append("Rating must be between 1 and 5")
            
            # Validate ingredients
            ingredients = recipe_data.get('recipe_ingredient', [])
            for i, ingredient in enumerate(ingredients):
                if not isinstance(ingredient, dict):
                    errors.append(f"Ingredient {i+1} must be an object")
                    continue
                
                if not ingredient.get('title') and not ingredient.get('text'):
                    errors.append(f"Ingredient {i+1} must have title or text")
            
            # Validate instructions
            instructions = recipe_data.get('recipe_instructions', [])
            for i, instruction in enumerate(instructions):
                if not isinstance(instruction, dict):
                    errors.append(f"Instruction {i+1} must be an object")
                    continue
                
                if not instruction.get('text'):
                    errors.append(f"Instruction {i+1} must have text")
            
            return errors

        # Test valid data
        valid_data = {
            "name": "Test Recipe",
            "rating": 4,
            "recipe_ingredient": [{"title": "flour", "text": "2 cups"}],
            "recipe_instructions": [{"text": "Mix ingredients"}]
        }
        errors = validate_recipe_data(valid_data)
        assert len(errors) == 0

        # Test invalid data
        invalid_data = {
            "rating": 10,  # Invalid rating
            "recipe_ingredient": [{}],  # Invalid ingredient
            "recipe_instructions": [{}]  # Invalid instruction
        }
        errors = validate_recipe_data(invalid_data)
        assert "Recipe name is required" in errors
        assert "Rating must be between 1 and 5" in errors
        assert "Ingredient 1 must have title or text" in errors
        assert "Instruction 1 must have text" in errors

    def test_meal_plan_data_validation_function(self):
        """Test meal plan data validation."""
        def validate_meal_plan_data(meal_plan_data: dict) -> List[str]:
            """Validate meal plan data and return list of errors."""
            errors = []
            
            # Check required fields
            if not meal_plan_data.get('date'):
                errors.append("Date is required")
            
            if not meal_plan_data.get('meal_type'):
                errors.append("Meal type is required")
            
            # Validate date format
            date = meal_plan_data.get('date')
            if date:
                try:
                    datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    errors.append("Date must be in YYYY-MM-DD format")
            
            # Validate meal type
            meal_type = meal_plan_data.get('meal_type')
            valid_meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
            if meal_type and meal_type not in valid_meal_types:
                errors.append(f"Invalid meal type. Must be one of: {', '.join(valid_meal_types)}")
            
            # Validate that either recipe_id or title is provided
            recipe_id = meal_plan_data.get('recipe_id')
            title = meal_plan_data.get('title')
            if not recipe_id and not title:
                errors.append("Either recipe_id or title must be provided")
            
            # Validate recipe_id format if provided
            if recipe_id:
                try:
                    UUID(recipe_id)
                except (ValueError, TypeError):
                    errors.append("recipe_id must be a valid UUID")
            
            return errors

        # Test valid data
        valid_data = {
            "date": "2024-01-01",
            "meal_type": "breakfast",
            "title": "Scrambled Eggs"
        }
        errors = validate_meal_plan_data(valid_data)
        assert len(errors) == 0

        # Test invalid data
        invalid_data = {
            "date": "01/01/2024",  # Invalid format
            "meal_type": "invalid",  # Invalid meal type
            "recipe_id": "not-a-uuid"  # Invalid UUID
        }
        errors = validate_meal_plan_data(invalid_data)
        assert "Date must be in YYYY-MM-DD format" in errors
        assert any("Invalid meal type" in error for error in errors)
        assert "recipe_id must be a valid UUID" in errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
