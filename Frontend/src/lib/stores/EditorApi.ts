import type { MangaBubble, RedrawingStroke } from './EditorTypes';

const BACKEND_URL = "http://127.0.0.1:8000";

/**
 * Reorders the pages in a workspace on the backend.
 */
export async function apiReorderPages(workspaceId: string, pageIds: string[]): Promise<any> {
    const response = await fetch(`${BACKEND_URL}/api/workspace/${workspaceId}/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_order: pageIds })
    });
    if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
    }
    return response.json();
}

/**
 * Deletes a page from the workspace on the backend.
 */
export async function apiDeletePage(workspaceId: string, pageId: string): Promise<any> {
    const response = await fetch(`${BACKEND_URL}/api/workspace/${workspaceId}/page/${pageId}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
    }
    return response.json();
}

/**
 * Initiates speech bubble detection on the backend.
 */
export async function apiDetectBubbles(workspaceId: string, pageId: string): Promise<any> {
    const response = await fetch(`${BACKEND_URL}/api/workspace/${workspaceId}/page/${pageId}/detect`, {
        method: 'POST'
    });
    if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
    }
    return response.json();
}

/**
 * Initiates Sound Effects (SFX) and bubble detection on the backend.
 */
export async function apiDetectSFX(workspaceId: string, pageId: string): Promise<any> {
    const response = await fetch(`${BACKEND_URL}/api/workspace/${workspaceId}/page/${pageId}/detect-sfx`, {
        method: 'POST'
    });
    if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
    }
    return response.json();
}

/**
 * Runs OCR on a target page.
 */
export async function apiRunOcr(workspaceId: string, pageId: string): Promise<any> {
    const response = await fetch(`${BACKEND_URL}/api/workspace/${workspaceId}/page/${pageId}/ocr`, {
        method: 'POST'
    });
    if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
    }
    return response.json();
}

/**
 * Runs Japanese -> English translation.
 */
export async function apiRunTranslation(workspaceId: string, pageId: string): Promise<any> {
    const response = await fetch(`${BACKEND_URL}/api/workspace/${workspaceId}/page/${pageId}/translate`, {
        method: 'POST'
    });
    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server responded with status ${response.status}`);
    }
    return response.json();
}

/**
 * Saves current manga speech bubble layouts.
 */
export async function apiSaveBubbles(workspaceId: string, pageId: string, bubbles: MangaBubble[]): Promise<any> {
    const response = await fetch(`${BACKEND_URL}/api/workspace/${workspaceId}/page/${pageId}/bubbles`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bubbles })
    });
    if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
    }
    return response.json();
}

/**
 * Saves redrawing tool brush strokes.
 */
export async function apiSaveRedrawingStrokes(workspaceId: string, pageId: string, strokes: RedrawingStroke[]): Promise<any> {
    const response = await fetch(`${BACKEND_URL}/api/workspace/${workspaceId}/page/${pageId}/strokes`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strokes })
    });
    if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
    }
    return response.json();
}

/**
 * Runs image inpainting inside speech bubbles on a target page.
 */
export async function apiRunInpainting(workspaceId: string, pageId: string, bubbles: MangaBubble[], borderErosion: number): Promise<any> {
    const response = await fetch(`${BACKEND_URL}/api/workspace/${workspaceId}/page/${pageId}/inpaint`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            bubbles,
            border_erosion: borderErosion
        })
    });
    if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
    }
    return response.json();
}

/**
 * Saves current typesetting/typeset configuration properties.
 */
export async function apiSaveTypesetting(workspaceId: string, pageId: string, bubbles: MangaBubble[]): Promise<any> {
    const response = await fetch(`${BACKEND_URL}/api/workspace/${workspaceId}/page/${pageId}/typesetting`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bubbles })
    });
    if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
    }
    return response.json();
}
