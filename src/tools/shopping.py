"""Shopping list management tools for the current Mealie household API."""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mealie_client import MealieAPIError

logger = logging.getLogger(__name__)


class ShoppingListCreate(BaseModel):
    """Model for creating a new shopping list."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: Optional[str] = Field(default=None, max_length=100)
    extras: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ShoppingListUpdate(BaseModel):
    """Model for updating a shopping list."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: Optional[str] = Field(default=None, max_length=100)
    extras: Optional[Dict[str, Any]] = None


class ShoppingItemPayload(BaseModel):
    """Flexible Mealie v3 shopping item payload.

    Mealie accepts nested food/unit objects as well as foodId/unitId references.
    The model deliberately allows extra fields so callers can pass through newer
    API fields without waiting for a MCP release.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    shoppingListId: Optional[str] = None
    shopping_list_id: Optional[str] = Field(default=None, exclude=True)
    name: Optional[str] = Field(default=None, exclude=True)
    display: Optional[str] = None
    quantity: Optional[float] = None
    note: Optional[str] = None
    checked: Optional[bool] = None
    position: Optional[int] = None
    foodId: Optional[str] = None
    food_id: Optional[str] = Field(default=None, exclude=True)
    unitId: Optional[str] = None
    unit_id: Optional[str] = Field(default=None, exclude=True)
    labelId: Optional[str] = None
    label_id: Optional[str] = Field(default=None, exclude=True)
    extras: Optional[Dict[str, Any]] = None


class ShoppingRecipeOptions(BaseModel):
    """Options used when adding or removing recipe ingredients."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    recipeIncrementQuantity: Optional[float] = None
    recipe_increment_quantity: Optional[float] = Field(default=None, exclude=True)
    recipeDecrementQuantity: Optional[float] = None
    recipe_decrement_quantity: Optional[float] = Field(default=None, exclude=True)
    recipeIngredients: Optional[List[Dict[str, Any]]] = None
    recipe_ingredients: Optional[List[Dict[str, Any]]] = Field(default=None, exclude=True)


def _drop_none(data: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def _model_payload(model: BaseModel) -> Dict[str, Any]:
    return _drop_none(model.model_dump(by_alias=True))


def _normalize_item_payload(item_data: Dict[str, Any], list_id: Optional[str] = None) -> Dict[str, Any]:
    item = ShoppingItemPayload(**item_data)
    payload = _model_payload(item)

    if item.shopping_list_id and "shoppingListId" not in payload:
        payload["shoppingListId"] = item.shopping_list_id
    if list_id and "shoppingListId" not in payload:
        payload["shoppingListId"] = list_id
    if item.name and "display" not in payload:
        payload["display"] = item.name
    if item.food_id and "foodId" not in payload:
        payload["foodId"] = item.food_id
    if item.unit_id and "unitId" not in payload:
        payload["unitId"] = item.unit_id
    if item.label_id and "labelId" not in payload:
        payload["labelId"] = item.label_id

    return payload


def _normalize_recipe_options(options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not options:
        return {}

    parsed = ShoppingRecipeOptions(**options)
    payload = _model_payload(parsed)
    if parsed.recipe_increment_quantity is not None and "recipeIncrementQuantity" not in payload:
        payload["recipeIncrementQuantity"] = parsed.recipe_increment_quantity
    if parsed.recipe_decrement_quantity is not None and "recipeDecrementQuantity" not in payload:
        payload["recipeDecrementQuantity"] = parsed.recipe_decrement_quantity
    if parsed.recipe_ingredients is not None and "recipeIngredients" not in payload:
        payload["recipeIngredients"] = parsed.recipe_ingredients
    return payload


def _merge_resource_update(current: Dict[str, Any], updates: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    merged = {field: current.get(field) for field in fields if field in current}
    merged.update(_drop_none(updates))
    return merged


def setup_shopping_tools(mcp_server, client_provider):
    """Setup shopping tools with the main MCP server."""

    @mcp_server.tool()
    async def list_shopping_lists(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List shopping lists with optional Mealie pagination/search filters."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get("/api/households/shopping/lists", filters or None)
            return {
                "shopping_lists": response.get("items", []),
                "total": response.get("total", 0),
                "page": response.get("page", 1),
                "per_page": response.get("per_page", response.get("perPage")),
            }
        except Exception as e:
            logger.error(f"List shopping lists failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_shopping_list(list_id: str) -> Dict[str, Any]:
        """Get specific shopping list details, including list items."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            shopping_list = await client.get(f"/api/households/shopping/lists/{list_id}")
            return {"shopping_list": shopping_list}
        except Exception as e:
            logger.error(f"Get shopping list failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def create_shopping_list(list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new shopping list."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            payload = _model_payload(ShoppingListCreate(**list_data))
            response = await client.post("/api/households/shopping/lists", payload)
            return {"shopping_list": response, "message": "Shopping list created successfully"}
        except Exception as e:
            logger.error(f"Create shopping list failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_shopping_list(list_id: str, list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing shopping list."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            updates = _model_payload(ShoppingListUpdate(**list_data))
            current = await client.get(f"/api/households/shopping/lists/{list_id}")
            payload = _merge_resource_update(
                current,
                updates,
                ["id", "groupId", "userId", "name", "extras", "listItems"],
            )
            response = await client.put(f"/api/households/shopping/lists/{list_id}", payload)
            return {"shopping_list": response, "message": "Shopping list updated successfully"}
        except Exception as e:
            logger.error(f"Update shopping list failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def delete_shopping_list(list_id: str) -> Dict[str, Any]:
        """Delete a shopping list."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            await client.delete(f"/api/households/shopping/lists/{list_id}")
            return {"message": f"Shopping list {list_id} deleted successfully"}
        except Exception as e:
            logger.error(f"Delete shopping list failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def list_shopping_items(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List shopping items with optional Mealie pagination/search filters."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get("/api/households/shopping/items", filters or None)
            return {
                "items": response.get("items", []),
                "total": response.get("total", 0),
                "page": response.get("page", 1),
                "per_page": response.get("per_page", response.get("perPage")),
            }
        except Exception as e:
            logger.error(f"List shopping items failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_shopping_item(item_id: str) -> Dict[str, Any]:
        """Get one shopping list item."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            item = await client.get(f"/api/households/shopping/items/{item_id}")
            return {"item": item}
        except Exception as e:
            logger.error(f"Get shopping item failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def add_shopping_item(list_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to a shopping list.

        Accepts both simple payloads like {"name": "mléko"} and Mealie-native
        payloads using display, foodId, unitId, quantity, note, etc.
        """
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            payload = _normalize_item_payload(item_data, list_id=list_id)
            response = await client.post("/api/households/shopping/items", payload)
            return {"item": response, "message": "Item added successfully"}
        except Exception as e:
            logger.error(f"Add shopping item failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def create_shopping_item(item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shopping item with a Mealie-native payload."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            payload = _normalize_item_payload(item_data)
            response = await client.post("/api/households/shopping/items", payload)
            return {"item": response, "message": "Item created successfully"}
        except Exception as e:
            logger.error(f"Create shopping item failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def create_shopping_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple shopping items."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            payload = [_normalize_item_payload(item) for item in items]
            response = await client.post("/api/households/shopping/items/create-bulk", payload)
            return {"result": response, "message": "Shopping items created successfully"}
        except Exception as e:
            logger.error(f"Create shopping items failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_shopping_item(item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update one shopping item."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            updates = _normalize_item_payload(item_data)
            current = await client.get(f"/api/households/shopping/items/{item_id}")
            payload = _merge_resource_update(
                current,
                updates,
                [
                    "shoppingListId",
                    "quantity",
                    "unit",
                    "food",
                    "referencedRecipe",
                    "note",
                    "display",
                    "checked",
                    "position",
                    "foodId",
                    "labelId",
                    "unitId",
                    "extras",
                    "recipeReferences",
                ],
            )
            response = await client.put(f"/api/households/shopping/items/{item_id}", payload)
            return {"item": response, "message": "Shopping item updated successfully"}
        except Exception as e:
            logger.error(f"Update shopping item failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_shopping_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk update shopping items. Each item must include id and shoppingListId."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            payload = [_normalize_item_payload(item) for item in items]
            response = await client.put("/api/households/shopping/items", payload)
            return {"result": response, "message": "Shopping items updated successfully"}
        except Exception as e:
            logger.error(f"Update shopping items failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def delete_shopping_item(item_id: str) -> Dict[str, Any]:
        """Delete one shopping item."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            await client.delete(f"/api/households/shopping/items/{item_id}")
            return {"message": f"Shopping item {item_id} deleted successfully"}
        except Exception as e:
            logger.error(f"Delete shopping item failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def delete_shopping_items(item_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple shopping items."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            await client.delete("/api/households/shopping/items", params={"ids": item_ids})
            return {"message": f"Deleted {len(item_ids)} shopping items"}
        except Exception as e:
            logger.error(f"Delete shopping items failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def add_recipe_to_shopping_list(
        list_id: str,
        recipe_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add one recipe's ingredients to a shopping list."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            payload = _normalize_recipe_options(options)
            response = await client.post(
                f"/api/households/shopping/lists/{list_id}/recipe/{recipe_id}",
                payload,
            )
            return {"result": response, "message": "Recipe ingredients added to shopping list"}
        except Exception as e:
            logger.error(f"Add recipe to shopping list failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def add_recipes_to_shopping_list(list_id: str, recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add multiple recipes' ingredients to a shopping list."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            payload = []
            for recipe in recipes:
                normalized = _normalize_recipe_options(recipe)
                if "recipe_id" in recipe and "recipeId" not in normalized:
                    normalized["recipeId"] = recipe["recipe_id"]
                payload.append(normalized)

            response = await client.post(f"/api/households/shopping/lists/{list_id}/recipe", payload)
            return {"result": response, "message": "Recipe ingredients added to shopping list"}
        except Exception as e:
            logger.error(f"Add recipes to shopping list failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def remove_recipe_from_shopping_list(
        list_id: str,
        recipe_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Remove one recipe's ingredients from a shopping list."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            payload = _normalize_recipe_options(options)
            response = await client.post(
                f"/api/households/shopping/lists/{list_id}/recipe/{recipe_id}/delete",
                payload,
            )
            return {"result": response, "message": "Recipe ingredients removed from shopping list"}
        except Exception as e:
            logger.error(f"Remove recipe from shopping list failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_shopping_list_label_settings(
        list_id: str,
        label_settings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Update shopping-list label settings/order."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.put(
                f"/api/households/shopping/lists/{list_id}/label-settings",
                label_settings,
            )
            return {"label_settings": response, "message": "Shopping list label settings updated"}
        except Exception as e:
            logger.error(f"Update shopping list label settings failed: {e}")
            return {"error": str(e)}


__all__ = [
    "setup_shopping_tools",
    "ShoppingListCreate",
    "ShoppingListUpdate",
    "ShoppingItemPayload",
    "ShoppingRecipeOptions",
    "_normalize_item_payload",
    "_normalize_recipe_options",
]
