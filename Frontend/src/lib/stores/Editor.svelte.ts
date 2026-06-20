import { layerStateManager } from './LayerStateManager.svelte';
import { imageState } from './Image.svelte';
import { historyManager } from './History.svelte';
import {
    type Point,
    type TypesetStyle,
    DEFAULT_TYPESET_STYLE,
    type MangaBubble,
    type RedrawingStroke,
    type MangaPage
} from './EditorTypes';
import {
    apiReorderPages,
    apiDeletePage,
    apiDetectBubbles,
    apiDetectSFX,
    apiRunOcr,
    apiRunTranslation,
    apiSaveBubbles,
    apiSaveRedrawingStrokes,
    apiRunInpainting,
    apiSaveTypesetting
} from './EditorApi';

class EditorState {
    activeSession = $state('detection');

    // QC visual proofing overlay states
    qcMode = $state<'onion' | 'split'>('onion');
    qcBlendValue = $state<number>(50);
    qcSplitPercentage = $state<number>(50);
    qcHighlightInpaint = $state<boolean>(false);
    exportHandler = $state<(() => Promise<void>) | null>(null);
    exportAllHandler = $state<(() => Promise<void>) | null>(null);

    workspaceId = $state<string | null>(null);
    workspaceName = $state<string | null>(null);
    activePageId = $state<string | null>(null);
    activeBubbleId = $state<number | null>(null);
    isProcessing = $state<boolean>(false);
    isOcrProcessing = $state<boolean>(false);
    isTranslating = $state<boolean>(false);
    pages = $state<MangaPage[]>([]);

    activeDetectionTool = $state<'edit' | 'drag' | 'create' | 'delete'>('edit');
    activeRedrawingTool = $state<'pan' | 'eraser' | 'restore'>('pan');
    activeTypesettingTool = $state<'select' | 'drag' | 'text' | 'edit' | 'delete'>('select');
    brushSize = $state(20);
    brushColor = $state('#ffffff');

    setDetectionTool(tool: 'edit' | 'drag' | 'create' | 'delete') {
        this.activeDetectionTool = tool;
    }

    setRedrawingTool(tool: 'pan' | 'eraser' | 'restore') {
        this.activeRedrawingTool = tool;
    }

    setTypesettingTool(tool: 'select' | 'drag' | 'text' | 'edit' | 'delete') {
        this.activeTypesettingTool = tool;
    }

    setBrushSize(size: number) {
        this.brushSize = size;
    }

    get activePage(): MangaPage | undefined {
        return this.pages.find(p => p.pageId === this.activePageId);
    }

    setActiveSession(section: string) {
        this.activeSession = section;
    }

    initWorkspace(workspaceData: { workspace_id: string; name?: string; pages: any[] }) {
        this.activePageId = null;
        this.activeBubbleId = null;
        layerStateManager.reset();
        imageState.reset();
        historyManager.clear();

        this.workspaceId = workspaceData.workspace_id;
        this.workspaceName = workspaceData.name || workspaceData.workspace_id;

        if (typeof window !== 'undefined') {
            localStorage.setItem('active_manga_workspace_id', this.workspaceId);
        }

        this.pages = workspaceData.pages.map((rawPage: any) => ({
            pageId: String(Number(rawPage.page_id.replace("page_", ""))),
            originalFilename: rawPage.original_filename,
            originalUrl: rawPage.original_url,
            inpaintedUrl: rawPage.inpainted_url,
            bubbles: rawPage.bubbles || [],
            detected: rawPage.detected ?? (rawPage.bubbles && rawPage.bubbles.length > 0),
            redrawingStrokes: rawPage.redrawingStrokes || [],
            layers: [],
            selectedLayerId: null
        }));

        if (this.pages.length > 0) {
            this.setActivePage(this.pages[0].pageId);
        }
    }

    setActivePage(pageId: string) {
        if (this.activePageId === pageId) return;

        if (this.activePageId) {
            layerStateManager.saveCurrentPage(this.activePageId);
        }

        this.activePageId = pageId;

        const page = this.pages.find(p => p.pageId === pageId);
        if (page && page.bubbles && page.bubbles.length > 0) {
            this.activeBubbleId = page.bubbles[0].id;
        } else {
            this.activeBubbleId = null;
        }

        layerStateManager.loadPage(pageId);
    }

    async reorderPages(fromIndex: number, toIndex: number) {
        if (fromIndex === toIndex) return;

        const newPages = [...this.pages];
        const [movedPage] = newPages.splice(fromIndex, 1);
        newPages.splice(toIndex, 0, movedPage);

        this.pages = newPages;

        if (this.workspaceId) {
            try {
                const newOrderIds = this.pages.map(p => p.pageId);
                await apiReorderPages(this.workspaceId, newOrderIds);
            } catch (err) {
                console.error("Failed to save new page order to server:", err);
            }
        }
    }

    async deletePage(pageId: string) {
        if (!this.workspaceId) return;
        try {
            const data = await apiDeletePage(this.workspaceId, pageId);
            if (data.status === 'success') {
                const index = this.pages.findIndex(p => p.pageId === pageId);
                if (index !== -1) {
                    this.pages.splice(index, 1);
                    layerStateManager.deletePage(pageId);

                    // If the deleted page was active, activate another page
                    if (this.activePageId === pageId) {
                        if (this.pages.length > 0) {
                            const nextActiveIndex = Math.min(index, this.pages.length - 1);
                            this.setActivePage(this.pages[nextActiveIndex].pageId);
                        } else {
                            this.activePageId = null;
                            this.activeBubbleId = null;
                            layerStateManager.loadPage(""); // Clear active layers
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Delete page failed:", error);
            alert("Failed to delete page. Is your FastAPI server running?");
        }
    }

    loadDummyBubbles() {
        const page = this.activePage;
        if (!page) return;

        page.bubbles = [
            {
                id: 1,
                points: [
                    { x: 150, y: 100 }, { x: 350, y: 100 },
                    { x: 400, y: 200 }, { x: 350, y: 300 },
                    { x: 200, y: 350 }, { x: 150, y: 300 },
                    { x: 100, y: 200 }
                ],
                ja_text: "テスト",
                en_text: "Test bubble",
                is_sfx: false
            }
        ];
    }

    async detectBubbles() {
        if (!this.workspaceId || !this.activePageId) return;
        historyManager.recordState(this.activePageId);

        this.isProcessing = true;

        try {
            const data = await apiDetectBubbles(this.workspaceId, this.activePageId);
            if (data.status === 'success') {
                const page = this.activePage;
                if (page) {
                    page.bubbles = data.bubbles;
                    page.detected = true;
                    if (page.bubbles.length > 0) {
                        this.activeBubbleId = page.bubbles[0].id;
                    } else {
                        this.activeBubbleId = null;
                    }
                }
            }
        } catch (error) {
            console.error("Speech bubble detection failed:", error);
            alert("Failed to run AI detection. Is your FastAPI server running?");
        } finally {
            this.isProcessing = false;
        }
    }

    async detectSFX() {
        if (!this.workspaceId || !this.activePageId) return;
        historyManager.recordState(this.activePageId);

        this.isProcessing = true;

        try {
            const data = await apiDetectSFX(this.workspaceId, this.activePageId);
            if (data.status === 'success') {
                const page = this.activePage;
                if (page) {
                    page.bubbles = data.bubbles;
                    page.detected = true;
                    if (page.bubbles.length > 0) {
                        this.activeBubbleId = page.bubbles[0].id;
                    } else {
                        this.activeBubbleId = null;
                    }
                }
            }
        } catch (error) {
            console.error("SFX detection failed:", error);
            alert("Failed to run AI SFX detection. Is your FastAPI server running?");
        } finally {
            this.isProcessing = false;
        }
    }

    async runOcr() {
        if (!this.workspaceId || !this.activePageId) return;
        historyManager.recordState(this.activePageId);

        this.isOcrProcessing = true;

        try {
            const data = await apiRunOcr(this.workspaceId, this.activePageId);
            if (data.status === 'success') {
                const page = this.activePage;
                if (page) {
                    page.bubbles = data.bubbles;
                    if (page.bubbles.length > 0 && this.activeBubbleId === null) {
                        this.activeBubbleId = page.bubbles[0].id;
                    }
                }

                const hasJaText = data.bubbles?.some((b: any) => b.ja_text?.trim());
                if (hasJaText) {
                    this.isOcrProcessing = false;
                    await this.runTranslation();
                    return;
                }
            }
        } catch (error) {
            console.error("Manga OCR failed:", error);
            alert("Failed to run Manga OCR. Is your FastAPI server running?");
        } finally {
            this.isOcrProcessing = false;
        }
    }

    async runTranslation() {
        if (!this.workspaceId || !this.activePageId || !this.activePage) return;
        historyManager.recordState(this.activePageId);

        this.isTranslating = true;

        try {
            const data = await apiRunTranslation(this.workspaceId, this.activePageId);
            if (data.status === 'success') {
                const page = this.activePage;
                if (page) {
                    page.bubbles = data.bubbles;
                }
            }
        } catch (error) {
            console.error("Translation failed:", error);
            alert(`Translation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
            this.isTranslating = false;
        }
    }

    async saveBubbles() {
        if (!this.workspaceId || !this.activePageId || !this.activePage) return;
        try {
            this.activePage.detected = true;
            await apiSaveBubbles(this.workspaceId, this.activePageId, this.activePage.bubbles);
        } catch (e) {
            console.error("Failed to save bubble layout to server", e);
        }
    }

    async saveRedrawingStrokes() {
        if (!this.workspaceId || !this.activePageId || !this.activePage) return;
        try {
            await apiSaveRedrawingStrokes(this.workspaceId, this.activePageId, this.activePage.redrawingStrokes);
        } catch (e) {
            console.error("Failed to save redrawing strokes to server", e);
        }
    }

    async runInpainting(borderErosion: number = 2) {
        if (!this.workspaceId || !this.activePageId || !this.activePage) return;
        historyManager.recordState(this.activePageId);

        this.isProcessing = true;

        try {
            const data = await apiRunInpainting(this.workspaceId, this.activePageId, this.activePage.bubbles, borderErosion);
            if (data.status === 'success') {
                const page = this.activePage;
                if (page) {
                    page.inpaintedUrl = data.inpainted_url + "?t=" + Date.now();
                }
            }
        } catch (error) {
            console.error("Inpainting failed:", error);
            alert("Failed to run inpainting. Is your FastAPI server running?");
        } finally {
            this.isProcessing = false;
        }
    }

    initializeTypesetStyles() {
        const page = this.activePage;
        if (!page) return;

        for (const bubble of page.bubbles) {
            if (!bubble.typeset) {
                bubble.typeset = { ...DEFAULT_TYPESET_STYLE };
            }
        }
    }

    async saveTypesetting() {
        if (!this.workspaceId || !this.activePageId || !this.activePage) return;
        try {
            await apiSaveTypesetting(this.workspaceId, this.activePageId, this.activePage.bubbles);
        } catch (e) {
            console.error("Failed to save typesetting data to server", e);
        }
    }
}

export const editorState = new EditorState();
export * from './EditorTypes';