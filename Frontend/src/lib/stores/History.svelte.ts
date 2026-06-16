import { editorState } from './Editor.svelte';
import type { MangaBubble, RedrawingStroke } from './EditorTypes';

export interface PageSnapshot {
    pageId: string;
    bubbles: MangaBubble[];
    redrawingStrokes: RedrawingStroke[];
}

class HistoryManager {
    undoStack = $state<PageSnapshot[]>([]);
    redoStack = $state<PageSnapshot[]>([]);

    get canUndo() {
        return this.undoStack.length > 0;
    }

    get canRedo() {
        return this.redoStack.length > 0;
    }

    captureSnapshot(pageId: string): PageSnapshot | null {
        const page = editorState.pages.find(p => p.pageId === pageId);
        if (!page) return null;

        return {
            pageId,
            bubbles: JSON.parse(JSON.stringify(page.bubbles)),
            redrawingStrokes: JSON.parse(JSON.stringify(page.redrawingStrokes))
        };
    }

    pushSnapshot(snapshot: PageSnapshot) {
        if (this.undoStack.length > 0) {
            const top = this.undoStack[this.undoStack.length - 1];
            if (
                top.pageId === snapshot.pageId &&
                JSON.stringify(top.bubbles) === JSON.stringify(snapshot.bubbles) &&
                JSON.stringify(top.redrawingStrokes) === JSON.stringify(snapshot.redrawingStrokes)
            ) {
                return;
            }
        }
        this.undoStack.push(snapshot);
        this.redoStack = [];
    }

    recordState(pageId: string) {
        const snapshot = this.captureSnapshot(pageId);
        if (snapshot) {
            this.pushSnapshot(snapshot);
        }
    }

    recordSnapshotChange(pageId: string, originalSnapshot: PageSnapshot) {
        const currentSnapshot = this.captureSnapshot(pageId);
        if (!currentSnapshot) return;

        if (
            JSON.stringify(originalSnapshot.bubbles) !== JSON.stringify(currentSnapshot.bubbles) ||
            JSON.stringify(originalSnapshot.redrawingStrokes) !== JSON.stringify(currentSnapshot.redrawingStrokes)
        ) {
            this.pushSnapshot(originalSnapshot);
        }
    }

    undo() {
        if (!this.canUndo) return;

        const snapshot = this.undoStack.pop()!;
        const page = editorState.pages.find(p => p.pageId === snapshot.pageId);
        if (!page) return;

        const currentSnapshot = this.captureSnapshot(snapshot.pageId);
        if (currentSnapshot) {
            this.redoStack.push(currentSnapshot);
        }

        this.applySnapshot(page, snapshot);
    }

    redo() {
        if (!this.canRedo) return;

        const snapshot = this.redoStack.pop()!;
        const page = editorState.pages.find(p => p.pageId === snapshot.pageId);
        if (!page) return;

        const currentSnapshot = this.captureSnapshot(snapshot.pageId);
        if (currentSnapshot) {
            this.undoStack.push(currentSnapshot);
        }

        this.applySnapshot(page, snapshot);
    }

    private async applySnapshot(page: any, snapshot: PageSnapshot) {
        if (editorState.activePageId !== snapshot.pageId) {
            editorState.setActivePage(snapshot.pageId);
        }

        page.bubbles = snapshot.bubbles;
        page.redrawingStrokes = snapshot.redrawingStrokes;

        try {
            await Promise.all([
                editorState.saveBubbles(),
                editorState.saveRedrawingStrokes(),
                editorState.saveTypesetting()
            ]);
        } catch (e) {
            console.error("Failed to save undone/redone state to server:", e);
        }
    }

    clear() {
        this.undoStack = [];
        this.redoStack = [];
    }
}

export const historyManager = new HistoryManager();
