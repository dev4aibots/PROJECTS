"""MCP facade contract tests prove it reuses the service layer."""

from uuid import uuid4

from app.services.mcp import MCPFacade
from tests.helpers import make_pdf


async def test_mcp_facade_lists_and_answers(world):
    session = uuid4()
    document = await world.document_service.upload(
        session,
        "policy.pdf",
        "application/pdf",
        make_pdf(["Refund requests are accepted within 30 days."]),
    )
    await world.document_service.process_all(document.id, session)

    facade = MCPFacade(world.document_service, world.chat_service)
    documents = await facade.list_documents(str(session))
    assert documents[0]["filename"] == "policy.pdf"

    response = await facade.ask_documents(
        str(session), "What is the refund period?", document_ids=[str(document.id)]
    )
    assert response["result"]["grounded"] is True
    assert response["result"]["citations"][0]["page"] == 1


async def test_mcp_facade_keeps_session_isolation(world):
    owner = uuid4()
    stranger = uuid4()
    conversation = await world.chat_service.start_conversation(owner)
    facade = MCPFacade(world.document_service, world.chat_service)

    try:
        await facade.get_conversation(str(stranger), str(conversation.id))
    except Exception as error:
        assert getattr(error, "code", None) == "not_found"
    else:
        raise AssertionError("cross-session MCP access unexpectedly succeeded")
