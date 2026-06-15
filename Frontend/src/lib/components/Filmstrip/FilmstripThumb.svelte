<script lang="ts">
    import { useSortable } from "@dnd-kit-svelte/sortable";
    import { CSS, styleObjectToString } from '@dnd-kit-svelte/utilities';
    import type { UniqueIdentifier } from "@dnd-kit-svelte/core";
    import type { MangaPage } from '$lib/stores/Editor.svelte';
    import { editorState } from '$lib/stores/Editor.svelte';

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
    class="relative flex flex-col items-center flex-shrink-0 w-[85%] mx-auto group"
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
            src={`${BACKEND_URL}${editorState.activeSession === 'redrawing' && page.inpaintedUrl ? page.inpaintedUrl : page.originalUrl}`}
            alt={page.originalFilename}
            class="w-full h-auto object-cover rounded-sm bg-white pointer-events-none"
            draggable="false"
        />
        <div class="bottom-0 w-full text-gray-600 text-xs py-1 text-center font-bold rounded-b-sm tracking-wider pointer-events-none">
            {page.originalFilename}
        </div>
    </button>

    {#if !isDragging.current}
    <button
        type="button"
        class="absolute top-1.5 right-1.5 z-20 p-1 rounded-full bg-red-600 hover:bg-red-700 text-white shadow-md opacity-0 group-hover:opacity-100 transition-opacity duration-150 hover:scale-110 cursor-pointer"
        onclick={(e) => {
            e.stopPropagation();
            if (confirm("Are you sure you want to delete this page? This cannot be undone.")) {
                editorState.deletePage(page.pageId);
            }
        }}
        title="Delete page"
        aria-label="Delete page"
    >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
    </button>
    {/if}
</div>