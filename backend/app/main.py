from __future__ import annotations

import asyncio
import mimetypes
import re
from itertools import chain
from pathlib import Path
from typing import Any, AsyncIterator, Iterable

from agents import Agent, RunConfig, Runner
from agents.model_settings import ModelSettings
from chatkit.agents import AgentContext, simple_to_agent_input, stream_agent_response
from chatkit.server import ChatKitServer, StreamingResult
from chatkit.types import (
    Annotation,
    AssistantMessageContent,
    AssistantMessageItem,
    Attachment,
    ClientToolCallItem,
    ThreadItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
)
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from openai.types.responses import ResponseInputContentParam
from starlette.responses import JSONResponse

from .assistant_agent import assistant_agent, title_agent
from .documents import (
    DOCUMENTS,
    DOCUMENTS_BY_FILENAME,
    DOCUMENTS_BY_ID,
    DOCUMENTS_BY_SLUG,
    DOCUMENTS_BY_STEM,
    DocumentMetadata,
    as_dicts,
)
from .memory_store import MemoryStore
from .vector_store_files import (
    delete_file_from_vector_store,
    extract_immatriculation_from_path,
    list_vector_store_files,
    upload_file_to_vector_store,
    upload_files_batch,
)


def _normalise_filename(value: str) -> str:
    return Path(value).name.strip().lower()


def _slug(value: str | None) -> str:
    if not value:
        return ""
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _user_message_text(item: UserMessageItem) -> str:
    parts: list[str] = []
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()


def _resolve_document(annotation: Annotation) -> DocumentMetadata | None:
    source = getattr(annotation, "source", None)
    if not source or getattr(source, "type", None) != "file":
        return None

    filename = getattr(source, "filename", None)
    if filename:
        normalised = _normalise_filename(filename)
        match = DOCUMENTS_BY_FILENAME.get(normalised)
        if match:
            return match
        stem_match = DOCUMENTS_BY_STEM.get(Path(normalised).stem.lower())
        if stem_match:
            return stem_match
        slug_match = DOCUMENTS_BY_SLUG.get(_slug(normalised))
        if slug_match:
            return slug_match

    title = getattr(source, "title", None)
    if title:
        candidate = DOCUMENTS_BY_SLUG.get(_slug(title))
        if candidate:
            return candidate

    description = getattr(source, "description", None)
    if description:
        candidate = DOCUMENTS_BY_SLUG.get(_slug(description))
        if candidate:
            return candidate

    return None


_FILENAME_REGEX = re.compile(r"(0[1-8]_[a-z0-9_\-]+\.(?:pdf|html))", re.IGNORECASE)


def _documents_from_text(text: str) -> Iterable[DocumentMetadata]:
    if not text:
        return []
    matches = {match.lower() for match in _FILENAME_REGEX.findall(text)}
    if not matches:
        return []
    results: list[DocumentMetadata] = []
    for filename in matches:
        doc = DOCUMENTS_BY_FILENAME.get(filename)
        if doc and doc not in results:
            results.append(doc)
    return results


def _is_tool_completion_item(item: Any) -> bool:
    return isinstance(item, ClientToolCallItem)


class KnowledgeAssistantServer(ChatKitServer[dict[str, Any]]):
    def __init__(self, agent: Agent[AgentContext]) -> None:
        self.store = MemoryStore()
        super().__init__(self.store)
        self.assistant = agent

    async def maybe_update_thread_title(
        self,
        thread: ThreadMetadata,
        input_item: UserMessageItem,
        context: dict[str, Any],
    ) -> None:
        if thread.title is not None:
            return
        agent_input = await simple_to_agent_input(input_item)
        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )
        run = await Runner.run(title_agent, input=agent_input, context=agent_context)
        thread.title = run.final_output
        await self.store.save_thread(thread, context)

    async def respond(
        self,
        thread: ThreadMetadata,
        item: ThreadItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        if item is None:
            return

        if _is_tool_completion_item(item):
            return

        if not isinstance(item, UserMessageItem):
            return

        asyncio.create_task(self.maybe_update_thread_title(thread, item, context))

        message_text = _user_message_text(item)
        if not message_text:
            return

        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )

        previous_response_id = thread.metadata.get("previous_response_id")
        result = Runner.run_streamed(
            self.assistant,
            message_text,
            context=agent_context,
            run_config=RunConfig(model_settings=ModelSettings()),
            previous_response_id=previous_response_id,
        )

        async for event in stream_agent_response(agent_context, result):
            yield event

        print("result.last_response_id: ", result.last_response_id) 
        thread.metadata["previous_response_id"] = result.last_response_id
        print("thread.metadata updated: ", thread.metadata)

    async def to_message_content(self, input: Attachment) -> ResponseInputContentParam:
        raise RuntimeError("File attachments are not supported in this demo.")

    async def latest_citations(
        self, thread_id: str, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        items = await self.store.load_thread_items(
            thread_id,
            after=None,
            limit=50,
            order="desc",
            context=context,
        )

        for item in items.data:
            if isinstance(item, AssistantMessageItem):
                citations = list(self._extract_citations(item))
                if citations:
                    return citations
        return []

    def _extract_citations(self, item: AssistantMessageItem) -> Iterable[dict[str, Any]]:
        found = False
        for content in item.content:
            if not isinstance(content, AssistantMessageContent):
                continue
            for annotation in content.annotations:
                document = _resolve_document(annotation)
                if not document:
                    continue
                found = True
                yield {
                    "document_id": document.id,
                    "filename": document.filename,
                    "title": document.title,
                    "description": document.description,
                    "annotation_index": annotation.index,
                }
        if not found:
            texts = chain.from_iterable(
                content.text.splitlines()
                for content in item.content
                if isinstance(content, AssistantMessageContent)
            )
            for line in texts:
                for document in _documents_from_text(line):
                    yield {
                        "document_id": document.id,
                        "filename": document.filename,
                        "title": document.title,
                        "description": document.description,
                        "annotation_index": None,
                    }


knowledge_server = KnowledgeAssistantServer(agent=assistant_agent)

app = FastAPI(title="ChatKit Knowledge Assistant API")

_DATA_DIR = Path(__file__).parent / "data"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_server() -> KnowledgeAssistantServer:
    return knowledge_server


@app.post("/knowledge/chatkit")
async def chatkit_endpoint(
    request: Request, server: KnowledgeAssistantServer = Depends(get_server)
) -> Response:
    payload = await request.body()
    result = await server.process(payload, {"request": request})
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return JSONResponse(result)


@app.get("/knowledge/documents")
async def list_documents() -> dict[str, Any]:
    return {"documents": as_dicts(DOCUMENTS)}


@app.get("/knowledge/documents/{document_id}/file")
async def document_file(document_id: str) -> FileResponse:
    document = DOCUMENTS_BY_ID.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = _DATA_DIR / document.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not available")

    media_type, _ = mimetypes.guess_type(str(file_path))
    headers = {"Content-Disposition": f'inline; filename="{document.filename}"'}
    return FileResponse(
        file_path,
        media_type=media_type or "application/octet-stream",
        headers=headers,
    )


@app.get("/knowledge/threads/{thread_id}/citations")
async def thread_citations(
    thread_id: str,
    request: Request,
    server: KnowledgeAssistantServer = Depends(get_server),
) -> dict[str, Any]:
    context = {"request": request}
    try:
        citations = await server.latest_citations(thread_id, context=context)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    document_ids = sorted({citation["document_id"] for citation in citations})
    return {"documentIds": document_ids, "citations": citations}


@app.get("/knowledge/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/knowledge/vector-store/files")
async def get_vector_store_files(
    immatriculation: str | None = Query(None, description="Filter by immatriculation"),
    client: str | None = Query(None, description="Filter by client"),
) -> dict[str, Any]:
    """List all files in the vector store, optionally filtered by metadata."""
    try:
        files = list_vector_store_files()
        
        if immatriculation or client:
            filtered_files = []
            for file in files:
                file_immat = file.get("immatriculation")
                file_client = file.get("client")
                
                immat_match = not immatriculation or file_immat == immatriculation
                client_match = not client or file_client == client
                
                if immat_match and client_match:
                    filtered_files.append(file)
            files = filtered_files
        
        return {"files": files}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/knowledge/vector-store/files")
async def upload_vector_store_file(
    file: UploadFile,
    immatriculation: str | None = Form(None),
    client: str | None = Form(None),
) -> dict[str, Any]:
    """Upload a single file to the vector store with optional metadata."""
    try:
        file_content = await file.read()
        result = upload_file_to_vector_store(
            file.filename or "unknown",
            file_content,
            immatriculation=immatriculation,
            client=client,
        )
        return {"file": result}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/knowledge/vector-store/files/batch")
async def upload_vector_store_files_batch(
    files: list[UploadFile] = File(...),
    immatriculation: str | None = Form(None),
    client: str | None = Form(None),
    folder_name: str | None = Form(None),
) -> dict[str, Any]:
    """Upload multiple files to the vector store (for folder uploads) with optional metadata."""
    try:
        if len(files) > 100:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files. Maximum is 100, received {len(files)}.",
            )
        
        final_immatriculation = immatriculation
        if not final_immatriculation and folder_name:
            extracted = extract_immatriculation_from_path(folder_name)
            if extracted:
                final_immatriculation = extracted
        
        file_data = []
        for file in files:
            file_content = await file.read()
            file_data.append((file.filename or "unknown", file_content))
        
        results = []
        errors = []
        for filename, content in file_data:
            try:
                clean_filename = Path(filename).name
                result = upload_file_to_vector_store(
                    clean_filename,
                    content,
                    immatriculation=final_immatriculation,
                    client=client,
                )
                results.append(result)
            except Exception as e:  # noqa: BLE001
                error_msg = str(e)
                print(f"Error uploading file {filename}: {error_msg}")
                errors.append({"file": filename, "error": error_msg})
        
        return {
            "files": results,
            "errors": errors,
            "success_count": len(results),
            "error_count": len(errors),
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.delete("/knowledge/vector-store/files/{file_id}")
async def delete_vector_store_file(file_id: str) -> dict[str, Any]:
    """Delete a file from both the vector store and Files API."""
    try:
        result = delete_file_from_vector_store(file_id)
        return result
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
