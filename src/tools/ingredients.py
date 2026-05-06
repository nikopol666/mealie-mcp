"""Ingredients and Foods management tools for Mealie MCP server.

This module provides comprehensive food and unit management functionality through MCP tools
that interface with the Mealie API. Foods (ingredients) can be created, searched, updated,
and merged. Units of measurement can also be managed. All tools include proper error handling,
input validation using Pydantic models, and async operations.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from mealie_client import MealieClient, MealieAPIError

logger = logging.getLogger(__name__)


class FoodSearchFilters(BaseModel):
    """Filters for food search operations."""

    query: Optional[str] = Field(
        default="",
        description="Search query for food name or description"
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Page number for pagination"
    )
    per_page: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of foods per page (max 100)"
    )


class FoodCreate(BaseModel):
    """Model for creating a new food."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        description="Food name",
        min_length=1,
        max_length=200
    )
    plural_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("plural_name", "pluralName"),
        description="Food plural name",
        max_length=200
    )
    description: Optional[str] = Field(
        default=None,
        description="Food description",
        max_length=500
    )
    extras: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom key-value pairs for additional food properties"
    )
    label_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("label_id", "labelId"),
        description="ID of the label to associate with this food"
    )
    aliases: Optional[List[Union[str, Dict[str, Any]]]] = Field(
        default=None,
        description="Alternative names for parsing ingredient text"
    )


class FoodUpdate(BaseModel):
    """Model for updating an existing food."""

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(
        default=None,
        description="Food name",
        min_length=1,
        max_length=200
    )
    plural_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("plural_name", "pluralName"),
        description="Food plural name",
        max_length=200
    )
    description: Optional[str] = Field(
        default=None,
        description="Food description",
        max_length=500
    )
    extras: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom key-value pairs for additional food properties"
    )
    label_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("label_id", "labelId"),
        description="ID of the label to associate with this food"
    )
    aliases: Optional[List[Union[str, Dict[str, Any]]]] = Field(
        default=None,
        description="Alternative names for parsing ingredient text"
    )


class UnitCreate(BaseModel):
    """Model for creating a new unit."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        description="Unit name",
        min_length=1,
        max_length=50
    )
    plural_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("plural_name", "pluralName"),
        description="Unit plural name",
        max_length=50
    )
    abbreviation: Optional[str] = Field(
        default=None,
        description="Unit abbreviation (e.g., 'kg', 'lb', 'ml')",
        max_length=20
    )
    plural_abbreviation: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("plural_abbreviation", "pluralAbbreviation"),
        description="Plural unit abbreviation",
        max_length=20
    )
    description: Optional[str] = Field(
        default=None,
        description="Unit description",
        max_length=200
    )
    fraction: Optional[bool] = Field(
        default=None,
        description="Whether this unit supports fractional amounts"
    )
    use_abbreviation: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("use_abbreviation", "useAbbreviation"),
        description="Whether to use the abbreviation in displays"
    )
    aliases: Optional[List[Union[str, Dict[str, Any]]]] = Field(
        default=None,
        description="Alternative unit names for parsing ingredient text"
    )
    standard_quantity: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("standard_quantity", "standardQuantity"),
        description="Quantity in the canonical Mealie unit"
    )
    standard_unit: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("standard_unit", "standardUnit"),
        description="Canonical Mealie unit name, e.g. gram, kilogram, milliliter"
    )


class UnitUpdate(BaseModel):
    """Model for updating an existing unit."""

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(
        default=None,
        description="Unit name",
        min_length=1,
        max_length=50
    )
    plural_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("plural_name", "pluralName"),
        description="Unit plural name",
        max_length=50
    )
    abbreviation: Optional[str] = Field(
        default=None,
        description="Unit abbreviation",
        max_length=20
    )
    plural_abbreviation: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("plural_abbreviation", "pluralAbbreviation"),
        description="Plural unit abbreviation",
        max_length=20
    )
    description: Optional[str] = Field(
        default=None,
        description="Unit description",
        max_length=200
    )
    fraction: Optional[bool] = Field(
        default=None,
        description="Whether this unit supports fractional amounts"
    )
    use_abbreviation: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("use_abbreviation", "useAbbreviation"),
        description="Whether to use the abbreviation in displays"
    )
    aliases: Optional[List[Union[str, Dict[str, Any]]]] = Field(
        default=None,
        description="Alternative unit names for parsing ingredient text"
    )
    standard_quantity: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("standard_quantity", "standardQuantity"),
        description="Quantity in the canonical Mealie unit"
    )
    standard_unit: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("standard_unit", "standardUnit"),
        description="Canonical Mealie unit name, e.g. gram, kilogram, milliliter"
    )


class FoodMerge(BaseModel):
    """Model for merging two foods."""

    from_food_id: str = Field(
        description="ID of the food to merge from (will be deleted)"
    )
    to_food_id: str = Field(
        description="ID of the food to merge into (will be kept)"
    )


class UnitMerge(BaseModel):
    """Model for merging two units."""

    from_unit_id: str = Field(
        description="ID of the unit to merge from (will be deleted)"
    )
    to_unit_id: str = Field(
        description="ID of the unit to merge into (will be kept)"
    )


def _normalize_aliases(aliases: Optional[List[Union[str, Dict[str, Any]]]]) -> Optional[List[Dict[str, Any]]]:
    """Normalize alias payloads to Mealie's object shape."""
    if aliases is None:
        return None

    normalized = []
    for alias in aliases:
        if isinstance(alias, str):
            normalized.append({"name": alias})
        elif isinstance(alias, dict) and alias.get("name"):
            normalized.append(alias)
    return normalized


def _compact(data: Dict[str, Any]) -> Dict[str, Any]:
    """Drop keys with None values while preserving explicit false/empty values."""
    return {key: value for key, value in data.items() if value is not None}


def _food_create_to_api_data(food: FoodCreate) -> Dict[str, Any]:
    return _compact({
        "name": food.name,
        "pluralName": food.plural_name,
        "description": food.description,
        "extras": food.extras or {},
        "labelId": food.label_id,
        "aliases": _normalize_aliases(food.aliases),
    })


def _food_update_to_api_data(food: FoodUpdate) -> Dict[str, Any]:
    return _compact({
        "name": food.name,
        "pluralName": food.plural_name,
        "description": food.description,
        "extras": food.extras,
        "labelId": food.label_id,
        "aliases": _normalize_aliases(food.aliases),
    })


def _unit_create_to_api_data(unit: UnitCreate) -> Dict[str, Any]:
    return _compact({
        "name": unit.name,
        "pluralName": unit.plural_name,
        "abbreviation": unit.abbreviation,
        "pluralAbbreviation": unit.plural_abbreviation,
        "description": unit.description,
        "fraction": unit.fraction,
        "useAbbreviation": unit.use_abbreviation,
        "aliases": _normalize_aliases(unit.aliases),
        "standardQuantity": unit.standard_quantity,
        "standardUnit": unit.standard_unit,
    })


def _unit_update_to_api_data(unit: UnitUpdate) -> Dict[str, Any]:
    return _compact({
        "name": unit.name,
        "pluralName": unit.plural_name,
        "abbreviation": unit.abbreviation,
        "pluralAbbreviation": unit.plural_abbreviation,
        "description": unit.description,
        "fraction": unit.fraction,
        "useAbbreviation": unit.use_abbreviation,
        "aliases": _normalize_aliases(unit.aliases),
        "standardQuantity": unit.standard_quantity,
        "standardUnit": unit.standard_unit,
    })


def _merge_resource_update(current: Dict[str, Any], updates: Dict[str, Any], allowed_fields: List[str]) -> Dict[str, Any]:
    """Build a full PUT payload so Mealie does not null fields omitted by MCP callers."""
    return {
        field: updates[field] if field in updates else current.get(field)
        for field in allowed_fields
        if field in updates or field in current
    }


def setup_ingredient_tools(mcp_server, client_provider):
    """Setup ingredient and food management tools with the main MCP server."""

    # ===== FOOD TOOLS =====

    @mcp_server.tool()
    async def list_foods(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List all foods with optional filtering and pagination."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            if filters is None:
                filters = {}

            search_filters = FoodSearchFilters(**filters)

            params = {
                "page": search_filters.page,
                "perPage": search_filters.per_page
            }

            if search_filters.query:
                params["search"] = search_filters.query

            response = await client.get_foods(params)

            return {
                "foods": response.get("items", []),
                "total": response.get("total", 0),
                "page": response.get("page", search_filters.page),
                "per_page": response.get("per_page", search_filters.per_page)
            }
        except Exception as e:
            logger.error(f"List foods failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_food(food_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific food by ID."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            food = await client.get_food(food_id)
            return {"food": food}
        except MealieAPIError as e:
            if "not found" in str(e).lower():
                return {"error": f"Food not found: {food_id}"}
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Get food failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def create_food(food_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new food/ingredient in Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            # Validate food data
            food = FoodCreate(**food_data)

            api_data = _food_create_to_api_data(food)

            response = await client.create_food(api_data)
            return {"food": response, "message": "Food created successfully"}
        except Exception as e:
            logger.error(f"Create food failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_food(food_id: str, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing food/ingredient in Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            # Validate food data
            food = FoodUpdate(**food_data)

            updates = _food_update_to_api_data(food)
            current = await client.get_food(food_id)
            api_data = _merge_resource_update(
                current,
                updates,
                ["id", "name", "pluralName", "description", "extras", "labelId", "aliases"],
            )

            response = await client.update_food(food_id, api_data)
            return {"food": response, "message": "Food updated successfully"}
        except MealieAPIError as e:
            if "not found" in str(e).lower():
                return {"error": f"Food not found: {food_id}"}
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Update food failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def delete_food(food_id: str) -> Dict[str, Any]:
        """Delete a food/ingredient from Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            await client.delete_food(food_id)
            return {"message": f"Food {food_id} deleted successfully"}
        except MealieAPIError as e:
            if "not found" in str(e).lower():
                return {"error": f"Food not found: {food_id}"}
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Delete food failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def search_foods(query: str, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """Search for foods by name or description."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.search_foods(query, page, per_page)

            return {
                "foods": response.get("items", []),
                "total": response.get("total", 0),
                "page": response.get("page", page),
                "per_page": response.get("per_page", per_page),
                "query": query
            }
        except Exception as e:
            logger.error(f"Search foods failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def merge_foods(merge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge one food into another (consolidate duplicates)."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            # Validate merge data
            merge = FoodMerge(**merge_data)

            response = await client.merge_foods(merge.from_food_id, merge.to_food_id)
            return {
                "message": f"Food {merge.from_food_id} merged into {merge.to_food_id}",
                "result": response
            }
        except Exception as e:
            logger.error(f"Merge foods failed: {e}")
            return {"error": str(e)}

    # ===== UNIT TOOLS =====

    @mcp_server.tool()
    async def list_units() -> Dict[str, Any]:
        """List all measurement units."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get_units()
            return {"units": response.get("items", [])}
        except Exception as e:
            logger.error(f"List units failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_unit(unit_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific unit by ID."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            unit = await client.get_unit(unit_id)
            return {"unit": unit}
        except MealieAPIError as e:
            if "not found" in str(e).lower():
                return {"error": f"Unit not found: {unit_id}"}
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Get unit failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def create_unit(unit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new measurement unit in Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            # Validate unit data
            unit = UnitCreate(**unit_data)

            api_data = _unit_create_to_api_data(unit)

            response = await client.create_unit(api_data)
            return {"unit": response, "message": "Unit created successfully"}
        except Exception as e:
            logger.error(f"Create unit failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_unit(unit_id: str, unit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing measurement unit in Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            # Validate unit data
            unit = UnitUpdate(**unit_data)

            updates = _unit_update_to_api_data(unit)
            current = await client.get_unit(unit_id)
            api_data = _merge_resource_update(
                current,
                updates,
                [
                    "name",
                    "pluralName",
                    "description",
                    "extras",
                    "fraction",
                    "abbreviation",
                    "pluralAbbreviation",
                    "useAbbreviation",
                    "aliases",
                    "standardQuantity",
                    "standardUnit",
                ],
            )

            response = await client.update_unit(unit_id, api_data)
            return {"unit": response, "message": "Unit updated successfully"}
        except MealieAPIError as e:
            if "not found" in str(e).lower():
                return {"error": f"Unit not found: {unit_id}"}
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Update unit failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def delete_unit(unit_id: str) -> Dict[str, Any]:
        """Delete a measurement unit from Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            await client.delete_unit(unit_id)
            return {"message": f"Unit {unit_id} deleted successfully"}
        except MealieAPIError as e:
            if "not found" in str(e).lower():
                return {"error": f"Unit not found: {unit_id}"}
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Delete unit failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def merge_units(merge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge one unit into another (consolidate duplicates)."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            merge = UnitMerge(**merge_data)

            response = await client.merge_units(merge.from_unit_id, merge.to_unit_id)
            return {
                "message": f"Unit {merge.from_unit_id} merged into {merge.to_unit_id}",
                "result": response,
            }
        except Exception as e:
            logger.error(f"Merge units failed: {e}")
            return {"error": str(e)}


# Export all tools for the MCP server
__all__ = [
    'setup_ingredient_tools',
    'FoodSearchFilters',
    'FoodCreate',
    'FoodUpdate',
    'FoodMerge',
    'UnitMerge',
    'UnitCreate',
    'UnitUpdate'
]
