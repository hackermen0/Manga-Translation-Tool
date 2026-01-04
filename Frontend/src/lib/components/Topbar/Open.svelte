<script lang="ts" module>

    import type { Component } from 'svelte';
    import type { IconProps } from '@lucide/svelte';

    interface Props{
		buttonName?: string;
        variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
        size?: 'default' | 'sm' | 'lg' | 'icon';
        icon?: Component<IconProps, {}, ''>;
	}

</script>

<script lang="ts">


    import { Button } from '$lib';
    import { imageState, layerStateManager } from '$lib';


	let fileInput: HTMLElement;
    let {buttonName, variant, size, icon}: Props = $props();

	let handleFileSelection = (event: Event) => {
		const target = event.target as HTMLInputElement;
        const file = target.files?.[0];

        if(file){
            const objectURL = URL.createObjectURL(file);
            
            const newImageID = imageState.addImage({
                name: file.name,
                type: file.type,
                size: file.size,
                lastModified: file.lastModified,
                imageURL: objectURL
            });

            const originalLayer = layerStateManager.layerList.find(l => l.name === 'Original Image');
            if (originalLayer) {
                console.log(originalLayer.imageID)
                if(!originalLayer.imageID){
                    layerStateManager.setLayerImage(originalLayer.id, newImageID);
                    layerStateManager.selectLayer(originalLayer.id)
                    return;
                }
            } 
            
            const newImageLayerID = layerStateManager.addLayer(file.name, "image");
            layerStateManager.setLayerImage(newImageLayerID, newImageID);
            layerStateManager.selectLayer(newImageLayerID);

            target.value = "";
        }
	}

</script>

<input
    bind:this={fileInput}
    type="file"
    id="manga_image"
    accept="image/png, image/jpeg"
    class="hidden"
    onchange="{handleFileSelection}"
/>

<Button variant={variant} size={size} icon={icon} onclick={() => fileInput.click()}>
    {buttonName}
</Button>