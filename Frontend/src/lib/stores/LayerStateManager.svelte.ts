export type LayerType = 'image' | 'drawing';

interface LayerState {
    id: string;
    name: string;
    type: LayerType;
    visibility: boolean;
    locked: boolean;
    opacity: number;
    zIndex: number;
    imageID?: string;
}

class LayerStateManager {
    layers = $state<Record<string, LayerState>>({});
    selectedLayerId = $state<string | null>(null);

    // In-memory cache to hold inactive pages without triggering Svelte reactivity overhead
    private pageCache: Record<string, { layers: Record<string, LayerState>, selectedLayerId: string | null }> = {};

    layerList = $derived(Object.values(this.layers).sort((a, b) => b.zIndex - a.zIndex));

    // --- NEW: Context Swapping Methods ---
    
    saveCurrentPage(pageId: string) {
        this.pageCache[pageId] = {
            // $state.snapshot strips away the Svelte proxies so we can safely store raw data
            layers: $state.snapshot(this.layers),
            selectedLayerId: this.selectedLayerId
        };
    }

    loadPage(pageId: string) {
        if (this.pageCache[pageId]) {
            // Re-assigning to this.layers automatically makes the cached data reactive again
            this.layers = this.pageCache[pageId].layers;
            this.selectedLayerId = this.pageCache[pageId].selectedLayerId;
        } else {
            // Brand new page
            this.layers = {};
            this.selectedLayerId = null;
        }
    }

    deletePage(pageId: string) {
        if (this.pageCache[pageId]) {
            delete this.pageCache[pageId];
        }
    }

    initializeLayer(id: string, name: string, type: LayerType, initialState?: Partial<LayerState>) {
        if (!this.layers[id]) {
            this.layers[id] = {
                id, name, type, visibility: true, locked: false, opacity: 100, zIndex: 0, ...initialState
            };
        }
    }
    
    addLayer(name: string, type: LayerType, initialState?: Partial<Omit<LayerState, 'id'>>) {
        const id = crypto.randomUUID();
        const maxZ = Math.max(0, ...Object.values(this.layers).map(l => l.zIndex ?? 0));
        
        this.initializeLayer(id, name, type, { ...initialState, id, zIndex: maxZ + 1 });
        this.selectLayer(id);
        
        return id;
    }

    deleteLayer(id: string){
        if (this.layers[id]){
            const {[id]: _, ...rest } = this.layers;
            this.layers = rest;
            if (this.selectedLayerId === id) this.selectedLayerId = null;
        }
    }
    
    selectLayer(id: string) {
        if (this.layers[id]) {
            this.selectedLayerId = id;
        }
    }

    getLayerState(id: string): LayerState {
        return this.layers[id] || { id: "undefined", name: "", type: 'drawing', visibility: true, locked: false, opacity: 100, zIndex: 0};
    }

    hasLayer(id: string): boolean {
        return id in this.layers;
    }

    toggleVisibility(id: string) {
        if (this.layers[id]) this.layers[id].visibility = !this.layers[id].visibility;
    }

    toggleLocked(id: string) {
        if (this.layers[id]) this.layers[id].locked = !this.layers[id].locked;
    }

    setOpacity(id: string, opacity: number) {
        if (this.layers[id]) {
            this.layers[id].opacity = Math.min(100, Math.max(0, opacity));
        }
    }

    setName(id: string, name: string){
        if (this.layers[id]) this.layers[id].name = name;
    }

    setLayerImage(id: string, imageID: string) {
        if (this.layers[id]) this.layers[id].imageID = imageID;
    }

    reorderLayers(newOrder: string[]) {
        newOrder.forEach((id, index) => {
            if (this.layers[id]) this.layers[id].zIndex = newOrder.length - index; 
        });
    }

    getVisibleLayers() {
        return Object.values(this.layers).filter((state) => state.visibility);
    }

    isLayerInteractable(id: string) {
        const state = this.layers[id];
        return state ? state.visibility && !state.locked : false;
    }

    reset() {
        this.layers = {};
        this.selectedLayerId = null;
        this.pageCache = {};
    }
}

export const layerStateManager = new LayerStateManager();