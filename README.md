# Manga Translation Tool

A full-stack desktop application for automated manga translation, built like a modern image editor, purpose-built for scanlation workflows.

The tool detects Japanese text in manga pages, groups it by speech bubble using spatial clustering, translates it to English, and redraws the translated text directly onto the page, all from a single Electron-based UI.

---

## Demo


<img width="720" height="1024" alt="bubble_cluster_024" src="https://github.com/user-attachments/assets/ca5e6458-ca23-4944-86e5-ca08fd8e3c77" />

<img width="720" height="1024" alt="final_processed_024" src="https://github.com/user-attachments/assets/dce16e52-6d00-4a0a-aade-fb70b0104538" />

<img width="720" height="1024" alt="textbox_024" src="https://github.com/user-attachments/assets/f926a9d3-d24e-423d-96c4-d1e94c2ed166" />

<img width="720" height="1024" alt="redrawn_024" src="https://github.com/user-attachments/assets/ce47f6dc-292f-4a4d-91e0-4930bcf4b318" />

<img width="1904" height="962" alt="image" src="https://github.com/user-attachments/assets/8461fe66-246c-407b-a67b-cd031442b506" />





---

## Features

- **OCR Text Detection** — Extracts Japanese text from manga pages using Google Vision API, with planned migration to Microsoft TrOCR for a fully offline, free pipeline
- **Spatial Clustering** — Groups detected text into speech bubbles using DBSCAN (Density-Based Spatial Clustering), eliminating the need for explicit contour-based bubble detection
- **Contextual Translation** — Translates grouped bubble text using Google Translate API, with surrounding bubble context passed in for improved accuracy
- **Text Redrawing** — Removes original Japanese text by drawing over it and redraws translated English text using PIL, respecting bounding box coordinates from OCR
- **Layered UI** — Photoshop-inspired interface built with SvelteKit + Electron, featuring a file explorer, layers panel, translation panel, and a 6-color theme system
- **SFX Handling** — Sound effects (SFX) are intentionally skipped to avoid redrawing over background artwork

---

## Tech Stack

| Layer | Tools |
|---|---|
| UI | SvelteKit, Tailwind CSS, Bits UI |
| Desktop Shell | Electron |
| Backend API | Python, FastAPI |
| Communication | Fetch, WebSockets |
| OCR | Google Vision API (current), Microsoft TrOCR (planned) |
| Translation | Google Translate API |
| Image Processing | PIL (Pillow), OpenCV |
| Clustering | scikit-learn (DBSCAN) |

---

## How It Works

### 1. OCR and Text Extraction
The manga page is sent to the Google Vision API which returns bounding box coordinates and raw Japanese text for each detected symbol or word fragment.

### 2. Text Grouping via DBSCAN
Raw OCR output is fragmented, each speech bubble may have dozens of individual detections. The center point of each bounding box is computed and DBSCAN clusters nearby detections together, effectively mapping each cluster to a single speech bubble without needing to detect the bubble outline itself.

### 3. Translation
Each cluster's text is concatenated into a single string. Surrounding bubble text is passed as context to the Google Translate API to improve translation coherence across a page.

### 4. Text Removal and Redrawing
The original text is removed by drawing a white rectangle with padding over the bounding region. The translated English text is then redrawn into the same area using PIL, with font sizing adjusted to fit within the detected region.

---

## Roadmap

### OCR
- [ ] Replace Google Vision API with Microsoft TrOCR (free, offline ML model)
- [ ] Train or integrate a dedicated speech bubble detection model (U-Net / Mask R-CNN)
- [ ] Explore EasyOCR as an alternative OCR backend

### Translation
- [ ] Character metadata system, associate speech bubbles with specific characters to provide richer translation context
- [ ] Evaluate custom fine-tuned translation models for manga-specific language

### Redrawing
- [ ] Automatic text wrapping and font size scaling relative to bubble size
- [ ] Bold and stylized text detection for emphasis preservation
- [ ] Stable Diffusion inpainting for cleaner text removal in complex backgrounds

### Speech Bubble Detection (Future)
- [ ] OpenCV contour detection for classic bubble shapes
- [ ] Canny edge detection + contour extraction pipeline
- [ ] Shape heuristics filtering (area, aspect ratio, solidity, circularity)
- [ ] MSER (Maximally Stable Extremal Regions) for blob-based detection
- [ ] Deep learning segmentation (U-Net / Mask R-CNN) for complex layouts
- [ ] Color-based segmentation for webtoons and colored manga

### UI
- [ ] Dark mode
- [ ] Status bar showing per-page translation progress
- [ ] Toggle between Bubble Text Grouping and Sentence Text Grouping
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

---

## Project Structure

```
Manga-Translation-Tool/
├── Backend/          # Python FastAPI server, OCR, clustering, translation logic
├── Frontend/         # SvelteKit + Electron desktop app
├── main.js           # Electron entry point
├── requirements.txt  # Python dependencies
└── package.json      # Node dependencies
```

---

## Acknowledgements

- [Google Vision API](https://cloud.google.com/vision) for OCR
- [Google Translate API](https://cloud.google.com/translate) for translation
- [BasicCAT](https://www.basiccat.org/) — the closest existing tool in this space, used as a reference for backend pipeline design
- [Bits UI](https://www.bits-ui.com/) for headless Svelte components

---

## License

MIT
