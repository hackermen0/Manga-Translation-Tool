<script lang="ts" module>

    interface Props {
        name: string,
        layerID: string,
        edit: boolean
    }
</script>


<script lang="ts">
    import { Eye, EyeOff, Lock, LockOpen, Trash2, GripVertical } from "@lucide/svelte";
    import { Button } from "$lib";
    import { layerStateManager } from "$lib";
    import { useSortable } from "@dnd-kit-svelte/sortable";
    import {CSS, styleObjectToString} from '@dnd-kit-svelte/utilities';
    import type { UniqueIdentifier } from "@dnd-kit-svelte/core";

    let hasFocused = false;

    const handleFocusOpacity = () => {
        hasFocused = true;
    }

    const handleBlurOpacity = () => {
        if (hasFocused){
            onCompleteFocus(opacity);
            hasFocused = false;
        }
    }
    const handleFocusName = () => {
        hasFocused = true;
    }

    const handleBlurName = () => {
        if (hasFocused){
            onCompleteName(name);
            hasFocused = false;
        }
    }

    const onCompleteFocus = (value: number) => {
        value = Math.min(100, Math.max(0, +value));
        opacity = value;
        layerStateManager.setOpacity(layerID, value)
    }

    const onCompleteName = (value: string) => {
        layerStateManager.setName(layerID, value)
    }

    const handleDelete = (id: string) => {
        layerStateManager.deleteLayer(id)
    }

    // const handleLayerUp = (id: string) => {
    //     layerStateManager.bringToFront(id)
    // }

    // const handleLayerDown = (id: string) => {
    //     layerStateManager.sendToBack(id)
    // }

    let { name, layerID, edit = $bindable(false) }: Props = $props();

    let layer = $derived(layerStateManager.getLayerState(layerID));
    let isVisible = $derived(layer.visibility);
    let isLocked = $derived(layer.locked);
    let opacity = $derived(layer.opacity);

	const { attributes, listeners, node, transform, transition, isDragging, activatorNode } = useSortable({
		id: layerID as UniqueIdentifier
	});

	const style = $derived(
		styleObjectToString({
			transform: CSS.Transform.toString(transform.current),
			transition: transition.current,
			zIndex: isDragging.current ? 1 : undefined
		})
	);

</script>

<div bind:this={node.current} {style} class="relative">
    <div class={["w-full border-1 border-primary-border flex flex-row justify-between p-4 rounded-lg text-sm bg-white", {invisible: isDragging.current}]}>
        <div class={["flex flex-row gap-3"]}>
            <div class="flex flex-row gap-2 items-center justify-center">
                {#if !edit}        
                    <button onclick={() => layerStateManager.toggleVisibility(layerID)} class="cursor-pointer">
                        {#if isVisible}
                            <Eye class="w-6 h-6 text-gray-500 hover:text-black"/>
                        {:else}
                            <EyeOff class="w-6 h-6 text-gray-500 hover:text-black"/>
                        {/if}
                    </button>
                    <button onclick={() => layerStateManager.toggleLocked(layerID)} class="cursor-pointer">
                        {#if isLocked}
                            <Lock class="w-5 h-5 text-gray-500 hover:text-black mb-[0.1rem]"/>
                        {:else}
                            <LockOpen class="w-5 h-5 text-gray-500 hover:text-black mb-[0.1rem]"/>
                        {/if}
                    </button>
                {:else}
                        <div
                            class="cursor-grab"
                            bind:this={activatorNode.current}
                            {...attributes.current}
                            {...listeners.current}
                        >
                        <GripVertical />
                    </div>
                {/if}
            </div>
            {#if !edit}         
                <button aria-label={name}>
                    <input
                        type="text"
                        class="w-auto px-1"
                        bind:value={name}
                        onfocus={handleFocusName}
                        onblur={handleBlurName} />
                </button>
            {:else}
                <p class="px-1 items-center justify-self-center my-auto">{name}</p>
            {/if}
        </div>
        <div class="flex flex-row">
            {#if !edit}
                <div class="border border-primary-border rounded-lg">
                    <input type="number" min="0" max="100" bind:value={opacity} onfocus={handleFocusOpacity} onblur={handleBlurOpacity} class="text-center p-0"/>
                </div>
                <span class="my-auto text-gray-500">%</span>
            {:else}
                <Button variant={"ghost"} onclick={() => handleDelete(layerID)}>
                    <Trash2 class="w-4 h-4"/>
                </Button>
            {/if}
        </div>
    </div>
    {#if isDragging.current}
        <!-- Drag placeholder: matches original size -->
        <div class="absolute inset-0 flex items-center justify-center z-10 pointer-events-none">
            <div class="w-full h-full bg-accent/10 rounded-lg border-2 border-accent border-dashed flex items-center justify-center">
                <span class="text-black">Moving: {name}</span>
            </div>
        </div>
    {/if}
</div>
