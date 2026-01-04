<script lang="ts">
    import { Upload, Plus } from '@lucide/svelte';
    import { Button } from '$lib';
    import { imageState, zoomState, layerStateManager } from '$lib';
    import { Open } from '$lib';
    import { onMount } from 'svelte';

    let sortedLayers = $derived([...layerStateManager.layerList].sort((a, b) => a.zIndex - b.zIndex));
    let hasImages = $derived(sortedLayers.some(l => l.imageID && imageState.images[l.imageID]));
    
    let scrollContainer: HTMLDivElement | undefined = $state();
    let containerWidth = $state(0);
    let containerHeight = $state(0);
    let isPanning = false;

    let canvasDimensions = $derived.by(() => {
        let maxWidth = 0;
        let maxHeight = 0;
        
        for (const layer of layerStateManager.layerList) {
            if (layer.imageID && imageState.images[layer.imageID]) {
                const img = imageState.images[layer.imageID];
                if (img.width > maxWidth) maxWidth = img.width;
                if (img.height > maxHeight) maxHeight = img.height;
            }
        }
        
        return { width: maxWidth, height: maxHeight };
    });

    let baseScale = $derived.by(() => {
        if (canvasDimensions.width === 0 || canvasDimensions.height === 0 || containerWidth === 0 || containerHeight === 0) return 1;
        
        const widthRatio = (containerWidth - 40) / canvasDimensions.width; 
        const heightRatio = (containerHeight - 40) / canvasDimensions.height;
        
        return Math.min(widthRatio, heightRatio);
    });

    let displayWidth = $derived(canvasDimensions.width * baseScale * (zoomState.zoomLevel / 100));
    let displayHeight = $derived(canvasDimensions.height * baseScale * (zoomState.zoomLevel / 100));

    function handleMouseDown(e: MouseEvent) {
        if (e.button === 2 || e.button === 1) { 
            isPanning = true;
            e.preventDefault();
        }
    }

    function handleMouseMove(e: MouseEvent) {
        if (!isPanning || !scrollContainer) return;
        scrollContainer.scrollLeft -= e.movementX;
        scrollContainer.scrollTop -= e.movementY;
    }

    function handleMouseUp() {
        isPanning = false;
    }

	function handleMouseWheel(e: WheelEvent) {
		if(!scrollContainer) return;
        if (e.ctrlKey) e.preventDefault();
        
		const zoomStep = 5
		if(e.deltaY < 0){
			zoomState.zoomIn(zoomStep)
		} else {
			zoomState.zoomOut(zoomStep)
		}
	}

    function handleContextMenu(e: MouseEvent) {
        e.preventDefault();
        return false;
    }
</script>

<svelte:window onmousemove={handleMouseMove} onmouseup={handleMouseUp} />

<div class="h-full w-full flex flex-col bg-secondary overflow-hidden">
    {#if hasImages}
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div 
            bind:this={scrollContainer}
            bind:clientWidth={containerWidth}
            bind:clientHeight={containerHeight}
            class="flex-1 w-full h-full overflow-auto flex cursor-grab active:cursor-grabbing relative" 
            onmousedown={handleMouseDown}
            oncontextmenu={handleContextMenu}
			onwheel={handleMouseWheel}
        >
            <div 
                class="m-auto relative bg-transparent transition-all duration-75 ease-out flex-shrink-0"
                style="width: {displayWidth}px; height: {displayHeight}px;"
            >
                {#each sortedLayers as layer (layer.id)}
                    {#if layer.visibility && layer.imageID && imageState.images[layer.imageID]}
                        <img 
                            src={imageState.images[layer.imageID].imageURL} 
                            alt={layer.name}
                            draggable="false"
                            class="absolute top-1/2 left-1/2 max-w-full max-h-full object-contain"
                            style="
                                transform: translate(-50%, -50%);
                                opacity: {layer.opacity / 100}; 
                                pointer-events: {layer.locked ? 'none' : 'auto'};
                                width: auto; 
                                height: auto;
                            "
                        />
                    {/if}
                {/each}
            </div>
        </div>
    {:else}
        <div class="h-full flex flex-col items-center justify-center gap-3 text-black">
            <div class="flex aspect-square w-32 items-center justify-center rounded-lg border-3 border-dashed border-gray-400 text-gray-400">
                <Upload size={48} />
            </div>
            <p class="text-center text-lg font-semibold">Import Manga Page</p>
            <p class="text-center text-base font-semibold text-slate-500">
                Upload a manga page to start translating
            </p>
            <div class="flex flex-row items-center justify-center gap-3">
                <Open buttonName={"Upload Image"} variant={"default"} icon={Upload}/>
                <Button icon={Plus} variant={'outline'}>Create New Project</Button>
            </div>
        </div>
    {/if}
</div>