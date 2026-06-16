from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WORKSPACES_DIR = BASE_DIR / "workspaces"
WORKSPACES_DIR.mkdir(exist_ok=True)

DETECTOR_WEIGHTS = str(BASE_DIR.parent / "models" / "bubble_segmenter_best.pt")
