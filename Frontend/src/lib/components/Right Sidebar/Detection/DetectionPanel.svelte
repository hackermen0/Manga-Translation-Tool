<script lang="ts">
	import { ScanText, Loader2, Sparkles, Hand, Trash2, Pencil, Plus } from '@lucide/svelte';
	import { Button, editorState } from '$lib';
	import { Separator } from 'bits-ui';

	let bubbles = $derived(editorState.activePage?.bubbles || []);
	let totalBubbles = $derived(bubbles.length);
	let isDetected = $derived(editorState.activePage?.detected || false);

	let detectionType = $state<'bubble' | 'sfx' | null>(null);

	async function handleDetectClick() {
		detectionType = 'bubble';
		try {
			await editorState.detectBubbles();
		} finally {
			detectionType = null;
		}
	}

	async function handleDetectSFXClick() {
		detectionType = 'sfx';
		try {
			await editorState.detectSFX();
		} finally {
			detectionType = null;
		}
	}
</script>

<div
	class="border-primary-border ring-accent flex h-auto flex-col gap-5 rounded-lg border-2 bg-white p-4 ring-1"
>
	<div class="flex flex-col gap-6">
		<div class="ml-1 flex flex-row items-center gap-4">
			<ScanText class="text-accent h-5 w-5" />
			<p class="font-semibold text-black">Speech Bubble Detection</p>
		</div>

		<div class="flex flex-col gap-3">
			<Button
				class="flex w-full items-center justify-center gap-3 shadow-md"
				onclick={handleDetectClick}
				disabled={editorState.isProcessing}
			>
				{#if editorState.isProcessing && detectionType === 'bubble'}
					<Loader2 class="h-4 w-4 animate-spin" />
					Detecting Speech Bubbles...
				{:else}
					Run AI Bubble Detection
				{/if}
			</Button>

			<Button
				variant="outline"
				class="flex w-full items-center justify-center gap-3 shadow-md border-purple-500 text-purple-600 hover:bg-purple-500/10 hover:text-purple-700"
				onclick={handleDetectSFXClick}
				disabled={editorState.isProcessing}
			>
				{#if editorState.isProcessing && detectionType === 'sfx'}
					<Loader2 class="h-4 w-4 animate-spin" />
					Detecting SFX...
				{:else}
					<Sparkles class="h-4 w-4" />
					Run AI SFX Detection
				{/if}
			</Button>
		</div>

		<Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200" />

		<div class="flex flex-col gap-3 px-1 text-sm">
			<div class="flex justify-between">
				<span class="font-medium text-gray-500">Detection Status:</span>
				<span class={`font-semibold ${isDetected ? 'text-green-600' : 'text-amber-500'}`}>
					{isDetected ? 'Detected' : 'Not Run Yet'}
				</span>
			</div>
			<div class="flex justify-between">
				<span class="font-medium text-gray-500">Total Bubbles:</span>
				<span class="font-semibold text-black">{totalBubbles}</span>
			</div>
		</div>
	</div>
</div>
