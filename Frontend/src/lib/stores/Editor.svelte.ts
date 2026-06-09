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
		
		this.pages = workspaceData.pages.map((rawPage: any) => ({
			pageId: rawPage.page_id,
			originalFilename: rawPage.original_filename,
			originalUrl: rawPage.original_url,
			inpaintedUrl: rawPage.inpainted_url,
			bubbles: rawPage.bubbles || []
		}));
		
		if (this.pages.length > 0) {
			this.activePageId = this.pages[0].pageId;
		}

		console.log("Normalized Frontend State Workspace Pages:", this.pages);
	}

	setActivePage(pageId: string) {
		this.activePageId = pageId;
	}
}

export const editorState = new EditorState();