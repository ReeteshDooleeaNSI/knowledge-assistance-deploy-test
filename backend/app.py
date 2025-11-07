from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv

from chatkit.server import ChatKitServer, StreamingResult
from chatkit.types import ThreadMetadata, UserMessageItem
from chatkit.agents import AgentContext, simple_to_agent_input, stream_agent_response
from agents.run import Runner

from assistant_agent import assistant
from memory_store import MemoryStore

load_dotenv()

app = FastAPI()
store = MemoryStore()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class BackendServer(ChatKitServer):
    def __init__(self) -> None:
        super().__init__(store, attachment_store=None)

    async def respond(
        self,
        thread: ThreadMetadata,
        input: UserMessageItem | None,
        context: dict,
    ):
        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )

        run_stream = Runner.run_streamed(
            assistant,
            await simple_to_agent_input(input) if input else [],
            context=agent_context,
        )

        async for event in stream_agent_response(agent_context, run_stream):
            yield event


server = BackendServer()


@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    result = await server.process(await request.body(), context={"userId": "demo"})

    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")

    return JSONResponse(result.data)


@app.get("/health")
async def health():
    return {"ok": True}

