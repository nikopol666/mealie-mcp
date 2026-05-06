# Contributing

Thanks for helping improve Mealie MCP Server.

## Development Setup

```bash
git clone https://github.com/nikopol666/mealie-mcp.git
cd mealie-mcp
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=src MEALIE_API_TOKEN=test-token pytest -q
```

## Local Runtime Check

```bash
export MEALIE_BASE_URL=http://localhost:9000
export MEALIE_API_TOKEN=your-mealie-api-token
python src/main.py --transport streamable-http
```

Then check:

```bash
curl -fsS http://localhost:8080/health
```

## Pull Request Expectations

- Keep changes focused and reversible.
- Add or update tests for behavior changes.
- Update `docs/TOOL_REFERENCE.md` whenever you add, remove, or rename an MCP tool.
- Update `README.md`, `DEPLOYMENT.md`, or examples when user-facing behavior changes.
- Do not commit real Mealie tokens, `.env` files, exports, or personal recipe data.

## Tool Design Guidelines

- Prefer Mealie v3 API field names in payloads.
- Accept common snake_case aliases when it improves MCP client ergonomics.
- Preserve existing Mealie fields before sending PUT updates to endpoints that require full records.
- Return structured errors instead of raising raw HTTP details to MCP clients.
- For binary data, use base64 fields so responses remain JSON-safe.

## Testing

Required before a pull request is ready:

```bash
PYTHONPATH=src MEALIE_API_TOKEN=test-token pytest -q
python -m compileall src tests
```

Recommended when Docker changes:

```bash
docker build -t mealie-mcp:test .
```

Optional release smoke test against a real Mealie instance:

```bash
export MEALIE_LIVE_SMOKE=1
export MEALIE_BASE_URL=http://localhost:9000
export MEALIE_API_TOKEN=your-mealie-api-token
PYTHONPATH=src pytest tests/test_live_smoke.py -q
```

The live smoke suite is read-only and intentionally skipped by default. Use a
dedicated Mealie token and do not paste real tokens into issues, logs, or pull
requests.
