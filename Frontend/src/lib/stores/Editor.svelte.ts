import { layerStateManager } from '$lib';

export interface MangaBubble {
	id: number;
	bbox: { x1: number; y1: number; x2: number; y2: number };
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
	activeSession = $state('translation');

	workspaceId = $state<string | null>(null);
	activePageId = $state<string | null>(null);
	isProcessing = $state<boolean>(false);
	pages = $state<MangaPage[]>([]);

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
				bbox: { x1: 100, y1: 150, x2: 300, y2: 400 },
				ja_text: "テスト",
				en_text: "Test bubble"
			},
			{
				id: 2,
				bbox: { x1: 450, y1: 200, x2: 700, y2: 350 },
				ja_text: "ダミー",
				en_text: "Dummy text"
			}
		];
	}
}

export const editorState = new EditorState();