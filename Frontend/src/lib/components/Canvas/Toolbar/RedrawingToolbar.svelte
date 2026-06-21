<script lang="ts">
	import { Hand, Eraser, Undo2, History, Bandage } from '@lucide/svelte';
	import { editorState } from '$lib/stores/Editor.svelte';

	const presetColors = [
		'#ffffff',
		'#f5f5f5',
		'#e0e0e0',
		'#c0c0c0',
		'#000000',
		'#f5e6d3',
		'#ffe4c4',
		'#fdf5e6'
	];

	function undoLastStroke() {
		if (!editorState.activePage || editorState.activePage.redrawingStrokes.length === 0) return;
		editorState.activePage.redrawingStrokes.pop();
		editorState.saveRedrawingStrokes();
	}
</script>

{#if editorState.activeSession === 'redrawing'}
	<div
		class="absolute bottom-6 left-1/2 z-50 flex -translate-x-1/2 flex-row items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 shadow-2xl transition-all"
	>
		<button
			onclick={() => editorState.setRedrawingTool('pan')}
			class="rounded-lg p-2 transition-colors {editorState.activeRedrawingTool === 'pan'
				? 'bg-accent/15 text-accent'
				: 'text-gray-500 hover:bg-gray-100'}"
			title="Pan (Move Canvas)"
		>
			<Hand class="h-5 w-5" />
		</button>

		<button
			onclick={() => editorState.setRedrawingTool('eraser')}
			class="rounded-lg p-2 transition-colors {editorState.activeRedrawingTool === 'eraser'
				? 'bg-accent/15 text-accent'
				: 'text-gray-500 hover:bg-gray-100'}"
			title="Eraser Tool"
		>
			<Eraser class="h-5 w-5" />
		</button>

		<button
			onclick={() => editorState.setRedrawingTool('restore')}
			class="rounded-lg p-2 transition-colors {editorState.activeRedrawingTool === 'restore'
				? 'bg-blue-100 text-blue-600'
				: 'text-gray-500 hover:bg-blue-50 hover:text-blue-500'}"
			title="Restore Tool (Bring back original image)"
		>
			<History class="h-5 w-5" />
		</button>

		<button
			onclick={() => editorState.setRedrawingTool('heal')}
			class="rounded-lg p-2 transition-colors {editorState.activeRedrawingTool === 'heal'
				? 'bg-emerald-100 text-emerald-600'
				: 'text-gray-500 hover:bg-emerald-50 hover:text-emerald-500'}"
			title="Heal Tool (Smart Patch — Ctrl+Click to set source)"
		>
			<Bandage class="h-5 w-5" />
		</button>

		<div class="mx-1 my-auto h-6 w-px bg-gray-300"></div>

		<!-- Brush size slider -->
		<div class="flex w-28 flex-col gap-1 px-1">
			<div class="flex w-full items-center justify-between">
				<span class="text-xs font-medium text-gray-500">Size</span>
				<span class="text-accent text-xs font-bold">{editorState.brushSize}</span>
			</div>
			<input
				type="range"
				min="1"
				max="100"
				bind:value={editorState.brushSize}
				class="accent-accent h-1 w-full cursor-pointer appearance-none rounded-lg bg-gray-200"
			/>
		</div>

		<!-- Color presets (only visible for eraser tool) -->
		{#if editorState.activeRedrawingTool === 'eraser'}
			<div class="mx-1 my-auto h-6 w-px bg-gray-300"></div>

			<div class="flex flex-row items-center gap-1.5 px-1">
				{#each presetColors as color}
					<!-- svelte-ignore a11y_consider_explicit_label -->
					<button
						onclick={() => (editorState.brushColor = color)}
						class="h-5 w-5 flex-shrink-0 rounded-full border-2 transition-all {editorState.brushColor ===
						color
							? 'border-accent scale-125 shadow-md'
							: 'border-gray-300 hover:scale-110 hover:border-gray-400'}"
						style="background-color: {color};"
						title={color}
					></button>
				{/each}

				<!-- Custom color picker -->
				<div class="relative h-5 w-5 flex-shrink-0">
					<input
						type="color"
						bind:value={editorState.brushColor}
						class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
						title="Pick custom color"
					/>
					<div
						class="pointer-events-none h-5 w-5 overflow-hidden rounded-full border-2 border-dashed border-gray-400"
						style="background: conic-gradient(red, yellow, lime, aqua, blue, magenta, red);"
					></div>
				</div>
			</div>
		{/if}

		<!-- Hardness slider (only visible for heal tool) -->
		{#if editorState.activeRedrawingTool === 'heal'}
			<div class="mx-1 my-auto h-6 w-px bg-gray-300"></div>

			<div class="flex w-24 flex-col gap-1 px-1">
				<div class="flex w-full items-center justify-between">
					<span class="text-xs font-medium text-gray-500">Hardness</span>
					<span class="text-xs font-bold text-emerald-600">{Math.round(editorState.healBrushHardness * 100)}%</span>
				</div>
				<input
					type="range"
					min="0"
					max="100"
					value={Math.round(editorState.healBrushHardness * 100)}
					oninput={(e) => { editorState.healBrushHardness = parseInt(e.currentTarget.value) / 100; }}
					class="accent-emerald-500 h-1 w-full cursor-pointer appearance-none rounded-lg bg-gray-200"
				/>
			</div>

			<div class="mx-1 my-auto h-6 w-px bg-gray-300"></div>

			<!-- Source mode badge -->
			<div class="flex items-center gap-1.5 px-1">
				<span
					class="rounded-full px-2 py-0.5 text-xs font-semibold {editorState.healSourceMode === 'manual'
						? 'bg-amber-100 text-amber-700'
						: 'bg-emerald-100 text-emerald-700'}"
				>
					{editorState.healSourceMode === 'manual' ? 'Manual' : 'Auto'}
				</span>
				{#if editorState.healSourceMode === 'manual' && editorState.healSourceAnchor}
					<button
						onclick={() => { editorState.healSourceMode = 'auto'; editorState.healSourceAnchor = null; }}
						class="text-xs text-gray-400 hover:text-gray-600 transition-colors"
						title="Reset to auto mode"
					>
						✕
					</button>
				{/if}
			</div>
		{/if}

		<div class="mx-1 my-auto h-6 w-px bg-gray-300"></div>

		<!-- Undo last stroke -->
		<button
			onclick={undoLastStroke}
			class="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 disabled:pointer-events-none disabled:opacity-30"
			title="Undo Last Stroke"
			disabled={!editorState.activePage || editorState.activePage.redrawingStrokes.length === 0}
		>
			<Undo2 class="h-5 w-5" />
		</button>
	</div>
{/if}
