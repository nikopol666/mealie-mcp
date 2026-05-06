# Changelog

All notable changes to Mealie MCP Server are documented here.

This project follows semantic versioning.

## 1.0.0 - 2026-05-06

- Added broad Mealie v3 recipe edit coverage, including patch/update, images, assets, imports, exports, comments, timeline events, and bulk recipe operations.
- Added household meal-plan and shopping-list support for current Mealie v3 endpoints.
- Added food, unit, tag, category, and recipe-tool master-data coverage, including duplicate food/unit merge operations.
- Added Docker, Docker Compose, GHCR publishing workflow, deployment documentation, security guidance, and tool reference documentation.
- Added regression coverage for Mealie response-shape differences seen in live v3 instances.
- Split runtime and development Python requirements so production images do not install pytest.
- Gated container publishing on the test job in GitHub Actions.
- Added an opt-in read-only live smoke suite for release checks against a real Mealie instance.
- Simplified public Docker Compose and `.env.example` files for release use with an existing Mealie instance.

## Release Checklist

Before publishing a release:

1. Run `PYTHONPATH=src MEALIE_API_TOKEN=test-token pytest -q`.
2. Run `python -m compileall src tests`.
3. Run `docker build -t mealie-mcp:release-check .`.
4. Run `MEALIE_LIVE_SMOKE=1 PYTHONPATH=src pytest tests/test_live_smoke.py -q` against a real Mealie instance.
5. Verify a deployed container with `/health` and `health_check`.
6. Test one read-only tool from each active group: recipes, meal plans, shopping lists, foods, units, tags, categories, and recipe tools.
7. Create a signed or annotated git tag such as `v1.0.0`.
8. Confirm GitHub Actions publishes the GHCR image tags.
