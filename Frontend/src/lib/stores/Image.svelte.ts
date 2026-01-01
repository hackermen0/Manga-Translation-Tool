interface ImageItem {
    id: string;
    name: string;
    type: string;
    size: number;
    lastModified: number;
    imageURL: string;
}


class ImageState {
    images = $state<Record<string, ImageItem>>({})

    layerList = $derived(Object.values(this.images));

    initializeImage(id: string, initialState? : Partial<ImageItem>){
        if(!this.images[id]){
            this.images[id] = {
                id,
                name: initialState?.name || "undefined",
                type: initialState?.name || "undefined",
                size: initialState?.size || 0,
                lastModified: initialState?.lastModified || Date.now(),
                imageURL: initialState?.imageURL || "undefined",
                ...initialState

            };
        }
    }

    addImage(initialState? : Partial<Omit<ImageItem, "id">>){
        const id = crypto.randomUUID();
        this.initializeImage(id, initialState);
        return id;

    }


}


export const imageState = new ImageState();