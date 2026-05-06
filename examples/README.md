# Examples

These examples show MCP JSON-RPC calls against the streamable HTTP endpoint.

Replace `http://localhost:8080/mcp` with your deployment URL.

## Initialize A Session

MCP streamable HTTP clients normally handle initialization for you. A raw HTTP test looks like this:

```bash
curl -i http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "manual-test",
        "version": "1.0"
      }
    }
  }'
```

Save the `mcp-session-id` response header and send it on following requests.

## List Tools

```bash
curl http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

## Search Recipes

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "search_recipes",
    "arguments": {
      "filters": {
        "query": "pasta",
        "page": 1,
        "per_page": 5
      }
    }
  }
}
```

## Create A Meal Plan Entry

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "create_meal_plan_entry",
    "arguments": {
      "entry_data": {
        "date": "2026-05-04",
        "meal_type": "dinner",
        "recipe_id": "fabf6ba1-d421-4130-84ed-157fe0e2ba0b",
        "text": "Dinner"
      }
    }
  }
}
```

## List Shopping Lists

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "list_shopping_lists",
    "arguments": {
      "filters": {
        "page": 1,
        "perPage": 10
      }
    }
  }
}
```

## Add A Shopping Item

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/call",
  "params": {
    "name": "add_shopping_item",
    "arguments": {
      "list_id": "shopping-list-uuid",
      "item_data": {
        "name": "Milk",
        "quantity": 2,
        "note": "Whole milk"
      }
    }
  }
}
```

## Merge Duplicate Foods

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "merge_foods",
    "arguments": {
      "merge_data": {
        "from_food_id": "duplicate-food-uuid",
        "to_food_id": "canonical-food-uuid"
      }
    }
  }
}
```

Merge and delete operations are destructive. Confirm IDs before running them.
