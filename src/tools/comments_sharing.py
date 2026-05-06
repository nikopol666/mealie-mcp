"""MCP tools for Mealie comments and shared recipe records."""

from __future__ import annotations

from typing import Any, Dict, Optional

from mealie_client import MealieAPIError


def setup_comments_sharing_tools(mcp_server, client_provider):
    """Register comment and shared recipe management tools."""

    @mcp_server.tool()
    async def list_comments(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List comments with optional Mealie filters."""
        try:
            return {"comments": await client_provider().get("/api/comments", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_comment(comment_id: str) -> Dict[str, Any]:
        """Get one comment by ID."""
        try:
            return {"comment": await client_provider().get(f"/api/comments/{comment_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_comment(comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comment using a Mealie-native payload."""
        try:
            return {"comment": await client_provider().post("/api/comments", comment_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_comment(comment_id: str, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update one comment by ID."""
        try:
            return {"comment": await client_provider().put(f"/api/comments/{comment_id}", comment_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_comment(comment_id: str) -> Dict[str, Any]:
        """Delete one comment by ID."""
        try:
            await client_provider().delete(f"/api/comments/{comment_id}")
            return {"message": "Comment deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_shared_recipe_records(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List shared recipe records."""
        try:
            return {"shared_recipes": await client_provider().get("/api/shared/recipes", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_shared_recipe_record(shared_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shared recipe record using a Mealie-native payload."""
        try:
            return {"shared_recipe": await client_provider().post("/api/shared/recipes", shared_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_shared_recipe_record(shared_recipe_id: str) -> Dict[str, Any]:
        """Get one shared recipe record by ID."""
        try:
            return {"shared_recipe": await client_provider().get(f"/api/shared/recipes/{shared_recipe_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_shared_recipe_record(shared_recipe_id: str) -> Dict[str, Any]:
        """Delete one shared recipe record by ID."""
        try:
            await client_provider().delete(f"/api/shared/recipes/{shared_recipe_id}")
            return {"message": "Shared recipe record deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}
