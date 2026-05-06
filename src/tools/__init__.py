"""Tools module for Mealie MCP server.

This module contains all MCP tools for interacting with Mealie API.
Tools are registered via setup functions that create closures with the MCP server.
"""

from .recipes import (
    setup_recipe_tools,
    RecipeSearchFilters,
    RecipeCreateUpdate,
    RecipeImportUrl,
    RecipeIngredient,
    RecipeInstruction,
    RecipeNutrition,
    validate_recipe_data
)

from .meal_plans import (
    setup_meal_plan_tools,
    MealPlanFilters,
    MealPlanEntry,
    RandomMealPlanEntry,
    MealPlanRule,
    MealType
)

from .shopping import (
    setup_shopping_tools,
    ShoppingListCreate,
    ShoppingListUpdate,
    ShoppingItemPayload,
    ShoppingRecipeOptions
)

__all__ = [
    # Setup functions
    'setup_recipe_tools',
    'setup_meal_plan_tools',
    'setup_shopping_tools',

    # Recipe models
    'RecipeSearchFilters',
    'RecipeCreateUpdate',
    'RecipeImportUrl',
    'RecipeIngredient',
    'RecipeInstruction',
    'RecipeNutrition',
    'validate_recipe_data',

    # Meal plan models
    'MealPlanFilters',
    'MealPlanEntry',
    'RandomMealPlanEntry',
    'MealPlanRule',
    'MealType',

    # Shopping models
    'ShoppingListCreate',
    'ShoppingListUpdate',
    'ShoppingItemPayload',
    'ShoppingRecipeOptions'
]
