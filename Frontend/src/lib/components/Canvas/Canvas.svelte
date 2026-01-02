<script lang="ts">
    import { Upload, Plus, ChevronRight, ChevronLeft } from '@lucide/svelte';
    import { Button } from '$lib';
    import { imageState, zoomState } from '$lib';
    import { Open } from '$lib';

    let images = $derived(imageState.layerList);
    let imageIndex = $derived(imageState.imageIndex);
    let imagesLength = $derived(imageState.layerList.length);

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
    {#if images.length > 0}
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div 
            bind:this={scrollContainer}
            class="flex-1 w-full overflow-auto bg-secondary flex items-center justify-center cursor-grab active:cursor-grabbing" 
            onmousedown={handleMouseDown}
            oncontextmenu={handleContextMenu}
			onwheel={handleMouseWheel}
        >
            <img 
                src={images[imageIndex].imageURL} 
                alt={images[imageIndex].name}
                class="transition-transform duration-200 ease-out origin-center select-none"
                draggable="false"
                style="transform: scale({zoomState.zoomLevel / 100});"
            />
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