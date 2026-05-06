"""Tests for recipe Pydantic models.

This module tests the validation logic of all Pydantic models
used in the recipe management tools.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.recipes import (
    RecipeSearchFilters, RecipeIngredient, RecipeInstruction,
    RecipeNutrition, RecipeCreateUpdate, RecipeImportUrl,
    validate_recipe_data, _async_search_recipes, _decode_base64_file,
    _extract_recipe_slug, _normalize_timeline_event_payload
)


class TestRecipeSearchFilters:
    """Test RecipeSearchFilters validation."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        filters = RecipeSearchFilters()
        assert filters.query == ""
        assert filters.page == 1
        assert filters.per_page == 10
        assert filters.categories is None
        assert filters.tags is None
        assert filters.tools is None
        assert filters.foods is None
        assert filters.households is None
    
    def test_valid_filters(self):
        """Test valid filter combinations."""
        filters = RecipeSearchFilters(
            query="chicken pasta",
            page=2,
            per_page=25,
            tags=["italian", "dinner"],
            categories=["main-course"],
            tools=["oven"],
            order_by="name",
            order_direction="asc",
            require_all_tags=True,
        )
        
        assert filters.query == "chicken pasta"
        assert filters.page == 2
        assert filters.per_page == 25
        assert filters.tags == ["italian", "dinner"]
        assert filters.categories == ["main-course"]
        assert filters.tools == ["oven"]
        assert filters.order_by == "name"
        assert filters.order_direction == "asc"
        assert filters.require_all_tags is True
    
    def test_page_validation(self):
        """Test page number validation."""
        # Valid page numbers
        RecipeSearchFilters(page=1)
        RecipeSearchFilters(page=10)
        
        # Invalid page numbers
        with pytest.raises(ValidationError):
            RecipeSearchFilters(page=0)
        
        with pytest.raises(ValidationError):
            RecipeSearchFilters(page=-1)
    
    def test_per_page_validation(self):
        """Test per_page validation."""
        # Valid per_page values
        RecipeSearchFilters(per_page=1)
        RecipeSearchFilters(per_page=50)
        RecipeSearchFilters(per_page=100)
        
        # Invalid per_page values
        with pytest.raises(ValidationError):
            RecipeSearchFilters(per_page=0)
        
        with pytest.raises(ValidationError):
            RecipeSearchFilters(per_page=101)
    
    def test_deprecated_aliases_are_still_accepted(self):
        """Test deprecated search aliases can still be accepted and normalized by search code."""
        filters = RecipeSearchFilters(
            include_tags=["italian"],
            category="main-course",
        )

        assert filters.include_tags == ["italian"]
        assert filters.category == "main-course"

    @pytest.mark.asyncio
    async def test_search_recipes_uses_current_v3_query_params(self):
        """Test recipe search emits Mealie v3 query parameter names."""
        class FakeClient:
            async def get(self, endpoint, params=None):
                self.endpoint = endpoint
                self.params = params
                return {"items": [], "total": 0, "page": 1, "perPage": 10}

        client = FakeClient()
        filters = RecipeSearchFilters(
            query="pasta",
            page=2,
            per_page=25,
            tags=["italian"],
            categories=["dinner"],
            order_by="name",
            order_direction="asc",
            require_all_tags=True,
        )

        await _async_search_recipes(filters, client)

        assert client.endpoint == "/api/recipes"
        assert client.params == {
            "search": "pasta",
            "page": 2,
            "perPage": 25,
            "categories": ["dinner"],
            "tags": ["italian"],
            "orderBy": "name",
            "orderDirection": "asc",
            "requireAllTags": True,
        }


class TestRecipeIngredient:
    """Test RecipeIngredient validation."""
    
    def test_minimal_ingredient(self):
        """Test minimal valid ingredient."""
        ingredient = RecipeIngredient(
            title="flour",
            text="2 cups all-purpose flour"
        )
        assert ingredient.title == "flour"
        assert ingredient.text == "2 cups all-purpose flour"
        assert ingredient.quantity is None
    
    def test_complete_ingredient(self):
        """Test ingredient with all fields."""
        ingredient = RecipeIngredient(
            title="flour",
            text="2 cups all-purpose flour, sifted",
            quantity=2.0,
            unit="cups",
            food="all-purpose flour",
            note="sifted"
        )
        
        assert ingredient.title == "flour"
        assert ingredient.text == "2 cups all-purpose flour, sifted"
        assert ingredient.quantity == 2.0
        assert ingredient.unit == "cups"
        assert ingredient.food == "all-purpose flour"
        assert ingredient.note == "sifted"
    
    def test_required_fields(self):
        """Test required fields validation."""
        # Missing title should fail
        with pytest.raises(ValidationError):
            RecipeIngredient(text="2 cups flour")
        
        # Missing text should fail
        with pytest.raises(ValidationError):
            RecipeIngredient(title="flour")


class TestRecipeInstruction:
    """Test RecipeInstruction validation."""
    
    def test_minimal_instruction(self):
        """Test minimal valid instruction."""
        instruction = RecipeInstruction(text="Mix all ingredients together.")
        assert instruction.text == "Mix all ingredients together."
        assert instruction.id is None
        assert instruction.title is None
    
    def test_complete_instruction(self):
        """Test instruction with all fields."""
        instruction = RecipeInstruction(
            id=1,
            title="Mixing",
            text="Mix all dry ingredients in a large bowl.",
            ingredient_references=[1, 2, 3]
        )
        
        assert instruction.id == 1
        assert instruction.title == "Mixing"
        assert instruction.text == "Mix all dry ingredients in a large bowl."
        assert instruction.ingredient_references == [1, 2, 3]
    
    def test_required_text(self):
        """Test that text field is required."""
        with pytest.raises(ValidationError):
            RecipeInstruction(title="Mixing")


class TestRecipeCreateUpdate:
    """Test RecipeCreateUpdate validation."""
    
    def test_minimal_recipe(self):
        """Test minimal valid recipe."""
        recipe = RecipeCreateUpdate(name="Test Recipe")
        assert recipe.name == "Test Recipe"
        assert recipe.description is None
        assert recipe.tags == []
    
    def test_complete_recipe(self):
        """Test recipe with all fields."""
        ingredients = [
            RecipeIngredient(title="flour", text="2 cups flour"),
            RecipeIngredient(title="sugar", text="1 cup sugar")
        ]
        
        instructions = [
            RecipeInstruction(text="Mix dry ingredients."),
            RecipeInstruction(text="Bake at 350°F for 30 minutes.")
        ]
        
        nutrition = RecipeNutrition(
            calories="250",
            protein_content="5g",
            carbohydrate_content="45g"
        )
        
        recipe = RecipeCreateUpdate(
            name="Complete Test Recipe",
            description="A test recipe with all fields",
            recipe_yield="12 servings",
            prep_time="15 minutes",
            cook_time="30 minutes",
            total_time="45 minutes",
            recipe_category="Dessert",
            tags=["test", "complete"],
            rating=5,
            recipe_ingredient=ingredients,
            recipe_instructions=instructions,
            nutrition=nutrition,
            notes=[{"title": "Note", "text": "This is a test recipe"}]
        )
        
        assert recipe.name == "Complete Test Recipe"
        assert len(recipe.recipe_ingredient) == 2
        assert len(recipe.recipe_instructions) == 2
        assert recipe.nutrition.calories == "250"
        assert recipe.rating == 5
    
    def test_name_validation(self):
        """Test recipe name validation."""
        # Empty name should fail
        with pytest.raises(ValidationError):
            RecipeCreateUpdate(name="")
        
        # Very long name should fail
        with pytest.raises(ValidationError):
            RecipeCreateUpdate(name="x" * 201)
    
    def test_rating_validation(self):
        """Test rating validation."""
        # Valid ratings
        for rating in [1, 2, 3, 4, 5]:
            RecipeCreateUpdate(name="Test", rating=rating)
        
        # Invalid ratings
        with pytest.raises(ValidationError):
            RecipeCreateUpdate(name="Test", rating=0)
        
        with pytest.raises(ValidationError):
            RecipeCreateUpdate(name="Test", rating=6)
    
    def test_tags_validation(self):
        """Test tags field validation and conversion."""
        # String tags should be converted to list
        recipe = RecipeCreateUpdate(name="Test", tags="italian, dinner, easy")
        assert recipe.tags == ["italian", "dinner", "easy"]
        
        # List tags should remain as list
        recipe = RecipeCreateUpdate(name="Test", tags=["italian", "dinner"])
        assert recipe.tags == ["italian", "dinner"]
        
        # None should become empty list
        recipe = RecipeCreateUpdate(name="Test", tags=None)
        assert recipe.tags == []
    
    def test_description_length(self):
        """Test description length validation."""
        # Valid description
        RecipeCreateUpdate(name="Test", description="A" * 2000)
        
        # Too long description should fail
        with pytest.raises(ValidationError):
            RecipeCreateUpdate(name="Test", description="A" * 2001)


class TestRecipeImportUrl:
    """Test RecipeImportUrl validation."""
    
    def test_valid_url(self):
        """Test valid URL import."""
        import_data = RecipeImportUrl(url="https://example.com/recipe")
        assert str(import_data.url) == "https://example.com/recipe"
        assert import_data.include_tags is False
        assert import_data.include_categories is False
    
    def test_url_with_import_flags(self):
        """Test URL import with Mealie scrape import flags."""
        import_data = RecipeImportUrl(
            url="https://example.com/recipe",
            include_tags=True,
            include_categories=True,
        )
        assert import_data.include_tags is True
        assert import_data.include_categories is True
    
    def test_invalid_url(self):
        """Test invalid URL validation."""
        with pytest.raises(ValidationError):
            RecipeImportUrl(url="not-a-url")
        
        with pytest.raises(ValidationError):
            RecipeImportUrl(url="")


class TestValidateRecipeData:
    """Test the validate_recipe_data utility function."""
    
    def test_valid_recipe_data(self):
        """Test validation of valid recipe data."""
        recipe_data = {
            "name": "Test Recipe",
            "description": "A test recipe",
            "recipe_ingredient": [
                {"title": "flour", "text": "2 cups flour"}
            ],
            "recipe_instructions": [
                {"text": "Mix ingredients"}
            ],
            "rating": 4
        }
        
        errors = validate_recipe_data(recipe_data)
        assert len(errors) == 0
    
    def test_missing_name(self):
        """Test validation with missing name."""
        recipe_data = {"description": "A test recipe"}
        errors = validate_recipe_data(recipe_data)
        assert "Recipe name is required" in errors
    
    def test_invalid_ingredients(self):
        """Test validation with invalid ingredients."""
        recipe_data = {
            "name": "Test Recipe",
            "recipe_ingredient": [
                {},  # Invalid ingredient - no title or text
                {"title": "flour"}  # Valid ingredient
            ]
        }
        
        errors = validate_recipe_data(recipe_data)
        assert any("Ingredient 1" in error for error in errors)
    
    def test_invalid_instructions(self):
        """Test validation with invalid instructions."""
        recipe_data = {
            "name": "Test Recipe",
            "recipe_instructions": [
                {},  # Invalid instruction - no text
                {"text": "Mix ingredients"}  # Valid instruction
            ]
        }
        
        errors = validate_recipe_data(recipe_data)
        assert any("Instruction 1" in error for error in errors)
    
    def test_invalid_rating(self):
        """Test validation with invalid rating."""
        recipe_data = {
            "name": "Test Recipe",
            "rating": 10  # Invalid rating
        }
        
        errors = validate_recipe_data(recipe_data)
        assert "Rating must be between 1 and 5" in errors


def test_extract_recipe_slug_from_current_mealie_create_responses():
    """Test create-recipe slug extraction supports Mealie v3 response shapes."""
    assert _extract_recipe_slug("test-recipe") == "test-recipe"
    assert _extract_recipe_slug({"slug": "test-recipe"}) == "test-recipe"
    assert _extract_recipe_slug({"id": "test-id"}) == "test-id"
    assert _extract_recipe_slug({}) is None


def test_decode_base64_file_accepts_data_urls():
    """Test base64 file decoding supports plain data and data URLs."""
    assert _decode_base64_file("Zm9v") == b"foo"
    assert _decode_base64_file("data:text/plain;base64,YmFy") == b"bar"


def test_timeline_event_payload_normalizes_snake_case_aliases():
    """Test timeline event payloads support Python-style aliases."""
    assert _normalize_timeline_event_payload({
        "recipe_id": "recipe-id",
        "user_id": "user-id",
        "event_type": "info",
        "event_message": "message",
        "subject": "subject",
        "unused_none": None,
    }) == {
        "recipeId": "recipe-id",
        "userId": "user-id",
        "eventType": "info",
        "eventMessage": "message",
        "subject": "subject",
    }


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
