<script lang="ts">
	import { Eraser, Loader2, ScanText } from '@lucide/svelte';
	import { Button, editorState } from '$lib';
	import { Separator } from 'bits-ui';

	let borderErosion = $state(2);

	async function handleAutoClear() {
		await editorState.runInpainting(borderErosion);
	}

	async function handleDetectClick() {
		editorState.setActiveSession('detection');
		await editorState.detectBubbles();
	}
</script>

{#if editorState.activePage && !editorState.activePage.detected}
	<div
		class="border-primary-border ring-accent flex h-auto flex-col items-center justify-center gap-6 rounded-lg border-2 bg-white p-6 text-center ring-1"
	>
		<div class="bg-accent/10 text-accent flex h-16 w-16 items-center justify-center rounded-full">
			<ScanText class="h-8 w-8" />
		</div>
		<div class="flex flex-col gap-2">
			<h3 class="text-lg font-bold text-black">Detection Required</h3>
			<p class="max-w-[280px] text-sm text-gray-500">
				To redraw (inpaint) speech bubbles, we first need to detect speech bubbles on this page.
			</p>
		</div>
		<Button
			class="flex w-full items-center justify-center gap-2 shadow-sm"
			onclick={handleDetectClick}
			disabled={editorState.isProcessing}
		>
			{#if editorState.isProcessing}
				<Loader2 class="h-4 w-4 animate-spin" />
				Detecting...
			{:else}
				<ScanText class="h-4 w-4" />
				Detect Speech Bubbles
			{/if}
		</Button>
	</div>
{:else}
	<div
		class="border-primary-border ring-accent flex h-auto flex-col gap-5 rounded-lg border-2 bg-white p-4 ring-1"
	>
		<div class="flex flex-col gap-6">
			<div class="ml-1 flex flex-row items-center gap-4">
				<Eraser class="text-accent h-5 w-5" />
				<p class="font-semibold text-black">Redrawing (Inpainting)</p>
			</div>

			<div class="flex flex-col gap-3">
				<div class="flex items-center justify-between text-sm">
					<span class="font-medium text-gray-500">Border Erosion (Dilation):</span>
					<span class="text-accent font-bold">{borderErosion}</span>
				</div>
				<input
					type="range"
					min="0"
					max="10"
					bind:value={borderErosion}
					class="accent-accent w-full"
				/>
			</div>

			<div class="flex flex-col gap-3">
				<Button
					class="flex w-full items-center justify-center gap-3 shadow-md"
					onclick={handleAutoClear}
					disabled={editorState.isProcessing}
				>
					{#if editorState.isProcessing}
						<Loader2 class="h-4 w-4 animate-spin" />
						Clearing Bubbles...
					{:else}
						Auto Clear Bubbles
					{/if}
				</Button>
			</div>

			<Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200" />

			<div class="flex flex-col gap-3 px-1 text-sm">
				<div class="flex justify-between">
					<span class="font-medium text-gray-500">Inpainting Status:</span>
					<span
						class={`font-semibold ${editorState.activePage?.inpaintedUrl ? 'text-green-600' : 'text-amber-500'}`}
					>
						{editorState.activePage?.inpaintedUrl ? 'Completed' : 'Not Run Yet'}
					</span>
				</div>
			</div>
		</div>
	</div>
{/if}
