# Meal Planning Guide

Mealie MCP Server exposes Mealie v3 household meal planning APIs as MCP tools.

This guide describes the actual tools available in the server. It does not include AI-generated meal suggestions or weekly-plan helper APIs; use Mealie's own meal-plan entries, random meal entry endpoint, and rules.

## Concepts

Meal plans are household-scoped entries with:

- `date`: `YYYY-MM-DD`
- `entryType`: meal type, such as `dinner`
- `recipeId`: optional recipe UUID
- `title`: custom meal title when no recipe is used
- `text`: optional notes

The MCP tools accept both Mealie-style and Python-style keys:

- `entryType` or `meal_type`
- `recipeId` or `recipe_id`
- `startDate` or `start_date`
- `endDate` or `end_date`

## Meal Types

- `breakfast`
- `lunch`
- `dinner`
- `side`
- `snack`
- `drink`
- `dessert`

## List Meal Plans

Tool: `list_meal_plans`

```json
{
  "filters": {
    "start_date": "2026-05-04",
    "end_date": "2026-05-10"
  }
}
```

Filter by meal type:

```json
{
  "filters": {
    "start_date": "2026-05-04",
    "end_date": "2026-05-10",
    "meal_type": "dinner"
  }
}
```

## Create A Meal With A Recipe

Tool: `create_meal_plan_entry`

```json
{
  "entry_data": {
    "date": "2026-05-04",
    "meal_type": "dinner",
    "recipe_id": "fabf6ba1-d421-4130-84ed-157fe0e2ba0b",
    "text": "Dinner"
  }
}
```

For recipe-only entries, the server sends empty strings for optional `title` and `text` fields when they are not provided. This matches current Mealie v3 validation.

## Create A Custom Meal

Tool: `create_meal_plan_entry`

```json
{
  "entry_data": {
    "date": "2026-05-04",
    "meal_type": "lunch",
    "title": "Leftovers",
    "text": "Use remaining food from yesterday"
  }
}
```

## Update A Meal Plan Entry

Tool: `update_meal_plan_entry`

```json
{
  "meal_plan_id": "8",
  "entry_data": {
    "date": "2026-05-05",
    "meal_type": "dinner",
    "title": "Pasta salad",
    "text": "Serve chilled"
  }
}
```

The server reads the current entry first and preserves the identity fields Mealie requires for update payloads.

## Delete A Meal Plan Entry

Tool: `delete_meal_plan_entry`

```json
{
  "meal_plan_id": "8"
}
```

## Today's Meals

Tool: `get_todays_meal_plans`

```json
{}
```

## Random Meal Entry

Tool: `create_random_meal_plan_entry`

```json
{
  "entry_data": {
    "date": "2026-05-06",
    "meal_type": "dinner"
  }
}
```

Mealie chooses the recipe according to its own random meal endpoint.

## Meal Plan Rules

Rules let Mealie select meals based on day, meal type, and query filters.

List rules:

```json
{
  "filters": {
    "page": 1,
    "perPage": 20
  }
}
```

Create rule:

```json
{
  "rule_data": {
    "day": "monday",
    "entry_type": "dinner",
    "query_filter_string": ""
  }
}
```

Tools:

- `list_meal_plan_rules`
- `get_meal_plan_rule`
- `create_meal_plan_rule`
- `update_meal_plan_rule`
- `delete_meal_plan_rule`

## Recommended Workflow

1. Use `search_recipes` or `get_recipe_suggestions` to find candidate recipes.
2. Use `list_meal_plans` to check the target date range.
3. Use `create_meal_plan_entry` for each planned meal.
4. Use `add_recipe_to_shopping_list` when you want ingredients on a shopping list.
5. Use `get_todays_meal_plans` for daily dashboards or assistants.

## Troubleshooting

### Date validation failed

Use `YYYY-MM-DD`, for example `2026-05-04`.

### The entry has neither title nor recipe_id

Mealie requires either a recipe or a custom title. Provide `recipe_id`/`recipeId` or `title`.

### Recipe ID validation failed

Use the recipe UUID from `get_recipe`, not just the slug. Slugs work for `get_recipe`, but meal-plan recipe links use UUIDs.
