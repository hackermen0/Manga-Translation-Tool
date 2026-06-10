<script lang="ts">
    import { useSortable } from "@dnd-kit-svelte/sortable";
    import { CSS, styleObjectToString } from '@dnd-kit-svelte/utilities';
    import type { UniqueIdentifier } from "@dnd-kit-svelte/core";
    import type { MangaPage } from '$lib/stores/Editor.svelte';

    let { page, isActivePage, onclick } = $props<{ 
        page: MangaPage, 
        isActivePage: boolean, 
        onclick: () => void 
    }>();
    
    const BACKEND_URL = "http://127.0.0.1:8000";

    const { attributes, listeners, node, transform, transition, isDragging, activatorNode } = useSortable({
        id: page.pageId as UniqueIdentifier
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
    class="flex flex-col items-center flex-shrink-0 w-[85%] mx-auto"
>
    <button
        bind:this={activatorNode.current}
        {...attributes.current}
        {...listeners.current}
        class="flex flex-col items-center flex-shrink-0 transition-all duration-200 focus:outline-none cursor-grab active:cursor-grabbing w-full
        {isActivePage ? 'ring-4 ring-accent rounded-md scale-105 opacity-100 shadow-lg z-10' : 'ring-1 ring-gray-300 rounded-md opacity-60 hover:opacity-100 hover:scale-105'} 
        {isDragging.current ? 'invisible' : ''}"
        {onclick}
    >
        <img
            src={`${BACKEND_URL}${page.inpaintedUrl || page.originalUrl}`}
            alt={page.originalFilename}
            class="w-full h-auto object-cover rounded-sm bg-white pointer-events-none"
            draggable="false"
        />
        <div class="bottom-0 w-full text-gray-600 text-xs py-1 text-center font-bold rounded-b-sm tracking-wider pointer-events-none">
            {page.originalFilename}
        </div>
    </button>
</div>