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
    get_lama_session,
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
    bubble_masks = [b["mask"] for b in bubble_payload["bubbles"]]

    combined_mask = np.zeros((h, w), dtype=np.uint8)
    for b in bubble_payload["bubbles"]:
        combined_mask = cv2.bitwise_or(combined_mask, b["mask"])

    masked_image = image_bgr.copy()
    masked_image[combined_mask > 0] = [255, 255, 255]

    text_results = text_detector.predict(source=masked_image, conf=0.25, verbose=False)[0]

    yolo_boxes = []
    if text_results.boxes is not None:
        for box in text_results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(float)
            yolo_boxes.append([x1, y1, x2, y2])

    from sfx_detection.masker import extract_sfx_mask_and_contours

    mask_res = extract_sfx_mask_and_contours(
        image_bgr=image_bgr,
        speech_bubble_masks=bubble_masks,
        yolo_boxes=yolo_boxes,
        padding=8,
        block_size=11,
        C=2,
        min_area=5,
        dilation_kernel_size=3,
        overlap_threshold=0.05
    )

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
    for sfx in mask_res["sfx_regions"]:
        frontend_bubbles.append(
            {
                "id": next_id,
                "points": sfx["points"],
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


@router.post("/{workspace_id}/page/{page_id}/inpaint-sfx")
async def run_page_sfx_inpaint(workspace_id: str, page_id: str, payload: InpaintPayload):
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

    filename = Path(target_page["original_url"]).name
    image_path = session_dir / "original" / filename
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Original image not found.")

    # Determine starting image (use existing inpainted image if it exists to layer the erasure)
    inpainted_dir = session_dir / "inpainted"
    inpainted_dir.mkdir(parents=True, exist_ok=True)
    inpainted_filename = f"{Path(filename).stem}_inpainted.png"
    inpainted_path = inpainted_dir / inpainted_filename

    # If the inpainted image already exists, load it to layer SFX inpainting on top of it.
    if inpainted_path.exists():
        img = cv2.imread(str(inpainted_path))
    else:
        img = cv2.imread(str(image_path))

    if img is None:
        raise HTTPException(status_code=500, detail="Failed to load image.")
    h, w = img.shape[:2]

    # Step 1: Initialize the LaMa ONNX Inference Engine
    try:
        session = get_lama_session()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load LaMa ONNX model session: {str(e)}")

    import torch
    from sfx_detection.masker import generate_single_sfx_mask

    # Process each SFX bubble independently
    for b in payload.bubbles:
        if not b.points or not b.is_sfx:
            continue
            
        # Parse points into list of dicts for our masker function
        points_list = [{"x": float(pt.x), "y": float(pt.y)} for pt in b.points]
        
        # Generate raw adaptive binarization mask
        raw_mask = generate_single_sfx_mask(
            image_bgr=img,
            points=points_list,
            padding=6,
            block_size=21,
            C=5,
            min_area=10,
            dilation_kernel_size=0  # Get raw sharp mask
        )
        
        # Step 2: Dynamic Safety Mask Dilation (Cushioning)
        ys, xs = np.where(raw_mask > 0)
        if len(xs) == 0 or len(ys) == 0:
            continue
            
        xmin, xmax = int(np.min(xs)), int(np.max(xs))
        ymin, ymax = int(np.min(ys)), int(np.max(ys))
        width = xmax - xmin
        height = ymax - ymin
        
        # Calculate bounding box diagonal to judge text scale
        bbox_diagonal = np.sqrt(width**2 + height**2)

        if bbox_diagonal > 150:
            # Use a wider kernel for massive title art or giant SFX
            kernel_size = (11, 11)
        elif bbox_diagonal > 75:
            kernel_size = (7, 7)
        else:
            kernel_size = (5, 5)

        dilation_element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, kernel_size)
        dilated_mask = cv2.dilate(raw_mask, dilation_element, iterations=1)
        
        # Step 3: Localized High-Resolution Patch Extraction
        # Add contextual padding safety buffer of exactly 24 pixels
        pad = 24
        xmin_pad = max(0, xmin - pad)
        ymin_pad = max(0, ymin - pad)
        xmax_pad = min(w, xmax + pad)
        ymax_pad = min(h, ymax + pad)
        
        if (xmax_pad - xmin_pad) <= 0 or (ymax_pad - ymin_pad) <= 0:
            continue
            
        # Slice high-res image, dilated mask, and raw mask patches
        img_patch = img[ymin_pad:ymax_pad, xmin_pad:xmax_pad].copy()
        mask_patch = dilated_mask[ymin_pad:ymax_pad, xmin_pad:xmax_pad].copy()
        raw_mask_patch = raw_mask[ymin_pad:ymax_pad, xmin_pad:xmax_pad].copy()
        crop_h, crop_w = img_patch.shape[:2]
        
        # Step 4: Mathematical Scale Alignment and Tensor Formatting
        # Calculate closest upper multiple of 8
        target_h = int(np.ceil(crop_h / 8.0) * 8)
        target_w = int(np.ceil(crop_w / 8.0) * 8)
        
        # Resize image (bilinear) and mask (nearest)
        img_resized = cv2.resize(img_patch, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        mask_resized = cv2.resize(mask_patch, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
        
        # Format tensors
        rgb_resized = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_tensor = rgb_resized.astype(np.float32) / 255.0
        img_tensor = np.transpose(img_tensor, (2, 0, 1))
        img_tensor = np.expand_dims(img_tensor, axis=0)  # NCHW: [1, 3, Target_H, Target_W]
        
        mask_tensor = (mask_resized > 0).astype(np.float32)
        mask_tensor = np.expand_dims(mask_tensor, axis=0)
        mask_tensor = np.expand_dims(mask_tensor, axis=0)  # NCHW: [1, 1, Target_H, Target_W]
        
        # Step 5: Execute Neural Inference Pass
        # Dynamic input key mapping (support both image/mask and dynamic keys)
        input_feed = {}
        for input_node in session.get_inputs():
            if "mask" in input_node.name.lower():
                input_feed[input_node.name] = mask_tensor
            elif "image" in input_node.name.lower() or "img" in input_node.name.lower():
                input_feed[input_node.name] = img_tensor
            else:
                if input_node.shape[1] == 1:
                    input_feed[input_node.name] = mask_tensor
                else:
                    input_feed[input_node.name] = img_tensor
                    
        try:
            with torch.no_grad():
                outputs = session.run(None, input_feed)
                out_tensor = outputs[0]
        except Exception as e:
            # Check for invalid shape runtime error and fall back to 512x512
            if "invalid dimensions" in str(e) or "invalid input" in str(e) or "Expected: 512" in str(e) or "Expected: 1" in str(e):
                fallback_h, fallback_w = 512, 512
                img_resized = cv2.resize(img_patch, (fallback_w, fallback_h), interpolation=cv2.INTER_LINEAR)
                mask_resized = cv2.resize(mask_patch, (fallback_w, fallback_h), interpolation=cv2.INTER_NEAREST)
                
                rgb_resized = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
                img_tensor = rgb_resized.astype(np.float32) / 255.0
                img_tensor = np.transpose(img_tensor, (2, 0, 1))
                img_tensor = np.expand_dims(img_tensor, axis=0)
                
                mask_tensor = (mask_resized > 0).astype(np.float32)
                mask_tensor = np.expand_dims(mask_tensor, axis=0)
                mask_tensor = np.expand_dims(mask_tensor, axis=0)
                
                fallback_feed = {}
                for input_node in session.get_inputs():
                    if "mask" in input_node.name.lower():
                        fallback_feed[input_node.name] = mask_tensor
                    elif "image" in input_node.name.lower() or "img" in input_node.name.lower():
                        fallback_feed[input_node.name] = img_tensor
                    else:
                        if input_node.shape[1] == 1:
                            fallback_feed[input_node.name] = mask_tensor
                        else:
                            fallback_feed[input_node.name] = img_tensor
                            
                with torch.no_grad():
                    outputs = session.run(None, fallback_feed)
                    out_tensor = outputs[0]
                target_h, target_w = fallback_h, fallback_w
            else:
                raise HTTPException(status_code=500, detail=f"Inference error during SFX inpainting: {str(e)}")
                
        # Step 6: Selective Stencil Blending and Global Canvas Re-pasting
        out_patch = out_tensor[0]
        out_patch = np.transpose(out_patch, (1, 2, 0))  # CHW -> HWC
        out_patch = np.clip(out_patch * 255.0, 0, 255).astype(np.uint8)
        out_patch_bgr = cv2.cvtColor(out_patch, cv2.COLOR_RGB2BGR)
        
        # Resize output patch back to original padded crop dimensions
        restored_patch = cv2.resize(out_patch_bgr, (crop_w, crop_h), interpolation=cv2.INTER_LINEAR)
        
        # Step 6.1: Extract and Dilate a High-Fidelity Blending Stencil
        # Keep original mask patch and dilate it with the dynamically scaled kernel size
        blending_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, kernel_size)
        stencil_patch = cv2.dilate(raw_mask_patch, blending_kernel, iterations=1)
        
        # Step 6.2: Implement Soft Alpha-Feathering
        blurred_stencil = cv2.GaussianBlur(stencil_patch, (5, 5), 0)
        alpha = blurred_stencil.astype(np.float32) / 255.0
        
        # Step 6.3: Inject Matching Micro-Texture Grain
        noise = np.random.normal(loc=0.0, scale=1.5, size=restored_patch.shape).astype(np.float32)
        restored_patch = np.clip(restored_patch.astype(np.float32) + noise, 0.0, 255.0).astype(np.uint8)
        
        # Step 6.4: Perform Alpha Weighted Stencil Blending with Structural Edge Preservation
        gray_patch = cv2.cvtColor(img_patch, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray_patch, 50, 150)
        
        edge_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        structural_mask = cv2.dilate(edges, edge_kernel, iterations=1)
        
        alpha_3d = np.expand_dims(alpha, axis=2)
        alpha_3d[structural_mask == 0] = alpha_3d[structural_mask == 0] * 0.15
        
        blended_crop = (alpha_3d * restored_patch.astype(np.float32)) + \
                       ((1.0 - alpha_3d) * img_patch.astype(np.float32))
                       
        # Paste back onto canvas
        img[ymin_pad:ymax_pad, xmin_pad:xmax_pad] = np.clip(blended_crop, 0.0, 255.0).astype(np.uint8)

    # Save final canvas image
    cv2.imwrite(str(inpainted_path), img)

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
