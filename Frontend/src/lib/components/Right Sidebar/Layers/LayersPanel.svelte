<script lang="ts" module>
	import {
		PointerSensor,
		type SensorDescriptor,
		type PointerSensorOptions,
		type DropAnimation,
		defaultDropAnimationSideEffects
	} from '@dnd-kit-svelte/core';

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
					opacity: '0.5'
				}
			}
		})
	};
</script>

<script lang="ts">
	import { DndContext, DragOverlay } from '@dnd-kit-svelte/core';
	import type { DragStartEvent, DragEndEvent } from '@dnd-kit-svelte/core';
	import { SortableContext, arrayMove } from '@dnd-kit-svelte/sortable';
	import LayerCard from './LayerCard.svelte';
	import { layerStateManager } from '$lib';
	import { Layers, Plus, Pencil } from '@lucide/svelte';
	import { onMount } from 'svelte';

	onMount(() => {
		if (layerStateManager.layerList.length === 0) {
			layerStateManager.addLayer('Original Image', 'image');
			layerStateManager.addLayer('Text Layer', 'drawing');
			layerStateManager.addLayer('Redrawing Layer', 'drawing');
			layerStateManager.addLayer('Effects', 'drawing');
		}
	});

	let layers = $derived(layerStateManager.layerList);
	let activeId = $state<string | null>(null);
	let edit = $state(false);

	function addNewLayer() {
		const name = `Layer ${layers.length + 1}`;
		layerStateManager.addLayer(name, 'drawing');
	}

	function toggleEdit() {
		edit = !edit;
	}

	function handleDragStart(e: DragStartEvent) {
		activeId = e.active.id as string;
		layerStateManager.selectLayer(activeId);
	}

	function handleDragEnd(e: DragEndEvent) {
		const { active, over } = e;
		if (!over || active.id === over.id) return;

		const currentIds = layers.map((l) => l.id);
		const oldIndex = currentIds.indexOf(active.id as string);
		const newIndex = currentIds.indexOf(over.id as string);

		const newOrder = arrayMove(currentIds, oldIndex, newIndex);
		layerStateManager.reorderLayers(newOrder);

		activeId = null;
	}
</script>

<DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
	<div
		class="border-primary-border ring-accent flex h-auto flex-col gap-5 rounded-lg border-2 bg-white p-4 ring-1"
	>
		<div class="flex flex-row items-center justify-between">
			<div class="ml-1 flex flex-row gap-3">
				<Layers />
				<p class="font-semibold text-black">Layers</p>
			</div>
			<div>
				<button
					onclick={toggleEdit}
					class={`rounded-full p-1 transition-all ${edit ? 'bg-accent/20 text-accent' : 'text-gray-500 hover:text-black'}`}
				>
					<Pencil class="h-4 w-4" />
				</button>
			</div>
		</div>
		<SortableContext items={layers}>
			<div class="flex flex-col gap-2">
				{#each layers as layer (layer.id)}
					<LayerCard
						name={layer.name}
						layerID={layer.id}
						type={layer.type}
						isSelected={layerStateManager.selectedLayerId === layer.id}
						bind:edit={edit}
					/>
				{/each}
			</div>
		</SortableContext>
		<button
			onclick={addNewLayer}
			class="transition-transform hover:scale-[1.01] active:scale-[0.99]"
		>
			<div
				class="border-primary-border hover:bg-accent/5 hover:text-accent hover:border-accent flex w-full flex-row justify-center rounded-lg border-1 border-dashed p-3 text-sm text-gray-500"
			>
				<Plus />
			</div>
		</button>
	</div>
	<DragOverlay dropAnimation={dropAnimation}>
		{#if activeId}
			{@const activeLayer = layers.find((l) => l.id === activeId)}
			<LayerCard
				name={activeLayer?.name ?? 'Unnamed'}
				layerID={activeId}
				type={activeLayer?.type ?? 'drawing'}
				isSelected={true}
				edit={edit}
			/>
		{/if}
	</DragOverlay>
</DndContext>
