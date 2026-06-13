import { layerStateManager } from '$lib';

export interface Point {
    x: number;
    y: number;
}
export interface MangaBubble {
	id: number;
	points: Point[];
	ja_text: string;
	en_text: string;
}

export interface RedrawingStroke {
	points: Point[];
	brushSize: number;
	brushColor: string;
	type: 'eraser' | 'restore';
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

class EditorState {
	activeSession = $state('detection');

	workspaceId = $state<string | null>(null);
	activePageId = $state<string | null>(null);
	activeBubbleId = $state<number | null>(null);
	isProcessing = $state<boolean>(false);
	isOcrProcessing = $state<boolean>(false);
	isTranslating = $state<boolean>(false);
	pages = $state<MangaPage[]>([]);

	activeDetectionTool = $state<'edit' | 'drag' | 'create' | 'delete'>('edit');
	activeRedrawingTool = $state<'pan' | 'eraser' | 'restore'>('pan');
	brushSize = $state(20);
	brushColor = $state('#ffffff');

	setDetectionTool(tool: 'edit' | 'drag' | 'create' | 'delete') {
		this.activeDetectionTool = tool;
	}

	setRedrawingTool(tool: 'pan' | 'eraser' | 'restore') {
		this.activeRedrawingTool = tool;
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

	initWorkspace(workspaceData: { workspace_id: string; pages: any[] }) {
		this.workspaceId = workspaceData.workspace_id;
		
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
                await fetch(`http://127.0.0.1:8000/api/workspace/${this.workspaceId}/reorder`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ new_order: newOrderIds })
                });
            } catch (err) {
                console.error("Failed to save new page order to server:", err);
            }
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
				en_text: "Test bubble"
			}
		];
	}

	async detectBubbles() {
		if (!this.workspaceId || !this.activePageId) return;

		this.isProcessing = true;
		
		try {
			const response = await fetch(`http://127.0.0.1:8000/api/workspace/${this.workspaceId}/page/${this.activePageId}/detect`, {
				method: 'POST'
			});

			if (!response.ok) {
				throw new Error(`Server responded with ${response.status}`);
			}

			const data = await response.json();

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

	async runOcr() {
		if (!this.workspaceId || !this.activePageId) return;

		this.isOcrProcessing = true;
		
		try {
			const response = await fetch(`http://127.0.0.1:8000/api/workspace/${this.workspaceId}/page/${this.activePageId}/ocr`, {
				method: 'POST'
			});

			if (!response.ok) {
				throw new Error(`Server responded with ${response.status}`);
			}

			const data = await response.json();

			if (data.status === 'success') {
				const page = this.activePage;
				if (page) {
					page.bubbles = data.bubbles;
					if (page.bubbles.length > 0 && this.activeBubbleId === null) {
						this.activeBubbleId = page.bubbles[0].id;
					}
				}

				// Automatically run translation after successful OCR
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

		this.isTranslating = true;

		try {
			const response = await fetch(`http://127.0.0.1:8000/api/workspace/${this.workspaceId}/page/${this.activePageId}/translate`, {
				method: 'POST'
			});

			if (!response.ok) {
				const errData = await response.json().catch(() => ({}));
				throw new Error(errData.detail || `Server responded with ${response.status}`);
			}

			const data = await response.json();

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
			await fetch(`http://127.0.0.1:8000/api/workspace/${this.workspaceId}/page/${this.activePageId}/bubbles`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ bubbles: this.activePage.bubbles })
			});
		} catch (e) {
			console.error("Failed to save bubble layout to server", e);
		}
	}

	async saveRedrawingStrokes() {
		if (!this.workspaceId || !this.activePageId || !this.activePage) return;
		try {
			await fetch(`http://127.0.0.1:8000/api/workspace/${this.workspaceId}/page/${this.activePageId}/strokes`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ strokes: this.activePage.redrawingStrokes })
			});
		} catch (e) {
			console.error("Failed to save redrawing strokes to server", e);
		}
	}

	async runInpainting(borderErosion: number = 2) {
		if (!this.workspaceId || !this.activePageId || !this.activePage) return;

		this.isProcessing = true;
		
		try {
			const response = await fetch(`http://127.0.0.1:8000/api/workspace/${this.workspaceId}/page/${this.activePageId}/inpaint`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					bubbles: this.activePage.bubbles,
					border_erosion: borderErosion
				})
			});

			if (!response.ok) {
				throw new Error(`Server responded with ${response.status}`);
			}

			const data = await response.json();

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
}

export const editorState = new EditorState();