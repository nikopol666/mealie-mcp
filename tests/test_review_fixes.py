"""Regression tests for path escaping, non-JSON responses and slug resolution."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
import sys
from unittest.mock import AsyncMock

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mealie_client import MealieAPIError, MealieClient, path_param
from tools.recipes import _async_delete_recipe, _async_upload_recipe_image


def _client_with_transport(handler) -> MealieClient:
    client = MealieClient(base_url="http://mealie.test", api_token="test-token")
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return client


@pytest.mark.parametrize(
    ("raw", "escaped"),
    [
        ("my-recipe", "my-recipe"),
        ("../admin/users", "..%2Fadmin%2Fusers"),
        ("a?b#c", "a%3Fb%23c"),
        ("x y/z", "x%20y%2Fz"),
    ],
)
def test_path_param_escapes_single_segment(raw, escaped):
    assert path_param(raw) == escaped


@pytest.mark.parametrize("raw", ["", ".", ".."])
def test_path_param_rejects_dot_and_empty_segments(raw):
    with pytest.raises(MealieAPIError):
        path_param(raw)


@pytest.mark.parametrize("endpoint", ["/api/recipes/../admin/users", "/api/recipes/%2e%2e/admin", "/api/./x"])
def test_build_url_rejects_dot_segments(endpoint):
    client = MealieClient(base_url="http://mealie.test", api_token="test-token")
    with pytest.raises(MealieAPIError):
        client._build_url(endpoint)


def test_delete_recipe_cannot_escape_recipe_endpoint():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.raw_path.decode())
        return httpx.Response(200, json={})

    client = _client_with_transport(handler)
    result = asyncio.run(_async_delete_recipe("../admin/users/1", client))

    assert "error" not in result
    assert seen == ["/api/recipes/..%2Fadmin%2Fusers%2F1"]


def test_delete_recipe_with_dot_dot_id_is_rejected_without_request():
    client = _client_with_transport(lambda request: pytest.fail("no request expected"))
    result = asyncio.run(_async_delete_recipe("..", client))
    assert "error" in result


def test_non_json_response_raises_mealie_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>proxy login</html>", headers={"content-type": "text/html"})

    client = _client_with_transport(handler)
    with pytest.raises(MealieAPIError, match="non-JSON"):
        asyncio.run(client.get("/api/app/about"))


def test_raw_request_with_broken_json_falls_back_to_base64():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"{broken", headers={"content-type": "application/json"})

    client = _client_with_transport(handler)
    result = asyncio.run(client.get_raw("/api/recipes/x/exports"))
    assert base64.b64decode(result["content_base64"]) == b"{broken"


def test_upload_recipe_image_resolves_uuid_to_slug():
    recipe_uuid = "0b9d3f4e-1234-4c3a-9a6b-1f2e3d4c5b6a"
    client = AsyncMock()
    client.get_recipe.return_value = {"id": recipe_uuid, "slug": "svickova-na-smetane"}
    client.upload_recipe_image.return_value = {"image": "abc"}
    image = base64.b64encode(b"\x89PNG fake").decode()

    result = asyncio.run(_async_upload_recipe_image(recipe_uuid, image, "png", client))

    client.get_recipe.assert_awaited_once_with(recipe_uuid)
    client.upload_recipe_image.assert_awaited_once()
    assert client.upload_recipe_image.await_args.args[0] == "svickova-na-smetane"
    assert result["image"] == "abc"
    assert "svickova-na-smetane" in result["message"]


def test_upload_recipe_image_falls_back_to_given_reference_without_slug():
    client = AsyncMock()
    client.get_recipe.return_value = {}
    client.upload_recipe_image.return_value = {"image": "abc"}
    image = base64.b64encode(b"img").decode()

    asyncio.run(_async_upload_recipe_image("plain-slug", image, "jpg", client))

    assert client.upload_recipe_image.await_args.args[0] == "plain-slug"


def test_upload_recipe_image_escapes_slug_in_url():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.raw_path.decode())
        return httpx.Response(200, json={"image": "x"})

    client = MealieClient(base_url="http://mealie.test", api_token="test-token")
    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    class PatchedClient(original):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    httpx.AsyncClient = PatchedClient
    try:
        asyncio.run(client.upload_recipe_image("a/b", b"img", "png"))
    finally:
        httpx.AsyncClient = original

    assert seen == ["/api/recipes/a%2Fb/image"]
