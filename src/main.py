"""Main FastMCP server for Mealie integration."""

import logging
import asyncio
import argparse
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from config import settings
from mealie_client import MealieClient

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(server):
    yield


# Initialize FastMCP server with host/port from settings
mcp = FastMCP(
    name=settings.mcp_server_name,
    instructions="MCP server for Mealie recipe management, meal planning, and shopping lists",
    host=settings.mcp_host,
    port=settings.mcp_port,
    json_response=True,
    lifespan=lifespan
)

# Global client instance
mealie_client = None

# Import and setup all tools
from tools.recipes import setup_recipe_tools
from tools.meal_plans import setup_meal_plan_tools
from tools.shopping import setup_shopping_tools
from tools.ingredients import setup_ingredient_tools
from tools.tags_categories import setup_tag_category_tools
from tools.platform import setup_platform_tools
from tools.comments_sharing import setup_comments_sharing_tools
from tools.households import setup_household_tools
from tools.groups import setup_group_tools
from tools.users import setup_user_tools
from tools.admin import setup_admin_tools
from tools.explore import setup_explore_tools

# Setup all tools with client provider function
def get_client():
    global mealie_client
    if mealie_client is not None and mealie_client.client.is_closed:
        logger.warning("Recreating closed Mealie client")
        mealie_client = MealieClient()
    return mealie_client

setup_recipe_tools(mcp, get_client)
setup_meal_plan_tools(mcp, get_client)
setup_shopping_tools(mcp, get_client)
setup_ingredient_tools(mcp, get_client)
setup_tag_category_tools(mcp, get_client)
setup_platform_tools(mcp, get_client)
setup_comments_sharing_tools(mcp, get_client)
setup_household_tools(mcp, get_client)
setup_group_tools(mcp, get_client)
setup_user_tools(mcp, get_client)
setup_admin_tools(mcp, get_client)
setup_explore_tools(mcp, get_client)


async def initialize_client():
    """Initialize the Mealie client and test connection."""
    global mealie_client
    logger.info("Initializing Mealie MCP Server...")
    mealie_client = MealieClient()

    for attempt in range(1, max(1, settings.max_retries) + 1):
        try:
            await mealie_client.get("/api/app/about")
            logger.info(f"Successfully connected to Mealie at {settings.mealie_base_url}")
            return
        except Exception as e:
            if attempt >= max(1, settings.max_retries):
                logger.error(f"Failed to connect to Mealie after {attempt} attempts: {e}")
                logger.warning("Server will start without Mealie connection")
                return
            logger.warning(f"Mealie connection attempt {attempt} failed: {e}")
            await asyncio.sleep(min(2 ** (attempt - 1), 5))


@mcp.custom_route("/health", methods=["GET"])
async def http_health_check(request: Request) -> JSONResponse:
    """HTTP health endpoint for Docker and Portainer."""
    try:
        about_info = await mealie_client.get("/api/app/about") if mealie_client else {}
        return JSONResponse({
            "status": "healthy",
            "message": "MCP server is running and connected to Mealie",
            "mealie_info": {
                "version": about_info.get("version", "unknown"),
                "base_url": settings.mealie_base_url
            },
            "server_info": {
                "name": settings.mcp_server_name,
                "port": settings.mcp_port,
                "transport": "streamable-http",
                "endpoint": "/mcp"
            }
        })
    except Exception as e:
        logger.error(f"HTTP health check failed: {e}")
        return JSONResponse({
            "status": "degraded",
            "message": f"MCP server is running but Mealie check failed: {str(e)}",
            "server_info": {
                "name": settings.mcp_server_name,
                "port": settings.mcp_port,
                "transport": "streamable-http",
                "endpoint": "/mcp"
            }
        })


@mcp.tool()
async def health_check() -> dict:
    """Check the health of the MCP server and Mealie connection."""
    try:
        if not mealie_client:
            return {
                "status": "error",
                "message": "Mealie client not initialized"
            }

        # Test Mealie connection
        about_info = await mealie_client.get("/api/app/about")

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
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}"
        }


async def main():
    """Run the MCP server."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Mealie MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport mode: stdio (for Claude Desktop) or streamable-http (for Docker/HTTP)"
    )
    args = parser.parse_args()

    # Initialize client
    await initialize_client()

    # Run the server with the appropriate async method
    if args.transport == "stdio":
        logger.info(f"Starting {settings.mcp_server_name} with stdio transport")
        await mcp.run_stdio_async()
    else:
        logger.info(f"Starting {settings.mcp_server_name} on {settings.mcp_host}:{settings.mcp_port}")
        await mcp.run_streamable_http_async()


if __name__ == "__main__":
    asyncio.run(main())
