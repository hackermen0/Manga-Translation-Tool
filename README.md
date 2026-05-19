# Manga Translation Tool

A full-stack desktop application for automated manga translation, built like a modern image editor and purpose-built for scanlation workflows.

The tool uses a custom-trained U-Net segmentation model (ResNet-34 backbone, 0.90 IoU) to detect speech bubbles, extracts Japanese text via OCR, translates it to English, and redraws the translated text directly onto the page, all from a single Electron-based UI.

---

## Demo

<img width="720" height="1024" alt="bubble_cluster_024" src="https://github.com/user-attachments/assets/ca5e6458-ca23-4944-86e5-ca08fd8e3c77" />

<img width="720" height="1024" alt="final_processed_024" src="https://github.com/user-attachments/assets/dce16e52-6d00-4a0a-aade-fb70b0104538" />

<img width="720" height="1024" alt="redrawn_024" src="https://github.com/user-attachments/assets/ce47f6dc-292f-4a4d-91e0-4930bcf4b318" />

<img width="1904" height="962" alt="image" src="https://github.com/user-attachments/assets/8461fe66-246c-407b-a67b-cd031442b506" />

---

## Features

- **Speech Bubble Detection** -- Custom-trained U-Net model with ResNet-34 backbone achieves 0.90 IoU and 0.94 Dice score on a dataset of 873 manga pages across 16 titles
- **OCR Text Detection** -- Extracts Japanese text from manga pages using Google Vision API, with planned migration to Microsoft TrOCR for a fully offline, free pipeline
- **Spatial Clustering** -- Groups detected text into speech bubbles using DBSCAN (Density-Based Spatial Clustering) as a lightweight fallback pipeline
- **Contextual Translation** -- Translates grouped bubble text using Google Translate API, with surrounding bubble context passed in for improved accuracy
- **Text Redrawing** -- Removes original Japanese text by drawing over it and redraws translated English text using PIL, respecting bounding box coordinates from OCR
- **Layered UI** -- Photoshop-inspired interface built with SvelteKit + Electron, featuring a file explorer, layers panel, translation panel, and a 6-color theme system
- **SFX Handling** -- Sound effects (SFX) are intentionally skipped to avoid redrawing over background artwork

---

## Speech Bubble Detection Model

The speech bubble detector is a U-Net segmentation model with a ResNet-34 encoder backbone, trained from scratch on a custom-labeled dataset of manga pages.

### Training Summary

| Run | Images | Epochs | Loss Function | IoU | Dice |
|-----|--------|--------|---------------|-----|------|
| 1 | 89 | 10 | BCE | 0.4294 | 0.5458 |
| 4 | 89 | 50 | BCE | 0.6155 | 0.7110 |
| 11 | 150 | 10 | BCE + Dice | 0.7267 | 0.8230 |
| 20 | 190 | 10 | BCE + Dice, ResNet-34 | 0.7474 | 0.8254 |
| 21 | 190 | 20 | BCE + Dice, ResNet-34 | 0.7884 | 0.8702 |
| 26 | 391 | 10 | BCE + Dice, ResNet-34 | 0.8680 | 0.9226 |
| 28 | 873 | 20 | BCE + Dice, ResNet-34 | 0.8951 | 0.9352 |
| 29 | 873 | 50 | BCE + Dice, ResNet-34 | **0.8995** | **0.9375** |

### Key Findings

- Switching from pure BCE loss to a combined BCE + Dice loss combo was the single biggest improvement, jumping IoU from 0.62 to 0.73
- Upgrading the encoder backbone from default to ResNet-34 pushed IoU past 0.74 and enabled consistent generalization across manga styles
- Scaling the dataset from 89 to 873 images across 16 diverse manga titles was critical -- more diversity directly translated to better generalization
- Data augmentation without the ResNet-34 backbone consistently hurt performance, suggesting the backbone change was a prerequisite for augmentation to help
- The best model (Run 29) was trained on 873 images across 16 manga titles over 50 epochs, achieving 0.90 IoU and 0.94 Dice score

### Dataset

873 labeled manga pages sourced from 16 titles covering a wide range of art styles, panel layouts, and bubble shapes to maximize generalization.

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
| ML Model | PyTorch, U-Net, ResNet-34 |

---

## How It Works

### 1. Speech Bubble Detection
The manga page is passed through the custom U-Net model which produces a segmentation mask identifying speech bubble regions with 0.90 IoU accuracy.

### 2. OCR and Text Extraction
Detected bubble regions are sent to the Google Vision API which returns bounding box coordinates and raw Japanese text for each detected symbol or word fragment.

### 3. Text Grouping via DBSCAN
Raw OCR output is fragmented -- each speech bubble may have dozens of individual detections. The center point of each bounding box is computed and DBSCAN clusters nearby detections together, mapping each cluster to a single speech bubble.

### 4. Translation
Each cluster's text is concatenated into a single string. Surrounding bubble text is passed as context to the Google Translate API to improve translation coherence across a page.

### 5. Text Removal and Redrawing
The original text is removed by drawing a white rectangle with padding over the bounding region. The translated English text is then redrawn into the same area using PIL, with font sizing adjusted to fit within the detected region.

---

## Roadmap

### OCR
- [ ] Replace Google Vision API with Microsoft TrOCR (free, offline ML model)
- [ ] Explore EasyOCR as an alternative OCR backend

### Speech Bubble Detection
- [x] Train U-Net segmentation model with ResNet-34 backbone
- [x] Achieve 0.90 IoU on 873-image custom dataset
- [ ] Expand dataset further to improve generalization on webtoons and colored manga
- [ ] Explore Mask R-CNN for instance-level bubble detection

### Translation
- [ ] Character metadata system -- associate speech bubbles with specific characters to provide richer translation context
- [ ] Evaluate custom fine-tuned translation models for manga-specific language

### Redrawing
- [ ] Automatic text wrapping and font size scaling relative to bubble size
- [ ] Bold and stylized text detection for emphasis preservation
- [ ] Stable Diffusion inpainting for cleaner text removal in complex backgrounds

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

### Speech Bubble Inpainting Pipeline (Detection → Mask → Inpainting)

```bash
python Backend/inpainting/pipeline.py --image <PATH_TO_PAGE> --inpaint-model <MODEL_ID_OR_PATH>
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
- [BasicCAT](https://www.basiccat.org/) -- the closest existing tool in this space, used as a reference for backend pipeline design
- [Bits UI](https://www.bits-ui.com/) for headless Svelte components

---

## License

MIT
