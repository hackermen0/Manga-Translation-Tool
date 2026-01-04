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

    layerList = $derived(Object.values(this.layers).sort((a, b) => b.zIndex - a.zIndex));

    initializeLayer(id: string, name: string, type: LayerType, initialState?: Partial<LayerState>) {
        if (!this.layers[id]) {
            this.layers[id] = {
                id,
                name,
                type,
                visibility: true,
                locked: false,
                opacity: 100,
                zIndex: 0,
                ...initialState
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
            
            if (this.selectedLayerId === id) {
                this.selectedLayerId = null;
            }
        }
    }
    
    selectLayer(id: string) {
        if (this.layers[id]) {
            this.selectedLayerId = id;
            console.log(`Layer Selected: ${this.layers[id].name} (${this.layers[id].type})`);
        }
    }

    getLayerState(id: string): LayerState {
        return this.layers[id] || { id: "undefined", name: "", type: 'drawing', visibility: true, locked: false, opacity: 100, zIndex: 0};
    }

    hasLayer(id: string): boolean {
        return id in this.layers;
    }

    toggleVisibility(id: string) {
        if (this.layers[id]) {
            this.layers[id].visibility = !this.layers[id].visibility;
        }
    }

    toggleLocked(id: string) {
        if (this.layers[id]) {
            this.layers[id].locked = !this.layers[id].locked;
        }
    }

    setOpacity(id: string, opacity: number) {
        if (this.layers[id]) {
            const clamped = Math.min(100, Math.max(0, opacity));
            this.layers[id].opacity = clamped;
        }
    }

    setName(id: string, name: string){
        if (this.layers[id]) {
            this.layers[id].name = name;
        }
    }

    setLayerImage(id: string, imageID: string) {
        if (this.layers[id]) {
            this.layers[id].imageID = imageID;
        }
    }

    reorderLayers(newOrder: string[]) {
        newOrder.forEach((id, index) => {
            if (this.layers[id]) {
                // Assuming newOrder is top-to-bottom, higher zIndex is top
                this.layers[id].zIndex = newOrder.length - index; 
            }
        });
    }

    getVisibleLayers() {
        return Object.values(this.layers).filter((state) => state.visibility);
    }

    isLayerInteractable(id: string) {
        const state = this.layers[id];
        return state ? state.visibility && !state.locked : false;
    }
}

export const layerStateManager = new LayerStateManager();