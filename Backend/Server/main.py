from __future__ import annotations
import sys
from pathlib import Path
import os
import json
import uuid
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from ocr.pipeline import MangaOCRPipeline  # noqa: E402
from translation.translate import MangaTranslationEngine  # noqa: E402

app = FastAPI(title="Manga Translation Engine Hub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
WORKSPACES_DIR = BASE_DIR / "workspaces"
WORKSPACES_DIR.mkdir(exist_ok=True)

app.mount("/workspaces", StaticFiles(directory=str(WORKSPACES_DIR)), name="workspaces")

DETECTOR_WEIGHTS = str(BASE_DIR / "models" / "bubble_segmenter_best.pt")


@app.post("/api/workspace/create")
async def create_workspace(files: List[UploadFile] = File(...)):
    """
    Accepts a batch of manga pages, provisions a dedicated sandbox folder,
    saves the raw images, and generates the master tracking JSON.
    """
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    workspace_id = f"chapter_{uuid.uuid4().hex[:8]}"
    session_dir = WORKSPACES_DIR / workspace_id

    original_dir = session_dir / "original"
    inpainted_dir = session_dir / "inpainted"
    masks_dir = session_dir / "masks"

    original_dir.mkdir(parents=True, exist_ok=True)
    inpainted_dir.mkdir(parents=True, exist_ok=True)
    masks_dir.mkdir(parents=True, exist_ok=True)

    chapter_state = {"workspace_id": workspace_id, "pages": []}

    try:
        sorted_files = sorted(files, key=lambda f: f.filename)

        for index, file in enumerate(sorted_files):
            file_extension = Path(file.filename).suffix
            safe_filename = f"page_{str(index + 1).zfill(2)}{file_extension}"
            save_path = original_dir / safe_filename

            with open(save_path, "wb") as buffer:
                buffer.write(await file.read())

            chapter_state["pages"].append(
                {
                    "page_id": f"page_{str(index + 1).zfill(2)}",
                    "original_filename": file.filename,
                    "original_url": f"/workspaces/{workspace_id}/original/{safe_filename}",
                    "inpainted_url": None,
                    "bubbles": [],
                }
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to write uploaded files: {str(e)}"
        )

    state_file_path = session_dir / "chapter_data.json"
    with open(state_file_path, "w", encoding="utf-8") as f:
        json.dump(chapter_state, f, ensure_ascii=False, indent=2)

    return {
        "status": "success",
        "message": f"Workspace {workspace_id} created successfully with {len(files)} pages.",
        "workspace": chapter_state,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
