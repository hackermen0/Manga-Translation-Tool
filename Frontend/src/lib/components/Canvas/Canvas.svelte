<script lang="ts">
    import { Upload, Plus } from '@lucide/svelte';
    import { Button } from '$lib';
    import { imageState, zoomState, layerStateManager } from '$lib';
    import { Open } from '$lib';

    let sortedLayers = $derived([...layerStateManager.layerList].sort((a, b) => a.zIndex - b.zIndex));
    let hasImages = $derived(sortedLayers.some(l => l.imageID && imageState.images[l.imageID]));

    let scrollContainer: HTMLDivElement | undefined = $state();
    let isPanning = false;

    function handleMouseDown(e: MouseEvent) {
        if (e.button === 2) { 
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

<div class="h-full w-full flex flex-col">
    {#if hasImages}
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div 
            bind:this={scrollContainer}
            class="flex-1 w-full overflow-auto bg-secondary flex items-center justify-center cursor-grab active:cursor-grabbing" 
            onmousedown={handleMouseDown}
            oncontextmenu={handleContextMenu}
			onwheel={handleMouseWheel}
        >
            <div 
                class="grid place-items-center transition-transform duration-200 ease-out origin-center select-none"
                style="transform: scale({zoomState.zoomLevel / 100});"
            >
                {#each sortedLayers as layer (layer.id)}
                    {#if layer.visibility && layer.imageID && imageState.images[layer.imageID]}
                        <img 
                            src={imageState.images[layer.imageID].imageURL} 
                            alt={layer.name}
                            draggable="false"
                            class="col-start-1 row-start-1"
                            style="opacity: {layer.opacity / 100}; pointer-events: {layer.locked ? 'none' : 'auto'};"
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