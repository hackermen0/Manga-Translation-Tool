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

export interface MangaPage {
	pageId: string;
	originalFilename: string;
	originalUrl: string;
	inpaintedUrl: string | null;
	bubbles: MangaBubble[];
}

class EditorState {
	activeSession = $state('detection');

	workspaceId = $state<string | null>(null);
	activePageId = $state<string | null>(null);
	isProcessing = $state<boolean>(false);
	pages = $state<MangaPage[]>([]);

	activeDetectionTool = $state<'edit' | 'drag' | 'create' | 'delete'>('edit');

	setDetectionTool(tool: 'edit' | 'drag' | 'create' | 'delete') {
		this.activeDetectionTool = tool;
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
				}
			}
		} catch (error) {
			console.error("Speech bubble detection failed:", error);
			alert("Failed to run AI detection. Is your FastAPI server running?");
		} finally {
			this.isProcessing = false;
		}
	}

	async saveBubbles() {
		if (!this.workspaceId || !this.activePageId || !this.activePage) return;
		try {
			await fetch(`http://127.0.0.1:8000/api/workspace/${this.workspaceId}/page/${this.activePageId}/bubbles`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ bubbles: this.activePage.bubbles })
			});
		} catch (e) {
			console.error("Failed to save bubble layout to server", e);
    }
	}
}

export const editorState = new EditorState();