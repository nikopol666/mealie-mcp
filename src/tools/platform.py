"""MCP tools for Mealie app info, parser, and media endpoints."""

from __future__ import annotations

from typing import Any, Dict, List

from mealie_client import MealieAPIError


def setup_platform_tools(mcp_server, client_provider):
    """Register app, parser, and media tools."""

    @mcp_server.tool()
    async def get_app_about() -> Dict[str, Any]:
        """Get public Mealie app/version information."""
        try:
            return {"about": await client_provider().get("/api/app/about")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_app_startup_info() -> Dict[str, Any]:
        """Get Mealie startup information exposed by the app endpoint."""
        try:
            return {"startup_info": await client_provider().get("/api/app/about/startup-info")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_app_theme() -> Dict[str, Any]:
        """Get Mealie theme information."""
        try:
            return {"theme": await client_provider().get("/api/app/about/theme")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def parse_ingredient(ingredient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse one ingredient line using Mealie's parser endpoint."""
        try:
            return {"parsed": await client_provider().post("/api/parser/ingredient", ingredient_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def parse_ingredients(ingredients_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse multiple ingredient lines using Mealie's parser endpoint."""
        try:
            return {"parsed": await client_provider().post("/api/parser/ingredients", ingredients_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def download_url(url: str) -> Dict[str, Any]:
        """Download a URL through Mealie's utility download endpoint."""
        try:
            return await client_provider().get_raw("/api/utils/download", params={"url": url})
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_media_docker_validation_text() -> Dict[str, Any]:
        """Get Mealie's Docker media validation text file."""
        try:
            return await client_provider().get_raw("/api/media/docker/validate.txt")
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_recipe_asset_media(recipe_id: str, file_name: str) -> Dict[str, Any]:
        """Download a recipe asset file as base64-safe data."""
        try:
            return await client_provider().get_raw(f"/api/media/recipes/{recipe_id}/assets/{file_name}")
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_recipe_image_media(recipe_id: str, file_name: str) -> Dict[str, Any]:
        """Download a recipe image file as base64-safe data."""
        try:
            return await client_provider().get_raw(f"/api/media/recipes/{recipe_id}/images/{file_name}")
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_recipe_timeline_image_media(recipe_id: str, timeline_event_id: str, file_name: str) -> Dict[str, Any]:
        """Download a recipe timeline image file as base64-safe data."""
        try:
            endpoint = f"/api/media/recipes/{recipe_id}/images/timeline/{timeline_event_id}/{file_name}"
            return await client_provider().get_raw(endpoint)
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_user_image_media(user_id: str, file_name: str) -> Dict[str, Any]:
        """Download a user image file as base64-safe data."""
        try:
            return await client_provider().get_raw(f"/api/media/users/{user_id}/{file_name}")
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}
