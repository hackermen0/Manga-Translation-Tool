<script lang="ts" module>
    import { PointerSensor, type SensorDescriptor, type PointerSensorOptions, type DropAnimation, defaultDropAnimationSideEffects } from '@dnd-kit-svelte/core';
    
    const sensors: SensorDescriptor<PointerSensorOptions>[] = [
        {
            sensor: PointerSensor,
            options: {
                activationConstraint: {
                    distance: 5,
                    delay: 0,
                    tolerance: 0
                }
            }
        }
    ];

    const dropAnimation: DropAnimation = {
        sideEffects: defaultDropAnimationSideEffects({
            styles: {
                active: {
                    opacity: '0.5',
                }
            }
        })
    }
</script>

<script lang="ts">
    import { DndContext, DragOverlay } from '@dnd-kit-svelte/core';
    import type { DragStartEvent, DragEndEvent } from '@dnd-kit-svelte/core';
    import { SortableContext } from '@dnd-kit-svelte/sortable';
    import FilmstripThumb from './FilmstripThumb.svelte';
    import { editorState } from '$lib/stores/Editor.svelte';

    const BACKEND_URL = "http://127.0.0.1:8000";

    let pages = $derived(editorState.pages);
    let activeId = $state<string | null>(null);

    function handleDragStart(e: DragStartEvent) {
        activeId = e.active.id as string;
        editorState.setActivePage(activeId);
    }

    function handleDragEnd(e: DragEndEvent) {
        const { active, over } = e;
        if (!over || active.id === over.id) {
            activeId = null;
            return;
        }
        
        const currentIds = pages.map(p => p.pageId);
        const oldIndex = currentIds.indexOf(active.id as string);
        const newIndex = currentIds.indexOf(over.id as string);

        editorState.reorderPages(oldIndex, newIndex);
        activeId = null;
    }
</script>

<DndContext {sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
    <div class="flex flex-col overflow-y-auto bg-gray-100 p-4 gap-2 w-full h-full items-center shadow-inner select-none">
        {#if pages.length === 0}
            <div class="flex w-full h-full items-center justify-center text-gray-500 text-sm italic font-medium text-center">
                No pages loaded. Upload a chapter to begin.
            </div>
        {:else}
            <SortableContext items={pages.map(p => p.pageId)}>
                <div class="flex flex-col gap-5 w-full">
                    {#each pages as page (page.pageId)}
                        <FilmstripThumb 
                            {page} 
                            isActivePage={editorState.activePageId === page.pageId}
                            onclick={() => editorState.setActivePage(page.pageId)}
                        />
                    {/each}
                </div>
            </SortableContext>
        {/if}
    </div>

    <DragOverlay {dropAnimation}>
        {#if activeId}
            {@const activePage = pages.find(p => p.pageId === activeId)}
            {#if activePage}
                <div class="relative flex flex-col items-center flex-shrink-0 ring-4 ring-accent rounded-md scale-105 opacity-100 z-10 shadow-lg cursor-grabbing">
                    <img
                        src={`${BACKEND_URL}${activePage.inpaintedUrl || activePage.originalUrl}`}
                        alt={activePage.originalFilename}
                        class="w-full h-auto object-cover rounded-sm bg-white pointer-events-none"
                    />
                    <div class="bottom-0 w-full text-gray-500 text-xs py-1 text-center font-bold rounded-b-sm tracking-wider pointer-events-none">
                        {activePage.originalFilename}
                    </div>
                </div>
            {/if}
        {/if}
    </DragOverlay>
</DndContext>