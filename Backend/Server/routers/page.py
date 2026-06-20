import json
import base64
from pathlib import Path
from typing import List
# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from config import WORKSPACES_DIR
from models import BubblesPayload, StrokesPayload, InpaintPayload
from dependencies import (
    bubble_detector,
    text_detector,
    get_ocr_processor,
    get_manga_cleaner,
    get_manga_translator,
)

router = APIRouter(prefix="/api/workspace")


@router.post("/{workspace_id}/page/{page_id}/detect")
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
                "is_sfx": False,
            }
        )

    target_page["bubbles"] = frontend_bubbles
    target_page["detected"] = True

    with open(state_file_path, "w", encoding="utf-8") as f:
        json.dump(chapter_state, f, ensure_ascii=False, indent=2)

    return {"status": "success", "bubbles": frontend_bubbles}


@router.post("/{workspace_id}/page/{page_id}/detect-sfx")
async def detect_sfx(workspace_id: str, page_id: str):
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

    image_bgr = cv2.imread(str(image_path))
    if image_bgr is None:
        raise HTTPException(status_code=500, detail="Failed to load image")
    h, w = image_bgr.shape[:2]

    bubble_payload = bubble_detector.process_page(str(image_path), conf=0.2)

    combined_mask = np.zeros((h, w), dtype=np.uint8)
    for b in bubble_payload["bubbles"]:
        combined_mask = cv2.bitwise_or(combined_mask, b["mask"])

    masked_image = image_bgr.copy()
    masked_image[combined_mask > 0] = [255, 255, 255]

    text_results = text_detector.predict(source=masked_image, conf=0.25, verbose=False)[0]

    frontend_bubbles = []
    
    for b in bubble_payload["bubbles"]:
        frontend_bubbles.append(
            {
                "id": b["bubble_id"],
                "points": b["points"],
                "ja_text": "",
                "en_text": "",
                "is_sfx": False,
            }
        )

    next_id = len(frontend_bubbles) + 1
    if text_results.boxes is not None:
        for box in text_results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            points = [
                {"x": float(x1), "y": float(y1)},
                {"x": float(x2), "y": float(y1)},
                {"x": float(x2), "y": float(y2)},
                {"x": float(x1), "y": float(y2)}
            ]
            frontend_bubbles.append(
                {
                    "id": next_id,
                    "points": points,
                    "ja_text": "",
                    "en_text": "",
                    "is_sfx": True,
                }
            )
            next_id += 1

    target_page["bubbles"] = frontend_bubbles
    target_page["detected"] = True

    with open(state_file_path, "w", encoding="utf-8") as f:
        json.dump(chapter_state, f, ensure_ascii=False, indent=2)

    return {"status": "success", "bubbles": frontend_bubbles}


@router.put("/{workspace_id}/page/{page_id}/bubbles")
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


@router.put("/{workspace_id}/page/{page_id}/strokes")
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


@router.put("/{workspace_id}/page/{page_id}/typesetting")
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


@router.post("/{workspace_id}/page/{page_id}/inpaint")
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
        if not b.points or b.is_sfx:
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


@router.get("/{workspace_id}/page/{page_id}/original-base64")
async def get_original_base64(workspace_id: str, page_id: str):
    session_dir = WORKSPACES_DIR / workspace_id
    state_file_path = session_dir / "chapter_data.json"

    if not state_file_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found.")

    with open(state_file_path, "r", encoding="utf-8") as f:
        chapter_state = json.load(f)

    target_page = next(
        (p for p in chapter_state["pages"] if str(int(p["page_id"].replace("page_", ""))) == page_id),
        None,
    )
    if not target_page:
        raise HTTPException(status_code=404, detail="Page not found.")

    filename = Path(target_page["original_url"]).name
    image_path = session_dir / "original" / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Original image not found.")

    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return {"status": "success", "base64": f"data:image/png;base64,{encoded_string}"}


@router.get("/{workspace_id}/page/{page_id}/inpainted-base64")
async def get_inpainted_base64(workspace_id: str, page_id: str):
    session_dir = WORKSPACES_DIR / workspace_id
    state_file_path = session_dir / "chapter_data.json"

    if not state_file_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found.")

    with open(state_file_path, "r", encoding="utf-8") as f:
        chapter_state = json.load(f)

    target_page = next(
        (p for p in chapter_state["pages"] if str(int(p["page_id"].replace("page_", ""))) == page_id),
        None,
    )
    if not target_page:
        raise HTTPException(status_code=404, detail="Page not found.")

    if not target_page.get("inpainted_url"):
        filename = Path(target_page["original_url"]).name
        image_path = session_dir / "original" / filename
    else:
        filename = Path(target_page["inpainted_url"]).name
        image_path = session_dir / "inpainted" / filename

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found.")

    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return {"status": "success", "base64": f"data:image/png;base64,{encoded_string}"}


@router.post("/{workspace_id}/page/{page_id}/ocr")
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


@router.post("/{workspace_id}/page/{page_id}/translate")
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
