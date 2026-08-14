# MCP Interface

DocuMind exposes the same services used by REST through the official Python MCP SDK's stateless Streamable HTTP transport.

## Endpoint and tools

Local endpoint: `http://localhost:8000/mcp`

| Tool | Important arguments | Result |
|---|---|---|
| `list_documents` | `session_id` | Session-owned document metadata |
| `search_documents` | `session_id`, `query`, optional `top_k`, `document_ids` | Ranked, shaped chunks with page and similarity |
| `ask_question` | `session_id`, `question`, optional conversation/document IDs | Grounded answer or honest refusal |
| `get_conversation` | `session_id`, `conversation_id` | Session-owned messages and validated citations |

Every tool requires a session UUID because the demonstration has anonymous browser sessions rather than production authentication. Cross-session resources return an error.

## Why Streamable HTTP

`app.main.create_app()` builds one dependency container, gives it to FastAPI and `MCPFacade`, starts the SDK session manager in the FastAPI lifespan, and mounts the MCP ASGI app. This avoids duplicated retrieval behavior and works with an HTTP serverless entrypoint. See [DECISIONS.md](../DECISIONS.md#2-streamable-http-mcp-mounted-in-fastapi) for tradeoffs.

## Local verification

```bash
# terminal 1
cd projects/documind-rag-mcp/backend
uvicorn app.main:app --port 8000

# terminal 2
cd projects/documind-rag-mcp
python scripts/test_mcp.py
```

The script uploads and indexes the generated refund policy through REST, initializes an MCP session, lists tools, invokes all four tools, and verifies cross-session denial. It exits nonzero on a failed assertion.

## Client configuration

Any MCP client that supports remote Streamable HTTP can use:

```json
{
  "mcpServers": {
    "documind": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Client configuration formats differ; consult the client's current documentation. A deployed URL must not be published until `/mcp` has been smoke-tested in that environment.

## Deployment topology

The repository is designed for two Vercel projects:

1. **Backend root:** `projects/documind-rag-mcp`, serving `/api/*` and `/mcp` through `api/index.py`.
2. **Frontend root:** `projects/documind-rag-mcp/frontend`, with `NEXT_PUBLIC_API_BASE_URL` set to the backend origin.

Set backend `FRONTEND_ORIGIN` to the exact frontend origin. This topology is configuration-ready but unverified because owner-managed credentials and projects are not available.
