from __future__ import annotations
from typing import List
# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class PointModel(BaseModel):
    x: float
    y: float


class TypesetStyleModel(BaseModel):
    fontSize: float = 16
    fontFamily: str = "Bangers"
    fontWeight: str | int = "normal"
    fontColor: str = "#000000"
    offsetX: float = 0
    offsetY: float = 0
    lineHeight: float = 1.2
    textAlign: str = "center"
    letterSpacing: float = 0.5
    autoFit: bool = True


class BubbleUpdateModel(BaseModel):
    id: int
    points: List[PointModel]
    ja_text: str = ""
    en_text: str = ""
    typeset: TypesetStyleModel | None = None


class BubblesPayload(BaseModel):
    bubbles: List[BubbleUpdateModel]


class ReorderRequest(BaseModel):
    new_order: List[str]


class StrokeModel(BaseModel):
    points: List[PointModel]
    brushSize: float
    brushColor: str = "#ffffff"
    type: str = "eraser"


class StrokesPayload(BaseModel):
    strokes: List[StrokeModel]


class InpaintPayload(BaseModel):
    bubbles: List[BubbleUpdateModel]
    border_erosion: int = 2
