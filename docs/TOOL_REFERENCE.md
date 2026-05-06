# Tool Reference

This document lists the MCP tools exposed by Mealie MCP Server.

Payloads generally follow Mealie v3 API field names. Where helpful, tools also accept snake_case aliases such as `recipe_id` for `recipeId` or `meal_type` for `entryType`.

Mealie also exposes streaming recipe import endpoints such as `/api/recipes/create/url/stream` and `/api/recipes/create/html-or-json/stream`. This MCP server exposes the equivalent non-streaming JSON import tools because MCP clients expect structured tool results rather than raw server-sent event streams.

## Health

| Tool | Purpose |
| --- | --- |
| `health_check` | Check MCP server status and Mealie API connectivity. |

## Recipes

| Tool | Purpose |
| --- | --- |
| `search_recipes` | Search recipes with Mealie v3 pagination, search, category/tag/tool/food, cookbook, ordering, and query filters. |
| `get_recipe` | Get one recipe by slug or ID. |
| `create_recipe` | Create a recipe. Mealie v3 creates by name first, then applies extra fields with a patch when possible. |
| `update_recipe` | Replace/update a recipe using Mealie's recipe payload. |
| `patch_recipe` | Partially update a recipe. |
| `update_many_recipes` | Replace/update multiple recipes through Mealie's batch endpoint. |
| `patch_many_recipes` | Partially update multiple recipes through Mealie's batch endpoint. |
| `upload_recipe_image` | Upload or replace a recipe image from base64 data. |
| `scrape_recipe_image` | Ask Mealie to scrape and set a recipe image from a URL. |
| `delete_recipe_image` | Delete a recipe image. |
| `delete_recipe` | Delete one recipe. |
| `import_recipe_from_url` | Import one recipe from a URL. |
| `test_recipe_scrape_url` | Test whether Mealie can scrape a URL. |
| `import_recipes_from_urls` | Bulk import recipes from URLs. |
| `import_recipe_from_html_or_json` | Create a recipe from raw HTML or JSON recipe data. |
| `import_recipe_from_zip` | Import recipes from a Mealie ZIP archive supplied as base64. |
| `import_recipe_from_images` | Create a recipe from one or more base64-encoded images. |
| `get_random_recipe` | Select a random recipe from the recipe list. |
| `get_recipe_suggestions` | Get Mealie recipe suggestions, optionally filtered by foods/tools. |
| `duplicate_recipe` | Duplicate a recipe, optionally with a new name. |
| `update_recipe_last_made` | Update a recipe's last-made timestamp. |
| `upload_recipe_asset` | Upload an asset file to a recipe from base64 data. |
| `bulk_tag_recipes` | Apply tags to multiple recipes. |
| `bulk_categorize_recipes` | Apply categories to multiple recipes. |
| `bulk_update_recipe_settings` | Apply settings to multiple recipes. |
| `bulk_delete_recipes` | Delete multiple recipes through Mealie's bulk endpoint. |
| `bulk_export_recipes` | Start a bulk recipe export. |
| `list_recipe_exports` | List recipe export jobs/files. |
| `purge_recipe_exports` | Purge recipe export jobs/files. |
| `download_recipe_export` | Download a bulk export as base64 content. |
| `list_recipe_export_formats` | List recipe export formats and templates. |
| `export_recipe` | Export one recipe with a named template as base64 content. |
| `get_shared_recipe` | Read a shared recipe by token ID. |
| `download_shared_recipe_zip` | Download a shared recipe ZIP as base64 content. |
| `get_recipe_comments` | Get comments for a recipe. |
| `list_recipe_timeline_events` | List recipe timeline events. |
| `create_recipe_timeline_event` | Create a recipe timeline event. |
| `get_recipe_timeline_event` | Get one recipe timeline event. |
| `update_recipe_timeline_event` | Update one recipe timeline event. |
| `delete_recipe_timeline_event` | Delete one recipe timeline event. |
| `upload_recipe_timeline_event_image` | Upload or replace a timeline event image from base64 data. |

### Recipe Examples

Search:

```json
{
  "filters": {
    "query": "pasta",
    "page": 1,
    "per_page": 10,
    "tags": ["weeknight"],
    "categories": ["dinner"],
    "order_by": "name",
    "order_direction": "asc"
  }
}
```

Create:

```json
{
  "recipe_data": {
    "name": "Tomato Pasta",
    "description": "Simple weeknight pasta",
    "recipeYield": "4 servings"
  }
}
```

Patch:

```json
{
  "recipe_id": "tomato-pasta",
  "recipe_data": {
    "description": "Updated description"
  }
}
```

Upload an asset:

```json
{
  "recipe_id": "tomato-pasta",
  "file_base64": "BASE64_FILE_DATA",
  "name": "Printable PDF",
  "icon": "file-text",
  "extension": "pdf"
}
```

Create a timeline event:

```json
{
  "event_data": {
    "recipe_id": "fabf6ba1-d421-4130-84ed-157fe0e2ba0b",
    "subject": "Made for dinner",
    "event_type": "info",
    "event_message": "Served with salad"
  }
}
```

## Meal Plans

| Tool | Purpose |
| --- | --- |
| `list_meal_plans` | List meal plans with date filters. |
| `get_meal_plan` | Get one meal-plan entry. |
| `create_meal_plan_entry` | Create a meal-plan entry. |
| `update_meal_plan_entry` | Update a meal-plan entry. |
| `delete_meal_plan_entry` | Delete a meal-plan entry. |
| `get_todays_meal_plans` | Get today's meal plans. |
| `create_random_meal_plan_entry` | Ask Mealie to create a random meal entry. |
| `list_meal_plan_rules` | List meal-plan rules. |
| `get_meal_plan_rule` | Get one meal-plan rule. |
| `create_meal_plan_rule` | Create a meal-plan rule. |
| `update_meal_plan_rule` | Update a meal-plan rule. |
| `delete_meal_plan_rule` | Delete a meal-plan rule. |

Meal type values:

- `breakfast`
- `lunch`
- `dinner`
- `side`
- `snack`
- `drink`
- `dessert`

Create an entry with a recipe:

```json
{
  "entry_data": {
    "date": "2026-05-04",
    "meal_type": "dinner",
    "recipe_id": "fabf6ba1-d421-4130-84ed-157fe0e2ba0b",
    "text": "Dinner plan"
  }
}
```

Create a custom entry:

```json
{
  "entry_data": {
    "date": "2026-05-04",
    "meal_type": "lunch",
    "title": "Leftovers",
    "text": "Use what is in the fridge"
  }
}
```

## Shopping Lists

| Tool | Purpose |
| --- | --- |
| `list_shopping_lists` | List household shopping lists. |
| `get_shopping_list` | Get one shopping list, including items when Mealie returns them. |
| `create_shopping_list` | Create a shopping list. |
| `update_shopping_list` | Update a shopping list. |
| `delete_shopping_list` | Delete a shopping list. |
| `list_shopping_items` | List shopping items. |
| `get_shopping_item` | Get one shopping item. |
| `add_shopping_item` | Add an item to a list using a list ID and item payload. |
| `create_shopping_item` | Create an item with a Mealie-native payload. |
| `create_shopping_items` | Bulk create shopping items. |
| `update_shopping_item` | Update one shopping item. |
| `update_shopping_items` | Bulk update shopping items. |
| `delete_shopping_item` | Delete one shopping item. |
| `delete_shopping_items` | Bulk delete shopping items. |
| `add_recipe_to_shopping_list` | Add one recipe's ingredients to a shopping list. |
| `add_recipes_to_shopping_list` | Add multiple recipes' ingredients to a shopping list. |
| `remove_recipe_from_shopping_list` | Remove a recipe's ingredients from a shopping list. |
| `update_shopping_list_label_settings` | Update label settings/order for a shopping list. |

Simple item:

```json
{
  "list_id": "shopping-list-uuid",
  "item_data": {
    "name": "Milk",
    "quantity": 2,
    "note": "Whole milk"
  }
}
```

Mealie-native item:

```json
{
  "item_data": {
    "shoppingListId": "shopping-list-uuid",
    "display": "Milk",
    "quantity": 2,
    "checked": false,
    "foodId": "food-uuid",
    "unitId": "unit-uuid"
  }
}
```

Add a recipe to a shopping list:

```json
{
  "list_id": "shopping-list-uuid",
  "recipe_id": "recipe-uuid",
  "options": {
    "recipeIncrementQuantity": 1
  }
}
```

## Foods

| Tool | Purpose |
| --- | --- |
| `list_foods` | List foods with optional pagination/search filters. |
| `get_food` | Get one food. |
| `create_food` | Create a food. |
| `update_food` | Update a food while preserving existing fields required by Mealie PUT. |
| `delete_food` | Delete a food. |
| `search_foods` | Search foods. |
| `merge_foods` | Merge one duplicate food into another. |

Food payloads support:

- `name`
- `pluralName` or `plural_name`
- `description`
- `aliases`
- `labelId` or `label_id`
- `extras`

## Units

| Tool | Purpose |
| --- | --- |
| `list_units` | List units. |
| `get_unit` | Get one unit. |
| `create_unit` | Create a unit. |
| `update_unit` | Update a unit while preserving existing fields required by Mealie PUT. |
| `delete_unit` | Delete a unit. |
| `merge_units` | Merge one duplicate unit into another. |

Unit payloads support:

- `name`
- `pluralName` or `plural_name`
- `abbreviation`
- `pluralAbbreviation` or `plural_abbreviation`
- `useAbbreviation` or `use_abbreviation`
- `fraction`
- `aliases`
- `standardQuantity` or `standard_quantity`
- `standardUnit` or `standard_unit`
- `description`

## Tags, Categories, And Recipe Tools

| Tool | Purpose |
| --- | --- |
| `list_tags` | List tags. |
| `get_tag` | Get one tag by ID. |
| `get_tag_by_slug` | Get one tag by slug. |
| `list_empty_tags` | List tags with no recipe assignments. |
| `create_tag` | Create a tag. |
| `update_tag` | Update a tag. |
| `delete_tag` | Delete a tag. |
| `list_categories` | List categories. |
| `get_category` | Get one category by ID. |
| `get_category_by_slug` | Get one category by slug. |
| `list_empty_categories` | List categories with no recipe assignments. |
| `create_category` | Create a category. |
| `update_category` | Update a category. |
| `delete_category` | Delete a category. |
| `list_recipe_tools` | List recipe tools/utensils. |
| `get_recipe_tool` | Get one recipe tool by ID. |
| `get_recipe_tool_by_slug` | Get one recipe tool by slug. |
| `create_recipe_tool` | Create a recipe tool. |
| `update_recipe_tool` | Update a recipe tool. |
| `delete_recipe_tool` | Delete a recipe tool. |

Mealie v3 creates and updates tags/categories by name. Slugs are generated by Mealie; use the slug lookup tools to fetch by slug.

## App, Parser, And Media

| Tool | Purpose |
| --- | --- |
| `get_app_about` | Get public Mealie app/version information. |
| `get_app_startup_info` | Get startup information exposed by Mealie. |
| `get_app_theme` | Get Mealie theme information. |
| `parse_ingredient` | Parse one ingredient line. |
| `parse_ingredients` | Parse multiple ingredient lines. |
| `download_url` | Download a URL through Mealie's utility endpoint. |
| `get_media_docker_validation_text` | Get Mealie's Docker media validation text file. |
| `get_recipe_asset_media` | Download a recipe asset as base64-safe data. |
| `get_recipe_image_media` | Download a recipe image as base64-safe data. |
| `get_recipe_timeline_image_media` | Download a recipe timeline image as base64-safe data. |
| `get_user_image_media` | Download a user image as base64-safe data. |

## Comments And Shared Recipe Records

| Tool | Purpose |
| --- | --- |
| `list_comments` | List comments with optional Mealie filters. |
| `get_comment` | Get one comment. |
| `create_comment` | Create a comment. |
| `update_comment` | Update a comment. |
| `delete_comment` | Delete a comment. |
| `list_shared_recipe_records` | List shared recipe records. |
| `create_shared_recipe_record` | Create a shared recipe record. |
| `get_shared_recipe_record` | Get one shared recipe record. |
| `delete_shared_recipe_record` | Delete a shared recipe record. |

## Household Resources

| Tool | Purpose |
| --- | --- |
| `get_household_self` | Get the current household. |
| `get_household_statistics` | Get current household statistics. |
| `list_household_members` | List household members. |
| `get_household_preferences` | Get household preferences. |
| `update_household_preferences` | Update household preferences. |
| `update_household_permissions` | Update household permissions. |
| `get_household_recipe_details` | Get household-specific details for one recipe. |
| `list_cookbooks` | List household cookbooks. |
| `get_cookbook` | Get one cookbook. |
| `create_cookbook` | Create a cookbook. |
| `update_cookbook` | Update one cookbook. |
| `update_cookbooks` | Bulk update cookbooks. |
| `delete_cookbook` | Delete one cookbook. |
| `list_household_invitations` | List household invitations. |
| `create_household_invitation` | Create a household invitation. |
| `send_household_invitation_email` | Send a household invitation email. |
| `list_household_notifications` | List household event notifications. |
| `get_household_notification` | Get one household event notification. |
| `create_household_notification` | Create a household event notification. |
| `update_household_notification` | Update a household event notification. |
| `delete_household_notification` | Delete a household event notification. |
| `test_household_notification` | Trigger a test notification. |
| `list_recipe_actions` | List household recipe actions. |
| `get_recipe_action` | Get one recipe action. |
| `create_recipe_action` | Create a recipe action. |
| `update_recipe_action` | Update a recipe action. |
| `delete_recipe_action` | Delete a recipe action. |
| `trigger_recipe_action` | Trigger a recipe action for a recipe. |
| `list_household_webhooks` | List household webhooks. |
| `get_household_webhook` | Get one household webhook. |
| `create_household_webhook` | Create a household webhook. |
| `update_household_webhook` | Update a household webhook. |
| `delete_household_webhook` | Delete a household webhook. |
| `test_household_webhook` | Trigger a test webhook. |
| `rerun_household_webhooks` | Rerun household webhooks. |

## Group Resources

| Tool | Purpose |
| --- | --- |
| `get_group_self` | Get the current group. |
| `list_group_households` | List group households. |
| `get_group_household` | Get one group household. |
| `list_group_members` | List group members. |
| `get_group_member` | Get one group member. |
| `get_group_preferences` | Get group preferences. |
| `update_group_preferences` | Update group preferences. |
| `get_group_storage` | Get group storage information. |
| `list_group_labels` | List group labels. |
| `get_group_label` | Get one group label. |
| `create_group_label` | Create a group label. |
| `update_group_label` | Update a group label. |
| `delete_group_label` | Delete a group label. |
| `list_group_reports` | List group reports. |
| `get_group_report` | Get one group report. |
| `delete_group_report` | Delete a group report. |
| `create_group_migration` | Create a group migration. |
| `seed_group_foods` | Run the group foods seeder. |
| `seed_group_labels` | Run the group labels seeder. |
| `seed_group_units` | Run the group units seeder. |

## User Resources

| Tool | Purpose |
| --- | --- |
| `get_self_user` | Get the current user. |
| `update_user` | Update one user. |
| `update_user_password` | Update the current user's password. |
| `create_user_api_token` | Create a Mealie API token. |
| `delete_user_api_token` | Delete a Mealie API token. |
| `list_self_favorites` | List current user favorites. |
| `list_user_favorites` | List one user's favorites. |
| `add_user_favorite` | Add one recipe to favorites. |
| `delete_user_favorite` | Remove one recipe from favorites. |
| `list_self_ratings` | List current user ratings. |
| `get_self_rating` | Get current user rating for one recipe. |
| `list_user_ratings` | List one user's ratings. |
| `set_user_rating` | Create or update one user's rating. |
| `upload_user_image` | Upload a user image from base64 data. |

## Explore Resources

| Tool | Purpose |
| --- | --- |
| `explore_group_recipes` | List public/explore recipes for a group. |
| `explore_group_recipe` | Get one public/explore recipe. |
| `explore_group_recipe_suggestions` | Get public/explore recipe suggestions. |
| `explore_group_cookbooks` | List public/explore cookbooks. |
| `explore_group_cookbook` | Get one public/explore cookbook. |
| `explore_group_households` | List public/explore households. |
| `explore_group_household` | Get one public/explore household. |
| `explore_group_foods` | List public/explore foods. |
| `explore_group_food` | Get one public/explore food. |
| `explore_group_tags` | List public/explore tags. |
| `explore_group_tag` | Get one public/explore tag. |
| `explore_group_categories` | List public/explore categories. |
| `explore_group_category` | Get one public/explore category. |
| `explore_group_tools` | List public/explore recipe tools. |
| `explore_group_tool` | Get one public/explore recipe tool. |

## Admin Resources

Admin tools require the configured Mealie token to belong to an admin user.

| Tool | Purpose |
| --- | --- |
| `get_admin_about` | Get admin app information. |
| `check_admin_about` | Run admin about/check. |
| `get_admin_statistics` | Get admin statistics. |
| `list_admin_backups` | List admin backups. |
| `create_admin_backup` | Create an admin backup. |
| `download_admin_backup` | Download an admin backup as base64-safe data. |
| `upload_admin_backup` | Upload an admin backup archive from base64 data. |
| `delete_admin_backup` | Delete an admin backup. |
| `restore_admin_backup` | Restore an admin backup. |
| `debug_admin_openai` | Run Mealie's admin OpenAI debug endpoint. |
| `get_admin_email` | Get admin email settings. |
| `update_admin_email` | Update admin email settings. |
| `list_admin_groups` | List admin-visible groups. |
| `get_admin_group` | Get one admin-visible group. |
| `create_admin_group` | Create a group through the admin API. |
| `update_admin_group` | Update an admin-visible group. |
| `delete_admin_group` | Delete an admin-visible group. |
| `list_admin_households` | List admin-visible households. |
| `get_admin_household` | Get one admin-visible household. |
| `create_admin_household` | Create a household through the admin API. |
| `update_admin_household` | Update an admin-visible household. |
| `delete_admin_household` | Delete an admin-visible household. |
| `list_admin_users` | List admin-visible users. |
| `get_admin_user` | Get one admin-visible user. |
| `create_admin_user` | Create a user through the admin API. |
| `update_admin_user` | Update an admin-visible user. |
| `delete_admin_user` | Delete an admin-visible user. |
| `create_admin_password_reset_token` | Create an admin password reset token. |
| `unlock_admin_users` | Unlock users through the admin API. |
| `get_admin_maintenance` | Get admin maintenance status. |
| `get_admin_maintenance_storage` | Get admin maintenance storage information. |
| `clean_admin_images` | Run admin image cleanup. |
| `clean_admin_recipe_folders` | Run admin recipe folder cleanup. |
| `clean_admin_temp` | Run admin temporary file cleanup. |

## Destructive Tools

These tools delete, merge, or bulk-modify data:

- `delete_recipe`
- `delete_recipe_image`
- `bulk_delete_recipes`
- `purge_recipe_exports`
- `delete_recipe_timeline_event`
- `delete_meal_plan_entry`
- `delete_meal_plan_rule`
- `delete_shopping_list`
- `delete_shopping_item`
- `delete_shopping_items`
- `remove_recipe_from_shopping_list`
- `delete_food`
- `merge_foods`
- `delete_unit`
- `merge_units`
- `delete_tag`
- `delete_category`
- `delete_recipe_tool`
- `delete_comment`
- `delete_shared_recipe_record`
- `delete_cookbook`
- `delete_household_notification`
- `delete_household_webhook`
- `delete_recipe_action`
- `delete_group_label`
- `delete_group_report`
- `delete_user_api_token`
- `delete_user_favorite`
- `delete_admin_backup`
- `restore_admin_backup`
- `delete_admin_group`
- `delete_admin_household`
- `delete_admin_user`
- `clean_admin_images`
- `clean_admin_recipe_folders`
- `clean_admin_temp`

Use a dedicated Mealie API token and restrict MCP access accordingly.

## Intentionally Excluded Endpoints

- Mealie auth/session endpoints are not exposed; MCP clients should authenticate by configuring `MEALIE_API_TOKEN`.
- Public password-reset endpoints (`/api/users/forgot-password`, `/api/users/reset-password`) are not exposed because they trigger Mealie's email/reset-password flow outside token-scoped cookbook operations.
- Streaming recipe import endpoints are not exposed because MCP tools return structured JSON; use the non-streaming import tools instead.
