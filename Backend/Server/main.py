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
from pydantic import BaseModel

backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from ocr.processor import MangaOCRProcessor  # noqa: E402
from translation.translate import MangaTranslationEngine  # noqa: E402
from speech_bubble_detection.detector import SpeechBubbleDetector  # noqa: E402
from inpainting.cleaner import HybridMangaCleaner  # noqa: E402
import cv2
import numpy as np

app = FastAPI(title="Manga Translation Engine Hub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
print(BASE_DIR)

WORKSPACES_DIR = BASE_DIR / "workspaces"
WORKSPACES_DIR.mkdir(exist_ok=True)

print(WORKSPACES_DIR)

app.mount("/workspaces", StaticFiles(directory=str(WORKSPACES_DIR)), name="workspaces")

DETECTOR_WEIGHTS = str(BASE_DIR.parent / "models" / "bubble_segmenter_best.pt")
print(DETECTOR_WEIGHTS)
bubble_detector = SpeechBubbleDetector(DETECTOR_WEIGHTS)


class PointModel(BaseModel):
    x: float
    y: float


class TypesetStyleModel(BaseModel):
    fontSize: float = 16
    fontFamily: str = "Bangers"
    fontWeight: str = "normal"
    fontColor: str = "#000000"
    offsetX: float = 0
    offsetY: float = 0
    lineHeight: float = 1.2
    textAlign: str = "center"
    letterSpacing: float = 0.5
    autoFit: bool = True


class BubbleUpdateModel(BaseModel):
    id: int
    points: List[PointModel]
    ja_text: str = ""
    en_text: str = ""
    typeset: TypesetStyleModel | None = None


class BubblesPayload(BaseModel):
    bubbles: List[BubbleUpdateModel]


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


@app.get("/api/workspace/{workspace_id}")
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


class ReorderRequest(BaseModel):
    new_order: List[str]


@app.post("/api/workspace/{workspace_id}/reorder")
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


@app.post("/api/workspace/{workspace_id}/page/{page_id}/detect")
async def detect_bubbles(workspace_id: str, page_id: str):
    session_dir = WORKSPACES_DIR / workspace_id
    state_file_path = session_dir / "chapter_data.json"

    if not state_file_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")

    with open(state_file_path, "r", encoding="utf-8") as f:
        chapter_state = json.load(f)

    target_page = next(
        (
            p
            for p in chapter_state["pages"]
            if str(int(p["page_id"].replace("page_", ""))) == page_id
        ),
        None,
    )

    if not target_page:
        raise HTTPException(status_code=404, detail="Page not found")

    filename = Path(target_page["original_url"]).name
    image_path = session_dir / "original" / filename

    payload = bubble_detector.process_page(str(image_path), conf=0.2)

    frontend_bubbles = []
    for b in payload["bubbles"]:
        frontend_bubbles.append(
            {
                "id": b["bubble_id"],
                "points": b["points"],
                "ja_text": "",
                "en_text": "",
            }
        )

    target_page["bubbles"] = frontend_bubbles
    target_page["detected"] = True

    with open(state_file_path, "w", encoding="utf-8") as f:
        json.dump(chapter_state, f, ensure_ascii=False, indent=2)

    return {"status": "success", "bubbles": frontend_bubbles}


@app.put("/api/workspace/{workspace_id}/page/{page_id}/bubbles")
async def update_bubbles(workspace_id: str, page_id: str, payload: BubblesPayload):
    session_dir = WORKSPACES_DIR / workspace_id
    state_file_path = session_dir / "chapter_data.json"

    if not state_file_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found.")

    with open(state_file_path, "r", encoding="utf-8") as f:
        chapter_state = json.load(f)

    target_page = next(
        (
            p
            for p in chapter_state["pages"]
            if str(int(p["page_id"].replace("page_", ""))) == page_id
        ),
        None,
    )

    if not target_page:
        raise HTTPException(status_code=404, detail="Page not found.")

    target_page["bubbles"] = [b.model_dump() for b in payload.bubbles]

    with open(state_file_path, "w", encoding="utf-8") as f:
        json.dump(chapter_state, f, ensure_ascii=False, indent=2)

    return {"status": "success"}


class StrokeModel(BaseModel):
    points: List[PointModel]
    brushSize: float
    brushColor: str = "#ffffff"
    type: str = "eraser"

class StrokesPayload(BaseModel):
    strokes: List[StrokeModel]

@app.put("/api/workspace/{workspace_id}/page/{page_id}/strokes")
async def update_strokes(workspace_id: str, page_id: str, payload: StrokesPayload):
    session_dir = WORKSPACES_DIR / workspace_id
    state_file_path = session_dir / "chapter_data.json"

    if not state_file_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found.")

    with open(state_file_path, "r", encoding="utf-8") as f:
        chapter_state = json.load(f)

    target_page = next(
        (
            p
            for p in chapter_state["pages"]
            if str(int(p["page_id"].replace("page_", ""))) == page_id
        ),
        None,
    )

    if not target_page:
        raise HTTPException(status_code=404, detail="Page not found.")

    target_page["redrawingStrokes"] = [s.model_dump() for s in payload.strokes]

    with open(state_file_path, "w", encoding="utf-8") as f:
        json.dump(chapter_state, f, ensure_ascii=False, indent=2)

    return {"status": "success"}


@app.put("/api/workspace/{workspace_id}/page/{page_id}/typesetting")
async def update_typesetting(workspace_id: str, page_id: str, payload: BubblesPayload):
    session_dir = WORKSPACES_DIR / workspace_id
    state_file_path = session_dir / "chapter_data.json"

    if not state_file_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found.")

    with open(state_file_path, "r", encoding="utf-8") as f:
        chapter_state = json.load(f)

    target_page = next(
        (
            p
            for p in chapter_state["pages"]
            if str(int(p["page_id"].replace("page_", ""))) == page_id
        ),
        None,
    )

    if not target_page:
        raise HTTPException(status_code=404, detail="Page not found.")

    target_page["bubbles"] = [b.model_dump() for b in payload.bubbles]

    with open(state_file_path, "w", encoding="utf-8") as f:
        json.dump(chapter_state, f, ensure_ascii=False, indent=2)

    return {"status": "success"}


ocr_processor = None


def get_ocr_processor():
    global ocr_processor
    if ocr_processor is None:
        ocr_processor = MangaOCRProcessor()
    return ocr_processor


manga_cleaner = None

def get_manga_cleaner():
    global manga_cleaner
    if manga_cleaner is None:
        manga_cleaner = HybridMangaCleaner(
            generative_model_id_or_path=None
        )
    return manga_cleaner


class InpaintPayload(BaseModel):
    bubbles: List[BubbleUpdateModel]
    border_erosion: int = 2


@app.post("/api/workspace/{workspace_id}/page/{page_id}/inpaint")
async def run_page_inpaint(workspace_id: str, page_id: str, payload: InpaintPayload):
    session_dir = WORKSPACES_DIR / workspace_id
    state_file_path = session_dir / "chapter_data.json"

    if not state_file_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found.")

    with open(state_file_path, "r", encoding="utf-8") as f:
        chapter_state = json.load(f)

    target_page = next(
        (
            p
            for p in chapter_state["pages"]
            if str(int(p["page_id"].replace("page_", ""))) == page_id
        ),
        None,
    )

    if not target_page:
        raise HTTPException(status_code=404, detail="Page not found.")

    if not target_page.get("detected", False):
        raise HTTPException(
            status_code=400, detail="Speech bubble detection must be run before inpainting."
        )

    filename = Path(target_page["original_url"]).name
    image_path = session_dir / "original" / filename
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Original image not found.")

    img = cv2.imread(str(image_path))
    if img is None:
        raise HTTPException(status_code=500, detail="Failed to load image.")
    h, w = img.shape[:2]

    bubble_metadata = []
    
    for b in payload.bubbles:
        if not b.points:
            continue
            
        points = np.array([[pt.x, pt.y] for pt in b.points], dtype=np.int32)
        
        x, y, bw, bh = cv2.boundingRect(points)
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(w, x + bw), min(h, y + bh)
        
        if x2 <= x1 or y2 <= y1:
            continue
            
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(mask, [points], 255)
        
        if payload.border_erosion > 0:
            kernel = np.ones((5, 5), np.uint8)
            # Match detector.py logic: dilate by 1, erode by border_erosion
            mask = cv2.dilate(mask, kernel, iterations=1)
            mask = cv2.erode(mask, kernel, iterations=payload.border_erosion)
            
        bubble_metadata.append({
            "bubble_id": b.id,
            "bbox": {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)},
            "mask": mask,
            "area_px": int((mask > 0).sum())
        })

    cleaner = get_manga_cleaner()
    try:
        cleaned_image = cleaner.generate_clean_page(str(image_path), bubble_metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inpainting failed: {str(e)}")

    inpainted_dir = session_dir / "inpainted"
    inpainted_dir.mkdir(parents=True, exist_ok=True)
    inpainted_filename = f"{Path(filename).stem}_inpainted.png"
    inpainted_path = inpainted_dir / inpainted_filename
    cv2.imwrite(str(inpainted_path), cleaned_image)

    inpainted_url = f"/workspaces/{workspace_id}/inpainted/{inpainted_filename}"
    target_page["inpainted_url"] = inpainted_url
    
    target_page["bubbles"] = [b.model_dump() for b in payload.bubbles]

    with open(state_file_path, "w", encoding="utf-8") as f:
        json.dump(chapter_state, f, ensure_ascii=False, indent=2)

    return {"status": "success", "inpainted_url": inpainted_url}


@app.post("/api/workspace/{workspace_id}/page/{page_id}/ocr")
async def run_page_ocr(workspace_id: str, page_id: str):
    session_dir = WORKSPACES_DIR / workspace_id
    state_file_path = session_dir / "chapter_data.json"

    if not state_file_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found.")

    with open(state_file_path, "r", encoding="utf-8") as f:
        chapter_state = json.load(f)

    target_page = next(
        (
            p
            for p in chapter_state["pages"]
            if str(int(p["page_id"].replace("page_", ""))) == page_id
        ),
        None,
    )

    if not target_page:
        raise HTTPException(status_code=404, detail="Page not found.")

    if not target_page.get("detected", False):
        raise HTTPException(
            status_code=400, detail="Speech bubble detection must be run before OCR."
        )

    filename = Path(target_page["original_url"]).name
    image_path = session_dir / "original" / filename

    bubbles = target_page.get("bubbles", [])
    if not bubbles:
        return {"status": "success", "bubbles": []}

    processor = get_ocr_processor()
    ocr_results = processor.extract_page_texts(str(image_path), bubbles)

    ocr_by_id = {res["bubble_id"]: res["original_text"] for res in ocr_results}

    for b in bubbles:
        bid = b["id"]
        if bid in ocr_by_id:
            b["ja_text"] = ocr_by_id[bid]

    target_page["bubbles"] = bubbles

    with open(state_file_path, "w", encoding="utf-8") as f:
        json.dump(chapter_state, f, ensure_ascii=False, indent=2)

    return {"status": "success", "bubbles": bubbles}


manga_translator = None

def get_manga_translator():
    global manga_translator
    if manga_translator is None:
        manga_translator = MangaTranslationEngine()
    return manga_translator


@app.post("/api/workspace/{workspace_id}/page/{page_id}/translate")
async def run_page_translate(workspace_id: str, page_id: str):
    session_dir = WORKSPACES_DIR / workspace_id
    state_file_path = session_dir / "chapter_data.json"

    if not state_file_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found.")

    with open(state_file_path, "r", encoding="utf-8") as f:
        chapter_state = json.load(f)

    target_page = next(
        (
            p
            for p in chapter_state["pages"]
            if str(int(p["page_id"].replace("page_", ""))) == page_id
        ),
        None,
    )

    if not target_page:
        raise HTTPException(status_code=404, detail="Page not found.")

    if not target_page.get("detected", False):
        raise HTTPException(
            status_code=400, detail="Speech bubble detection must be run before translation."
        )

    bubbles = target_page.get("bubbles", [])
    if not bubbles:
        return {"status": "success", "bubbles": []}

    has_ocr = any(b.get("ja_text", "").strip() for b in bubbles)
    if not has_ocr:
        raise HTTPException(
            status_code=400, detail="OCR must be run before translation. No Japanese text found."
        )

    translation_input = []
    for b in bubbles:
        ja_text = b.get("ja_text", "").strip()

        pts = b.get("points", [])
        if pts:
            xs = [p["x"] for p in pts]
            ys = [p["y"] for p in pts]
            bbox = {"x1": int(min(xs)), "y1": int(min(ys)), "x2": int(max(xs)), "y2": int(max(ys))}
            area = (bbox["x2"] - bbox["x1"]) * (bbox["y2"] - bbox["y1"])
        else:
            bbox = {"x1": 0, "y1": 0, "x2": 0, "y2": 0}
            area = 0

        translation_input.append({
            "bubble_id": b["id"],
            "bbox": bbox,
            "ja_text": ja_text if ja_text else "",
            "area_px": area
        })

    if not translation_input:
        return {"status": "success", "bubbles": bubbles}

    translator = get_manga_translator()
    try:
        translated_results = translator.translate_page_bubbles(translation_input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

    translated_by_id = {}
    for item in translated_results:
        bid = item.get("bubble_id")
        en_text = item.get("en_text", "")
        if bid is not None and en_text.strip():
            translated_by_id[bid] = en_text

    for b in bubbles:
        bid = b["id"]
        if bid in translated_by_id:
            b["en_text"] = translated_by_id[bid]

    target_page["bubbles"] = bubbles

    with open(state_file_path, "w", encoding="utf-8") as f:
        json.dump(chapter_state, f, ensure_ascii=False, indent=2)

    return {"status": "success", "bubbles": bubbles}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
