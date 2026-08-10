"""Prove Streamable HTTP MCP is mounted on the deployed ASGI app."""

import json

import httpx

from app.main import create_app


async def test_mcp_tools_list_and_rest_coexist():
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 200, response.text
            data_line = next(line for line in response.text.splitlines() if line.startswith("data: "))
            payload = json.loads(data_line.removeprefix("data: "))
            names = {tool["name"] for tool in payload["result"]["tools"]}
            assert names == {
                "ask_question",
                "get_conversation",
                "list_documents",
                "search_documents",
            }

            health = await client.get("/api/health")
            assert health.status_code == 200
            assert health.json()["status"] == "ok"


async def test_mcp_rejects_invalid_protocol_payload():
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/mcp",
                json={"not": "json-rpc"},
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 400
