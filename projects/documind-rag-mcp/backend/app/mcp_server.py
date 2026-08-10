"""Streamable HTTP MCP server over the same services used by REST."""
from mcp.server.fastmcp import FastMCP

from .core.wiring import Container, build_container
from .services.mcp import MCPFacade


def build_mcp(container: Container) -> FastMCP:
    facade = MCPFacade(container.document_service, container.chat_service)
    server = FastMCP("DocuMind", stateless_http=True)

    @server.tool()
    async def list_documents(session_id: str) -> list[dict]:
        """List PDF documents owned by a session UUID."""
        return await facade.list_documents(session_id)

    @server.tool()
    async def search_documents(
        session_id: str,
        query: str,
        top_k: int = 8,
        document_ids: list[str] | None = None,
    ) -> list[dict]:
        """Search session-owned documents and return ranked page chunks."""
        return await facade.search_documents(session_id, query, top_k, document_ids)

    @server.tool()
    async def ask_question(
        session_id: str,
        question: str,
        conversation_id: str | None = None,
        document_ids: list[str] | None = None,
    ) -> dict:
        """Ask an evidence-gated question and receive validated citations."""
        return await facade.ask_documents(session_id, question, conversation_id, document_ids)

    @server.tool()
    async def get_conversation(session_id: str, conversation_id: str) -> dict:
        """Read a session-owned conversation and its validated citations."""
        return await facade.get_conversation(session_id, conversation_id)

    return server


if __name__ == "__main__":
    build_mcp(build_container()).run(transport="streamable-http")
