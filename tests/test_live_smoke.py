"""Opt-in live smoke tests for a real Mealie instance.

These tests are read-only and are skipped unless MEALIE_LIVE_SMOKE=1 is set.
They are intended for release checks, not for normal unit-test runs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mealie_client import MealieAPIError, MealieClient


def _live_client() -> MealieClient:
    if os.getenv("MEALIE_LIVE_SMOKE") != "1":
        pytest.skip("set MEALIE_LIVE_SMOKE=1 to run read-only live Mealie smoke tests")

    base_url = os.getenv("MEALIE_BASE_URL")
    api_token = os.getenv("MEALIE_API_TOKEN")
    if not base_url:
        pytest.skip("MEALIE_BASE_URL is required for live smoke tests")
    if not api_token or api_token == "test-token":
        pytest.skip("a real MEALIE_API_TOKEN is required for live smoke tests")

    return MealieClient(base_url=base_url, api_token=api_token)


async def _get(client: MealieClient, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        result = await client.get(endpoint, params=params)
    except MealieAPIError as exc:
        pytest.fail(f"GET {endpoint} failed: {exc}")

    assert isinstance(result, dict), f"GET {endpoint} returned non-object response"
    return result


@pytest.mark.asyncio
async def test_live_core_read_endpoints_are_compatible_with_current_mealie():
    client = _live_client()

    try:
        about = await _get(client, "/api/app/about")
        assert about.get("version"), "app about response should include a Mealie version"

        paged_endpoints = [
            "/api/recipes",
            "/api/foods",
            "/api/units",
            "/api/organizers/tags",
            "/api/organizers/categories",
            "/api/organizers/tools",
            "/api/households/cookbooks",
            "/api/households/shopping/lists",
            "/api/households/shopping/items",
        ]
        for endpoint in paged_endpoints:
            await _get(client, endpoint, {"page": 1, "perPage": 1})
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_live_current_user_group_and_household_endpoints_are_reachable():
    client = _live_client()

    try:
        for endpoint in [
            "/api/users/self",
            "/api/groups/self",
            "/api/households/self",
            "/api/households/statistics",
            "/api/households/members",
            "/api/households/preferences",
        ]:
            await _get(client, endpoint)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_live_meal_plan_reads_are_reachable():
    client = _live_client()

    try:
        await _get(client, "/api/households/mealplans", {"page": 1, "perPage": 1})
        await _get(client, "/api/households/mealplans/today")
        await _get(client, "/api/households/mealplans/rules", {"page": 1, "perPage": 1})
    finally:
        await client.close()
