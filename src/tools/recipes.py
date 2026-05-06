"""Recipe management tools for Mealie MCP server.

This module provides comprehensive recipe management functionality through MCP tools
that interface with the Mealie API. All tools include proper error handling,
input validation using Pydantic models, and async operations.
"""

import base64
import binascii
import logging
import mimetypes
import random
from typing import Dict, Any, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from mealie_client import MealieClient, MealieAPIError

logger = logging.getLogger(__name__)


class RecipeSearchFilters(BaseModel):
    """Filters for recipe search operations."""

    model_config = ConfigDict(extra="allow")
    
    query: Optional[str] = Field(
        default="", 
        description="Search query for recipe name, description, or ingredients"
    )
    page: int = Field(
        default=1, 
        ge=1, 
        description="Page number for pagination"
    )
    per_page: int = Field(
        default=10, 
        ge=1, 
        le=100, 
        description="Number of recipes per page (max 100)"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Category IDs or slugs to include"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tag IDs or slugs to include"
    )
    tools: Optional[List[str]] = Field(
        default=None,
        description="Recipe tool/utensil IDs or slugs to include"
    )
    foods: Optional[List[str]] = Field(
        default=None,
        description="Food IDs or slugs to include"
    )
    households: Optional[List[str]] = Field(
        default=None,
        description="Household IDs or slugs to include"
    )
    cookbook: Optional[str] = Field(
        default=None,
        description="Cookbook ID or slug"
    )
    order_by: Optional[str] = Field(default=None, description="Mealie orderBy field")
    order_by_null_position: Optional[str] = Field(default=None, description="Mealie orderByNullPosition")
    order_direction: Optional[str] = Field(default=None, description="asc or desc")
    query_filter: Optional[str] = Field(default=None, description="Mealie queryFilter")
    pagination_seed: Optional[str] = Field(default=None, description="Mealie paginationSeed")
    require_all_categories: Optional[bool] = Field(default=None)
    require_all_tags: Optional[bool] = Field(default=None)
    require_all_tools: Optional[bool] = Field(default=None)
    require_all_foods: Optional[bool] = Field(default=None)
    include_tags: Optional[List[str]] = Field(
        default=None, 
        description="Deprecated alias for tags"
    )
    category: Optional[str] = Field(
        default=None, 
        description="Deprecated alias for one category"
    )


class RecipeIngredient(BaseModel):
    """Recipe ingredient model."""
    
    title: str = Field(description="Ingredient name")
    text: str = Field(description="Full ingredient text with quantity and preparation")
    quantity: Optional[float] = Field(default=None, description="Ingredient quantity")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    food: Optional[str] = Field(default=None, description="Food item name")
    note: Optional[str] = Field(default=None, description="Additional notes")


class RecipeInstruction(BaseModel):
    """Recipe instruction model."""
    
    id: Optional[int] = Field(default=None, description="Instruction ID")
    title: Optional[str] = Field(default=None, description="Instruction title")
    text: str = Field(description="Instruction text")
    ingredient_references: Optional[List[int]] = Field(
        default=None, 
        description="References to ingredients used in this step"
    )


class RecipeNutrition(BaseModel):
    """Recipe nutrition information."""
    
    calories: Optional[str] = Field(default=None, description="Calories per serving")
    fat_content: Optional[str] = Field(default=None, description="Fat content")
    protein_content: Optional[str] = Field(default=None, description="Protein content")
    carbohydrate_content: Optional[str] = Field(default=None, description="Carbohydrate content")
    fiber_content: Optional[str] = Field(default=None, description="Fiber content")
    sugar_content: Optional[str] = Field(default=None, description="Sugar content")
    sodium_content: Optional[str] = Field(default=None, description="Sodium content")


class RecipeCreateUpdate(BaseModel):
    """Model for creating or updating recipes."""
    
    name: str = Field(description="Recipe name", min_length=1, max_length=200)
    description: Optional[str] = Field(
        default=None, 
        description="Recipe description",
        max_length=2000
    )
    image: Optional[HttpUrl] = Field(default=None, description="Recipe image URL")
    recipe_yield: Optional[str] = Field(default=None, description="Recipe yield/servings")
    prep_time: Optional[str] = Field(default=None, description="Preparation time")
    cook_time: Optional[str] = Field(default=None, description="Cooking time")
    total_time: Optional[str] = Field(default=None, description="Total time")
    recipe_category: Optional[str] = Field(default=None, description="Recipe category")
    tags: Optional[List[str]] = Field(default=[], description="Recipe tags")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Recipe rating (1-5)")
    recipe_ingredient: Optional[List[RecipeIngredient]] = Field(
        default=[], 
        description="Recipe ingredients"
    )
    recipe_instructions: Optional[List[RecipeInstruction]] = Field(
        default=[], 
        description="Recipe instructions"
    )
    nutrition: Optional[RecipeNutrition] = Field(
        default=None, 
        description="Nutrition information"
    )
    notes: Optional[List[Dict[str, Any]]] = Field(
        default=[], 
        description="Recipe notes"
    )

    @field_validator('tags', mode='before')
    @classmethod
    def validate_tags(cls, v):
        """Ensure tags is always a list."""
        if v is None:
            return []
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(',') if tag.strip()]
        return v


class RecipeImportUrl(BaseModel):
    """Model for importing recipes from URL."""
    
    url: HttpUrl = Field(description="URL to import recipe from")
    include_tags: bool = Field(default=False, description="Ask Mealie to import scraped tags")
    include_categories: bool = Field(default=False, description="Ask Mealie to import scraped categories")


def setup_recipe_tools(mcp_server, client_provider):
    """Setup recipe tools with the main MCP server."""
    
    @mcp_server.tool()
    async def search_recipes(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search for recipes in Mealie with advanced filtering options."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}
            
            if filters is None:
                filters = {}
            
            search_filters = RecipeSearchFilters(**filters)
            return await _async_search_recipes(search_filters, client)
        except Exception as e:
            logger.error(f"Recipe search failed: {e}")
            return {"error": str(e)}
    
    @mcp_server.tool()
    async def get_recipe(recipe_id: str) -> Dict[str, Any]:
        """Get detailed recipe information by ID or slug."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}
            
            return await _async_get_recipe(recipe_id, client)
        except Exception as e:
            logger.error(f"Get recipe failed: {e}")
            return {"error": str(e)}
    
    @mcp_server.tool()
    async def create_recipe(recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new recipe in Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}
            
            return await _async_create_recipe(recipe_data, client)
        except Exception as e:
            logger.error(f"Create recipe failed: {e}")
            return {"error": str(e)}
    
    @mcp_server.tool()
    async def update_recipe(recipe_id: str, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing recipe in Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}
            
            return await _async_update_recipe(recipe_id, recipe_data, client)
        except Exception as e:
            logger.error(f"Update recipe failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def patch_recipe(recipe_id: str, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update an existing recipe in Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.patch(f"/api/recipes/{recipe_id}", recipe_data)
            return {"recipe": response, "message": "Recipe patched successfully"}
        except Exception as e:
            logger.error(f"Patch recipe failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def upload_recipe_image(
        recipe_id: str,
        image_base64: str,
        extension: str = "png",
    ) -> Dict[str, Any]:
        """Upload or replace a recipe image from base64-encoded image data."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            return await _async_upload_recipe_image(recipe_id, image_base64, extension, client)
        except Exception as e:
            logger.error(f"Upload recipe image failed: {e}")
            return {"error": str(e)}
    
    @mcp_server.tool()
    async def delete_recipe(recipe_id: str) -> Dict[str, Any]:
        """Delete a recipe from Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}
            
            return await _async_delete_recipe(recipe_id, client)
        except Exception as e:
            logger.error(f"Delete recipe failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def delete_recipe_image(recipe_id: str) -> Dict[str, Any]:
        """Delete a recipe image."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            await client.delete(f"/api/recipes/{recipe_id}/image")
            return {"message": f"Recipe image deleted successfully for {recipe_id}"}
        except Exception as e:
            logger.error(f"Delete recipe image failed: {e}")
            return {"error": str(e)}
    
    @mcp_server.tool()
    async def import_recipe_from_url(
        url: str,
        include_tags: bool = False,
        include_categories: bool = False,
    ) -> Dict[str, Any]:
        """Import a recipe from a URL."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}
            
            return await _async_import_recipe_from_url(url, client, include_tags, include_categories)
        except Exception as e:
            logger.error(f"Import recipe failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def test_recipe_scrape_url(url: str, use_openai: bool = False) -> Dict[str, Any]:
        """Test whether Mealie can scrape a recipe URL."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.post(
                "/api/recipes/test-scrape-url",
                {"url": url, "useOpenAI": use_openai},
            )
            return {"result": response}
        except Exception as e:
            logger.error(f"Test recipe scrape URL failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def import_recipes_from_urls(imports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk import recipes from URLs using Mealie's bulk URL importer."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.post("/api/recipes/create/url/bulk", {"imports": imports})
            return {"result": response, "message": "Recipe URL bulk import started"}
        except Exception as e:
            logger.error(f"Bulk import recipes from URLs failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def import_recipe_from_html_or_json(data: str, url: Optional[str] = None, include_tags: bool = False, include_categories: bool = False) -> Dict[str, Any]:
        """Create a recipe from raw HTML or JSON recipe data."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            payload = {
                "data": data,
                "includeTags": include_tags,
                "includeCategories": include_categories,
            }
            if url is not None:
                payload["url"] = url
            response = await client.post("/api/recipes/create/html-or-json", payload)
            return {"recipe": response, "message": "Recipe imported from HTML/JSON successfully"}
        except Exception as e:
            logger.error(f"Import recipe from HTML/JSON failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def import_recipe_from_zip(archive_base64: str, filename: str = "recipes.zip") -> Dict[str, Any]:
        """Create recipes from a Mealie recipe ZIP archive encoded as base64."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            archive_bytes = _decode_base64_file(archive_base64)
            response = await client.post_multipart(
                "/api/recipes/create/zip",
                files={"archive": (filename, archive_bytes, "application/zip")},
            )
            return {"result": response, "message": "Recipe ZIP import completed"}
        except Exception as e:
            logger.error(f"Import recipe from ZIP failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def import_recipe_from_images(
        images_base64: List[str],
        filenames: Optional[List[str]] = None,
        translate_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a recipe from one or more base64-encoded images."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            files = []
            for index, image in enumerate(images_base64):
                filename = _filename_at(filenames, index, f"recipe-image-{index + 1}.png")
                files.append((
                    "images",
                    (filename, _decode_base64_file(image), _guess_content_type(filename)),
                ))
            params = {"translateLanguage": translate_language} if translate_language else None
            response = await client.post_multipart("/api/recipes/create/image", files=files, params=params)
            return {"recipe": response, "message": "Recipe imported from image successfully"}
        except Exception as e:
            logger.error(f"Import recipe from image failed: {e}")
            return {"error": str(e)}
    
    @mcp_server.tool()
    async def get_random_recipe() -> Dict[str, Any]:
        """Get a random recipe from Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}
            
            return await _async_get_random_recipe(client)
        except Exception as e:
            logger.error(f"Get random recipe failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_recipe_suggestions(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get recipe suggestions from Mealie using optional foods/tools filters."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get("/api/recipes/suggestions", filters or None)
            return {
                "recipes": response.get("items", []),
                "total": response.get("total", 0),
                "page": response.get("page", 1),
                "per_page": response.get("per_page", response.get("perPage")),
            }
        except Exception as e:
            logger.error(f"Get recipe suggestions failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def duplicate_recipe(recipe_id: str, duplicate_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Duplicate a recipe, optionally with a new name."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.post(f"/api/recipes/{recipe_id}/duplicate", duplicate_data or {})
            return {"recipe": response, "message": "Recipe duplicated successfully"}
        except Exception as e:
            logger.error(f"Duplicate recipe failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_recipe_last_made(recipe_id: str, timestamp: str) -> Dict[str, Any]:
        """Update the recipe last-made timestamp (ISO datetime string)."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.patch(f"/api/recipes/{recipe_id}/last-made", {"timestamp": timestamp})
            return {"recipe": response, "message": "Recipe last-made timestamp updated successfully"}
        except Exception as e:
            logger.error(f"Update recipe last-made failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_many_recipes(recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Replace/update multiple recipes through Mealie's batch endpoint."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.put("/api/recipes", recipes)
            return {"recipes": response, "message": "Recipes updated successfully"}
        except Exception as e:
            logger.error(f"Update many recipes failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def patch_many_recipes(recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Partially update multiple recipes through Mealie's batch endpoint."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.patch("/api/recipes", recipes)
            return {"recipes": response, "message": "Recipes patched successfully"}
        except Exception as e:
            logger.error(f"Patch many recipes failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def scrape_recipe_image(recipe_id: str, url: str, include_tags: bool = False, include_categories: bool = False) -> Dict[str, Any]:
        """Ask Mealie to scrape and set a recipe image from a URL."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.post(
                f"/api/recipes/{recipe_id}/image",
                {"url": url, "includeTags": include_tags, "includeCategories": include_categories},
            )
            return {"image": response, "message": "Recipe image scraped successfully"}
        except Exception as e:
            logger.error(f"Scrape recipe image failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def upload_recipe_asset(
        recipe_id: str,
        file_base64: str,
        name: str,
        icon: str,
        extension: str,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload an asset file to a recipe from base64-encoded data."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            clean_extension = extension.lower().lstrip(".")
            file_name = filename or f"{name}.{clean_extension}"
            response = await client.post_multipart(
                f"/api/recipes/{recipe_id}/assets",
                data={"name": name, "icon": icon, "extension": clean_extension},
                files={"file": (file_name, _decode_base64_file(file_base64), _guess_content_type(file_name))},
            )
            return {"asset": response, "message": "Recipe asset uploaded successfully"}
        except Exception as e:
            logger.error(f"Upload recipe asset failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def bulk_tag_recipes(bulk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply tags to multiple recipes."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.post("/api/recipes/bulk-actions/tag", bulk_data)
            return {"result": response, "message": "Bulk recipe tag action completed"}
        except Exception as e:
            logger.error(f"Bulk tag recipes failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def bulk_categorize_recipes(bulk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply categories to multiple recipes."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.post("/api/recipes/bulk-actions/categorize", bulk_data)
            return {"result": response, "message": "Bulk recipe categorize action completed"}
        except Exception as e:
            logger.error(f"Bulk categorize recipes failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def bulk_update_recipe_settings(bulk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply recipe settings to multiple recipes."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.post("/api/recipes/bulk-actions/settings", bulk_data)
            return {"result": response, "message": "Bulk recipe settings action completed"}
        except Exception as e:
            logger.error(f"Bulk update recipe settings failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def bulk_delete_recipes(bulk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Delete multiple recipes through Mealie's bulk action endpoint."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.post("/api/recipes/bulk-actions/delete", bulk_data)
            return {"result": response, "message": "Bulk recipe delete action completed"}
        except Exception as e:
            logger.error(f"Bulk delete recipes failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def bulk_export_recipes(bulk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start a bulk recipe export."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.post("/api/recipes/bulk-actions/export", bulk_data)
            return {"result": response, "message": "Bulk recipe export started"}
        except Exception as e:
            logger.error(f"Bulk export recipes failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def list_recipe_exports() -> Dict[str, Any]:
        """List recipe export jobs/files."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get("/api/recipes/bulk-actions/export")
            return {"exports": response}
        except Exception as e:
            logger.error(f"List recipe exports failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def purge_recipe_exports() -> Dict[str, Any]:
        """Purge recipe export jobs/files."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.delete("/api/recipes/bulk-actions/export/purge")
            return {"result": response, "message": "Recipe exports purged"}
        except Exception as e:
            logger.error(f"Purge recipe exports failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def download_recipe_export(export_id: str) -> Dict[str, Any]:
        """Download a bulk recipe export as base64 content."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            content = await client.get_raw(f"/api/recipes/bulk-actions/export/{export_id}/download")
            return {"download": content}
        except Exception as e:
            logger.error(f"Download recipe export failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def list_recipe_export_formats() -> Dict[str, Any]:
        """List recipe export formats and templates available in Mealie."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get("/api/recipes/exports")
            return {"exports": response}
        except Exception as e:
            logger.error(f"List recipe export formats failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def export_recipe(recipe_id: str, template_name: str) -> Dict[str, Any]:
        """Export one recipe with a named Mealie template as base64 content."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            content = await client.get_raw(f"/api/recipes/{recipe_id}/exports", params={"template_name": template_name})
            return {"download": content}
        except Exception as e:
            logger.error(f"Export recipe failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_shared_recipe(token_id: str) -> Dict[str, Any]:
        """Read a shared recipe by share token ID."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get(f"/api/recipes/shared/{token_id}")
            return {"recipe": response}
        except Exception as e:
            logger.error(f"Get shared recipe failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def download_shared_recipe_zip(token_id: str) -> Dict[str, Any]:
        """Download a shared recipe ZIP as base64 content."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            content = await client.get_raw(f"/api/recipes/shared/{token_id}/zip")
            return {"download": content}
        except Exception as e:
            logger.error(f"Download shared recipe ZIP failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_recipe_comments(recipe_id: str) -> Dict[str, Any]:
        """Get comments for a recipe."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get(f"/api/recipes/{recipe_id}/comments")
            if isinstance(response, dict):
                return {"comments": response.get("items", response)}
            return {"comments": response}
        except Exception as e:
            logger.error(f"Get recipe comments failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def list_recipe_timeline_events(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List recipe timeline events with optional Mealie filters."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get("/api/recipes/timeline/events", filters or None)
            return {
                "events": response.get("items", []),
                "total": response.get("total", 0),
                "page": response.get("page", 1),
                "per_page": response.get("per_page", response.get("perPage")),
            }
        except Exception as e:
            logger.error(f"List recipe timeline events failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def create_recipe_timeline_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a recipe timeline event."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.post("/api/recipes/timeline/events", _normalize_timeline_event_payload(event_data))
            return {"event": response, "message": "Recipe timeline event created successfully"}
        except Exception as e:
            logger.error(f"Create recipe timeline event failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def get_recipe_timeline_event(event_id: str) -> Dict[str, Any]:
        """Get one recipe timeline event."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.get(f"/api/recipes/timeline/events/{event_id}")
            return {"event": response}
        except Exception as e:
            logger.error(f"Get recipe timeline event failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def update_recipe_timeline_event(event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update one recipe timeline event."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            response = await client.put(f"/api/recipes/timeline/events/{event_id}", _normalize_timeline_event_payload(event_data))
            return {"event": response, "message": "Recipe timeline event updated successfully"}
        except Exception as e:
            logger.error(f"Update recipe timeline event failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def delete_recipe_timeline_event(event_id: str) -> Dict[str, Any]:
        """Delete one recipe timeline event."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            await client.delete(f"/api/recipes/timeline/events/{event_id}")
            return {"message": f"Recipe timeline event {event_id} deleted successfully"}
        except Exception as e:
            logger.error(f"Delete recipe timeline event failed: {e}")
            return {"error": str(e)}

    @mcp_server.tool()
    async def upload_recipe_timeline_event_image(event_id: str, image_base64: str, extension: str = "png") -> Dict[str, Any]:
        """Upload or replace a timeline event image from base64-encoded image data."""
        try:
            client = client_provider()
            if not client:
                return {"error": "Mealie client not initialized"}

            clean_extension = extension.lower().lstrip(".")
            filename = f"timeline-event-image.{clean_extension}"
            response = await client.put_multipart(
                f"/api/recipes/timeline/events/{event_id}/image",
                data={"extension": clean_extension},
                files={"image": (filename, _decode_base64_file(image_base64), _guess_content_type(filename))},
            )
            return {"image": response, "message": "Recipe timeline event image uploaded successfully"}
        except Exception as e:
            logger.error(f"Upload recipe timeline event image failed: {e}")
            return {"error": str(e)}


# Internal async functions
async def _async_search_recipes(filters: RecipeSearchFilters, client: MealieClient) -> Dict[str, Any]:
    """Internal async recipe search function."""
    try:
        params = {}
        
        if filters.query:
            params['search'] = filters.query
        
        # Add pagination
        params['page'] = filters.page
        params['perPage'] = min(filters.per_page, 100)  # Limit to 100
        
        list_filters = {
            "categories": filters.categories or ([filters.category] if filters.category else None),
            "tags": filters.tags or filters.include_tags,
            "tools": filters.tools,
            "foods": filters.foods,
            "households": filters.households,
        }
        for key, value in list_filters.items():
            if value:
                params[key] = value

        scalar_filters = {
            "cookbook": filters.cookbook,
            "orderBy": filters.order_by,
            "orderByNullPosition": filters.order_by_null_position,
            "orderDirection": filters.order_direction,
            "queryFilter": filters.query_filter,
            "paginationSeed": filters.pagination_seed,
            "requireAllCategories": filters.require_all_categories,
            "requireAllTags": filters.require_all_tags,
            "requireAllTools": filters.require_all_tools,
            "requireAllFoods": filters.require_all_foods,
        }
        for key, value in scalar_filters.items():
            if value is not None:
                params[key] = value
        
        response = await client.get("/api/recipes", params=params)
        
        return {
            "recipes": response.get("items", []),
            "total": response.get("total", 0),
            "page": response.get("page", filters.page),
            "per_page": response.get("per_page", response.get("perPage", filters.per_page)),
            "total_pages": response.get("total_pages", response.get("totalPages", 1))
        }
        
    except MealieAPIError as e:
        logger.error(f"Recipe search API error: {e}")
        return {"error": f"API error: {e}"}
    except Exception as e:
        logger.error(f"Recipe search failed: {e}")
        return {"error": f"Search failed: {e}"}


async def _async_get_recipe(recipe_id: str, client: MealieClient) -> Dict[str, Any]:
    """Internal async get recipe function."""
    try:
        recipe = await client.get(f"/api/recipes/{recipe_id}")
        return {"recipe": recipe}
    except MealieAPIError as e:
        if "not found" in str(e).lower():
            return {"error": f"Recipe not found: {recipe_id}"}
        return {"error": f"API error: {e}"}
    except Exception as e:
        logger.error(f"Get recipe failed: {e}")
        return {"error": f"Failed to get recipe: {e}"}


async def _async_create_recipe(recipe_data: Dict[str, Any], client: MealieClient) -> Dict[str, Any]:
    """Internal async create recipe function."""
    try:
        # Validate recipe data
        errors = validate_recipe_data(recipe_data)
        if errors:
            return {"error": "Validation failed", "errors": errors}

        response = await client.post("/api/recipes", {"name": recipe_data["name"]})
        has_extra_recipe_fields = any(key != "name" for key in recipe_data)
        if has_extra_recipe_fields:
            recipe_slug = _extract_recipe_slug(response)
            if not recipe_slug:
                return {
                    "recipe": response,
                    "warning": "Recipe was created, but the response did not include a slug for applying full recipe data.",
                }
            response = await client.patch(f"/api/recipes/{recipe_slug}", recipe_data)
        return {"recipe": response, "message": "Recipe created successfully"}
    except MealieAPIError as e:
        return {"error": f"API error: {e}"}
    except Exception as e:
        logger.error(f"Create recipe failed: {e}")
        return {"error": f"Failed to create recipe: {e}"}


async def _async_update_recipe(recipe_id: str, recipe_data: Dict[str, Any], client: MealieClient) -> Dict[str, Any]:
    """Internal async update recipe function."""
    try:
        # Validate recipe data
        errors = validate_recipe_data(recipe_data)
        if errors:
            return {"error": "Validation failed", "errors": errors}
        
        response = await client.put(f"/api/recipes/{recipe_id}", recipe_data)
        return {"recipe": response, "message": "Recipe updated successfully"}
    except MealieAPIError as e:
        if "not found" in str(e).lower():
            return {"error": f"Recipe not found: {recipe_id}"}
        return {"error": f"API error: {e}"}
    except Exception as e:
        logger.error(f"Update recipe failed: {e}")
        return {"error": f"Failed to update recipe: {e}"}


async def _async_upload_recipe_image(
    recipe_id: str,
    image_base64: str,
    extension: str,
    client: MealieClient,
) -> Dict[str, Any]:
    """Internal async recipe image upload function."""
    try:
        clean_extension = extension.lower().lstrip(".")
        if clean_extension not in {"png", "jpg", "jpeg", "webp"}:
            return {"error": "Unsupported image extension. Use png, jpg, jpeg, or webp."}

        encoded = image_base64.strip()
        if "," in encoded and encoded.split(",", 1)[0].startswith("data:"):
            encoded = encoded.split(",", 1)[1]

        try:
            image_bytes = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            return {"error": f"Invalid base64 image data: {exc}"}

        if not image_bytes:
            return {"error": "Image data is empty"}
        if len(image_bytes) > 15 * 1024 * 1024:
            return {"error": "Image is too large; maximum supported size is 15 MB"}

        response = await client.upload_recipe_image(recipe_id, image_bytes, clean_extension)
        return {
            "image": response.get("image"),
            "message": f"Recipe image uploaded successfully for {recipe_id}",
        }
    except MealieAPIError as e:
        if "not found" in str(e).lower():
            return {"error": f"Recipe not found: {recipe_id}"}
        return {"error": f"API error: {e}"}
    except Exception as e:
        logger.error(f"Upload recipe image failed: {e}")
        return {"error": f"Failed to upload recipe image: {e}"}


async def _async_delete_recipe(recipe_id: str, client: MealieClient) -> Dict[str, Any]:
    """Internal async delete recipe function."""
    try:
        await client.delete(f"/api/recipes/{recipe_id}")
        return {"message": f"Recipe {recipe_id} deleted successfully"}
    except MealieAPIError as e:
        if "not found" in str(e).lower():
            return {"error": f"Recipe not found: {recipe_id}"}
        return {"error": f"API error: {e}"}
    except Exception as e:
        logger.error(f"Delete recipe failed: {e}")
        return {"error": f"Failed to delete recipe: {e}"}


async def _async_import_recipe_from_url(
    url: str,
    client: MealieClient,
    include_tags: bool = False,
    include_categories: bool = False,
) -> Dict[str, Any]:
    """Internal async import recipe function."""
    try:
        import_data = {
            "url": url,
            "includeTags": include_tags,
            "includeCategories": include_categories,
        }
        response = await client.post("/api/recipes/create/url", import_data)
        return {"recipe": response, "message": f"Recipe imported successfully from {url}"}
    except MealieAPIError as e:
        return {"error": f"API error: {e}"}
    except Exception as e:
        logger.error(f"Import recipe failed: {e}")
        return {"error": f"Failed to import recipe: {e}"}


async def _async_get_random_recipe(client: MealieClient) -> Dict[str, Any]:
    """Internal async get random recipe function."""
    try:
        response = await client.get("/api/recipes", params={"page": 1, "perPage": 100})
        recipes = response.get("items", [])
        if not recipes:
            return {"error": "No recipes found"}

        selected = random.choice(recipes)
        slug = selected.get("slug") or selected.get("id")
        if not slug:
            return {"recipe": selected}

        recipe = await client.get(f"/api/recipes/{slug}")
        return {"recipe": recipe}
    except MealieAPIError as e:
        return {"error": f"API error: {e}"}
    except Exception as e:
        logger.error(f"Get random recipe failed: {e}")
        return {"error": f"Failed to get random recipe: {e}"}


def _extract_recipe_slug(response: Any) -> Optional[str]:
    """Extract a recipe slug from Mealie's create response."""
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        for key in ("slug", "id"):
            if response.get(key):
                return response[key]

    return None


def _decode_base64_file(encoded: str) -> bytes:
    """Decode plain or data-URL base64 input."""
    data = encoded.strip()
    if "," in data and data.split(",", 1)[0].startswith("data:"):
        data = data.split(",", 1)[1]
    try:
        decoded = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"Invalid base64 file data: {exc}") from exc
    if not decoded:
        raise ValueError("File data is empty")
    return decoded


def _filename_at(filenames: Optional[List[str]], index: int, fallback: str) -> str:
    if filenames and index < len(filenames) and filenames[index]:
        return filenames[index]
    return fallback


def _guess_content_type(filename: str) -> str:
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def _normalize_timeline_event_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    aliases = {
        "recipe_id": "recipeId",
        "user_id": "userId",
        "event_type": "eventType",
        "event_message": "eventMessage",
    }
    return {aliases.get(key, key): value for key, value in data.items() if value is not None}


# Utility function
def validate_recipe_data(recipe_data: Dict[str, Any]) -> List[str]:
    """Validate recipe data and return list of validation errors.
    
    Args:
        recipe_data: Recipe data dictionary to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Required fields
    if not recipe_data.get('name'):
        errors.append("Recipe name is required")
    
    # Validate ingredients
    ingredients = recipe_data.get('recipe_ingredient', [])
    if ingredients:
        for i, ingredient in enumerate(ingredients):
            if not ingredient.get('title') and not ingredient.get('text'):
                errors.append(f"Ingredient {i+1}: Either title or text is required")
    
    # Validate instructions
    instructions = recipe_data.get('recipe_instructions', [])
    if instructions:
        for i, instruction in enumerate(instructions):
            if not instruction.get('text'):
                errors.append(f"Instruction {i+1}: Text is required")
    
    # Validate rating
    rating = recipe_data.get('rating')
    if rating is not None and (rating < 1 or rating > 5):
        errors.append("Rating must be between 1 and 5")
    
    return errors


# Export all tools for the MCP server
__all__ = [
    'setup_recipe_tools',
    'RecipeSearchFilters',
    'RecipeCreateUpdate', 
    'RecipeImportUrl',
    'RecipeIngredient',
    'RecipeInstruction',
    'RecipeNutrition',
    'validate_recipe_data'
]
