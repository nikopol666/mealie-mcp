# Support

Use this guide before opening an issue.

## First Checks

1. Confirm Mealie itself is reachable.
2. Confirm the MCP server health endpoint returns useful status:

   ```bash
   curl -fsS http://localhost:8080/health
   ```

3. Confirm the configured Mealie API token is valid and belongs to a user with access to the target household/group.
4. Check the Mealie version. This project targets Mealie v3.x.

## Useful Issue Details

Include:

- Mealie MCP Server version, commit, image tag, or image digest
- Mealie version
- deployment mode: Docker Compose, Docker, stdio, or other
- tool name
- sanitized request shape
- sanitized error response
- relevant Mealie endpoint from `/openapi.json` when available

Do not include real API tokens, private recipe exports, personal household data, or public URLs for private services.
