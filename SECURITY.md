# Security Policy

## Supported Versions

Security updates are provided for the current `main` branch and the latest published container image.

## Reporting A Vulnerability

Please report vulnerabilities privately through GitHub's security advisory flow when available. If that is not available, open a minimal GitHub issue that states a private report is needed, without including exploit details, tokens, logs, or personal data.

Include:

- affected version or commit
- deployment mode (`stdio` or `streamable-http`)
- affected Mealie version
- clear reproduction steps
- expected and observed impact

## Token Handling

This server authenticates to Mealie with `MEALIE_API_TOKEN`. Treat that token as a secret.

- Use a dedicated Mealie API token for this service.
- Do not commit `.env` files, compose overrides, screenshots, or logs containing tokens.
- Rotate the token immediately if it is exposed.
- Prefer the least-privileged Mealie user that still supports the tools you need.

## Network Exposure

The streamable HTTP transport has no separate authentication layer in this project. Anyone who can reach the MCP endpoint can ask the server to perform actions allowed by the configured Mealie token.

Recommended deployment:

- keep `/mcp` on a trusted private network, or
- put it behind a reverse proxy with authentication, TLS, and request logging controls, and
- avoid exposing it directly to the public internet.

## Destructive Actions

The MCP tool surface includes create, update, delete, merge, purge, and bulk operations. Restrict access to trusted MCP clients and operators.

Examples of destructive operations include recipe deletes, bulk recipe deletes, export purges, shopping list deletes, food/unit merges, tag/category deletes, household/group administration, user administration, backup restore/delete, storage cleanup, and recipe-folder cleanup.

The optional live smoke suite in `tests/test_live_smoke.py` is read-only and skipped by default. Run it only with a dedicated Mealie token for the instance you intend to verify.

## Operational Notes

- The `/health` endpoint may report degraded Mealie connectivity while the MCP server itself is still running.
- Recipe import and scraping behavior depends on upstream Mealie and the target site being scraped.
- Binary downloads are returned as base64 in MCP responses so clients can handle them safely over JSON.
