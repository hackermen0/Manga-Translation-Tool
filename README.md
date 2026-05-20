# Manga Translation Tool

A full-stack desktop application for automated manga translation, built like a modern image editor and purpose-built for scanlation workflows.

The tool detects speech bubbles using a custom-trained YOLOv8 segmentation model, inpaints the original Japanese text to produce a clean canvas, translates the extracted text, and redraws translated English text directly onto the page — all from a single Electron-based UI.

---

## Demo

<img width="720" height="1024" alt="bubble_cluster_024" src="https://github.com/user-attachments/assets/ca5e6458-ca23-4944-86e5-ca08fd8e3c77" />
<img width="720" height="1024" alt="final_processed_024" src="https://github.com/user-attachments/assets/dce16e52-6d00-4a0a-aade-fb70b0104538" />
<img width="720" height="1024" alt="redrawn_024" src="https://github.com/user-attachments/assets/ce47f6dc-292f-4a4d-91e0-4930bcf4b318" />
<img width="1904" height="962" alt="image" src="https://github.com/user-attachments/assets/8461fe66-246c-407b-a67b-cd031442b506" />

---

## Features

- **Speech Bubble Detection** — Custom fine-tuned YOLOv8m-seg model achieves 0.981 mask mAP50 and 0.904 mask mAP50-95, trained on 8,200+ manga images across diverse art styles and panel layouts
- **Hybrid Inpainting** — Programmatic white-fill with variable border erosion and per-page confidence tuning produces a clean canvas for text redrawing; Stable Diffusion inpainting support planned for complex backgrounds
- **OCR Text Detection** — Extracts Japanese text from manga pages using Google Vision API, with planned migration to MangaOCR for a fully offline, free pipeline
- **Mask-Contained Text Grouping** — OCR detections are assigned to speech bubbles using pixel-level mask containment; DBSCAN spatial clustering serves as a fallback for floating text and SFX outside bubble regions
- **Contextual Translation** — Translates grouped bubble text using Google Translate API, with surrounding bubble context passed in for improved coherence across a page
- **Text Redrawing** — Redraws translated English text onto the clean canvas using PIL, respecting bounding box coordinates from OCR
- **Layered UI** — Photoshop-inspired interface built with SvelteKit + Electron, featuring a file explorer, layers panel, translation panel, and a 6-color theme system
- **SFX Handling** — Sound effects outside bubble regions are identified via DBSCAN and skipped to preserve background artwork

---

## Speech Bubble Detection Model

The speech bubble detector is a fine-tuned YOLOv8m-seg instance segmentation model, trained on 8,200+ manga images sourced from diverse titles, art styles, and panel layouts.

### Evaluation Results

| Metric | Bounding Box | Segmentation Mask |
|--------|-------------|-------------------|
| Precision (P) | 0.965 | 0.966 |
| Recall (R) | 0.971 | 0.977 |
| mAP50 | 0.980 | 0.981 |
| mAP50-95 | 0.954 | 0.904 |

**14,741 instances** evaluated across the validation set.

### What the numbers mean

- **Precision 0.966** — when the model flags a speech bubble, it is correct 96.6% of the time. False positives (misidentifying artwork as a bubble) are extremely rare in practice.
- **Recall 0.977** — the model successfully captures 97.7% of all speech bubbles on a page, missing practically nothing.
- **Mask mAP50 0.981** — at a 50% IoU threshold, bubble boundary alignment is near-perfect.
- **Mask mAP50-95 0.904** — the generated polygon masks track intricate, irregular bubble curves with high geometric precision even at strict IoU thresholds. This is the most meaningful metric for clean text removal.

---

## Inpainting Pipeline

The inpainting step converts a raw manga page into a clean canvas ready for translated text, using a detection → mask → fill pipeline.

### How it works

1. The YOLOv8 model runs inference on the page and returns per-bubble segmentation masks
2. Each mask is optionally eroded inward by a configurable number of pixels (`--erosion`) to preserve bubble border lines
3. The programmatic processor evaluates each bubble's interior — if the background variance is below a threshold, it white-fills the masked region
4. Bubbles with complex or textured backgrounds fall through to a generative inpainting engine (Stable Diffusion, planned)

### CLI usage

```bash
# Standard manga page
python -m inpainting.pipeline --image page.jpg --inpaint-model none --conf 0.5 --erosion 3

# Complex borderless bubble style
python -m inpainting.pipeline --image page.jpg --inpaint-model none --conf 0.2 --erosion 5
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--conf` | 0.5 | Detection confidence threshold. Lower values catch borderless and irregular bubbles. |
| `--erosion` | 3 | Inward mask erosion in pixels. Prevents fill from eating bubble border lines. |
| `--inpaint-model` | none | Stable Diffusion model ID or path. Pass `none` to use programmatic white fill only. |

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| UI | SvelteKit, Tailwind CSS, Bits UI |
| Desktop Shell | Electron |
| Backend API | Python, FastAPI |
| Communication | Fetch, WebSockets |
| Speech Bubble Detection | YOLOv8m-seg (Ultralytics) |
| Inpainting | OpenCV, PIL — Stable Diffusion (planned) |
| OCR | Google Vision API — MangaOCR (planned) |
| Translation | Google Translate API |
| Text Grouping | Mask containment + DBSCAN fallback (scikit-learn) |
| Image Processing | PIL (Pillow), OpenCV |

---

## How It Works

### 1. Speech Bubble Detection
The manga page is passed through the fine-tuned YOLOv8m-seg model, which returns per-instance segmentation masks and bounding boxes for every detected speech bubble.

### 2. Inpainting
Each bubble mask is eroded inward to preserve border lines, then white-filled to produce a clean canvas. Bubbles with non-white or textured interiors will fall through to Stable Diffusion inpainting (planned).

### 3. OCR and Text Extraction
The original (pre-inpainted) page is passed to the Google Vision API, which returns bounding box coordinates and raw Japanese text for each detected symbol or word fragment.

### 4. Text Grouping
Each OCR detection is assigned to a speech bubble by checking whether its center point falls within that bubble's pixel mask. Text that falls outside all bubble masks is clustered using DBSCAN — this catches floating narrative text and SFX, which are flagged and skipped during translation.

### 5. Translation
Each bubble's concatenated text is sent to the Google Translate API. Surrounding bubble text is passed as context to improve translation coherence across a page.

### 6. Text Redrawing
Translated English text is redrawn onto the clean canvas using PIL, positioned within the original bubble bounding box with font sizing adjusted to fit.

---

## Roadmap

### Speech Bubble Detection
- [x] Fine-tune YOLOv8m-seg on 8,200+ manga images
- [x] Achieve 0.981 mask mAP50 and 0.904 mask mAP50-95
- [ ] Expand dataset with webtoon and colored manga styles
- [ ] Evaluate YOLOv8l-seg for marginal accuracy gains on irregular bubbles

### Inpainting
- [x] Programmatic white-fill with border erosion and variance threshold
- [x] Variable `--conf` and `--erosion` CLI tuning per page
- [x] Detection → mask → inpainting pipeline
- [ ] Stable Diffusion inpainting for complex and textured backgrounds

### OCR
- [ ] Replace Google Vision API with MangaOCR (free, offline, manga-specific)
- [ ] Evaluate EasyOCR as an alternative backend

### Text Grouping
- [x] Mask containment as primary grouping method
- [x] DBSCAN as fallback for floating text and SFX
- [ ] SFX auto-detection and skip logic

### Translation
- [ ] Rework translation pipeline to consume new mask-based bubble grouping
- [ ] Support DeepL as an alternative translation backend
- [ ] Character metadata system — associate bubbles with specific characters for richer context
- [ ] Evaluate manga-specific fine-tuned translation models

### Redrawing
- [ ] Automatic text wrapping and font size scaling relative to bubble size
- [ ] Bold and stylized text detection for emphasis preservation

### UI
- [ ] Dark mode
- [ ] Per-page translation progress in status bar
- [ ] Manual correction layer for missed or incorrect bubbles
- [ ] Export pipeline

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- Google Vision API key
- Google Translate API key

### Installation

```bash
# Clone the repository
git clone https://github.com/hackermen0/Manga-Translation-Tool.git
cd Manga-Translation-Tool

# Install frontend dependencies
cd Frontend
npm install

# Install backend dependencies
cd ../Backend
pip install -r requirements.txt
```

### Running the App

```bash
# Start the Python backend
cd Backend
uvicorn main:app --reload

# Start the Electron frontend (in a separate terminal)
cd Frontend
npm run dev
```

### Running the Inpainting Pipeline

```bash
python -m inpainting.pipeline \
  --image <PATH_TO_PAGE> \
  --inpaint-model none \
  --conf 0.5 \
  --erosion 3
```

---

## Project Structure

```
Manga-Translation-Tool/
├── Backend/
│   ├── inpainting/       # Detection → mask → inpainting pipeline
│   │   ├── pipeline.py
│   │   ├── cleaner.py
│   │   └── processors/
│   │       ├── programmatic.py
│   │       └── generative.py
│   ├── models/           # Trained model weights
│   └── main.py           # FastAPI entry point
├── Frontend/             # SvelteKit + Electron desktop app
├── main.js               # Electron entry point
├── requirements.txt
└── package.json
```

---

## Acknowledgements

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) for the segmentation model
- [Manga109](http://www.manga109.org/) for the training dataset
- [Google Vision API](https://cloud.google.com/vision) for OCR
- [Google Translate API](https://cloud.google.com/translate) for translation
- [BasicCAT](https://www.basiccat.org/) — the closest existing tool in this space, used as a reference for pipeline design
- [Bits UI](https://www.bits-ui.com/) for headless Svelte components

---

## License

MIT