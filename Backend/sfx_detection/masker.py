import cv2
import numpy as np

def extract_sfx_mask_and_contours(
    image_bgr: np.ndarray,
    speech_bubble_masks: list[np.ndarray],
    yolo_boxes: list[list[float]] | np.ndarray,
    padding: int = 8,
    block_size: int = 11,
    C: int = 2,
    min_area: int = 5,
    dilation_kernel_size: int = 3,
    overlap_threshold: float = 0.05
) -> dict:
    """
    Implements the 6-step Pixel-Perfect Non-Speech Bubble Text Masking and Extraction Pipeline.
    
    Args:
        image_bgr: The original page BGR image matrix.
        speech_bubble_masks: A list of 2D binary numpy arrays (same size as image_bgr) representing fine-grained speech bubbles.
        yolo_boxes: Bounding boxes from the text detector, e.g. [[xmin, ymin, xmax, ymax], ...]
        padding: Padding margin in pixels around boundary during crop.
        block_size: Adaptive local neighborhood size (must be odd).
        C: Subtract constant parameter from mean.
        min_area: Minimum pixel area to keep a connected component.
        dilation_kernel_size: Morphological dilation kernel size.
        overlap_threshold: Intersection over area threshold to classify as bubble text vs SFX text.
        
    Returns:
        dict:
            - "master_mask": Page-level binary mask (0 or 255) containing refined SFX contours.
            - "sfx_regions": List of dicts representing SFX target regions, each containing:
                - "bbox": [xmin, ymin, xmax, ymax]
                - "points": List of {"x": float, "y": float} representing the simplified polygon.
    """
    h, w = image_bgr.shape[:2]
    master_canvas = np.zeros((h, w), dtype=np.uint8)
    sfx_regions = []
    
    for box in yolo_boxes:
        # Step 1: Spatial Geometry Subtraction
        # Parse box coordinates
        xmin, ymin, xmax, ymax = map(int, box)
        xmin = max(0, xmin)
        ymin = max(0, ymin)
        xmax = min(w, xmax)
        ymax = min(h, ymax)
        
        box_area = (xmax - xmin) * (ymax - ymin)
        if box_area <= 0:
            continue
            
        # Compute intersection-over-area ratio against all speech bubble masks
        is_bubble_text = False
        for bubble_mask in speech_bubble_masks:
            intersection = np.sum(bubble_mask[ymin:ymax, xmin:xmax] > 0)
            overlap_ratio = intersection / box_area
            if overlap_ratio >= overlap_threshold:
                is_bubble_text = True
                break
                
        if is_bubble_text:
            continue  # Exclusion Rule: Discard bubble text boxes
            
        # Step 2: Localized Patch and Grayscale Conversion
        xmin_pad = max(0, xmin - padding)
        ymin_pad = max(0, ymin - padding)
        xmax_pad = min(w, xmax + padding)
        ymax_pad = min(h, ymax + padding)
        
        patch = image_bgr[ymin_pad:ymax_pad, xmin_pad:xmax_pad]
        if patch.size == 0:
            continue
            
        patch_gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        
        # Step 3: Adaptive Local Binarization
        # Adjust block size dynamically if patch size is smaller than block_size
        actual_block_size = block_size
        max_possible = min(patch_gray.shape[0], patch_gray.shape[1])
        if max_possible < actual_block_size:
            actual_block_size = max_possible if max_possible % 2 == 1 else max_possible - 1
            if actual_block_size < 3:
                actual_block_size = 3
                
        if patch_gray.shape[0] < 3 or patch_gray.shape[1] < 3:
            # Fallback to standard Otsu binarization
            _, binary_patch = cv2.threshold(patch_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        else:
            # Contextual light/dark decision
            h_p, w_p = patch_gray.shape
            boundary_pixels = []
            # Gather top/bottom borders
            boundary_pixels.extend(patch_gray[0, :])
            boundary_pixels.extend(patch_gray[-1, :])
            # Gather left/right borders
            boundary_pixels.extend(patch_gray[:, 0])
            boundary_pixels.extend(patch_gray[:, -1])
            
            bg_mean = np.mean(boundary_pixels) if boundary_pixels else 255.0
            
            if bg_mean > 127:
                # Light background -> dark text
                binary_patch = cv2.adaptiveThreshold(
                    patch_gray,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY_INV,
                    actual_block_size,
                    C
                )
            else:
                # Dark background -> light text
                binary_patch = cv2.adaptiveThreshold(
                    patch_gray,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    actual_block_size,
                    C
                )
                
        # Step 4: High-Frequency Screentone Noise Filtering
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_patch)
        cleaned_binary_patch = np.zeros_like(binary_patch)
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= min_area:
                cleaned_binary_patch[labels == i] = 255
                
        # Step 5: Contour Extraction and Polygon Rasterization
        contours, _ = cv2.findContours(
            cleaned_binary_patch,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        global_contours = []
        all_pts = []
        for contour in contours:
            global_contour = contour.copy()
            global_contour[:, 0, 0] += xmin_pad
            global_contour[:, 0, 1] += ymin_pad
            global_contours.append(global_contour)
            for pt in global_contour:
                all_pts.append(pt[0])
                
        if global_contours:
            cv2.drawContours(master_canvas, global_contours, -1, 255, thickness=cv2.FILLED)
            
        # Compute simplified convex hull to initialize Svelte vector node
        if all_pts:
            hull = cv2.convexHull(np.array(all_pts, dtype=np.int32))
            epsilon = 0.005 * cv2.arcLength(hull, True)
            approx_hull = cv2.approxPolyDP(hull, epsilon, True)
            sfx_points = [{"x": float(pt[0][0]), "y": float(pt[0][1])} for pt in approx_hull]
        else:
            # Fallback to the original YOLO bounding box points
            sfx_points = [
                {"x": float(xmin), "y": float(ymin)},
                {"x": float(xmax), "y": float(ymin)},
                {"x": float(xmax), "y": float(ymax)},
                {"x": float(xmin), "y": float(ymax)}
            ]
            
        sfx_regions.append({
            "bbox": [xmin, ymin, xmax, ymax],
            "points": sfx_points
        })
        
    # Step 6: Targeted Morphological Boundary Expansion
    if dilation_kernel_size > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilation_kernel_size, dilation_kernel_size))
        dilated_master_mask = cv2.dilate(master_canvas, kernel, iterations=1)
    else:
        dilated_master_mask = master_canvas.copy()
        
    return {
        "master_mask": dilated_master_mask,
        "sfx_regions": sfx_regions
    }

def generate_single_sfx_mask(
    image_bgr: np.ndarray,
    points: list[dict],
    padding: int = 8,
    block_size: int = 11,
    C: int = 2,
    min_area: int = 5,
    dilation_kernel_size: int = 3
) -> np.ndarray:
    """
    Generates a pixel-perfect binary mask for a single SFX bubble based on its points.
    
    Args:
        image_bgr: The original page BGR image matrix.
        points: List of {"x": float, "y": float} representing the SFX polygon points.
        padding: Padding margin in pixels around boundary during crop.
        block_size: Adaptive local neighborhood size (must be odd).
        C: Subtract constant parameter from mean.
        min_area: Minimum pixel area to keep a connected component.
        dilation_kernel_size: Morphological dilation kernel size.
        
    Returns:
        np.ndarray: Binary mask (0 or 255) of size (H, W) for the single SFX bubble.
    """
    h, w = image_bgr.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    
    if not points:
        return mask
        
    xs = [pt["x"] for pt in points]
    ys = [pt["y"] for pt in points]
    xmin, ymin, xmax, ymax = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
    
    xmin = max(0, xmin)
    ymin = max(0, ymin)
    xmax = min(w, xmax)
    ymax = min(h, ymax)
    
    if (xmax - xmin) <= 0 or (ymax - ymin) <= 0:
        return mask
        
    # Crop and padding
    xmin_pad = max(0, xmin - padding)
    ymin_pad = max(0, ymin - padding)
    xmax_pad = min(w, xmax + padding)
    ymax_pad = min(h, ymax + padding)
    
    patch = image_bgr[ymin_pad:ymax_pad, xmin_pad:xmax_pad]
    if patch.size == 0:
        return mask
        
    patch_gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    
    # Adaptive thresholding
    actual_block_size = block_size
    max_possible = min(patch_gray.shape[0], patch_gray.shape[1])
    if max_possible < actual_block_size:
        actual_block_size = max_possible if max_possible % 2 == 1 else max_possible - 1
        if actual_block_size < 3:
            actual_block_size = 3
            
    if patch_gray.shape[0] < 3 or patch_gray.shape[1] < 3:
        _, binary_patch = cv2.threshold(patch_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:
        h_p, w_p = patch_gray.shape
        boundary_pixels = []
        boundary_pixels.extend(patch_gray[0, :])
        boundary_pixels.extend(patch_gray[-1, :])
        boundary_pixels.extend(patch_gray[:, 0])
        boundary_pixels.extend(patch_gray[:, -1])
        
        bg_mean = np.mean(boundary_pixels) if boundary_pixels else 255.0
        
        if bg_mean > 127:
            binary_patch = cv2.adaptiveThreshold(
                patch_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, actual_block_size, C
            )
        else:
            binary_patch = cv2.adaptiveThreshold(
                patch_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, actual_block_size, C
            )
            
    # Connected components noise filtering
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_patch)
    cleaned_binary_patch = np.zeros_like(binary_patch)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_area:
            cleaned_binary_patch[labels == i] = 255
            
    # Contour finding and global mapping
    contours, _ = cv2.findContours(
        cleaned_binary_patch,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    global_contours = []
    for contour in contours:
        global_contour = contour.copy()
        global_contour[:, 0, 0] += xmin_pad
        global_contour[:, 0, 1] += ymin_pad
        global_contours.append(global_contour)
        
    if global_contours:
        cv2.drawContours(mask, global_contours, -1, 255, thickness=cv2.FILLED)
    else:
        # Fallback to filling the polygon
        pts_arr = np.array([[pt["x"], pt["y"]] for pt in points], dtype=np.int32)
        cv2.fillPoly(mask, [pts_arr], 255)
        
    # Apply morphological dilation if requested
    if dilation_kernel_size > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilation_kernel_size, dilation_kernel_size))
        mask = cv2.dilate(mask, kernel, iterations=1)
        
    return mask
