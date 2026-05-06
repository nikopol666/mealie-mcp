"""Application startup and integration tests.

This module tests the application startup process, MCP server initialization,
and integration with external dependencies.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import settings
from mealie_client import MealieClient, MealieAPIError


class TestApplicationStartup:
    """Test application startup scenarios."""
    
    def test_fastmcp_import_and_setup(self):
        """Test that FastMCP can be imported and set up correctly."""
        from mcp.server.fastmcp import FastMCP
        
        # Test with correct parameters based on actual signature
        mcp_server = FastMCP(
            name="Test Mealie MCP Server",
            instructions="Test MCP server for Mealie integration",
            json_response=True,
            host="0.0.0.0",
            port=8080
        )
        
        assert mcp_server is not None
        
        # Test tool registration works
        @mcp_server.tool()
        def test_tool() -> str:
            """A test tool."""
            return "test result"
        
        # Verify tool was registered (if we can check)
        assert test_tool is not None
    
    @pytest.mark.asyncio
    async def test_mealie_client_connection_simulation(self):
        """Test Mealie client connection scenarios."""
        # Test successful connection
        client = MealieClient(
            base_url="http://test.example.com",
            api_token="test_token"
        )
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {
                "version": "1.0.0",
                "demo": False,
                "allow_signup": True
            }
            
            # Simulate the initialize_client function logic
            try:
                about_info = await client.get("/api/app/about")
                connection_result = {
                    "status": "success",
                    "mealie_info": about_info
                }
            except Exception as e:
                connection_result = {
                    "status": "error", 
                    "error": str(e)
                }
            
            assert connection_result["status"] == "success"
            assert connection_result["mealie_info"]["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_mealie_client_connection_failure(self):
        """Test Mealie client connection failure handling."""
        client = MealieClient(
            base_url="http://unreachable.example.com",
            api_token="test_token"
        )
        
        with patch.object(client, '_request') as mock_request:
            mock_request.side_effect = MealieAPIError("Connection refused")
            
            # Simulate the initialize_client function error handling
            try:
                await client.get("/api/app/about")
                connection_result = {"status": "success"}
            except Exception as e:
                connection_result = {
                    "status": "error",
                    "error": str(e),
                    "should_continue": True  # Server should start anyway
                }
            
            assert connection_result["status"] == "error"
            assert connection_result["should_continue"] is True
            assert "Connection refused" in connection_result["error"]
    
    @pytest.mark.asyncio
    async def test_health_check_tool_functionality(self):
        """Test the health check tool logic."""
        # Mock a healthy Mealie connection
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "version": "1.0.0",
            "demo": False
        }
        
        # Simulate health_check tool logic from main.py
        async def health_check_logic(client):
            try:
                if not client:
                    return {
                        "status": "error",
                        "message": "Mealie client not initialized"
                    }
                
                about_info = await client.get("/api/app/about")
                
                return {
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
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Health check failed: {str(e)}"
                }
        
        # Test with healthy client
        result = await health_check_logic(mock_client)
        assert result["status"] == "healthy"
        assert result["mealie_info"]["version"] == "1.0.0"
        assert result["server_info"]["name"] == settings.mcp_server_name
        
        # Test with no client
        result = await health_check_logic(None)
        assert result["status"] == "error"
        assert "not initialized" in result["message"]
        
        # Test with failing client
        mock_client.get.side_effect = Exception("Connection failed")
        result = await health_check_logic(mock_client)
        assert result["status"] == "error"
        assert "Health check failed" in result["message"]
    
    def test_environment_configuration(self):
        """Test various environment configurations."""
        test_cases = [
            {
                "env": {
                    "MEALIE_BASE_URL": "https://mealie.example.com",
                    "MEALIE_API_TOKEN": "custom_token",
                    "MCP_PORT": "9090",
                    "LOG_LEVEL": "DEBUG"
                },
                "expected": {
                    "base_url": "https://mealie.example.com",
                    "port": 9090,
                    "log_level": "DEBUG"
                }
            },
            {
                "env": {
                    "MEALIE_BASE_URL": "http://localhost:9000",
                    "MEALIE_API_TOKEN": "local_token",
                    "REQUEST_TIMEOUT": "60",
                    "MAX_RETRIES": "5"
                },
                "expected": {
                    "base_url": "http://localhost:9000",
                    "timeout": 60,
                    "retries": 5
                }
            }
        ]
        
        for test_case in test_cases:
            with patch.dict(os.environ, test_case["env"]):
                # Import fresh settings
                from config import Settings
                test_settings = Settings()
                
                if "base_url" in test_case["expected"]:
                    assert test_settings.mealie_base_url == test_case["expected"]["base_url"]
                if "port" in test_case["expected"]:
                    assert test_settings.mcp_port == test_case["expected"]["port"]
                if "log_level" in test_case["expected"]:
                    assert test_settings.log_level == test_case["expected"]["log_level"]
                if "timeout" in test_case["expected"]:
                    assert test_settings.request_timeout == test_case["expected"]["timeout"]
                if "retries" in test_case["expected"]:
                    assert test_settings.max_retries == test_case["expected"]["retries"]
    
    def test_logging_configuration(self):
        """Test logging configuration setup."""
        import logging
        
        # Test that we can set different log levels
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in log_levels:
            with patch.dict(os.environ, {"LOG_LEVEL": level}):
                # Simulate the logging setup from main.py
                log_level_obj = getattr(logging, level)
                assert log_level_obj is not None
                
                # Test logger creation
                logger = logging.getLogger("test_mealie_mcp")
                logger.setLevel(log_level_obj)
                
                assert logger.level == log_level_obj
    
    @pytest.mark.asyncio
    async def test_concurrent_client_requests(self):
        """Test that the client can handle concurrent requests."""
        client = MealieClient(
            base_url="http://test.example.com",
            api_token="test_token"
        )
        
        with patch.object(client, '_request') as mock_request:
            # Mock different responses for different endpoints
            def mock_response(method, endpoint, **kwargs):
                if endpoint == "/api/recipes":
                    return {"items": [{"id": "1", "name": "Recipe 1"}]}
                elif endpoint == "/api/households/mealplans":
                    return {"items": [{"id": "1", "date": "2024-01-01"}]}
                elif endpoint == "/api/households/shopping/lists":
                    return {"items": [{"id": "1", "name": "Shopping List 1"}]}
                else:
                    return {"result": "success"}
            
            mock_request.side_effect = mock_response
            
            # Run multiple concurrent requests
            tasks = [
                client.search_recipes("pasta"),
                client.get_meal_plans("2024-01-01", "2024-01-07"), 
                client.get_shopping_lists(),
                client.get("/api/app/about")
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Verify all requests completed successfully
            assert len(results) == 4
            assert "items" in results[0]  # recipes
            assert "items" in results[1]  # meal plans
            assert "items" in results[2]  # shopping lists
            assert "result" in results[3]  # about
    
    @pytest.mark.asyncio
    async def test_client_resource_cleanup(self):
        """Test proper cleanup of client resources."""
        client = MealieClient(
            base_url="http://test.example.com",
            api_token="test_token"
        )
        
        # Mock the httpx client
        mock_http_client = AsyncMock()
        client.client = mock_http_client
        
        # Test that close is called
        await client.close()
        mock_http_client.aclose.assert_called_once()
    
    def test_url_edge_cases(self):
        """Test URL construction edge cases."""
        test_cases = [
            {
                "base_url": "http://example.com/",
                "expected": "http://example.com"
            },
            {
                "base_url": "http://example.com",
                "expected": "http://example.com"
            },
            {
                "base_url": "https://mealie.example.com/subpath/",
                "expected": "https://mealie.example.com/subpath"
            }
        ]
        
        for case in test_cases:
            client = MealieClient(
                base_url=case["base_url"],
                api_token="test"
            )
            assert client.base_url == case["expected"]
    
    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Test that errors are properly propagated through the stack."""
        client = MealieClient(
            base_url="http://test.example.com",
            api_token="test_token"
        )
        
        # Test different HTTP error codes
        error_cases = [
            (400, "Bad Request"),
            (401, "Unauthorized"), 
            (403, "Forbidden"),
            (404, "Not Found"),
            (500, "Internal Server Error")
        ]
        
        for status_code, error_text in error_cases:
            with patch.object(client.client, 'request') as mock_request:
                import httpx
                
                mock_response = Mock()
                mock_response.status_code = status_code
                mock_response.text = error_text
                
                error = httpx.HTTPStatusError(
                    f"{status_code}", 
                    request=Mock(), 
                    response=mock_response
                )
                mock_request.side_effect = error
                
                with pytest.raises(MealieAPIError) as exc_info:
                    await client.get("/api/test")
                
                assert str(status_code) in str(exc_info.value)
                assert error_text in str(exc_info.value)


class TestMCPToolsIntegration:
    """Test MCP tools integration without requiring actual tool imports."""
    
    def test_tool_decorator_functionality(self):
        """Test that MCP tool decorator works as expected."""
        from mcp.server.fastmcp import FastMCP
        
        mcp_server = FastMCP(name="Test Server")
        
        # Test basic tool registration
        @mcp_server.tool()
        def simple_tool() -> str:
            """A simple test tool."""
            return "success"
        
        assert simple_tool is not None
        
        # Test tool with parameters
        @mcp_server.tool()
        def parameterized_tool(name: str, count: int = 1) -> dict:
            """A tool with parameters."""
            return {"name": name, "count": count}
        
        assert parameterized_tool is not None
    
    @pytest.mark.asyncio
    async def test_async_tool_functionality(self):
        """Test async tool functionality."""
        from mcp.server.fastmcp import FastMCP
        
        mcp_server = FastMCP(name="Test Server")
        
        @mcp_server.tool()
        async def async_tool(data: str) -> dict:
            """An async test tool."""
            # Simulate some async work
            await asyncio.sleep(0.001)
            return {"processed": data, "status": "complete"}
        
        # Test that the tool can be called
        result = await async_tool("test_data")
        assert result["processed"] == "test_data"
        assert result["status"] == "complete"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
