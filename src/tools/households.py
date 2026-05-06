"""MCP tools for Mealie household-scoped resources beyond meals/shopping."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mealie_client import MealieAPIError


def setup_household_tools(mcp_server, client_provider):
    """Register household, cookbook, notification, webhook, and action tools."""

    @mcp_server.tool()
    async def get_household_self() -> Dict[str, Any]:
        """Get the current household."""
        try:
            return {"household": await client_provider().get("/api/households/self")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_household_statistics() -> Dict[str, Any]:
        """Get current household statistics."""
        try:
            return {"statistics": await client_provider().get("/api/households/statistics")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_household_members() -> Dict[str, Any]:
        """List current household members."""
        try:
            return {"members": await client_provider().get("/api/households/members")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_household_preferences() -> Dict[str, Any]:
        """Get current household preferences."""
        try:
            return {"preferences": await client_provider().get("/api/households/preferences")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_household_preferences(preferences_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update current household preferences."""
        try:
            return {"preferences": await client_provider().put("/api/households/preferences", preferences_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_household_permissions(permissions_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update current household permissions."""
        try:
            return {"permissions": await client_provider().put("/api/households/permissions", permissions_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_household_recipe_details(recipe_slug: str) -> Dict[str, Any]:
        """Get household-specific details for one recipe."""
        try:
            return {"recipe": await client_provider().get(f"/api/households/self/recipes/{recipe_slug}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_cookbooks(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List household cookbooks."""
        try:
            return {"cookbooks": await client_provider().get("/api/households/cookbooks", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_cookbook(cookbook_id: str) -> Dict[str, Any]:
        """Get one household cookbook by ID."""
        try:
            return {"cookbook": await client_provider().get(f"/api/households/cookbooks/{cookbook_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_cookbook(cookbook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a household cookbook."""
        try:
            return {"cookbook": await client_provider().post("/api/households/cookbooks", cookbook_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_cookbook(cookbook_id: str, cookbook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update one household cookbook by ID."""
        try:
            return {"cookbook": await client_provider().put(f"/api/households/cookbooks/{cookbook_id}", cookbook_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_cookbooks(cookbooks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk update household cookbooks."""
        try:
            return {"cookbooks": await client_provider().put("/api/households/cookbooks", cookbooks)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_cookbook(cookbook_id: str) -> Dict[str, Any]:
        """Delete one household cookbook by ID."""
        try:
            await client_provider().delete(f"/api/households/cookbooks/{cookbook_id}")
            return {"message": "Cookbook deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_household_invitations() -> Dict[str, Any]:
        """List household invitations."""
        try:
            return {"invitations": await client_provider().get("/api/households/invitations")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_household_invitation(invitation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a household invitation."""
        try:
            return {"invitation": await client_provider().post("/api/households/invitations", invitation_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def send_household_invitation_email(invitation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a household invitation email using Mealie's native payload."""
        try:
            return {"result": await client_provider().post("/api/households/invitations/email", invitation_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_household_notifications(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List household event notifications."""
        try:
            return {"notifications": await client_provider().get("/api/households/events/notifications", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_household_notification(notification_id: str) -> Dict[str, Any]:
        """Get one household event notification by ID."""
        try:
            return {"notification": await client_provider().get(f"/api/households/events/notifications/{notification_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_household_notification(notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a household event notification."""
        try:
            return {"notification": await client_provider().post("/api/households/events/notifications", notification_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_household_notification(notification_id: str, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update one household event notification by ID."""
        try:
            endpoint = f"/api/households/events/notifications/{notification_id}"
            return {"notification": await client_provider().put(endpoint, notification_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_household_notification(notification_id: str) -> Dict[str, Any]:
        """Delete one household event notification by ID."""
        try:
            await client_provider().delete(f"/api/households/events/notifications/{notification_id}")
            return {"message": "Household notification deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def test_household_notification(notification_id: str) -> Dict[str, Any]:
        """Trigger a test for one household event notification."""
        try:
            endpoint = f"/api/households/events/notifications/{notification_id}/test"
            return {"result": await client_provider().post(endpoint, {})}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_recipe_actions(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List household recipe actions."""
        try:
            return {"recipe_actions": await client_provider().get("/api/households/recipe-actions", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_recipe_action(action_id: str) -> Dict[str, Any]:
        """Get one household recipe action by ID."""
        try:
            return {"recipe_action": await client_provider().get(f"/api/households/recipe-actions/{action_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_recipe_action(action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a household recipe action."""
        try:
            return {"recipe_action": await client_provider().post("/api/households/recipe-actions", action_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_recipe_action(action_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update one household recipe action by ID."""
        try:
            return {"recipe_action": await client_provider().put(f"/api/households/recipe-actions/{action_id}", action_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_recipe_action(action_id: str) -> Dict[str, Any]:
        """Delete one household recipe action by ID."""
        try:
            await client_provider().delete(f"/api/households/recipe-actions/{action_id}")
            return {"message": "Recipe action deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def trigger_recipe_action(action_id: str, recipe_slug: str) -> Dict[str, Any]:
        """Trigger one household recipe action for a recipe slug."""
        try:
            endpoint = f"/api/households/recipe-actions/{action_id}/trigger/{recipe_slug}"
            return {"result": await client_provider().post(endpoint, {})}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def list_household_webhooks(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List household webhooks."""
        try:
            return {"webhooks": await client_provider().get("/api/households/webhooks", filters or None)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def get_household_webhook(webhook_id: str) -> Dict[str, Any]:
        """Get one household webhook by ID."""
        try:
            return {"webhook": await client_provider().get(f"/api/households/webhooks/{webhook_id}")}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def create_household_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a household webhook."""
        try:
            return {"webhook": await client_provider().post("/api/households/webhooks", webhook_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def update_household_webhook(webhook_id: str, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update one household webhook by ID."""
        try:
            return {"webhook": await client_provider().put(f"/api/households/webhooks/{webhook_id}", webhook_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def delete_household_webhook(webhook_id: str) -> Dict[str, Any]:
        """Delete one household webhook by ID."""
        try:
            await client_provider().delete(f"/api/households/webhooks/{webhook_id}")
            return {"message": "Household webhook deleted successfully"}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def test_household_webhook(webhook_id: str) -> Dict[str, Any]:
        """Trigger a test for one household webhook."""
        try:
            return {"result": await client_provider().post(f"/api/households/webhooks/{webhook_id}/test", {})}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}

    @mcp_server.tool()
    async def rerun_household_webhooks(rerun_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rerun household webhooks with a Mealie-native payload."""
        try:
            return {"result": await client_provider().post("/api/households/webhooks/rerun", rerun_data)}
        except MealieAPIError as e:
            return {"error": f"API error: {e}"}
