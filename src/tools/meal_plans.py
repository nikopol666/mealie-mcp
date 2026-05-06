"""Meal planning tools for Mealie MCP server.

This module provides comprehensive meal planning functionality through MCP tools
that interface with the Mealie API. All tools include proper error handling,
input validation using Pydantic models, and async operations for meal planning,
weekly scheduling, and meal suggestions.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date, timedelta
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

from mealie_client import MealieClient, MealieAPIError

logger = logging.getLogger(__name__)


class MealType(str, Enum):
    """Supported meal types."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SIDE = "side"
    SNACK = "snack"
    DRINK = "drink"
    DESSERT = "dessert"


class MealPlanFilters(BaseModel):
    """Filters for meal plan operations."""
    
    start_date: Optional[str] = Field(
        default=None,
        description="Start date for meal plan search (YYYY-MM-DD format)"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date for meal plan search (YYYY-MM-DD format)"
    )
    meal_type: Optional[MealType] = Field(
        default=None,
        description="Filter by specific meal type"
    )
    recipe_id: Optional[str] = Field(
        default=None,
        description="Filter by specific recipe ID"
    )
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        """Validate date format."""
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        """Ensure end_date is after start_date."""
        if v is not None and info.data.get('start_date') is not None:
            start = datetime.strptime(info.data['start_date'], '%Y-%m-%d')
            end = datetime.strptime(v, '%Y-%m-%d')
            if end < start:
                raise ValueError('end_date must be after start_date')
        return v


class MealPlanEntry(BaseModel):
    """Model for meal plan entry data."""
    
    date: str = Field(
        description="Date for the meal plan (YYYY-MM-DD format)"
    )
    meal_type: MealType = Field(
        description="Type of meal (breakfast, lunch, dinner, snack)"
    )
    recipe_id: Optional[str] = Field(
        default=None,
        description="ID of the recipe for this meal"
    )
    title: Optional[str] = Field(
        default=None,
        description="Custom title for the meal (if not using a recipe)"
    )
    text: Optional[str] = Field(
        default=None,
        description="Additional notes or description for the meal"
    )
    
    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v):
        """Validate date format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @field_validator('recipe_id')
    @classmethod
    def validate_recipe_id(cls, v):
        """Validate recipe ID format if provided."""
        if v is not None:
            try:
                UUID(v)
            except ValueError:
                raise ValueError('recipe_id must be a valid UUID')
        return v
    
    @model_validator(mode='after')
    def validate_title_or_recipe(self):
        """Ensure either title or recipe_id is provided."""
        if self.title is None and self.recipe_id is None:
            raise ValueError('Either title or recipe_id must be provided')
        return self


class RandomMealPlanEntry(BaseModel):
    """Model for creating a random meal plan entry."""

    date: str = Field(description="Date for the meal plan (YYYY-MM-DD format)")
    meal_type: MealType = Field(
        default=MealType.DINNER,
        description="Type of meal to generate"
    )

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v


class MealPlanRule(BaseModel):
    """Flexible meal-plan rule payload."""

    day: str = Field(default="unset")
    entry_type: str = Field(default="unset")
    query_filter_string: str = Field(default="")


def _normalize_meal_plan_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Accept both Python-style and Mealie API-style filter keys."""
    aliases = {
        "startDate": "start_date",
        "endDate": "end_date",
        "mealType": "meal_type",
        "recipeId": "recipe_id",
    }
    return {aliases.get(key, key): value for key, value in filters.items()}


def _normalize_meal_plan_entry(entry_data: Dict[str, Any]) -> Dict[str, Any]:
    """Accept both Python-style and Mealie API-style meal plan keys."""
    aliases = {
        "entryType": "meal_type",
        "recipeId": "recipe_id",
    }
    return {aliases.get(key, key): value for key, value in entry_data.items()}


def _meal_plan_entry_to_api_data(entry: MealPlanEntry) -> Dict[str, Any]:
    """Convert validated entry data to Mealie's API shape."""
    return {
        "date": entry.date,
        "entryType": entry.meal_type.value,
        "title": entry.title or "",
        "text": entry.text or "",
        "recipeId": entry.recipe_id,
    }


def _random_meal_plan_entry_to_api_data(entry: RandomMealPlanEntry) -> Dict[str, Any]:
    return {
        "date": entry.date,
        "entryType": entry.meal_type.value,
    }


def _meal_plan_rule_to_api_data(rule: MealPlanRule) -> Dict[str, Any]:
    return {
        "day": rule.day,
        "entryType": rule.entry_type,
        "queryFilterString": rule.query_filter_string,
    }


def _meal_plan_update_to_api_data(current: Dict[str, Any], entry: MealPlanEntry) -> Dict[str, Any]:
    return {
        **{
            "id": current.get("id"),
            "groupId": current.get("groupId"),
            "userId": current.get("userId"),
        },
        **_meal_plan_entry_to_api_data(entry),
    }


def setup_meal_plan_tools(mcp_server, client_provider):
    """Setup meal planning tools with the main MCP server."""
    
    @mcp_server.tool()
    async def list_meal_plans(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List meal plans with optional filtering."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}
            
            query_params = {}
            if filters:
                parsed_filters = MealPlanFilters(**_normalize_meal_plan_filters(filters))
                if parsed_filters.start_date:
                    query_params["start_date"] = parsed_filters.start_date
                if parsed_filters.end_date:
                    query_params["end_date"] = parsed_filters.end_date

            response = await client.get("/api/households/mealplans", query_params)
            items = response.get("items", [])

            if filters:
                parsed_filters = MealPlanFilters(**_normalize_meal_plan_filters(filters))
                if parsed_filters.meal_type:
                    items = [
                        item for item in items
                        if item.get("entryType") == parsed_filters.meal_type.value
                    ]
                if parsed_filters.recipe_id:
                    items = [
                        item for item in items
                        if item.get("recipeId") == parsed_filters.recipe_id
                    ]

            return {"meal_plans": items}
        except Exception as e:
            logger.error(f"List meal plans failed: {e}")
            return {"error": str(e)}
    
    @mcp_server.tool()
    async def get_meal_plan(meal_plan_id: str) -> Dict[str, Any]:
        """Get specific meal plan details."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}
            
            meal_plan = await client.get(f"/api/households/mealplans/{meal_plan_id}")
            return {"meal_plan": meal_plan}
        except Exception as e:
            logger.error(f"Get meal plan failed: {e}")
            return {"error": str(e)}
    
    @mcp_server.tool()
    async def create_meal_plan_entry(entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new meal plan entry."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}
            
            # Validate the entry data
            entry = MealPlanEntry(**_normalize_meal_plan_entry(entry_data))
            
            api_data = _meal_plan_entry_to_api_data(entry)
            
            response = await client.post("/api/households/mealplans", api_data)
            return {"meal_plan": response, "message": "Meal plan entry created successfully"}
        except Exception as e:
            logger.error(f"Create meal plan entry failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_meal_plan_entry(meal_plan_id: str, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing meal plan entry."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            # Validate the entry data
            entry = MealPlanEntry(**_normalize_meal_plan_entry(entry_data))

            current = await client.get(f"/api/households/mealplans/{meal_plan_id}")
            api_data = _meal_plan_update_to_api_data(current, entry)

            response = await client.put(f"/api/households/mealplans/{meal_plan_id}", api_data)
            return {"meal_plan": response, "message": "Meal plan entry updated successfully"}
        except Exception as e:
            logger.error(f"Update meal plan entry failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def delete_meal_plan_entry(meal_plan_id: str) -> Dict[str, Any]:
        """Delete a meal plan entry."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            await client.delete(f"/api/households/mealplans/{meal_plan_id}")
            return {"message": f"Meal plan entry {meal_plan_id} deleted successfully"}
        except Exception as e:
            logger.error(f"Delete meal plan entry failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_todays_meal_plans() -> Dict[str, Any]:
        """Get today's meal plans from Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get("/api/households/mealplans/today")
            return {"meal_plans": response.get("items", response)}
        except Exception as e:
            logger.error(f"Get today's meal plans failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def create_random_meal_plan_entry(entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a random meal plan entry for a date and meal type."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            normalized = _normalize_meal_plan_entry(entry_data)
            entry = RandomMealPlanEntry(**normalized)
            response = await client.post(
                "/api/households/mealplans/random",
                _random_meal_plan_entry_to_api_data(entry),
            )
            return {"meal_plan": response, "message": "Random meal plan entry created successfully"}
        except Exception as e:
            logger.error(f"Create random meal plan entry failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def list_meal_plan_rules(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List meal planning rules."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get("/api/households/mealplans/rules", filters or None)
            return {
                "rules": response.get("items", []),
                "total": response.get("total", 0),
                "page": response.get("page", 1),
                "per_page": response.get("per_page", response.get("perPage")),
            }
        except Exception as e:
            logger.error(f"List meal plan rules failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_meal_plan_rule(rule_id: str) -> Dict[str, Any]:
        """Get one meal planning rule."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get(f"/api/households/mealplans/rules/{rule_id}")
            return {"rule": response}
        except Exception as e:
            logger.error(f"Get meal plan rule failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def create_meal_plan_rule(rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a meal planning rule."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            data = {
                "day": rule_data.get("day", "unset"),
                "entry_type": rule_data.get("entry_type", rule_data.get("entryType", "unset")),
                "query_filter_string": rule_data.get(
                    "query_filter_string",
                    rule_data.get("queryFilterString", ""),
                ),
            }
            rule = MealPlanRule(**data)
            response = await client.post("/api/households/mealplans/rules", _meal_plan_rule_to_api_data(rule))
            return {"rule": response, "message": "Meal plan rule created successfully"}
        except Exception as e:
            logger.error(f"Create meal plan rule failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_meal_plan_rule(rule_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a meal planning rule."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            data = {
                "day": rule_data.get("day", "unset"),
                "entry_type": rule_data.get("entry_type", rule_data.get("entryType", "unset")),
                "query_filter_string": rule_data.get(
                    "query_filter_string",
                    rule_data.get("queryFilterString", ""),
                ),
            }
            rule = MealPlanRule(**data)
            response = await client.put(f"/api/households/mealplans/rules/{rule_id}", _meal_plan_rule_to_api_data(rule))
            return {"rule": response, "message": "Meal plan rule updated successfully"}
        except Exception as e:
            logger.error(f"Update meal plan rule failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def delete_meal_plan_rule(rule_id: str) -> Dict[str, Any]:
        """Delete a meal planning rule."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            await client.delete(f"/api/households/mealplans/rules/{rule_id}")
            return {"message": f"Meal plan rule {rule_id} deleted successfully"}
        except Exception as e:
            logger.error(f"Delete meal plan rule failed: {e}")
            return {"error": str(e)}


# Export all tools for the MCP server
__all__ = [
    'setup_meal_plan_tools',
    'MealPlanFilters',
    'MealPlanEntry',
    'RandomMealPlanEntry',
    'MealPlanRule',
    'MealType',
    '_normalize_meal_plan_filters',
    '_normalize_meal_plan_entry',
    '_meal_plan_entry_to_api_data',
    '_random_meal_plan_entry_to_api_data',
    '_meal_plan_rule_to_api_data',
    '_meal_plan_update_to_api_data',
]
