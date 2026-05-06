# Mealie MCP Server

Community-ready Model Context Protocol (MCP) server for [Mealie](https://github.com/mealie-recipes/mealie).

It exposes Mealie recipes, meal plans, shopping lists, foods, units, tags, categories, and recipe tools to MCP clients through either streamable HTTP or stdio.

## Features

- Recipe search, create, patch, update, duplicate, URL/HTML/ZIP/image import, assets, images, timeline events, comments, exports, suggestions, and last-made updates
- Household meal-plan entries, today's meals, random meal entries, and meal-plan rules
- Mealie v3 household shopping lists, shopping item CRUD, bulk item changes, recipe-to-list operations, and label settings
- Food and unit master data, including aliases, plural names, duplicate food merges, and duplicate unit merges
- Tags, categories, recipe tools/utensils, cookbooks, comments, shared links, parser, media, users, groups, households, explore endpoints, and admin endpoints
- Docker-first deployment with a health endpoint and non-root container user

## Requirements

- Mealie v3.x
- A Mealie API token
- Docker, Docker Compose, or Python 3.12+
- An MCP client that supports streamable HTTP or stdio

## Quick Start With Docker

```bash
docker run -d \
  --name mealie-mcp \
  --restart unless-stopped \
  -p 8080:8080 \
  --add-host=host.docker.internal:host-gateway \
  -e MEALIE_BASE_URL=http://your-mealie-instance:9000 \
  -e MEALIE_API_TOKEN=your-mealie-api-token \
  ghcr.io/nikopol666/mealie-mcp:latest
```

Health check:

```bash
curl http://localhost:8080/health
```

MCP endpoint:

```text
http://localhost:8080/mcp
```

## Docker Compose

Copy the example environment file, fill in your Mealie URL and API token, then start the service:

```bash
cp .env.example .env
docker compose up -d
```

For the default single-service example, see [docker-compose.yml](./docker-compose.yml).

For attaching to an existing Mealie Docker network, see [docker-compose.integration.yml](./docker-compose.integration.yml).

```yaml
services:
  mealie-mcp:
    image: ghcr.io/nikopol666/mealie-mcp:latest
    restart: unless-stopped
    ports:
      - "${MCP_HTTP_PORT:-8080}:8080"
    environment:
      MEALIE_BASE_URL: ${MEALIE_BASE_URL:?Set MEALIE_BASE_URL in .env}
      MEALIE_API_TOKEN: ${MEALIE_API_TOKEN:?Set MEALIE_API_TOKEN in .env}
```

## Configuration

Copy [.env.example](./.env.example) to `.env` and fill in your Mealie URL and API token.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `MEALIE_BASE_URL` | Yes | none | Base URL for your Mealie API. Use `http://host.docker.internal:9000` for a host Mealie service or `http://mealie:9000` on a shared Docker network. |
| `MEALIE_API_TOKEN` | Yes | none | Mealie API token from the user's profile settings. |
| `MCP_HTTP_PORT` | No | `8080` | Host port used by the example Docker Compose files. |
| `MCP_SERVER_NAME` | No | `Mealie MCP Server` | Display name advertised to MCP clients. |
| `MCP_HOST` | No | `0.0.0.0` | Host/interface for streamable HTTP. |
| `MCP_PORT` | No | `8080` | Internal server port. |
| `LOG_LEVEL` | No | `INFO` | Python logging level. |
| `REQUEST_TIMEOUT` | No | `30` | Mealie API request timeout in seconds. |
| `MAX_RETRIES` | No | `3` | Retry attempts for transient GET failures and startup checks. |

## MCP Client Setup

### Streamable HTTP

Use this endpoint when your client supports streamable HTTP:

```text
http://localhost:8080/mcp
```

Inside the same Docker network:

```text
http://mealie-mcp:8080/mcp
```

### Stdio

For clients that launch MCP servers as local processes:

```bash
git clone https://github.com/nikopol666/mealie-mcp.git
cd mealie-mcp
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export MEALIE_BASE_URL=http://localhost:9000
export MEALIE_API_TOKEN=your-mealie-api-token
python src/main.py --transport stdio
```

## Tool Coverage

See [docs/TOOL_REFERENCE.md](./docs/TOOL_REFERENCE.md) for the complete tool list and payload notes.

High-level groups:

- Health
- Recipes
- Meal plans
- Shopping lists
- Foods and units
- Tags, categories, and recipe tools
- Cookbooks, comments, shared links, parser, media, users, groups, households, explore, and admin tools

## Development

```bash
git clone https://github.com/nikopol666/mealie-mcp.git
cd mealie-mcp
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=src MEALIE_API_TOKEN=test-token pytest -q
```

Optional read-only smoke check against a real Mealie instance:

```bash
export MEALIE_LIVE_SMOKE=1
export MEALIE_BASE_URL=http://localhost:9000
export MEALIE_API_TOKEN=your-mealie-api-token
PYTHONPATH=src pytest tests/test_live_smoke.py -q
```

Run with streamable HTTP:

```bash
export MEALIE_BASE_URL=http://localhost:9000
export MEALIE_API_TOKEN=your-mealie-api-token
python src/main.py --transport streamable-http
```

Build the Docker image:

```bash
docker build -t mealie-mcp:local .
```

## Documentation

- [Deployment guide](./DEPLOYMENT.md)
- [Tool reference](./docs/TOOL_REFERENCE.md)
- [Meal planning guide](./docs/meal_planning_guide.md)
- [Examples](./examples/README.md)
- [Changelog](./CHANGELOG.md)
- [Contributing guide](./CONTRIBUTING.md)
- [Support guide](./SUPPORT.md)
- [Security policy](./SECURITY.md)

## Security Notes

- Treat `MEALIE_API_TOKEN` as a secret.
- Run the container only on trusted networks or behind authentication.
- The MCP server can create, update, and delete Mealie data using the privileges of the configured Mealie token.
- Use a dedicated Mealie API token for this service when possible.
See [SECURITY.md](./SECURITY.md) for disclosure and deployment guidance.

## Compatibility

This project targets current Mealie v3 APIs. Mealie has moved some resources between group and household scopes over time; if a tool fails after a Mealie upgrade, compare the failing endpoint against your instance's `/openapi.json`.

## License

MIT
