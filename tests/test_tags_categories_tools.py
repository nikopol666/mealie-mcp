"""Tests for tag/category response normalization."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.tags_categories import setup_tag_category_tools  # noqa: E402


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def register(func):
            self.tools[func.__name__] = func
            return func

        return register


class FakeClient:
    async def get_tags(self):
        return [{"id": "tag-1", "name": "tag"}]

    async def get_categories(self):
        return {"items": [{"id": "category-1", "name": "category"}]}

    async def get(self, endpoint, params=None):
        if endpoint == "/api/organizers/tags/empty":
            return [{"id": "empty-tag", "name": "empty tag"}]
        if endpoint == "/api/organizers/categories/empty":
            return [{"id": "empty-category", "name": "empty category"}]
        raise AssertionError(f"Unexpected endpoint: {endpoint}")


def registered_tools():
    mcp = FakeMCP()
    setup_tag_category_tools(mcp, lambda: FakeClient())
    return mcp.tools


def test_list_tags_accepts_plain_list_response():
    result = asyncio.run(registered_tools()["list_tags"]())

    assert result == {"tags": [{"id": "tag-1", "name": "tag"}]}


def test_list_empty_tags_accepts_plain_list_response():
    result = asyncio.run(registered_tools()["list_empty_tags"]())

    assert result == {"tags": [{"id": "empty-tag", "name": "empty tag"}]}


def test_list_categories_accepts_paginated_response():
    result = asyncio.run(registered_tools()["list_categories"]())

    assert result == {"categories": [{"id": "category-1", "name": "category"}]}


def test_list_empty_categories_accepts_plain_list_response():
    result = asyncio.run(registered_tools()["list_empty_categories"]())

    assert result == {
        "categories": [{"id": "empty-category", "name": "empty category"}]
    }
