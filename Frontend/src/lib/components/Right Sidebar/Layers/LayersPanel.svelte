<script lang="ts" module>

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
	import { DndContext, DragOverlay, PointerSensor, defaultDropAnimationSideEffects } from '@dnd-kit-svelte/core';
    import type {  SensorDescriptor, PointerSensorOptions, DragStartEvent, DragEndEvent, DropAnimation } from '@dnd-kit-svelte/core'
	import { SortableContext, arrayMove } from '@dnd-kit-svelte/sortable';
	import LayerCard from './LayerCard.svelte';
	import { layerStateManager } from '$lib';
	import { Layers, Plus, Pencil } from '@lucide/svelte';
	import { onMount } from 'svelte';

	onMount(() => {
		const defaultNames = ['Original Image', 'Text Layer', 'Redrawing Layer', 'Effects'];

		if (layerStateManager.layerList.length === 0) {
			for (const name of defaultNames) {
				layerStateManager.addLayer(name);
			}
		}
	});

	let layers = $derived(layerStateManager.layerList);
	let activeId = $state<string | null>(null);
	let edit = $state(false);


	function addNewLayer() {
		const name = `Layer ${layers.length + 1}`;
		layerStateManager.addLayer(name);
	}

	function toggleEdit() {
		edit = !edit;
	}

    function handleDragStart(e: DragStartEvent) {
        activeId = e.active.id as string;
    }

    function handleDragEnd(e: DragEndEvent) {
        const { active, over } = e;
        if (!over || active.id === over.id) return;

        const oldIndex = layers.findIndex((l) => l.id === active.id);
        const newIndex = layers.findIndex((l) => l.id === over.id);

        layers = arrayMove(layers, oldIndex, newIndex);
        layerStateManager.reorderLayers(layers.map((l) => l.id));

        activeId = null;
    }
</script>
<div>

</div>

<DndContext {sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
	<div class="h-auto p-4 border-2 border-primary-border flex flex-col gap-5 rounded-lg ring-1 ring-accent">
		<div class="flex flex-row justify-between">
			<div class="flex flex-row gap-3 ml-1">
				<Layers />
				<p class="font-semibold text-black">Layers</p>
			</div>
			<div>
				<button onclick={toggleEdit} class={`mt-0.5 mr-2 rounded-full ${edit ? "ring-2 ring-offset-4 ring-accent" : "ring-0"}`}>
					<Pencil class="w-4 h-4 text-gray-500 hover:text-black"/>
				</button>
			</div>
		</div>
		<SortableContext items={layers}>
			<div class="flex flex-col gap-2">
				{#each layers as layer (layer.id)}
					<LayerCard name={layer.name} layerID={layer.id} bind:edit={edit} />
				{/each}
			</div>
		</SortableContext>
		<button onclick={addNewLayer}>
			<div class="w-full border-1 border-primary-border border-dashed flex flex-row justify-center p-3 rounded-lg text-sm text-gray-500 hover:bg-accent/70">
				<Plus />
			</div>
		</button>
	</div>
	<DragOverlay {dropAnimation}>
		{#if activeId}
			<LayerCard
                name={layers.find(l => l.id === activeId)?.name ?? 'Unnamed'}
                layerID={activeId ?? ''}
                edit={edit}
            />
		{/if}
	</DragOverlay>
</DndContext>
