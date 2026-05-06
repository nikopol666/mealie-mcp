"""Tags and Categories management tools for Mealie MCP server.

This module provides comprehensive tag and category management functionality through MCP tools
that interface with the Mealie API. Tags and categories help organize recipes for better
discoverability and filtering. All tools include proper error handling, input validation
using Pydantic models, and async operations.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from mealie_client import MealieClient, MealieAPIError

logger = logging.getLogger(__name__)


def _collection_items(response: Any) -> List[Any]:
    """Normalize Mealie collection responses that may be paginated or plain lists."""
    if isinstance(response, dict):
        return response.get("items", [])
    if isinstance(response, list):
        return response
    return []


class TagCreate(BaseModel):
    """Model for creating a new tag."""

    name: str = Field(
        description="Tag name",
        min_length=1,
        max_length=100
    )
    slug: Optional[str] = Field(
        default=None,
        description="URL-friendly slug (auto-generated if not provided)",
        max_length=100
    )


class TagUpdate(BaseModel):
    """Model for updating an existing tag."""

    name: Optional[str] = Field(
        default=None,
        description="Tag name",
        min_length=1,
        max_length=100
    )
    slug: Optional[str] = Field(
        default=None,
        description="URL-friendly slug",
        max_length=100
    )


class CategoryCreate(BaseModel):
    """Model for creating a new category."""

    name: str = Field(
        description="Category name",
        min_length=1,
        max_length=100
    )
    slug: Optional[str] = Field(
        default=None,
        description="URL-friendly slug (auto-generated if not provided)",
        max_length=100
    )


class CategoryUpdate(BaseModel):
    """Model for updating an existing category."""

    name: Optional[str] = Field(
        default=None,
        description="Category name",
        min_length=1,
        max_length=100
    )
    slug: Optional[str] = Field(
        default=None,
        description="URL-friendly slug",
        max_length=100
    )


class RecipeToolCreate(BaseModel):
    """Model for creating or updating a Mealie recipe tool/utensil."""

    name: str = Field(
        description="Recipe tool name",
        min_length=1,
        max_length=100
    )
    householdsWithTool: Optional[List[str]] = Field(default_factory=list)


def setup_tag_category_tools(mcp_server, client_provider):
    """Setup tag and category management tools with the main MCP server."""

    # ===== TAG TOOLS =====

    @mcp_server.tool()
    async def list_tags() -> Dict[str, Any]:
        """List all recipe tags."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get_tags()
            return {"tags": _collection_items(response)}
        except Exception as e:
            logger.error(f"List tags failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_tag(tag_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific tag by ID or slug."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            tag = await client.get_tag(tag_id)
            return {"tag": tag}
        except MealieAPIError as e:
            if "not found" in str(e).lower():
                return {"error": f"Tag not found: {tag_id}"}
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Get tag failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def create_tag(tag_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new recipe tag in Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            # Validate tag data
            tag = TagCreate(**tag_data)

            api_data = {"name": tag.name}

            response = await client.create_tag(api_data)
            return {"tag": response, "message": "Tag created successfully"}
        except Exception as e:
            logger.error(f"Create tag failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_tag(tag_id: str, tag_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing recipe tag in Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            # Validate tag data
            tag = TagUpdate(**tag_data)

            api_data = {}
            if tag.name is not None:
                api_data["name"] = tag.name

            response = await client.update_tag(tag_id, api_data)
            return {"tag": response, "message": "Tag updated successfully"}
        except MealieAPIError as e:
            if "not found" in str(e).lower():
                return {"error": f"Tag not found: {tag_id}"}
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Update tag failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def delete_tag(tag_id: str) -> Dict[str, Any]:
        """Delete a recipe tag from Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            await client.delete_tag(tag_id)
            return {"message": f"Tag {tag_id} deleted successfully"}
        except MealieAPIError as e:
            if "not found" in str(e).lower():
                return {"error": f"Tag not found: {tag_id}"}
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Delete tag failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_tag_by_slug(tag_slug: str) -> Dict[str, Any]:
        """Get detailed information about a specific tag by slug."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            tag = await client.get(f"/api/organizers/tags/slug/{tag_slug}")
            return {"tag": tag}
        except Exception as e:
            logger.error(f"Get tag by slug failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def list_empty_tags() -> Dict[str, Any]:
        """List tags that are not assigned to recipes."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get("/api/organizers/tags/empty")
            return {"tags": _collection_items(response)}
        except Exception as e:
            logger.error(f"List empty tags failed: {e}")
            return {"error": str(e)}

    # ===== CATEGORY TOOLS =====

    @mcp_server.tool()
    async def list_categories() -> Dict[str, Any]:
        """List all recipe categories."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get_categories()
            return {"categories": _collection_items(response)}
        except Exception as e:
            logger.error(f"List categories failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_category(category_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific category by ID or slug."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            category = await client.get_category(category_id)
            return {"category": category}
        except MealieAPIError as e:
            if "not found" in str(e).lower():
                return {"error": f"Category not found: {category_id}"}
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Get category failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def create_category(category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new recipe category in Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            # Validate category data
            category = CategoryCreate(**category_data)

            api_data = {"name": category.name}

            response = await client.create_category(api_data)
            return {"category": response, "message": "Category created successfully"}
        except Exception as e:
            logger.error(f"Create category failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_category(category_id: str, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing recipe category in Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            # Validate category data
            category = CategoryUpdate(**category_data)

            api_data = {}
            if category.name is not None:
                api_data["name"] = category.name

            response = await client.update_category(category_id, api_data)
            return {"category": response, "message": "Category updated successfully"}
        except MealieAPIError as e:
            if "not found" in str(e).lower():
                return {"error": f"Category not found: {category_id}"}
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Update category failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def delete_category(category_id: str) -> Dict[str, Any]:
        """Delete a recipe category from Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            await client.delete_category(category_id)
            return {"message": f"Category {category_id} deleted successfully"}
        except MealieAPIError as e:
            if "not found" in str(e).lower():
                return {"error": f"Category not found: {category_id}"}
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Delete category failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_category_by_slug(category_slug: str) -> Dict[str, Any]:
        """Get detailed information about a specific category by slug."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            category = await client.get(f"/api/organizers/categories/slug/{category_slug}")
            return {"category": category}
        except Exception as e:
            logger.error(f"Get category by slug failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def list_empty_categories() -> Dict[str, Any]:
        """List categories that are not assigned to recipes."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get("/api/organizers/categories/empty")
            return {"categories": _collection_items(response)}
        except Exception as e:
            logger.error(f"List empty categories failed: {e}")
            return {"error": str(e)}

    # ===== RECIPE TOOL / UTENSIL TOOLS =====

    @mcp_server.tool()
    async def list_recipe_tools(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List Mealie recipe tools/utensils."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get("/api/organizers/tools", filters or None)
            return {
                "tools": response.get("items", []),
                "total": response.get("total", 0),
                "page": response.get("page", 1),
                "per_page": response.get("per_page", response.get("perPage")),
            }
        except Exception as e:
            logger.error(f"List recipe tools failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_recipe_tool(tool_id: str) -> Dict[str, Any]:
        """Get a Mealie recipe tool/utensil by ID."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            tool = await client.get(f"/api/organizers/tools/{tool_id}")
            return {"tool": tool}
        except Exception as e:
            logger.error(f"Get recipe tool failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_recipe_tool_by_slug(tool_slug: str) -> Dict[str, Any]:
        """Get a Mealie recipe tool/utensil by slug."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            tool = await client.get(f"/api/organizers/tools/slug/{tool_slug}")
            return {"tool": tool}
        except Exception as e:
            logger.error(f"Get recipe tool by slug failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def create_recipe_tool(tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Mealie recipe tool/utensil."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            tool = RecipeToolCreate(**tool_data)
            api_data = {
                "name": tool.name,
                "householdsWithTool": tool.householdsWithTool or [],
            }
            response = await client.post("/api/organizers/tools", api_data)
            return {"tool": response, "message": "Recipe tool created successfully"}
        except Exception as e:
            logger.error(f"Create recipe tool failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_recipe_tool(tool_id: str, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a Mealie recipe tool/utensil."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            tool = RecipeToolCreate(**tool_data)
            api_data = {
                "name": tool.name,
                "householdsWithTool": tool.householdsWithTool or [],
            }
            response = await client.put(f"/api/organizers/tools/{tool_id}", api_data)
            return {"tool": response, "message": "Recipe tool updated successfully"}
        except Exception as e:
            logger.error(f"Update recipe tool failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def delete_recipe_tool(tool_id: str) -> Dict[str, Any]:
        """Delete a Mealie recipe tool/utensil."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            await client.delete(f"/api/organizers/tools/{tool_id}")
            return {"message": f"Recipe tool {tool_id} deleted successfully"}
        except Exception as e:
            logger.error(f"Delete recipe tool failed: {e}")
            return {"error": str(e)}


# Export all tools for the MCP server
__all__ = [
    'setup_tag_category_tools',
    'TagCreate',
    'TagUpdate',
    'CategoryCreate',
    'CategoryUpdate',
    'RecipeToolCreate',
]
