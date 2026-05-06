"""Regression tests for Docker/Portainer runtime stability."""

from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import AsyncMock

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import main
import mealie_client
from mealie_client import MealieAPIError, MealieClient


def test_http_health_route_exists_for_container_healthchecks(monkeypatch):
    mock_client = AsyncMock()
    mock_client.get.return_value = {"version": "test-version"}
    monkeypatch.setattr(main, "mealie_client", mock_client)

    response = main.asyncio.run(main.http_health_check(None))

    assert response.status_code == 200
    body = response.body.decode()
    assert '"status":"healthy"' in body
    assert "test-version" in body
    assert '"endpoint":"/mcp"' in body


def test_http_health_route_is_registered_before_server_start():
    route_paths = {getattr(route, "path", None) for route in main.mcp._custom_starlette_routes}
    assert "/health" in route_paths
    assert main.mcp.settings.streamable_http_path == "/mcp"


def test_http_health_route_stays_up_when_mealie_is_temporarily_down(monkeypatch):
    mock_client = AsyncMock()
    mock_client.get.side_effect = MealieAPIError("temporary failure")
    monkeypatch.setattr(main, "mealie_client", mock_client)

    response = main.asyncio.run(main.http_health_check(None))

    assert response.status_code == 200
    assert '"status":"degraded"' in response.body.decode()


def test_get_client_recreates_client_closed_by_previous_session(monkeypatch):
    old_client = MealieClient(base_url="http://test.example.com", api_token="test-token")
    old_client.client._state = httpx._client.ClientState.CLOSED
    new_client = AsyncMock()

    monkeypatch.setattr(main, "mealie_client", old_client)
    monkeypatch.setattr(main, "MealieClient", lambda: new_client)

    assert main.get_client() is new_client
    assert main.mealie_client is new_client


@pytest.mark.asyncio
async def test_lifespan_does_not_close_global_client(monkeypatch):
    mock_client = AsyncMock()
    monkeypatch.setattr(main, "mealie_client", mock_client)

    async with main.lifespan(main.mcp):
        pass

    mock_client.close.assert_not_called()


@pytest.mark.asyncio
async def test_mealie_client_retries_transient_request_errors(monkeypatch):
    client = MealieClient(base_url="http://test.example.com", api_token="test-token")
    monkeypatch.setattr(mealie_client.settings, "max_retries", 3)
    monkeypatch.setattr(mealie_client.asyncio, "sleep", AsyncMock())

    response = httpx.Response(200, json={"ok": True}, request=httpx.Request("GET", "http://test.example.com/api/app/about"))
    client.client.request = AsyncMock(side_effect=[httpx.ConnectError("boom"), response])

    result = await client.get("/api/app/about")

    assert result == {"ok": True}
    assert client.client.request.call_count == 2
    await client.close()


def test_compose_maps_host_port_to_actual_container_port():
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "ghcr.io/nikopol666/mealie-mcp:latest" in compose
    assert '"${MCP_HTTP_PORT:-8080}:8080"' in compose
    assert "POSTGRES_PASSWORD" not in compose
    assert "build:" not in compose
    assert "http://localhost:8080/health" in compose
    assert "asyncio.run(httpx.get" not in compose
