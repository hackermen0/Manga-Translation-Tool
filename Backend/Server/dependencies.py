import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

# noqa: E402
from ocr.processor import MangaOCRProcessor
from translation.translate import MangaTranslationEngine
from speech_bubble_detection.detector import SpeechBubbleDetector
from inpainting.cleaner import HybridMangaCleaner

from config import SPEECH_BUBBLE_DETECTOR_WEIGHTS, TEXT_DETECTOR_WEIGHTS
from ultralytics import YOLO

bubble_detector = SpeechBubbleDetector(SPEECH_BUBBLE_DETECTOR_WEIGHTS)
text_detector = YOLO(TEXT_DETECTOR_WEIGHTS, task="detect")

ocr_processor = None
manga_cleaner = None
manga_translator = None


def get_ocr_processor():
    global ocr_processor
    if ocr_processor is None:
        ocr_processor = MangaOCRProcessor()
    return ocr_processor


def get_manga_cleaner():
    global manga_cleaner
    if manga_cleaner is None:
        manga_cleaner = HybridMangaCleaner(
            generative_model_id_or_path=None
        )
    return manga_cleaner


def get_manga_translator():
    global manga_translator
    if manga_translator is None:
        manga_translator = MangaTranslationEngine()
    return manga_translator


lama_session = None

def get_lama_session():
    global lama_session
    if lama_session is None:
        import onnxruntime as ort
        import torch
        
        # Paths to the model files
        model_dir = Path(__file__).resolve().parent.parent / "models"
        onnx_path = model_dir / "lama_manga_dynamic.onnx"
        
        if not onnx_path.exists():
            import urllib.request
            print("Downloading LaMa ONNX model...")
            url = "https://huggingface.co/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx"
            urllib.request.urlretrieve(url, str(onnx_path))
            print("LaMa ONNX model download complete!")
            
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if torch.cuda.is_available() else ['CPUExecutionProvider']
        print(f"Initializing LaMa InferenceSession with providers: {providers}")
        lama_session = ort.InferenceSession(str(onnx_path), providers=providers)
        
    return lama_session
