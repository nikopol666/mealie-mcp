"""MCP tools for Mealie admin endpoints.

These tools require the configured Mealie API token to belong to an admin user.
"""

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


def setup_admin_tools(mcp_server, client_provider):
    """Register admin-only Mealie tools."""

    @mcp_server.tool()
    async def get_admin_about() -> Dict[str, Any]:
        """Get admin app information."""
        try:
            return {"about": await client_provider().get("/api/admin/about")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def check_admin_about() -> Dict[str, Any]:
        """Run the admin about/check endpoint."""
        try:
            return {"check": await client_provider().get("/api/admin/about/check")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_admin_statistics() -> Dict[str, Any]:
        """Get admin statistics."""
        try:
            return {"statistics": await client_provider().get("/api/admin/about/statistics")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_admin_backups() -> Dict[str, Any]:
        """List Mealie admin backups."""
        try:
            return {"backups": await client_provider().get("/api/admin/backups")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_admin_backup(backup_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a Mealie admin backup."""
        try:
            return {"backup": await client_provider().post("/api/admin/backups", backup_data or {})}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def download_admin_backup(file_name: str) -> Dict[str, Any]:
        """Download one admin backup as base64-safe data."""
        try:
            return await client_provider().get_raw(f"/api/admin/backups/{file_name}")
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def upload_admin_backup(file_base64: str, filename: str = "backup.zip") -> Dict[str, Any]:
        """Upload a Mealie backup archive from base64 data."""
        try:
            archive_bytes = _decode_base64(file_base64)
            response = await client_provider().post_multipart(
                "/api/admin/backups/upload",
                files={"archive": (filename, archive_bytes, "application/zip")},
            )
            return {"backup": response}
        except ValueError as e:
            return {"error": str(e)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_admin_backup(file_name: str) -> Dict[str, Any]:
        """Delete one admin backup by file name."""
        try:
            await client_provider().delete(f"/api/admin/backups/{file_name}")
            return {"message": "Admin backup deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def restore_admin_backup(file_name: str, restore_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Restore one admin backup by file name."""
        try:
            endpoint = f"/api/admin/backups/{file_name}/restore"
            return {"result": await client_provider().post(endpoint, restore_data or {})}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def debug_admin_openai(debug_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run Mealie's admin OpenAI debug endpoint."""
        try:
            return {"result": await client_provider().post("/api/admin/debug/openai", debug_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_admin_email() -> Dict[str, Any]:
        """Get Mealie admin email settings."""
        try:
            return {"email": await client_provider().get("/api/admin/email")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_admin_email(email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update Mealie admin email settings."""
        try:
            return {"email": await client_provider().post("/api/admin/email", email_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_admin_groups(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List admin-visible groups."""
        try:
            return {"groups": await client_provider().get("/api/admin/groups", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_admin_group(group_id: str) -> Dict[str, Any]:
        """Get one admin-visible group by ID."""
        try:
            return {"group": await client_provider().get(f"/api/admin/groups/{group_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_admin_group(group_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a group through the admin API."""
        try:
            return {"group": await client_provider().post("/api/admin/groups", group_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_admin_group(group_id: str, group_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update one admin-visible group by ID."""
        try:
            return {"group": await client_provider().put(f"/api/admin/groups/{group_id}", group_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_admin_group(group_id: str) -> Dict[str, Any]:
        """Delete one admin-visible group by ID."""
        try:
            await client_provider().delete(f"/api/admin/groups/{group_id}")
            return {"message": "Admin group deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_admin_households(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List admin-visible households."""
        try:
            return {"households": await client_provider().get("/api/admin/households", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_admin_household(household_id: str) -> Dict[str, Any]:
        """Get one admin-visible household by ID."""
        try:
            return {"household": await client_provider().get(f"/api/admin/households/{household_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_admin_household(household_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a household through the admin API."""
        try:
            return {"household": await client_provider().post("/api/admin/households", household_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_admin_household(household_id: str, household_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update one admin-visible household by ID."""
        try:
            return {"household": await client_provider().put(f"/api/admin/households/{household_id}", household_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_admin_household(household_id: str) -> Dict[str, Any]:
        """Delete one admin-visible household by ID."""
        try:
            await client_provider().delete(f"/api/admin/households/{household_id}")
            return {"message": "Admin household deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_admin_users(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List admin-visible users."""
        try:
            return {"users": await client_provider().get("/api/admin/users", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_admin_user(user_id: str) -> Dict[str, Any]:
        """Get one admin-visible user by ID."""
        try:
            return {"user": await client_provider().get(f"/api/admin/users/{user_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_admin_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a user through the admin API."""
        try:
            return {"user": await client_provider().post("/api/admin/users", user_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_admin_user(user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update one admin-visible user by ID."""
        try:
            return {"user": await client_provider().put(f"/api/admin/users/{user_id}", user_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_admin_user(user_id: str) -> Dict[str, Any]:
        """Delete one admin-visible user by ID."""
        try:
            await client_provider().delete(f"/api/admin/users/{user_id}")
            return {"message": "Admin user deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_admin_password_reset_token(reset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a password reset token through the admin API."""
        try:
            return {"reset_token": await client_provider().post("/api/admin/users/password-reset-token", reset_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def unlock_admin_users(unlock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Unlock users through the admin API."""
        try:
            return {"result": await client_provider().post("/api/admin/users/unlock", unlock_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_admin_maintenance() -> Dict[str, Any]:
        """Get admin maintenance status."""
        try:
            return {"maintenance": await client_provider().get("/api/admin/maintenance")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_admin_maintenance_storage() -> Dict[str, Any]:
        """Get admin maintenance storage information."""
        try:
            return {"storage": await client_provider().get("/api/admin/maintenance/storage")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def clean_admin_images(clean_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run admin image cleanup."""
        try:
            return {"result": await client_provider().post("/api/admin/maintenance/clean/images", clean_data or {})}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def clean_admin_recipe_folders(clean_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run admin recipe folder cleanup."""
        try:
            return {"result": await client_provider().post("/api/admin/maintenance/clean/recipe-folders", clean_data or {})}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def clean_admin_temp(clean_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run admin temporary file cleanup."""
        try:
            return {"result": await client_provider().post("/api/admin/maintenance/clean/temp", clean_data or {})}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}
