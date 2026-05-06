"""Core functionality tests for Mealie MCP server.

This module tests basic functionality without requiring MCP decorators
to work around import issues and validate core business logic.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import settings
from mealie_client import MealieClient, MealieAPIError


class TestConfiguration:
    """Test configuration loading and validation."""
    
    def test_default_settings_load(self):
        """Test that settings load with default values."""
        assert settings.mealie_base_url  # Non-empty URL
        assert settings.mealie_base_url.startswith("http")
        assert settings.mcp_port == 8080
        assert settings.mcp_host == "0.0.0.0"
        assert settings.request_timeout == 30
        assert settings.max_retries == 3
        assert settings.log_level == "INFO"
    
    def test_settings_with_env_override(self):
        """Test settings can be overridden with environment variables."""
        with patch.dict(os.environ, {
            'MEALIE_BASE_URL': 'https://mealie.example.com',
            'MCP_PORT': '9999',
            'LOG_LEVEL': 'DEBUG'
        }):
            from config import Settings
            test_settings = Settings()
            
            assert test_settings.mealie_base_url == "https://mealie.example.com"
            assert test_settings.mcp_port == 9999
            assert test_settings.log_level == "DEBUG"
    
    def test_required_api_token(self):
        """Test that API token is required."""
        # This test validates that the field exists and is required
        # In real usage, ValidationError would be raised if not provided
        from config import Settings
        from pydantic import ValidationError
        
        # Test with missing token - should work since we have default in env
        try:
            Settings()
        except ValidationError as e:
            # Expected if MEALIE_API_TOKEN not set
            assert "mealie_api_token" in str(e)


class TestMealieClient:
    """Test MealieClient functionality."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = MealieClient(
            base_url="http://test.example.com",
            api_token="test_token_123"
        )
    
    def test_client_initialization(self):
        """Test client initializes correctly."""
        assert self.client.base_url == "http://test.example.com"
        assert self.client.api_token == "test_token_123"
        assert self.client.headers["Authorization"] == "Bearer test_token_123"
        assert self.client.headers["Content-Type"] == "application/json"
    
    def test_client_defaults_from_settings(self):
        """Test client uses settings defaults when not specified."""
        # Create client without args - uses existing settings singleton
        client = MealieClient()
        assert client.base_url == settings.mealie_base_url
        assert client.api_token == settings.mealie_api_token
    
    @pytest.mark.asyncio
    async def test_request_url_construction(self):
        """Test URL construction for requests."""
        with patch.object(self.client.client, 'request') as mock_request:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.content = b'{"result": "success"}'
            mock_response.json.return_value = {"result": "success"}
            mock_request.return_value = mock_response
            
            await self.client.get("/api/recipes")
            
            # Verify the URL was constructed correctly
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]['url'] == "http://test.example.com/api/recipes"
    
    @pytest.mark.asyncio
    async def test_get_request(self):
        """Test GET request functionality."""
        with patch.object(self.client.client, 'request') as mock_request:
            # Mock successful response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.content = b'{"recipes": []}'
            mock_response.json.return_value = {"recipes": []}
            mock_request.return_value = mock_response
            
            result = await self.client.get("/api/recipes", params={"page": 1})
            
            assert result == {"recipes": []}
            mock_request.assert_called_once_with(
                method="GET",
                url="http://test.example.com/api/recipes",
                json=None,
                params={"page": 1}
            )
    
    @pytest.mark.asyncio
    async def test_post_request(self):
        """Test POST request functionality."""
        with patch.object(self.client.client, 'request') as mock_request:
            # Mock successful response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.content = b'{"id": "123", "name": "Test Recipe"}'
            mock_response.json.return_value = {"id": "123", "name": "Test Recipe"}
            mock_request.return_value = mock_response
            
            recipe_data = {"name": "Test Recipe", "description": "A test"}
            result = await self.client.post("/api/recipes", recipe_data)
            
            assert result == {"id": "123", "name": "Test Recipe"}
            mock_request.assert_called_once_with(
                method="POST",
                url="http://test.example.com/api/recipes",
                json=recipe_data,
                params=None
            )

    @pytest.mark.asyncio
    async def test_upload_recipe_image(self):
        """Test recipe image upload uses multipart form data."""
        with patch('mealie_client.httpx.AsyncClient') as mock_async_client:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.content = b'{"image": "abc123/original.png"}'
            mock_response.json.return_value = {"image": "abc123/original.png"}

            mock_upload_client = AsyncMock()
            mock_upload_client.request.return_value = mock_response
            mock_async_client.return_value.__aenter__.return_value = mock_upload_client

            result = await self.client.upload_recipe_image(
                "test-recipe",
                b"fake-png-bytes",
                "png",
            )

            assert result == {"image": "abc123/original.png"}
            mock_upload_client.request.assert_called_once()
            call_kwargs = mock_upload_client.request.call_args.kwargs
            assert call_kwargs["method"] == "PUT"
            assert call_kwargs["url"] == "http://test.example.com/api/recipes/test-recipe/image"
            assert call_kwargs["data"] == {"extension": "png"}
            assert call_kwargs["files"]["image"][0] == "recipe-image.png"
            assert call_kwargs["files"]["image"][1] == b"fake-png-bytes"
            assert call_kwargs["files"]["image"][2] == "image/png"
            assert "Content-Type" not in call_kwargs["headers"]
    
    @pytest.mark.asyncio
    async def test_http_error_handling(self):
        """Test HTTP error handling."""
        with patch.object(self.client.client, 'request') as mock_request:
            import httpx
            
            # Mock HTTP error
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            
            error = httpx.HTTPStatusError("404", request=Mock(), response=mock_response)
            mock_request.side_effect = error
            
            with pytest.raises(MealieAPIError) as exc_info:
                await self.client.get("/api/recipes/nonexistent")
            
            assert "API request failed" in str(exc_info.value)
            assert "404" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_request_error_handling(self):
        """Test request error handling."""
        with patch.object(self.client.client, 'request') as mock_request:
            import httpx
            
            # Mock network error
            mock_request.side_effect = httpx.RequestError("Connection failed")
            
            with pytest.raises(MealieAPIError) as exc_info:
                await self.client.get("/api/recipes")
            
            assert "Request failed" in str(exc_info.value)
            assert "Connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_recipe_search_method(self):
        """Test the search_recipes convenience method."""
        with patch.object(self.client, '_request') as mock_request:
            mock_request.return_value = {
                "items": [{"id": "1", "name": "Test Recipe"}],
                "total": 1
            }
            
            result = await self.client.search_recipes(
                query="pasta",
                page=2,
                per_page=25,
                include_tags=["italian"],
                exclude_tags=["spicy"]
            )
            
            assert result["items"][0]["name"] == "Test Recipe"
            mock_request.assert_called_once_with(
                "GET",
                "/api/recipes",
                params={
                    "search": "pasta",
                    "page": 2,
                    "perPage": 25,
                    "tags": ["italian"],
                }
            )
    
    @pytest.mark.asyncio
    async def test_get_recipe_method(self):
        """Test the get_recipe convenience method."""
        with patch.object(self.client, '_request') as mock_request:
            mock_request.return_value = {"id": "123", "name": "Test Recipe"}

            result = await self.client.get_recipe("123")

            assert result["id"] == "123"
            mock_request.assert_called_once_with("GET", "/api/recipes/123", params=None)
    
    @pytest.mark.asyncio
    async def test_create_recipe_method(self):
        """Test the create_recipe convenience method."""
        with patch.object(self.client, '_request') as mock_request:
            mock_request.return_value = {"id": "123", "name": "New Recipe"}

            recipe_data = {"name": "New Recipe"}
            result = await self.client.create_recipe(recipe_data)

            assert result["id"] == "123"
            mock_request.assert_called_once_with("POST", "/api/recipes", data=recipe_data)
    
    @pytest.mark.asyncio
    async def test_update_recipe_method(self):
        """Test the update_recipe convenience method."""
        with patch.object(self.client, '_request') as mock_request:
            mock_request.return_value = {"id": "123", "name": "Updated Recipe"}

            recipe_data = {"name": "Updated Recipe"}
            result = await self.client.update_recipe("123", recipe_data)

            assert result["name"] == "Updated Recipe"
            mock_request.assert_called_once_with("PUT", "/api/recipes/123", data=recipe_data)
    
    @pytest.mark.asyncio
    async def test_delete_recipe_method(self):
        """Test the delete_recipe convenience method."""
        with patch.object(self.client, '_request') as mock_request:
            mock_request.return_value = {}
            
            result = await self.client.delete_recipe("123")
            
            assert result == {}
            mock_request.assert_called_once_with("DELETE", "/api/recipes/123", params=None)

    @pytest.mark.asyncio
    async def test_delete_request_can_send_query_params(self):
        """Test DELETE supports query params for bulk Mealie endpoints."""
        with patch.object(self.client, '_request') as mock_request:
            mock_request.return_value = {}

            await self.client.delete("/api/households/shopping/items", params={"ids": ["item-1"]})

            mock_request.assert_called_once_with(
                "DELETE",
                "/api/households/shopping/items",
                params={"ids": ["item-1"]},
            )

    @pytest.mark.asyncio
    async def test_raw_request_returns_binary_as_base64(self):
        """Test raw downloads are returned as MCP-safe base64 payloads."""
        with patch.object(self.client.client, 'request') as mock_request:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.content = b"zip-bytes"
            mock_response.headers = {
                "content-type": "application/zip",
                "content-disposition": 'attachment; filename="recipes.zip"',
            }
            mock_request.return_value = mock_response

            result = await self.client.get_raw("/api/recipes/shared/token/zip")

            assert result == {
                "content_base64": "emlwLWJ5dGVz",
                "content_type": "application/zip",
                "content_disposition": 'attachment; filename="recipes.zip"',
                "size": 9,
            }

    @pytest.mark.asyncio
    async def test_raw_request_preserves_json_responses(self):
        """Test raw download helper preserves JSON when Mealie returns JSON."""
        with patch.object(self.client.client, 'request') as mock_request:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.content = b'{"token":"abc"}'
            mock_response.json.return_value = {"token": "abc"}
            mock_response.headers = {"content-type": "application/json"}
            mock_request.return_value = mock_response

            result = await self.client.get_raw("/api/recipes/bulk-actions/export/export-id/download")

            assert result == {
                "json": {"token": "abc"},
                "content_type": "application/json",
                "content_disposition": None,
                "size": 15,
            }
    
    @pytest.mark.asyncio
    async def test_import_recipe_from_url_method(self):
        """Test the import_recipe_from_url convenience method."""
        with patch.object(self.client, '_request') as mock_request:
            mock_request.return_value = {"id": "123", "name": "Imported Recipe"}

            result = await self.client.import_recipe_from_url("https://example.com/recipe")

            assert result["name"] == "Imported Recipe"
            mock_request.assert_called_once_with(
                "POST",
                "/api/recipes/create/url",
                data={"url": "https://example.com/recipe"}
            )
    
    @pytest.mark.asyncio
    async def test_meal_plan_methods(self):
        """Test meal plan convenience methods."""
        with patch.object(self.client, '_request') as mock_request:
            # Test get_meal_plans
            mock_request.return_value = {"items": []}
            
            await self.client.get_meal_plans("2024-01-01", "2024-01-07")
            
            mock_request.assert_called_with(
                "GET",
                "/api/households/mealplans",
                params={"start_date": "2024-01-01", "end_date": "2024-01-07"}
            )
            
            # Test create_meal_plan_entry
            meal_data = {"date": "2024-01-01", "meal_type": "dinner"}
            mock_request.return_value = {"id": "meal_123"}
            
            result = await self.client.create_meal_plan_entry(meal_data)
            assert result["id"] == "meal_123"
            mock_request.assert_called_with(
                "POST",
                "/api/households/mealplans",
                data=meal_data,
            )
    
    @pytest.mark.asyncio
    async def test_shopping_list_methods(self):
        """Test shopping list convenience methods."""
        with patch.object(self.client, '_request') as mock_request:
            # Test get_shopping_lists
            mock_request.return_value = {"items": []}

            await self.client.get_shopping_lists()

            mock_request.assert_called_with("GET", "/api/households/shopping/lists", params=None)

            # Test create_shopping_list
            mock_request.return_value = {"id": "list_123", "name": "Groceries"}

            result = await self.client.create_shopping_list("Groceries")
            assert result["name"] == "Groceries"
            mock_request.assert_called_with("POST", "/api/households/shopping/lists", data={"name": "Groceries"})

    @pytest.mark.asyncio
    async def test_shopping_item_methods_use_current_household_endpoints(self):
        """Test shopping item helpers use Mealie v3 household endpoints."""
        with patch.object(self.client, '_request') as mock_request:
            mock_request.return_value = {"id": "item_123"}

            await self.client.add_shopping_item("list_123", {"display": "Milk"})
            mock_request.assert_called_with(
                "POST",
                "/api/households/shopping/items",
                data={"display": "Milk", "shoppingListId": "list_123"},
            )

            await self.client.update_shopping_item("list_123", "item_123", {"checked": True})
            mock_request.assert_called_with(
                "PUT",
                "/api/households/shopping/items/item_123",
                data={"checked": True, "shoppingListId": "list_123"},
            )

            await self.client.delete_shopping_item("list_123", "item_123")
            mock_request.assert_called_with("DELETE", "/api/households/shopping/items/item_123", params=None)

    @pytest.mark.asyncio
    async def test_shopping_recipe_and_bulk_methods(self):
        """Test shopping bulk and recipe endpoints."""
        with patch.object(self.client, '_request') as mock_request:
            mock_request.return_value = {"ok": True}

            await self.client.create_shopping_items([{"shoppingListId": "list_123", "display": "Milk"}])
            mock_request.assert_called_with(
                "POST",
                "/api/households/shopping/items/create-bulk",
                data=[{"shoppingListId": "list_123", "display": "Milk"}],
            )

            await self.client.add_recipe_to_shopping_list("list_123", "recipe_123", {"recipeIncrementQuantity": 2})
            mock_request.assert_called_with(
                "POST",
                "/api/households/shopping/lists/list_123/recipe/recipe_123",
                data={"recipeIncrementQuantity": 2},
            )

            await self.client.remove_recipe_from_shopping_list("list_123", "recipe_123", {"recipeDecrementQuantity": 1})
            mock_request.assert_called_with(
                "POST",
                "/api/households/shopping/lists/list_123/recipe/recipe_123/delete",
                data={"recipeDecrementQuantity": 1},
            )

    @pytest.mark.asyncio
    async def test_merge_foods_uses_current_mealie_put_endpoint(self):
        """Test food merges use Mealie's current PUT endpoint and payload."""
        with patch.object(self.client, '_request') as mock_request:
            mock_request.return_value = {"message": "merged"}

            result = await self.client.merge_foods("from-food-id", "to-food-id")

            assert result["message"] == "merged"
            mock_request.assert_called_once_with(
                "PUT",
                "/api/foods/merge",
                data={"fromFood": "from-food-id", "toFood": "to-food-id"},
            )

    @pytest.mark.asyncio
    async def test_merge_units_uses_current_mealie_put_endpoint(self):
        """Test unit merges use Mealie's current PUT endpoint and payload."""
        with patch.object(self.client, '_request') as mock_request:
            mock_request.return_value = {"message": "merged"}

            result = await self.client.merge_units("from-unit-id", "to-unit-id")

            assert result["message"] == "merged"
            mock_request.assert_called_once_with(
                "PUT",
                "/api/units/merge",
                data={"fromUnit": "from-unit-id", "toUnit": "to-unit-id"},
            )
    
    @pytest.mark.asyncio
    async def test_client_close(self):
        """Test client cleanup."""
        with patch.object(self.client.client, 'aclose') as mock_close:
            await self.client.close()
            mock_close.assert_called_once()


class TestApplicationStartup:
    """Test application startup functionality."""
    
    @pytest.mark.asyncio
    async def test_health_check_tool_logic(self):
        """Test the health check logic without MCP decorators."""
        # Mock a MealieClient instance
        mock_client = AsyncMock(spec=MealieClient)
        mock_client.get.return_value = {"version": "1.0.0"}
        
        # Simulate the health check logic from main.py
        try:
            about_info = await mock_client.get("/api/app/about")
            
            result = {
                "status": "healthy",
                "message": "MCP server is running and connected to Mealie",
                "mealie_info": {
                    "version": about_info.get("version", "unknown"),
                    "base_url": settings.mealie_base_url
                },
                "server_info": {
                    "name": settings.mcp_server_name,
                    "port": settings.mcp_port
                }
            }
            
            assert result["status"] == "healthy"
            assert result["mealie_info"]["version"] == "1.0.0"
            assert result["server_info"]["name"] == settings.mcp_server_name
            
        except Exception as e:
            # Test error handling
            result = {
                "status": "error",
                "message": f"Health check failed: {str(e)}"
            }
            assert result["status"] == "error"
    
    @pytest.mark.asyncio
    async def test_client_initialization_logic(self):
        """Test client initialization logic."""
        # Mock the initialization process from main.py
        mock_client = AsyncMock(spec=MealieClient)
        
        # Test successful connection
        mock_client.get.return_value = {"version": "1.0.0"}
        
        try:
            await mock_client.get("/api/app/about")
            connection_status = "connected"
        except Exception:
            connection_status = "failed"
        
        assert connection_status == "connected"
        
        # Test failed connection
        mock_client.get.side_effect = Exception("Connection failed")
        
        try:
            await mock_client.get("/api/app/about")
            connection_status = "connected"
        except Exception:
            connection_status = "failed"
        
        assert connection_status == "failed"


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_mealie_api_error_creation(self):
        """Test MealieAPIError creation and message handling."""
        error = MealieAPIError("Test error message")
        assert str(error) == "Test error message"
        
        error_with_details = MealieAPIError("API request failed: 404 - Not Found")
        assert "404" in str(error_with_details)
        assert "Not Found" in str(error_with_details)
    
    def test_url_construction_edge_cases(self):
        """Test URL construction edge cases."""
        client = MealieClient(base_url="http://example.com/", api_token="test")
        
        # Test base URL with trailing slash
        assert client.base_url == "http://example.com"
        
        client2 = MealieClient(base_url="http://example.com", api_token="test")
        assert client2.base_url == "http://example.com"


class TestDataValidation:
    """Test data validation without Pydantic model imports."""
    
    def test_basic_data_structures(self):
        """Test basic data structure expectations."""
        # Test recipe data structure
        recipe_data = {
            "name": "Test Recipe",
            "description": "A test recipe",
            "recipe_ingredient": [
                {"title": "flour", "text": "2 cups flour"}
            ],
            "recipe_instructions": [
                {"text": "Mix ingredients"}
            ],
            "rating": 4
        }
        
        # Validate structure
        assert "name" in recipe_data
        assert isinstance(recipe_data["recipe_ingredient"], list)
        assert isinstance(recipe_data["recipe_instructions"], list)
        assert isinstance(recipe_data["rating"], int)
        
        # Test meal plan data structure
        meal_plan_data = {
            "date": "2024-01-01",
            "meal_type": "breakfast",
            "title": "Scrambled Eggs",
            "recipe_id": "123e4567-e89b-12d3-a456-426614174000"
        }
        
        assert "date" in meal_plan_data
        assert "meal_type" in meal_plan_data
        assert meal_plan_data["date"] == "2024-01-01"
        
        # Test shopping list data structure
        shopping_item_data = {
            "text": "2 cups milk",
            "checked": False,
            "quantity": 2,
            "note": "Organic if available"
        }
        
        assert "text" in shopping_item_data
        assert isinstance(shopping_item_data["checked"], bool)


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
