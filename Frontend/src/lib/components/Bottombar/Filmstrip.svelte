<script lang="ts">
    import { editorState } from '$lib/stores/Editor.svelte';
    
    const BACKEND_URL = "http://127.0.0.1:8000";
</script>

<div class="flex overflow-x-auto bg-gray-100 p-4 gap-4 border-t border-gray-300 w-full h-48 items-center shadow-inner select-none">
    
    {#if editorState.pages.length === 0}
        <div class="flex w-full h-full items-center justify-center text-gray-500 text-sm italic font-medium">
            No pages loaded. Upload a chapter to begin.
        </div>
    {:else}
        {#each editorState.pages as page}
            <button
                class="relative flex flex-col items-center flex-shrink-0 transition-all duration-200 focus:outline-none 
                {editorState.activePageId === page.pageId 
                    ? 'ring-4 ring-blue-500 rounded-md scale-105 opacity-100 z-10 shadow-lg' 
                    : 'ring-1 ring-gray-300 rounded-md opacity-60 hover:opacity-100 hover:scale-105'}"
                onclick={() => editorState.setActivePage(page.pageId)}
                aria-label={`Go to ${page.pageId}`}
            >
                <img
                    src={`${BACKEND_URL}${page.inpaintedUrl || page.originalUrl}`}
                    alt={page.originalFilename}
                    class="h-32 w-auto object-cover rounded-sm bg-white"
                    loading="lazy"
                    draggable="false"
                />
                
                <div class="absolute bottom-0 w-full bg-black bg-opacity-70 text-white text-xs py-1 text-center font-bold rounded-b-sm tracking-wider">
                    {page.pageId.replace('page_', '')}
                </div>
            </button>
        {/each}
    {/if}
</div>

<style>
    /* Custom scrollbar styling to make the horizontal scroll smooth and slim */
    div::-webkit-scrollbar {
        height: 8px;
    }
    div::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    div::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
    }
    div::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
</style>