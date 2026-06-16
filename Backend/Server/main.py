from __future__ import annotations
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))
sys.path.append(str(backend_dir / "server"))

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles

from config import WORKSPACES_DIR
from routers.workspace import router as workspace_router
from routers.page import router as page_router

app = FastAPI(title="Manga Translation Engine Hub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimpleCORSMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers = [h for h in headers if h[0].lower() not in (b"access-control-allow-origin", b"access-control-allow-methods", b"access-control-allow-headers")]
                headers.append((b"access-control-allow-origin", b"*"))
                headers.append((b"access-control-allow-methods", b"*"))
                headers.append((b"access-control-allow-headers", b"*"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


app.mount("/workspaces", SimpleCORSMiddleware(StaticFiles(directory=str(WORKSPACES_DIR))), name="workspaces")

app.include_router(workspace_router)
app.include_router(page_router)

if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
