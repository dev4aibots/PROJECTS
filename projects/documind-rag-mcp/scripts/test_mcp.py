#!/usr/bin/env python3
"""Exercise every DocuMind MCP tool against a running local server.

Start the backend first:
    cd backend && uvicorn app.main:app --port 8000
Then run:
    python scripts/test_mcp.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def _structured(result):
    if result.structuredContent is not None:
        return result.structuredContent
    for item in result.content:
        text = getattr(item, "text", None)
        if text:
            import json

            return json.loads(text)
    return None


async def arrange(base_url: str, session_id: str) -> str:
    pdf = Path(__file__).resolve().parents[1] / "sample_docs" / "refund_policy.pdf"
    async with httpx.AsyncClient(base_url=base_url, timeout=30) as client:
        uploaded = await client.post(
            "/api/documents/upload",
            headers={"X-Session-ID": session_id},
            files={"file": (pdf.name, pdf.read_bytes(), "application/pdf")},
        )
        uploaded.raise_for_status()
        document_id = uploaded.json()["id"]
        while True:
            processed = await client.post(
                f"/api/documents/{document_id}/process",
                headers={"X-Session-ID": session_id},
            )
            processed.raise_for_status()
            if processed.json()["done"]:
                break
    print(f"arranged: uploaded {pdf.name} as {document_id} for session {session_id}")
    return document_id


async def main(mcp_url: str) -> int:
    base_url = mcp_url.removesuffix("/mcp")
    session_id = str(uuid4())
    document_id = await arrange(base_url, session_id)

    async with streamablehttp_client(mcp_url) as (read, write, _):
        async with ClientSession(read, write) as client:
            await client.initialize()
            tools = await client.list_tools()
            names = sorted(tool.name for tool in tools.tools)
            expected = ["ask_question", "get_conversation", "list_documents", "search_documents"]
            assert names == expected, names
            print("tools/list ->", names)

            listed = await client.call_tool("list_documents", {"session_id": session_id})
            listed_value = _structured(listed)
            assert not listed.isError and len(listed_value) == 1
            print(f"list_documents -> {len(listed_value)} document(s)")

            searched = await client.call_tool(
                "search_documents",
                {
                    "session_id": session_id,
                    "query": "What is the refund period?",
                    "document_ids": [document_id],
                },
            )
            searched_value = _structured(searched)
            assert not searched.isError and searched_value
            print(f"search_documents -> {len(searched_value)} ranked chunk(s)")

            asked = await client.call_tool(
                "ask_question",
                {
                    "session_id": session_id,
                    "question": "What is the refund period?",
                    "document_ids": [document_id],
                },
            )
            asked_value = _structured(asked)
            assert not asked.isError and asked_value["result"]["grounded"] is True
            print("ask_question -> grounded=True")

            history = await client.call_tool(
                "get_conversation",
                {
                    "session_id": session_id,
                    "conversation_id": asked_value["conversation_id"],
                },
            )
            history_value = _structured(history)
            assert not history.isError and len(history_value["messages"]) == 2
            print("get_conversation -> 2 message(s)")

            denied = await client.call_tool(
                "get_conversation",
                {
                    "session_id": str(uuid4()),
                    "conversation_id": asked_value["conversation_id"],
                },
            )
            assert denied.isError
            print("cross-session get_conversation -> isError=True")

    print("\nAll MCP tools verified.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000/mcp")
    try:
        raise SystemExit(asyncio.run(main(parser.parse_args().url)))
    except (AssertionError, httpx.HTTPError) as error:
        print(f"MCP smoke failed: {error}", file=sys.stderr)
        raise SystemExit(1)
