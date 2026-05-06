"""MCP tools for Mealie user-scoped resources."""

from __future__ import annotations

import base64
import binascii
from typing import Any, Dict, Optional

from mealie_client import MealieAPIError


def _decode_base64(encoded: str) -> bytes:
    if "," in encoded and encoded.split(",", 1)[0].startswith("data:"):
        encoded = encoded.split(",", 1)[1]
    try:
        return base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"Invalid base64 data: {exc}") from exc


def setup_user_tools(mcp_server, client_provider):
    """Register user profile, token, favorite, rating, and image tools."""

    @mcp_server.tool()
    async def get_self_user() -> Dict[str, Any]:
        """Get the current user."""
        try:
            return {"user": await client_provider().get("/api/users/self")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_user(user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update one user by ID."""
        try:
            return {"user": await client_provider().put(f"/api/users/{user_id}", user_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_user_password(password_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update the current user's password using a Mealie-native payload."""
        try:
            return {"result": await client_provider().put("/api/users/password", password_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_user_api_token(token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Mealie API token for the current user."""
        try:
            return {"api_token": await client_provider().post("/api/users/api-tokens", token_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_user_api_token(token_id: str) -> Dict[str, Any]:
        """Delete one Mealie API token by ID."""
        try:
            await client_provider().delete(f"/api/users/api-tokens/{token_id}")
            return {"message": "User API token deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_self_favorites(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List the current user's favorite recipes."""
        try:
            return {"favorites": await client_provider().get("/api/users/self/favorites", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_user_favorites(user_id: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List one user's favorite recipes."""
        try:
            return {"favorites": await client_provider().get(f"/api/users/{user_id}/favorites", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def add_user_favorite(user_id: str, recipe_slug: str) -> Dict[str, Any]:
        """Add one recipe to a user's favorites."""
        try:
            return {"favorite": await client_provider().post(f"/api/users/{user_id}/favorites/{recipe_slug}", {})}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_user_favorite(user_id: str, recipe_slug: str) -> Dict[str, Any]:
        """Remove one recipe from a user's favorites."""
        try:
            await client_provider().delete(f"/api/users/{user_id}/favorites/{recipe_slug}")
            return {"message": "User favorite deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_self_ratings(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List the current user's recipe ratings."""
        try:
            return {"ratings": await client_provider().get("/api/users/self/ratings", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_self_rating(recipe_id: str) -> Dict[str, Any]:
        """Get the current user's rating for one recipe."""
        try:
            return {"rating": await client_provider().get(f"/api/users/self/ratings/{recipe_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_user_ratings(user_id: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List one user's recipe ratings."""
        try:
            return {"ratings": await client_provider().get(f"/api/users/{user_id}/ratings", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def set_user_rating(user_id: str, recipe_slug: str, rating_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update one user's rating for a recipe."""
        try:
            return {"rating": await client_provider().post(f"/api/users/{user_id}/ratings/{recipe_slug}", rating_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def upload_user_image(user_id: str, image_base64: str, extension: str = "png") -> Dict[str, Any]:
        """Upload one user's image from base64 data."""
        try:
            clean_extension = extension.lower().lstrip(".")
            media_type = "image/jpeg" if clean_extension in {"jpg", "jpeg"} else f"image/{clean_extension}"
            image_bytes = _decode_base64(image_base64)
            response = await client_provider().post_multipart(
                f"/api/users/{user_id}/image",
                data={"extension": clean_extension},
                files={"image": (f"user-image.{clean_extension}", image_bytes, media_type)},
            )
            return {"image": response}
        except ValueError as e:
            return {"error": str(e)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}
