"""Thin REST routes over the shared service layer."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Header, Request, Response, UploadFile, status
from pydantic import BaseModel, Field

from ..domain.models import GroundedAnswer

router = APIRouter(prefix="/api")
SessionId = Annotated[UUID, Header(alias="X-Session-ID")]


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None
    document_ids: list[UUID] | None = None


class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    result: GroundedAnswer


@router.get("/health")
async def health(request: Request) -> dict:
    container = request.app.state.container
    return {
        "status": "ok",
        "persistence": container.mode,
        "llm": container.llm_mode,
        "live_integrations_configured": container.mode == "supabase" and container.llm_mode != "deterministic",
    }


@router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    session_id: SessionId,
    file: UploadFile = File(...),
) -> dict:
    data = await file.read()
    document = await request.app.state.container.document_service.upload(
        session_id, file.filename or "document.pdf", file.content_type or "", data
    )
    return document.model_dump(mode="json")


@router.post("/documents/{document_id}/process")
async def process_document(
    document_id: UUID, request: Request, session_id: SessionId
) -> dict:
    document = await request.app.state.container.document_service.process_batch(
        document_id, session_id
    )
    return {
        **document.model_dump(mode="json"),
        "done": document.status.value == "ready",
        "progress": (
            document.last_processed_page / document.page_count
            if document.page_count
            else 0.0
        ),
    }


@router.get("/documents")
async def list_documents(request: Request, session_id: SessionId) -> list[dict]:
    documents = await request.app.state.container.document_service.list(session_id)
    return [document.model_dump(mode="json") for document in documents]


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID, request: Request, session_id: SessionId
) -> Response:
    await request.app.state.container.document_service.delete(document_id, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request, session_id: SessionId) -> ChatResponse:
    service = request.app.state.container.chat_service
    conversation = (
        await service.get_conversation(body.conversation_id, session_id)
        if body.conversation_id
        else await service.start_conversation(session_id)
    )
    message, answer = await service.ask(
        conversation.id, session_id, body.question, body.document_ids
    )
    return ChatResponse(
        conversation_id=conversation.id,
        message_id=message.id,
        result=answer,
    )


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID, request: Request, session_id: SessionId
) -> dict:
    service = request.app.state.container.chat_service
    conversation = await service.get_conversation(conversation_id, session_id)
    messages = await service.list_messages(conversation_id, session_id)
    return {"conversation": conversation.model_dump(mode="json"), "messages": messages}


@router.get("/retrieval/{message_id}")
async def get_retrieval(
    message_id: UUID, request: Request, session_id: SessionId
) -> dict:
    log = await request.app.state.container.chat_service.get_retrieval(
        message_id, session_id
    )
    return log.model_dump(mode="json")
