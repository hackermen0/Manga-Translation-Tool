<script lang="ts">
    import { PenTool, Move, MousePointer2, Trash2 } from '@lucide/svelte';
    import { editorState } from '$lib/stores/Editor.svelte';
</script>

{#if editorState.activeSession === 'detection'}
    <div class="absolute bottom-6 left-1/2 -translate-x-1/2 bg-white px-3 py-2 rounded-xl shadow-2xl border border-gray-200 flex flex-row gap-2 z-50 transition-all">
        
        <button 
            onclick={() => editorState.setDetectionTool('edit')}
            class="p-2 rounded-lg transition-colors {editorState.activeDetectionTool === 'edit' ? 'bg-accent/15 text-accent' : 'text-gray-500 hover:bg-gray-100'}"
            title="Edit Points"
        >
            <MousePointer2 class="w-5 h-5" />
        </button>

        <button 
            onclick={() => editorState.setDetectionTool('drag')}
            class="p-2 rounded-lg transition-colors {editorState.activeDetectionTool === 'drag' ? 'bg-accent/15 text-accent' : 'text-gray-500 hover:bg-gray-100'}"
            title="Move Bubble"
        >
            <Move class="w-5 h-5" />
        </button>

        <button 
            onclick={() => editorState.setDetectionTool('create')}
            class="p-2 rounded-lg transition-colors {editorState.activeDetectionTool === 'create' ? 'bg-accent/15 text-accent' : 'text-gray-500 hover:bg-gray-100'}"
            title="Draw Polygon (Double Click to close)"
        >
            <PenTool class="w-5 h-5" />
        </button>

        <div class="w-px h-6 bg-gray-300 my-auto mx-1"></div>

        <button 
            onclick={() => editorState.setDetectionTool('delete')}
            class="p-2 rounded-lg transition-colors {editorState.activeDetectionTool === 'delete' ? 'bg-red-100 text-red-600' : 'text-gray-500 hover:bg-red-50 hover:text-red-500'}"
            title="Delete Bubble"
        >
            <Trash2 class="w-5 h-5" />
        </button>
        
    </div>
{/if}