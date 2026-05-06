"""Read-only MCP tools for Mealie explore endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

from mealie_client import MealieAPIError


def setup_explore_tools(mcp_server, client_provider):
    """Register read-only public explore tools."""

    @mcp_server.tool()
    async def explore_group_recipes(group_slug: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List public/explore recipes for a group."""
        try:
            return {"recipes": await client_provider().get(f"/api/explore/groups/{group_slug}/recipes", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_recipe(group_slug: str, recipe_slug: str) -> Dict[str, Any]:
        """Get one public/explore recipe for a group."""
        try:
            return {"recipe": await client_provider().get(f"/api/explore/groups/{group_slug}/recipes/{recipe_slug}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_recipe_suggestions(group_slug: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get public/explore recipe suggestions for a group."""
        try:
            endpoint = f"/api/explore/groups/{group_slug}/recipes/suggestions"
            return {"suggestions": await client_provider().get(endpoint, filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_cookbooks(group_slug: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List public/explore cookbooks for a group."""
        try:
            return {"cookbooks": await client_provider().get(f"/api/explore/groups/{group_slug}/cookbooks", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_cookbook(group_slug: str, cookbook_id: str) -> Dict[str, Any]:
        """Get one public/explore cookbook for a group."""
        try:
            return {"cookbook": await client_provider().get(f"/api/explore/groups/{group_slug}/cookbooks/{cookbook_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_households(group_slug: str) -> Dict[str, Any]:
        """List public/explore households for a group."""
        try:
            return {"households": await client_provider().get(f"/api/explore/groups/{group_slug}/households")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_household(group_slug: str, household_slug: str) -> Dict[str, Any]:
        """Get one public/explore household for a group."""
        try:
            endpoint = f"/api/explore/groups/{group_slug}/households/{household_slug}"
            return {"household": await client_provider().get(endpoint)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_foods(group_slug: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List public/explore foods for a group."""
        try:
            return {"foods": await client_provider().get(f"/api/explore/groups/{group_slug}/foods", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_food(group_slug: str, food_id: str) -> Dict[str, Any]:
        """Get one public/explore food for a group."""
        try:
            return {"food": await client_provider().get(f"/api/explore/groups/{group_slug}/foods/{food_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_tags(group_slug: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List public/explore tags for a group."""
        try:
            endpoint = f"/api/explore/groups/{group_slug}/organizers/tags"
            return {"tags": await client_provider().get(endpoint, filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_tag(group_slug: str, tag_id: str) -> Dict[str, Any]:
        """Get one public/explore tag for a group."""
        try:
            endpoint = f"/api/explore/groups/{group_slug}/organizers/tags/{tag_id}"
            return {"tag": await client_provider().get(endpoint)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_categories(group_slug: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List public/explore categories for a group."""
        try:
            endpoint = f"/api/explore/groups/{group_slug}/organizers/categories"
            return {"categories": await client_provider().get(endpoint, filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_category(group_slug: str, category_id: str) -> Dict[str, Any]:
        """Get one public/explore category for a group."""
        try:
            endpoint = f"/api/explore/groups/{group_slug}/organizers/categories/{category_id}"
            return {"category": await client_provider().get(endpoint)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_tools(group_slug: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List public/explore recipe tools for a group."""
        try:
            endpoint = f"/api/explore/groups/{group_slug}/organizers/tools"
            return {"tools": await client_provider().get(endpoint, filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def explore_group_tool(group_slug: str, tool_id: str) -> Dict[str, Any]:
        """Get one public/explore recipe tool for a group."""
        try:
            endpoint = f"/api/explore/groups/{group_slug}/organizers/tools/{tool_id}"
            return {"tool": await client_provider().get(endpoint)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}
