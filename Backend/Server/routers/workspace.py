import uuid
import json
from pathlib import Path
from typing import List
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, UploadFile, File, HTTPException
from config import WORKSPACES_DIR
from models import ReorderRequest

router = APIRouter(prefix="/api/workspace")


@router.post("/create")
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
                    "detected": False,
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


@router.get("/{workspace_id}")
async def load_workspace(workspace_id: str):
    """
    Looks up an existing workspace directory by its ID and returns
    the stored master chapter_data.json configuration state.
    """
    session_dir = WORKSPACES_DIR / workspace_id
    state_file_path = session_dir / "chapter_data.json"

    if not session_dir.exists() or not state_file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Workspace session '{workspace_id}' not found on server disk.",
        )

    try:
        with open(state_file_path, "r", encoding="utf-8") as f:
            chapter_state = json.load(f)
        return {"status": "success", "workspace": chapter_state}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to read existing workspace state: {str(e)}"
        )


@router.post("/{workspace_id}/reorder")
async def reorder_workspace(workspace_id: str, payload: ReorderRequest):
    session_dir = WORKSPACES_DIR / workspace_id
    state_file_path = session_dir / "chapter_data.json"

    if not state_file_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found.")

    with open(state_file_path, "r", encoding="utf-8") as f:
        chapter_state = json.load(f)

    pages_dict = {
        str(int(p["page_id"].replace("page_", ""))): p for p in chapter_state["pages"]
    }

    reordered_pages = []
    for frontend_id in payload.new_order:
        if frontend_id in pages_dict:
            reordered_pages.append(pages_dict[frontend_id])

    chapter_state["pages"] = reordered_pages

    with open(state_file_path, "w", encoding="utf-8") as f:
        json.dump(chapter_state, f, ensure_ascii=False, indent=2)

    return {"status": "success", "message": "Workspace reordered."}


@router.delete("/{workspace_id}/page/{page_id}")
async def delete_page(workspace_id: str, page_id: str):
    session_dir = WORKSPACES_DIR / workspace_id
    state_file_path = session_dir / "chapter_data.json"

    if not state_file_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found.")

    try:
        with open(state_file_path, "r", encoding="utf-8") as f:
            chapter_state = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read workspace state: {str(e)}")

    target_index = -1
    for index, p in enumerate(chapter_state["pages"]):
        try:
            curr_id = str(int(p["page_id"].replace("page_", "")))
        except ValueError:
            curr_id = p["page_id"]
        
        if curr_id == page_id:
            target_index = index
            break

    if target_index == -1:
        raise HTTPException(status_code=404, detail="Page not found in workspace.")

    deleted_page = chapter_state["pages"].pop(target_index)

    # Clean up associated files from disk
    try:
        original_url = deleted_page.get("original_url")
        if original_url:
            filename = Path(original_url).name
            original_file_path = session_dir / "original" / filename
            if original_file_path.exists():
                original_file_path.unlink()

        inpainted_url = deleted_page.get("inpainted_url")
        if inpainted_url:
            inpainted_url_clean = inpainted_url.split("?")[0]
            inpainted_filename = Path(inpainted_url_clean).name
            inpainted_file_path = session_dir / "inpainted" / inpainted_filename
            if inpainted_file_path.exists():
                inpainted_file_path.unlink()
    except Exception as e:
        print(f"Error deleting page files from disk: {e}")

    try:
        with open(state_file_path, "w", encoding="utf-8") as f:
            json.dump(chapter_state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save updated workspace state: {str(e)}")

    return {"status": "success", "message": f"Page {page_id} deleted successfully."}
