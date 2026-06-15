<script lang="ts">
	import { CheckCircle, Loader2, Download } from '@lucide/svelte';
	import { editorState, Button } from '$lib';
	import { Separator } from 'bits-ui';

	let bubbles = $derived(editorState.activePage?.bubbles || []);

	let isExporting = $state(false);

	async function handleExport() {
		if (!editorState.exportHandler) {
			alert('Export functionality is not ready yet. Please ensure the canvas has loaded the page.');
			return;
		}
		isExporting = true;
		try {
			await editorState.exportHandler();
		} catch (error) {
			console.error('Export failed:', error);
			alert('Failed to export: ' + (error instanceof Error ? error.message : String(error)));
		} finally {
			isExporting = false;
		}
	}
</script>

<div
	class="border-primary-border ring-accent flex h-auto flex-col gap-5 rounded-lg border-2 bg-white p-4 ring-1"
>
	<div class="flex flex-col gap-5">
		<!-- Header -->
		<div class="flex flex-row items-center justify-between">
			<div class="ml-1 flex flex-row items-center gap-4">
				<CheckCircle class="text-accent h-5 w-5" />
				<p class="font-semibold text-black">Quality Control</p>
			</div>
		</div>

		<Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200" />

		<!-- Comparison Mode Segmented Control -->
		<div class="flex flex-col gap-2 px-1">
			<p class="text-sm font-semibold text-black">Visual Proofing Mode</p>
			<div class="border-primary-border flex flex-row rounded-lg border bg-gray-50 p-0.5">
				<button
					onclick={() => editorState.qcMode = 'onion'}
					class="flex flex-1 items-center justify-center gap-2 rounded-md py-1.5 text-sm font-medium transition-all duration-150 {editorState.qcMode === 'onion' ? 'bg-accent text-white shadow-sm' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'}"
				>
					<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-10 5L12 13l10-5-10-5Z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/></svg>
					Onion Skin
				</button>
				<button
					onclick={() => editorState.qcMode = 'split'}
					class="flex flex-1 items-center justify-center gap-2 rounded-md py-1.5 text-sm font-medium transition-all duration-150 {editorState.qcMode === 'split' ? 'bg-accent text-white shadow-sm' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'}"
				>
					<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M12 3v18"/></svg>
					Split Screen
				</button>
			</div>
		</div>

		<!-- Parameters Sliders -->
		{#if editorState.qcMode === 'onion'}
			<div class="flex flex-col gap-2 px-1">
				<div class="flex items-center justify-between">
					<p class="text-sm font-semibold text-black">Blend Opacity</p>
					<span class="text-accent text-sm font-bold">{editorState.qcBlendValue}%</span>
				</div>
				<div class="flex items-center gap-3">
					<span class="text-xs text-gray-400 font-medium select-none">Original</span>
					<input
						type="range"
						min="0"
						max="100"
						bind:value={editorState.qcBlendValue}
						class="accent-accent w-full cursor-pointer"
					/>
					<span class="text-xs text-gray-400 font-medium select-none">Final</span>
				</div>
			</div>
		{:else}
			<div class="flex flex-col gap-2 px-1">
				<div class="flex items-center justify-between">
					<p class="text-sm font-semibold text-black">Split Position</p>
					<span class="text-accent text-sm font-bold">{Math.round(editorState.qcSplitPercentage)}%</span>
				</div>
				<div class="flex items-center gap-3">
					<span class="text-xs text-gray-400 font-medium select-none">Original</span>
					<input
						type="range"
						min="0"
						max="100"
						bind:value={editorState.qcSplitPercentage}
						class="accent-accent w-full cursor-pointer"
					/>
					<span class="text-xs text-gray-400 font-medium select-none">Final</span>
				</div>
			</div>
		{/if}

		<!-- Compare Quick-Toggles -->
		<div class="flex flex-row gap-2 px-1 w-full">
			<button
				onclick={() => {
					if (editorState.qcMode === 'onion') editorState.qcBlendValue = 0;
					else editorState.qcSplitPercentage = 0;
				}}
				class="flex-1 py-1.5 px-2 border border-gray-200 text-gray-600 hover:bg-gray-50 text-xs font-semibold rounded-lg shadow-sm transition-colors cursor-pointer text-center"
			>
				Original
			</button>
			<button
				onclick={() => {
					if (editorState.qcMode === 'onion') editorState.qcBlendValue = 50;
					else editorState.qcSplitPercentage = 50;
				}}
				class="flex-1 py-1.5 px-2 border border-gray-200 text-gray-600 hover:bg-gray-50 text-xs font-semibold rounded-lg shadow-sm transition-colors cursor-pointer text-center"
			>
				Reset (50%)
			</button>
			<button
				onclick={() => {
					if (editorState.qcMode === 'onion') editorState.qcBlendValue = 100;
					else editorState.qcSplitPercentage = 100;
				}}
				class="flex-1 py-1.5 px-2 border border-gray-200 text-gray-600 hover:bg-gray-50 text-xs font-semibold rounded-lg shadow-sm transition-colors cursor-pointer text-center"
			>
				Final
			</button>
		</div>

		<Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200" />

		<!-- Inpainting Switch Toggle -->
		<div class="flex flex-row items-center justify-between px-2 py-3 rounded-lg bg-gray-50 border border-gray-100">
			<div class="flex flex-col gap-0.5">
				<p class="text-sm font-semibold text-black">Inpainting Highlights</p>
				<p class="text-[11px] text-gray-400 max-w-[170px]">Overlay inpainted areas in neon red to catch erasures & artifacts.</p>
			</div>
			<label class="relative inline-flex items-center cursor-pointer select-none">
				<input
					type="checkbox"
					bind:checked={editorState.qcHighlightInpaint}
					class="sr-only peer"
				/>
				<div class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
			</label>
		</div>

		<Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200" />

		<!-- Page Summary Card -->
		<div class="flex flex-col gap-2 px-1">
			<p class="text-sm font-semibold text-black">Page Summary</p>
			<div class="flex flex-col gap-2 rounded-lg border border-accent/20 bg-accent/5 p-3 text-xs shadow-inner">
				<div class="flex items-center justify-between">
					<span class="font-semibold text-gray-500">Original File:</span>
					<span class="font-medium text-black select-all">{editorState.activePage?.originalFilename || 'N/A'}</span>
				</div>
				<div class="flex items-center justify-between">
					<span class="font-semibold text-gray-500">Inpainted URL:</span>
					<span class="font-medium text-black select-all">{editorState.activePage?.inpaintedUrl ? 'Generated' : 'Not Generated'}</span>
				</div>
				<div class="flex items-center justify-between">
					<span class="font-semibold text-gray-500">Speech Bubbles:</span>
					<span class="font-medium text-accent font-bold">{bubbles.length}</span>
				</div>
			</div>
		</div>

		<Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200" />

		<!-- Export Action Button -->
		<div class="px-1">
			<Button
				variant="secondary"
				class="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-md font-semibold text-black bg-[var(--color-accent)] hover:bg-[var(--color-accent)]/85 transition-colors shadow-sm disabled:opacity-50 select-none cursor-pointer"
				onclick={handleExport}
				disabled={isExporting}
			>
				{#if isExporting}
					<Loader2 class="h-4 w-4 animate-spin shrink-0" />
					Exporting...
				{:else}
					<Download class="h-4 w-4 shrink-0" />
					Export Page
				{/if}
			</Button>
		</div>
	</div>
</div>
