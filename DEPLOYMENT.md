# Deployment Guide

This guide covers production-oriented deployment for Mealie MCP Server.

## Architecture

```text
MCP client
   |
   | streamable HTTP / stdio
   v
Mealie MCP Server
   |
   | Mealie REST API + API token
   v
Mealie
```

The MCP server does not store recipe data. It forwards tool calls to Mealie using the configured API token.

## Recommended Docker Compose

Use this when Mealie already runs on the same host, another host, or a Docker network reachable from the MCP container.

```yaml
services:
  mealie-mcp:
    image: ghcr.io/nikopol666/mealie-mcp:latest
    container_name: mealie-mcp
    restart: unless-stopped
    ports:
      - "${MCP_HTTP_PORT:-8080}:8080"
    environment:
      MEALIE_BASE_URL: ${MEALIE_BASE_URL:?Set MEALIE_BASE_URL in .env}
      MEALIE_API_TOKEN: ${MEALIE_API_TOKEN:?Set MEALIE_API_TOKEN in .env}
      MCP_SERVER_NAME: ${MCP_SERVER_NAME:-Mealie MCP Server}
      MCP_HOST: 0.0.0.0
      MCP_PORT: 8080
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      REQUEST_TIMEOUT: ${REQUEST_TIMEOUT:-30}
      MAX_RETRIES: ${MAX_RETRIES:-3}
    extra_hosts:
      - "host.docker.internal:host-gateway"
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - "import httpx; httpx.get('http://localhost:8080/health', timeout=5).raise_for_status()"
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

If Mealie is on an external Docker network, use `docker-compose.integration.yml`, set `MEALIE_DOCKER_NETWORK`, and set `MEALIE_BASE_URL` to the internal Mealie URL reachable from the MCP container.

## Environment File

Create `.env`:

```env
MEALIE_BASE_URL=http://host.docker.internal:9000
MEALIE_API_TOKEN=replace-with-a-mealie-api-token
MCP_HTTP_PORT=8080
LOG_LEVEL=INFO
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

Generate the token in Mealie from the profile/API tokens area. Use a dedicated token for this integration.

## Start, Upgrade, Stop

Start:

```bash
docker compose up -d
```

Upgrade:

```bash
docker compose pull mealie-mcp
docker compose up -d mealie-mcp
```

Stop:

```bash
docker compose stop mealie-mcp
```

## Health Checks

Host health endpoint:

```bash
curl -fsS http://localhost:8080/health
```

Expected healthy shape:

```json
{
  "status": "healthy",
  "message": "MCP server is running and connected to Mealie",
  "mealie_info": {
    "version": "3.x.x",
    "base_url": "http://mealie:9000"
  },
  "server_info": {
    "name": "Mealie MCP Server",
    "port": 8080,
    "transport": "streamable-http",
    "endpoint": "/mcp"
  }
}
```

Container logs:

```bash
docker logs --tail 100 mealie-mcp
```

## MCP Endpoint

From the host:

```text
http://localhost:8080/mcp
```

From another container on the same network:

```text
http://mealie-mcp:8080/mcp
```

## Reverse Proxy

If you expose the server through a reverse proxy, protect it with authentication. The MCP server can modify Mealie data with the configured API token.

Example Traefik labels:

```yaml
services:
  mealie-mcp:
    labels:
      traefik.enable: "true"
      traefik.http.routers.mealie-mcp.rule: Host(`mcp.example.com`)
      traefik.http.routers.mealie-mcp.entrypoints: websecure
      traefik.http.routers.mealie-mcp.tls: "true"
      traefik.http.services.mealie-mcp.loadbalancer.server.port: "8080"
```

## Security Recommendations

- Do not publish the MCP endpoint without authentication.
- Use a dedicated Mealie API token.
- Rotate the token if it is exposed in logs, screenshots, or support requests.
- Prefer an internal Docker network between Mealie and the MCP server.
- Keep Mealie and this MCP server updated together.
- Review which users or clients can call destructive tools such as delete and merge operations.

## Resource Use

Typical resource use is low. A conservative starting point:

```yaml
services:
  mealie-mcp:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.5"
```

`deploy.resources` is honored by Docker Swarm and some platforms. Plain Docker Compose may ignore it.

## Troubleshooting

### Container starts but health is degraded

Check:

- `MEALIE_BASE_URL` is reachable from inside the MCP container.
- `MEALIE_API_TOKEN` is valid.
- Mealie is fully started.
- The token belongs to a user with access to the target household/group data.

### MCP client cannot connect

Check:

- Port mapping: `docker port mealie-mcp`
- Health endpoint: `curl -fsS http://localhost:8080/health`
- Client URL: `http://localhost:8080/mcp`
- Reverse proxy websocket/streaming settings if applicable

### Tool calls fail after upgrading Mealie

Mealie API routes can change between releases. Compare the failing endpoint against your instance's OpenAPI document:

```text
http://your-mealie-instance:9000/openapi.json
```

Open an issue with:

- Mealie version
- Mealie MCP Server version or image digest
- Tool name
- Sanitized error response
- Relevant endpoint from `/openapi.json`

## Local Stdio Deployment

For desktop MCP clients that launch stdio servers:

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

## Verification Checklist

- `docker compose ps` shows `mealie-mcp` running.
- `curl -fsS http://localhost:8080/health` returns `healthy`.
- Your MCP client can list tools.
- `health_check` succeeds from the MCP client.
- A read-only tool such as `search_recipes` returns data.
- If shopping lists are needed, `list_shopping_lists` can see your Mealie v3 household lists.
- For releases, use the checklist in `CHANGELOG.md` before tagging.
