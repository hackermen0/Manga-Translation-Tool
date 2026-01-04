interface LayerState {
	id: string;
    name: string;
	visibility: boolean;
	locked: boolean;
	opacity: number;
    zIndex: number;
}

class LayerStateManager {

    layers = $state<Record<string, LayerState>>({});

    layerList = $derived(Object.values(this.layers));

    initializeLayer(id: string, name: string, initialState?: Partial<LayerState>) {
        if (!this.layers[id]) {
            this.layers[id] = {
                id,
                name,
                visibility: true,
                locked: false,
                opacity: 100,
                zIndex: 0,
                ...initialState
            };
        }
    }
    
    addLayer(name: string, initialState?: Partial<Omit<LayerState, 'id'>>) {
        const id = crypto.randomUUID();
        const maxZ = Math.max(0, ...Object.values(this.layers).map(l => l.zIndex ?? 0));
        this.initializeLayer(id, name, { ...initialState, id, zIndex: maxZ + 1 });
        return id;
    }

    deleteLayer(id: string){
        if (this.layers[id]){
            const {[id]: _, ...rest } = this.layers;
            this.layers = rest;
        }
    }
    
    getLayerState(id: string): LayerState {
        // If layer doesn't exist, return a default (but don't mutate state)
        return this.layers[id] || { name: "", visibility: true, locked: false, opacity: 100};
    }

    hasLayer(id: string): boolean {
        return id in this.layers;
    }

    toggleVisibility(id: string) {
        if (this.layers[id]) {
            this.layers[id].visibility = !this.layers[id].visibility;
            console.log(id, this.layers[id].name, this.layers[id].visibility)
        }
    }

    toggleLocked(id: string) {
        if (this.layers[id]) {
            this.layers[id].locked = !this.layers[id].locked;
            console.log(id, this.layers[id].name, this.layers[id].locked)
        }
    }

    setOpacity(id: string, opacity: number) {
        if (this.layers[id]) {
            const clamped = Math.min(100, Math.max(0, opacity));
            this.layers[id].opacity = clamped;
            console.log(id, this.layers[id].name, this.layers[id].opacity)
        }
    }

    setName(id: string, name: string){
        if (this.layers[id]) {
            this.layers[id].name = name;
            console.log(id, name)
        }
    }

    reorderLayers(newOrder: string[]) {
        newOrder.forEach((id, index) => {
            if (this.layers[id]) {
                this.layers[id].zIndex = newOrder.length - index; // higher index = top
            }
        });
        console.log(this.layers)
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