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

from config import DETECTOR_WEIGHTS

bubble_detector = SpeechBubbleDetector(DETECTOR_WEIGHTS)

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
