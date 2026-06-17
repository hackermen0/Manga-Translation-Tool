from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WORKSPACES_DIR = BASE_DIR / "workspaces"
WORKSPACES_DIR.mkdir(exist_ok=True)

SPEECH_BUBBLE_DETECTOR_WEIGHTS = str(BASE_DIR.parent / "models" / "speech_bubble_detector.pt")
TEXT_DETECTOR_WEIGHTS = str(BASE_DIR.parent / "models" / "text_detector.onnx")
