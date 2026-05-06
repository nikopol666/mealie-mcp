"""MCP tools for Mealie group-scoped resources."""

from __future__ import annotations

from typing import Any, Dict, Optional

from mealie_client import MealieAPIError


def setup_group_tools(mcp_server, client_provider):
    """Register group, label, member, report, seeder, and storage tools."""

    @mcp_server.tool()
    async def get_group_self() -> Dict[str, Any]:
        """Get the current group."""
        try:
            return {"group": await client_provider().get("/api/groups/self")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_group_households() -> Dict[str, Any]:
        """List households in the current group."""
        try:
            return {"households": await client_provider().get("/api/groups/households")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_group_household(household_slug: str) -> Dict[str, Any]:
        """Get one group household by slug."""
        try:
            return {"household": await client_provider().get(f"/api/groups/households/{household_slug}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_group_members() -> Dict[str, Any]:
        """List members in the current group."""
        try:
            return {"members": await client_provider().get("/api/groups/members")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_group_member(username_or_id: str) -> Dict[str, Any]:
        """Get one group member by username or ID."""
        try:
            return {"member": await client_provider().get(f"/api/groups/members/{username_or_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_group_preferences() -> Dict[str, Any]:
        """Get current group preferences."""
        try:
            return {"preferences": await client_provider().get("/api/groups/preferences")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_group_preferences(preferences_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update current group preferences."""
        try:
            return {"preferences": await client_provider().put("/api/groups/preferences", preferences_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_group_storage() -> Dict[str, Any]:
        """Get current group storage information."""
        try:
            return {"storage": await client_provider().get("/api/groups/storage")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_group_labels(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List group labels."""
        try:
            return {"labels": await client_provider().get("/api/groups/labels", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_group_label(label_id: str) -> Dict[str, Any]:
        """Get one group label by ID."""
        try:
            return {"label": await client_provider().get(f"/api/groups/labels/{label_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_group_label(label_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a group label."""
        try:
            return {"label": await client_provider().post("/api/groups/labels", label_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_group_label(label_id: str, label_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update one group label by ID."""
        try:
            return {"label": await client_provider().put(f"/api/groups/labels/{label_id}", label_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_group_label(label_id: str) -> Dict[str, Any]:
        """Delete one group label by ID."""
        try:
            await client_provider().delete(f"/api/groups/labels/{label_id}")
            return {"message": "Group label deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_group_reports(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List group reports."""
        try:
            return {"reports": await client_provider().get("/api/groups/reports", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_group_report(report_id: str) -> Dict[str, Any]:
        """Get one group report by ID."""
        try:
            return {"report": await client_provider().get(f"/api/groups/reports/{report_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_group_report(report_id: str) -> Dict[str, Any]:
        """Delete one group report by ID."""
        try:
            await client_provider().delete(f"/api/groups/reports/{report_id}")
            return {"message": "Group report deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_group_migration(migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a group migration using a Mealie-native payload."""
        try:
            return {"migration": await client_provider().post("/api/groups/migrations", migration_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def seed_group_foods(seed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the group foods seeder using a Mealie-native payload."""
        try:
            return {"result": await client_provider().post("/api/groups/seeders/foods", seed_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def seed_group_labels(seed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the group labels seeder using a Mealie-native payload."""
        try:
            return {"result": await client_provider().post("/api/groups/seeders/labels", seed_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def seed_group_units(seed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the group units seeder using a Mealie-native payload."""
        try:
            return {"result": await client_provider().post("/api/groups/seeders/units", seed_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}
