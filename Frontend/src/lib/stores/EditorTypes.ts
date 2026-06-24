export interface Point {
    x: number;
    y: number;
}

export interface TypesetStyle {
    fontSize: number;
    fontFamily: string;
    fontWeight: string | number;
    fontColor: string;
    offsetX: number;
    offsetY: number;
    lineHeight: number;
    textAlign: 'center' | 'left' | 'right';
    letterSpacing: number;
    autoFit: boolean;
    fontStyle?: 'normal' | 'italic';
    writingMode?: 'horizontal' | 'vertical';
    outline?: boolean;
    outlineColor?: string;
    outlineWidth?: number;
}

export const DEFAULT_TYPESET_STYLE: TypesetStyle = {
    fontSize: 16,
    fontFamily: 'CC Wild Words',
    fontWeight: 'normal',
    fontColor: '#000000',
    offsetX: 0,
    offsetY: 0,
    lineHeight: 1.2,
    textAlign: 'center',
    letterSpacing: 0.5,
    autoFit: true,
    fontStyle: 'normal',
    writingMode: 'horizontal',
    outline: false,
    outlineColor: '#ffffff',
    outlineWidth: 2
};

export interface MangaBubble {
    id: number;
    points: Point[];
    ja_text: string;
    en_text: string;
    typeset?: TypesetStyle;
    is_sfx?: boolean;
}

export interface RedrawingStroke {
    points: Point[];
    brushSize: number;
    brushColor: string;
    type: 'eraser' | 'restore' | 'heal';
    hardness?: number;
    sourceMode?: 'auto' | 'manual';
    sourceAnchor?: Point | null;
}

export interface MangaPage {
    pageId: string;
    originalFilename: string;
    originalUrl: string;
    inpaintedUrl: string | null;
    bubbles: MangaBubble[];
    detected: boolean;
    redrawingStrokes: RedrawingStroke[];
}
