"""HTTP client for interacting with Mealie API."""

import asyncio
import base64
import httpx
import logging
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urljoin

from config import settings

logger = logging.getLogger(__name__)


class MealieAPIError(Exception):
    """Exception raised for Mealie API errors."""
    pass


class MealieClient:
    """HTTP client for Mealie API operations."""
    
    def __init__(self, base_url: str = None, api_token: str = None):
        self.base_url = (base_url or settings.mealie_base_url).rstrip("/")
        self.api_token = api_token or settings.mealie_api_token
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Configure HTTP client with timeout and retries
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=settings.request_timeout,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Mealie API."""
        url = urljoin(f"{self.base_url}/", endpoint.lstrip("/"))
        method_upper = method.upper()
        retryable_statuses = {502, 503, 504}
        attempts = max(1, settings.max_retries)
        
        for attempt in range(1, attempts + 1):
            try:
                logger.debug(f"{method_upper} {url} (attempt {attempt}/{attempts})")
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=data if method_upper in ["POST", "PUT", "PATCH"] else None,
                    params=params
                )
                response.raise_for_status()
                
                if response.content:
                    return response.json()
                return {}
                
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                if method_upper == "GET" and status_code in retryable_statuses and attempt < attempts:
                    await asyncio.sleep(min(2 ** (attempt - 1), 5))
                    continue
                logger.error(f"HTTP {status_code} error: {e.response.text}")
                raise MealieAPIError(f"API request failed: {status_code} - {e.response.text}")
            except httpx.RequestError as e:
                if method_upper == "GET" and attempt < attempts:
                    logger.warning(f"Request error on attempt {attempt}/{attempts}: {str(e)}")
                    await asyncio.sleep(min(2 ** (attempt - 1), 5))
                    continue
                logger.error(f"Request error: {str(e)}")
                raise MealieAPIError(f"Request failed: {str(e)}")

        raise MealieAPIError("Request failed after retries")

    async def _multipart_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a multipart/form-data request to Mealie."""
        url = urljoin(f"{self.base_url}/", endpoint.lstrip("/"))
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as upload_client:
                response = await upload_client.request(
                    method=method,
                    url=url,
                    data=data,
                    files=files,
                    params=params,
                    headers=headers,
                )
            response.raise_for_status()

            if not response.content:
                return {}
            try:
                return response.json()
            except ValueError:
                return {"content": response.text}
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error(f"HTTP {status_code} error: {e.response.text}")
            raise MealieAPIError(f"API request failed: {status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise MealieAPIError(f"Request failed: {str(e)}")

    async def _raw_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return a non-JSON Mealie response as base64-safe MCP data."""
        url = urljoin(f"{self.base_url}/", endpoint.lstrip("/"))
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "*/*",
        }

        try:
            response = await self.client.request(method=method, url=url, params=params, headers=headers)
            response.raise_for_status()
            content_type = response.headers.get("content-type")
            if content_type and "application/json" in content_type and response.content:
                return {
                    "json": response.json(),
                    "content_type": content_type,
                    "content_disposition": response.headers.get("content-disposition"),
                    "size": len(response.content),
                }
            return {
                "content_base64": base64.b64encode(response.content).decode("ascii"),
                "content_type": content_type,
                "content_disposition": response.headers.get("content-disposition"),
                "size": len(response.content),
            }
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error(f"HTTP {status_code} error: {e.response.text}")
            raise MealieAPIError(f"API request failed: {status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise MealieAPIError(f"Request failed: {str(e)}")
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request to Mealie API."""
        return await self._request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, data: Any) -> Dict[str, Any]:
        """POST request to Mealie API."""
        return await self._request("POST", endpoint, data=data)
    
    async def put(self, endpoint: str, data: Any) -> Dict[str, Any]:
        """PUT request to Mealie API."""
        return await self._request("PUT", endpoint, data=data)
    
    async def patch(self, endpoint: str, data: Any) -> Dict[str, Any]:
        """PATCH request to Mealie API."""
        return await self._request("PATCH", endpoint, data=data)
    
    async def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """DELETE request to Mealie API."""
        return await self._request("DELETE", endpoint, params=params)

    async def post_multipart(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """POST multipart/form-data to Mealie."""
        return await self._multipart_request("POST", endpoint, data=data, files=files, params=params)

    async def put_multipart(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """PUT multipart/form-data to Mealie."""
        return await self._multipart_request("PUT", endpoint, data=data, files=files, params=params)

    async def get_raw(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET a binary or arbitrary response from Mealie as base64."""
        return await self._raw_request("GET", endpoint, params=params)
    
    # Recipe operations
    async def search_recipes(
        self, 
        query: str = "", 
        page: int = 1, 
        per_page: int = 10,
        include_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Search for recipes."""
        params = {
            "search": query,
            "page": page,
            "perPage": per_page
        }
        if include_tags:
            params["tags"] = include_tags
            
        return await self.get("/api/recipes", params)
    
    async def get_recipe(self, recipe_id: str) -> Dict[str, Any]:
        """Get a specific recipe by ID."""
        return await self.get(f"/api/recipes/{recipe_id}")
    
    async def create_recipe(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new recipe."""
        return await self.post("/api/recipes", recipe_data)
    
    async def update_recipe(self, recipe_id: str, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing recipe."""
        return await self.put(f"/api/recipes/{recipe_id}", recipe_data)

    async def upload_recipe_image(self, recipe_id: str, image_bytes: bytes, extension: str) -> Dict[str, Any]:
        """Upload or replace a recipe image."""
        url = urljoin(f"{self.base_url}/", f"/api/recipes/{recipe_id}/image".lstrip("/"))
        clean_extension = extension.lower().lstrip(".")
        media_type = "image/jpeg" if clean_extension in {"jpg", "jpeg"} else f"image/{clean_extension}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as upload_client:
                response = await upload_client.request(
                    method="PUT",
                    url=url,
                    data={"extension": clean_extension},
                    files={
                        "image": (
                            f"recipe-image.{clean_extension}",
                            image_bytes,
                            media_type,
                        )
                    },
                    headers=headers,
                )
            response.raise_for_status()

            if response.content:
                return response.json()
            return {}
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error(f"HTTP {status_code} error: {e.response.text}")
            raise MealieAPIError(f"API request failed: {status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise MealieAPIError(f"Request failed: {str(e)}")
    
    async def delete_recipe(self, recipe_id: str) -> Dict[str, Any]:
        """Delete a recipe."""
        return await self.delete(f"/api/recipes/{recipe_id}")
    
    async def import_recipe_from_url(self, url: str) -> Dict[str, Any]:
        """Import a recipe from a URL."""
        return await self.post("/api/recipes/create/url", {"url": url})
    
    # Meal plan operations
    async def get_meal_plans(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get meal plans for a date range."""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return await self.get("/api/households/mealplans", params)
    
    async def create_meal_plan_entry(self, meal_plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new meal plan entry."""
        return await self.post("/api/households/mealplans", meal_plan_data)
    
    async def update_meal_plan_entry(self, meal_plan_id: str, meal_plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a meal plan entry."""
        return await self.put(f"/api/households/mealplans/{meal_plan_id}", meal_plan_data)
    
    async def delete_meal_plan_entry(self, meal_plan_id: str) -> Dict[str, Any]:
        """Delete a meal plan entry."""
        return await self.delete(f"/api/households/mealplans/{meal_plan_id}")
    
    # Shopping list operations
    async def get_shopping_lists(self) -> Dict[str, Any]:
        """Get all shopping lists."""
        return await self.get("/api/households/shopping/lists")
    
    async def create_shopping_list(self, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Create a new shopping list."""
        payload = {"name": data} if isinstance(data, str) else data
        return await self.post("/api/households/shopping/lists", payload)
    
    async def get_shopping_list(self, list_id: str) -> Dict[str, Any]:
        """Get a specific shopping list."""
        return await self.get(f"/api/households/shopping/lists/{list_id}")

    async def update_shopping_list(self, list_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a shopping list."""
        return await self.put(f"/api/households/shopping/lists/{list_id}", data)

    async def delete_shopping_list(self, list_id: str) -> Dict[str, Any]:
        """Delete a shopping list."""
        return await self.delete(f"/api/households/shopping/lists/{list_id}")

    async def get_shopping_items(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get all shopping list items."""
        return await self.get("/api/households/shopping/items", params=params)

    async def get_shopping_item(self, item_id: str) -> Dict[str, Any]:
        """Get a specific shopping list item."""
        return await self.get(f"/api/households/shopping/items/{item_id}")
    
    async def add_shopping_item(self, list_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to a shopping list."""
        payload = dict(item_data)
        payload.setdefault("shoppingListId", list_id)
        return await self.post("/api/households/shopping/items", payload)
    
    async def update_shopping_item(self, list_id: str, item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a shopping list item."""
        payload = dict(item_data)
        payload.setdefault("shoppingListId", list_id)
        return await self.put(f"/api/households/shopping/items/{item_id}", payload)
    
    async def delete_shopping_item(self, list_id: str, item_id: str) -> Dict[str, Any]:
        """Delete a shopping list item."""
        return await self.delete(f"/api/households/shopping/items/{item_id}")

    async def create_shopping_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple shopping list items."""
        return await self.post("/api/households/shopping/items/create-bulk", items)

    async def update_shopping_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update multiple shopping list items."""
        return await self.put("/api/households/shopping/items", items)

    async def delete_shopping_items(self, item_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple shopping list items."""
        return await self.delete("/api/households/shopping/items", params={"ids": item_ids})

    async def add_recipe_to_shopping_list(
        self,
        list_id: str,
        recipe_id: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a recipe's ingredients to a shopping list."""
        return await self.post(f"/api/households/shopping/lists/{list_id}/recipe/{recipe_id}", data or {})

    async def add_recipes_to_shopping_list(self, list_id: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add multiple recipes' ingredients to a shopping list."""
        return await self.post(f"/api/households/shopping/lists/{list_id}/recipe", data)

    async def remove_recipe_from_shopping_list(
        self,
        list_id: str,
        recipe_id: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Remove a recipe's ingredients from a shopping list."""
        return await self.post(f"/api/households/shopping/lists/{list_id}/recipe/{recipe_id}/delete", data or {})

    async def update_shopping_list_label_settings(self, list_id: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update shopping list label ordering/settings."""
        return await self.put(f"/api/households/shopping/lists/{list_id}/label-settings", data)

    # Foods operations
    async def get_foods(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get all foods with optional filtering."""
        return await self.get("/api/foods", params=params)

    async def get_food(self, food_id: str) -> Dict[str, Any]:
        """Get a specific food by ID."""
        return await self.get(f"/api/foods/{food_id}")

    async def create_food(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new food."""
        return await self.post("/api/foods", food_data)

    async def update_food(self, food_id: str, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing food."""
        return await self.put(f"/api/foods/{food_id}", food_data)

    async def delete_food(self, food_id: str) -> Dict[str, Any]:
        """Delete a food."""
        return await self.delete(f"/api/foods/{food_id}")

    async def search_foods(self, query: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Search for foods."""
        params = {
            "search": query,
            "page": page,
            "perPage": per_page
        }
        return await self.get("/api/foods", params=params)

    async def merge_foods(self, from_food_id: str, to_food_id: str) -> Dict[str, Any]:
        """Merge one food into another."""
        merge_data = {
            "fromFood": from_food_id,
            "toFood": to_food_id
        }
        return await self.put("/api/foods/merge", merge_data)

    # Units operations
    async def get_units(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get all units with optional filtering."""
        return await self.get("/api/units", params=params)

    async def get_unit(self, unit_id: str) -> Dict[str, Any]:
        """Get a specific unit by ID."""
        return await self.get(f"/api/units/{unit_id}")

    async def create_unit(self, unit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new unit."""
        return await self.post("/api/units", unit_data)

    async def update_unit(self, unit_id: str, unit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing unit."""
        return await self.put(f"/api/units/{unit_id}", unit_data)

    async def delete_unit(self, unit_id: str) -> Dict[str, Any]:
        """Delete a unit."""
        return await self.delete(f"/api/units/{unit_id}")

    async def merge_units(self, from_unit_id: str, to_unit_id: str) -> Dict[str, Any]:
        """Merge one unit into another."""
        merge_data = {
            "fromUnit": from_unit_id,
            "toUnit": to_unit_id
        }
        return await self.put("/api/units/merge", merge_data)

    # Tags operations
    async def get_tags(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get all tags with optional filtering."""
        return await self.get("/api/organizers/tags", params=params)

    async def get_tag(self, tag_id: str) -> Dict[str, Any]:
        """Get a specific tag by ID."""
        return await self.get(f"/api/organizers/tags/{tag_id}")

    async def create_tag(self, tag_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tag."""
        return await self.post("/api/organizers/tags", tag_data)

    async def update_tag(self, tag_id: str, tag_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing tag."""
        return await self.put(f"/api/organizers/tags/{tag_id}", tag_data)

    async def delete_tag(self, tag_id: str) -> Dict[str, Any]:
        """Delete a tag."""
        return await self.delete(f"/api/organizers/tags/{tag_id}")

    # Categories operations
    async def get_categories(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get all categories with optional filtering."""
        return await self.get("/api/organizers/categories", params=params)

    async def get_category(self, category_id: str) -> Dict[str, Any]:
        """Get a specific category by ID."""
        return await self.get(f"/api/organizers/categories/{category_id}")

    async def create_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new category."""
        return await self.post("/api/organizers/categories", category_data)

    async def update_category(self, category_id: str, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing category."""
        return await self.put(f"/api/organizers/categories/{category_id}", category_data)

    async def delete_category(self, category_id: str) -> Dict[str, Any]:
        """Delete a category."""
        return await self.delete(f"/api/organizers/categories/{category_id}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
