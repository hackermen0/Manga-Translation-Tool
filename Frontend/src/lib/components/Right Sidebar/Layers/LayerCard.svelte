<script lang="ts" module>
    import type { LayerType } from "$lib/stores/LayerStateManager.svelte";

    interface Props {
        name: string,
        layerID: string,
        type: LayerType,
        isSelected: boolean,
        edit: boolean
    }
</script>

<script lang="ts">
    import { Eye, EyeOff, Lock, LockOpen, Trash2, GripVertical, Image as ImageIcon, PenTool } from "@lucide/svelte";
    import { Button } from "$lib";
    import { layerStateManager } from "$lib";
    import { useSortable } from "@dnd-kit-svelte/sortable";
    import { CSS, styleObjectToString } from '@dnd-kit-svelte/utilities';
    import type { UniqueIdentifier } from "@dnd-kit-svelte/core";

    let { name = $bindable(), layerID, type, isSelected, edit = $bindable(false) }: Props = $props();

    const handleName = (event: Event) => {
        const target = event.target as HTMLInputElement;
        const value = target.value || "";

        name = value;

        layerStateManager.setName(layerID, value);
    }

    const handleOpacity = (event: Event) => {
        const target = event.target as HTMLInputElement;
		const value = parseInt(target.value) || 0;

        opacity = value;

        layerStateManager.setOpacity(layerID, value)
    }

    const handleDelete = (id: string) => {
        layerStateManager.deleteLayer(id)
    }
    
    const handleSelect = () => {
        layerStateManager.selectLayer(layerID);
    }

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

<div 
    bind:this={node.current} 
    {style} 
    class="relative group"
>
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <div 
        onclick={handleSelect}
        class={[
            "w-full border-l-4 flex flex-row justify-between p-3 rounded-r-lg shadow-sm text-sm transition-all cursor-pointer",
            isSelected ? "bg-accent/10 border-accent ring-1 ring-accent/50" : "bg-white hover:bg-gray-50 border-1 border-primary-border",
            {invisible: isDragging.current}
        ]}
    >
        <div class="flex flex-row gap-3 items-center">
            <div class="text-gray-400" title={type === 'image' ? "Image Layer" : "Drawing Layer"}>
                 {#if type === 'image'}
                    <ImageIcon class="w-4 h-4" />
                 {:else}
                    <PenTool class="w-4 h-4" />
                 {/if}
             </div>

            <div class="flex flex-row gap-1 items-center justify-center">
                {#if !edit}        
                    <button onclick={(e) => { e.stopPropagation(); layerStateManager.toggleVisibility(layerID); }} class="cursor-pointer p-1 rounded hover:bg-gray-200">
                        {#if isVisible}
                            <Eye class="w-4 h-4 text-gray-500 hover:text-black"/>
                        {:else}
                            <EyeOff class="w-4 h-4 text-gray-400 hover:text-black"/>
                        {/if}
                    </button>
                    <button onclick={(e) => { e.stopPropagation(); layerStateManager.toggleLocked(layerID); }} class="cursor-pointer p-1 rounded hover:bg-gray-200">
                        {#if isLocked}
                            <Lock class="w-4 h-4 text-gray-500 hover:text-black"/>
                        {:else}
                            <LockOpen class="w-4 h-4 text-gray-300 hover:text-black"/>
                        {/if}
                    </button>
                {:else}
                    <div
                        class="cursor-grab p-1 hover:bg-gray-100 rounded"
                        bind:this={activatorNode.current}
                        {...attributes.current}
                        {...listeners.current}
                    >
                        <GripVertical class="w-4 h-4 text-gray-400"/>
                    </div>
                {/if}
            </div>

            {#if !edit}  
                <div class="flex-grow">
                     <input
                        type="text"
                        class="w-full bg-transparent border-b border-transparent hover:border-gray-300 focus:border-accent focus:outline-none px-1 text-gray-700 font-medium truncate"
                        bind:value={name} 
                        oninput={handleName}
                        onclick={(e) => e.stopPropagation()} 
                    />
                </div>
            {:else}
                 <p class="px-1 text-gray-600 font-medium">{name}</p>
            {/if}
        </div>

        <div class="flex flex-row items-center gap-2">
            {#if !edit}
                <div class="flex items-center gap-1 bg-gray-50 rounded px-1 border border-gray-200">
                    <input 
                        type="number" 
                        min="0" 
                        max="100" 
                        bind:value={opacity} 
                        oninput={handleOpacity}
                        onclick={(e) => e.stopPropagation()}
                        class="w-8 text-right bg-transparent text-[0.6rem] focus:outline-none"
                    />
                    <span class="text-xs text-gray-400">%</span>
                </div>
            {:else}
                <Button variant={"ghost"} size={"icon"} class="h-8 w-8 text-red-500 hover:bg-red-50 hover:text-red-600" onclick={(e: Event) => { e.stopPropagation(); handleDelete(layerID); }}>
                    <Trash2 class="w-4 h-4"/>
                </Button>
            {/if}
        </div>
    </div>

    {#if isDragging.current}
        <div class="absolute inset-0 z-10 pointer-events-none">
            <div class="w-full h-full bg-accent/5 rounded-lg border-2 border-accent border-dashed flex items-center justify-center backdrop-blur-[1px]">
                 <span class="text-accent font-semibold text-sm bg-white/80 px-2 py-1 rounded">Moving {name}</span>
            </div>
        </div>
    {/if}
</div>