import io
import cv2
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, Query, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO

# Paths to the renamed model weights
BUBBLE_MODEL_PATH = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\models\speech_bubble_detector.pt"
TEXT_MODEL_PATH = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\models\text_detector.onnx"

# Load models
try:
    bubble_model = YOLO(BUBBLE_MODEL_PATH)
    text_model = YOLO(TEXT_MODEL_PATH, task="detect")
except Exception as e:
    print(f"Error loading models from absolute paths: {e}")
    # Fallback to local paths
    bubble_model = YOLO("Backend/models/speech_bubble_detector.pt")
    text_model = YOLO("Backend/models/text_detector.onnx", task="detect")

app = FastAPI(
    title="SFX Detection Service",
    description="Microservice to detect manga Sound Effects (SFX) using speech bubble masking and YOLO ONNX text detection"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/detect")
async def detect_sfx(
    file: UploadFile = File(...),
    conf: float = Query(0.25, ge=0.0, le=1.0, description="Confidence threshold for text detection")
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")

    try:
        # Read uploaded image bytes
        contents = await file.read()
        
        # Load image with PIL and convert to numpy BGR format for OpenCV & YOLO
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
        image_rgb = np.array(pil_image)
        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        h, w = image_bgr.shape[:2]
        
        # 1. Run speech bubble detector (instance segmentation)
        # Use low conf threshold (0.2) to capture speech bubbles reliably
        bubble_results = bubble_model.predict(source=image_bgr, conf=0.2, verbose=False)[0]
        
        # 2. Build a combined speech bubble binary mask
        combined_mask = np.zeros((h, w), dtype=np.uint8)
        if bubble_results.masks is not None:
            for mask in bubble_results.masks.data:
                mask_np = mask.cpu().numpy()
                mask_resized = cv2.resize(
                    mask_np, (w, h), interpolation=cv2.INTER_LINEAR
                )
                binary_mask = (mask_resized > 0.1).astype(np.uint8) * 255
                
                # Apply morphological operations to ensure the text boundary is fully covered
                kernel = np.ones((5, 5), np.uint8)
                binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
                binary_mask = cv2.dilate(binary_mask, kernel, iterations=2)
                
                combined_mask = cv2.bitwise_or(combined_mask, binary_mask)
        
        # 3. Mask out the speech bubble areas on a copy of the original image
        masked_image = image_bgr.copy()
        masked_image[combined_mask > 0] = [255, 255, 255] # Paint white over bubbles to remove speech text
        
        # 4. Run the text detector (model.onnx renamed to text_detector.onnx) on the masked image
        text_results = text_model.predict(source=masked_image, conf=conf, verbose=False)[0]
        
        # 5. Draw the bounding boxes of the remaining text (only SFX) on the ORIGINAL image
        annotated_img = image_bgr.copy()
        num_sfx = 0
        
        if text_results.boxes is not None:
            for box in text_results.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                score = float(box.conf[0].cpu().numpy())
                
                # Draw bounding box (vibrant violet-purple color)
                color = (180, 80, 240) # BGR
                cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)
                
                # Draw a clean background panel for label text
                label = f"SFX {score:.2f}"
                (w_label, h_label), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                cv2.rectangle(
                    annotated_img, 
                    (x1, max(0, y1 - h_label - 6)), 
                    (x1 + w_label + 4, max(0, y1)), 
                    color, 
                    -1
                )
                cv2.putText(
                    annotated_img, 
                    label, 
                    (x1 + 2, max(0, y1 - 3)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.4, 
                    (255, 255, 255), 
                    1, 
                    cv2.LINE_AA
                )
                num_sfx += 1
                
        # Encode annotated image as PNG
        success, img_encoded = cv2.imencode(".png", annotated_img)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to encode annotated image.")
            
        # Return the annotated image to client, with SFX count in the header
        return StreamingResponse(
            io.BytesIO(img_encoded.tobytes()),
            media_type="image/png",
            headers={"X-Detected-Objects": str(num_sfx)}
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def get_gui():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manga SFX Detector Hub</title>
    <meta name="description" content="AI-powered tool to automatically detect sound effects (SFX) in manga pages by masking speech bubbles and running text detection.">
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #090d16;
            --bg-card: rgba(17, 24, 39, 0.65);
            --border-color: rgba(255, 255, 255, 0.08);
            --accent: #8b5cf6; /* Violet */
            --accent-hover: #7c3aed;
            --accent-glow: rgba(139, 92, 246, 0.3);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --success: #10b981;
            --radius-lg: 16px;
            --radius-md: 12px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-main);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            padding: 2rem;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(139, 92, 246, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(99, 102, 241, 0.08) 0%, transparent 40%);
            background-attachment: fixed;
        }

        header {
            text-align: center;
            margin-bottom: 2.5rem;
            max-width: 600px;
        }

        h1 {
            font-size: 2.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #c084fc 0%, #8b5cf6 50%, #6366f1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            letter-spacing: -0.025em;
        }

        p.subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
            line-height: 1.5;
        }

        .container {
            width: 100%;
            max-width: 1200px;
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 2.5rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }

        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 1.5rem;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }

        .slider-group {
            display: flex;
            align-items: center;
            gap: 1rem;
            background: rgba(255, 255, 255, 0.03);
            padding: 0.75rem 1.25rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
        }

        .slider-group label {
            font-size: 0.95rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .slider-group input[type="range"] {
            -webkit-appearance: none;
            width: 150px;
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            outline: none;
            cursor: pointer;
        }

        .slider-group input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: var(--accent);
            cursor: pointer;
            transition: var(--transition);
        }

        .slider-group input[type="range"]::-webkit-slider-thumb:hover {
            transform: scale(1.2);
            box-shadow: 0 0 10px var(--accent-glow);
        }

        .slider-val {
            font-weight: 600;
            color: var(--accent);
            min-width: 2.5rem;
            text-align: right;
        }

        .upload-section {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border: 2px dashed rgba(139, 92, 246, 0.3);
            border-radius: var(--radius-md);
            padding: 3rem 2rem;
            cursor: pointer;
            transition: var(--transition);
            background: rgba(139, 92, 246, 0.02);
            text-align: center;
            position: relative;
        }

        .upload-section:hover, .upload-section.dragover {
            border-color: var(--accent);
            background: rgba(139, 92, 246, 0.06);
            transform: translateY(-2px);
        }

        .upload-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            color: var(--accent);
        }

        .upload-text {
            font-size: 1.1rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }

        .upload-subtext {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        #fileInput {
            display: none;
        }

        .workspace {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-top: 1rem;
        }

        @media (max-width: 768px) {
            .workspace {
                grid-template-columns: 1fr;
            }
        }

        .pane {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 350px;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }

        .pane-title {
            align-self: flex-start;
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            width: 100%;
        }

        .image-wrapper {
            max-width: 100%;
            max-height: 600px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            position: relative;
        }

        .image-wrapper img {
            max-width: 100%;
            max-height: 550px;
            object-fit: contain;
            display: block;
        }

        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            color: var(--text-secondary);
            gap: 0.5rem;
        }

        .btn {
            background: var(--accent);
            color: white;
            border: none;
            padding: 0.8rem 1.8rem;
            font-size: 1rem;
            font-weight: 600;
            border-radius: var(--radius-md);
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: 0 4px 12px var(--accent-glow);
        }

        .btn:hover:not(:disabled) {
            background: var(--accent-hover);
            transform: translateY(-1px);
            box-shadow: 0 6px 16px var(--accent-glow);
        }

        .btn:disabled {
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-secondary);
            cursor: not-allowed;
            box-shadow: none;
        }

        /* Loading Spinner */
        .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255,255,255,0.05);
            border-top: 3px solid var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 1rem;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .stats-badge {
            background: rgba(16, 185, 129, 0.15);
            color: var(--success);
            padding: 0.35rem 0.75rem;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 600;
            border: 1px solid rgba(16, 185, 129, 0.25);
            display: none;
        }

        footer {
            margin-top: 3rem;
            color: var(--text-secondary);
            font-size: 0.85rem;
            text-align: center;
        }

        .action-bar {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
            width: 100%;
            justify-content: flex-end;
        }
    </style>
</head>
<body>

    <header>
        <h1>Manga SFX Detector</h1>
        <p class="subtitle">Upload a manga page to automatically identify sound effects (SFX). The engine segments speech bubbles, filters them out using a mask, and extracts the remaining action/ambient SFX text blocks.</p>
    </header>

    <div class="container">
        <div class="controls">
            <div class="slider-group">
                <label for="confRange">Confidence Threshold</label>
                <input type="range" id="confRange" min="0.05" max="0.95" step="0.05" value="0.25">
                <span class="slider-val" id="confVal">0.25</span>
            </div>
            
            <div style="display: flex; gap: 1rem; align-items: center;">
                <span id="detectedCount" class="stats-badge">Detected: 0 SFX</span>
                <button id="detectBtn" class="btn" disabled>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    Extract SFX
                </button>
            </div>
        </div>

        <div class="upload-section" id="dropzone">
            <div class="upload-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
            </div>
            <div class="upload-text">Drag & drop your manga page here or click to browse</div>
            <div class="upload-subtext">Supports PNG, JPG, JPEG, WEBP</div>
            <input type="file" id="fileInput" accept="image/*">
        </div>

        <div class="workspace">
            <!-- Left: Original Image -->
            <div class="pane" id="originalPane">
                <div class="pane-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                    Original Page
                </div>
                <div class="empty-state" id="originalEmpty">
                    <span>No image uploaded</span>
                </div>
                <div class="image-wrapper" id="originalWrapper" style="display: none;">
                    <img id="originalImg" src="" alt="Original Manga Page">
                </div>
            </div>

            <!-- Right: Annotated Image -->
            <div class="pane" id="resultPane">
                <div class="pane-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
                    SFX Detections (Speech Bubbles Masked)
                </div>
                <div class="empty-state" id="resultEmpty">
                    <span>Awaiting SFX extraction...</span>
                </div>
                
                <div class="empty-state" id="resultLoading" style="display: none;">
                    <div class="spinner"></div>
                    <span style="font-weight: 500;">Segmenting bubbles & detecting SFX...</span>
                </div>

                <div class="image-wrapper" id="resultWrapper" style="display: none;">
                    <img id="resultImg" src="" alt="Annotated SFX Manga Page">
                </div>
            </div>
        </div>

        <div class="action-bar" id="actionBar" style="display: none;">
            <a id="downloadBtn" class="btn" style="background: rgba(255, 255, 255, 0.05); border: 1px solid var(--border-color); color: var(--text-primary); text-decoration: none;" download="annotated_sfx.png">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                Download SFX Map
            </a>
        </div>
    </div>

    <footer>
        Manga Translation Tool SFX Detector &copy; 2026
    </footer>

    <script>
        const dropzone = document.getElementById('dropzone');
        const fileInput = document.getElementById('fileInput');
        const detectBtn = document.getElementById('detectBtn');
        const downloadBtn = document.getElementById('downloadBtn');
        const confRange = document.getElementById('confRange');
        const confVal = document.getElementById('confVal');
        const detectedCount = document.getElementById('detectedCount');
        const actionBar = document.getElementById('actionBar');

        const originalPane = document.getElementById('originalPane');
        const originalEmpty = document.getElementById('originalEmpty');
        const originalWrapper = document.getElementById('originalWrapper');
        const originalImg = document.getElementById('originalImg');

        const resultPane = document.getElementById('resultPane');
        const resultEmpty = document.getElementById('resultEmpty');
        const resultLoading = document.getElementById('resultLoading');
        const resultWrapper = document.getElementById('resultWrapper');
        const resultImg = document.getElementById('resultImg');

        let selectedFile = null;

        // Config slider logic
        confRange.addEventListener('input', (e) => {
            confVal.textContent = e.target.value;
        });

        // Click to upload
        dropzone.addEventListener('click', () => fileInput.click());

        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });

        // Drag & drop logic
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            }, false);
        });

        dropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });

        function handleFile(file) {
            if (!file.type.startsWith('image/')) {
                alert('Please upload an image file (PNG, JPG, JPEG, WEBP).');
                return;
            }
            selectedFile = file;
            
            // Show original image preview
            const reader = new FileReader();
            reader.onload = (e) => {
                originalImg.src = e.target.result;
                originalEmpty.style.display = 'none';
                originalWrapper.style.display = 'flex';
                detectBtn.disabled = false;
                
                // Reset result pane
                resultEmpty.style.display = 'flex';
                resultLoading.style.display = 'none';
                resultWrapper.style.display = 'none';
                detectedCount.style.display = 'none';
                actionBar.style.display = 'none';
            };
            reader.readAsDataURL(file);
        }

        // Detect API call
        detectBtn.addEventListener('click', async () => {
            if (!selectedFile) return;

            // Update UI state
            detectBtn.disabled = true;
            resultEmpty.style.display = 'none';
            resultLoading.style.display = 'flex';
            resultWrapper.style.display = 'none';
            detectedCount.style.display = 'none';
            actionBar.style.display = 'none';

            const formData = new FormData();
            formData.append('file', selectedFile);
            
            const conf = confRange.value;

            try {
                const response = await fetch(`/detect?conf=${conf}`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`Server returned status: ${response.status}`);
                }

                // Read headers for stats
                const count = response.headers.get('X-Detected-Objects');
                if (count !== null) {
                    detectedCount.textContent = `Detected: ${count} SFX`;
                    detectedCount.style.display = 'inline-block';
                }

                // Get blob URL and show it
                const blob = await response.blob();
                const objectURL = URL.createObjectURL(blob);
                
                resultImg.src = objectURL;
                downloadBtn.href = objectURL;
                
                resultLoading.style.display = 'none';
                resultWrapper.style.display = 'flex';
                actionBar.style.display = 'flex';

            } catch (error) {
                console.error(error);
                alert('Error running detection: ' + error.message);
                resultEmpty.style.display = 'flex';
                resultLoading.style.display = 'none';
            } finally {
                detectBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
