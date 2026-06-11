<script lang="ts">
	import { Languages, Scan, ChevronRight, ChevronLeft, Loader2, ScanText } from '@lucide/svelte';
	import { Button, GlossaryButton, editorState } from '$lib';
	import { Separator } from 'bits-ui';

	let bubbles = $derived(editorState.activePage?.bubbles || []);
	let totalBubbles = $derived(bubbles.length);

	let activeBubbleIndex = $derived.by(() => {
		if (bubbles.length === 0) return -1;
		const idx = bubbles.findIndex((b) => b.id === editorState.activeBubbleId);
		return idx !== -1 ? idx : 0;
	});

	let activeBubble = $derived(bubbles[activeBubbleIndex]);

	$effect(() => {
		if (
			bubbles.length > 0 &&
			(editorState.activeBubbleId === null ||
				!bubbles.some((b) => b.id === editorState.activeBubbleId))
		) {
			editorState.activeBubbleId = bubbles[0].id;
		}
	});

	function handlePrev() {
		if (totalBubbles === 0) return;
		const newIdx = (activeBubbleIndex - 1 + totalBubbles) % totalBubbles;
		editorState.activeBubbleId = bubbles[newIdx].id;
	}

	function handleNext() {
		if (totalBubbles === 0) return;
		const newIdx = (activeBubbleIndex + 1) % totalBubbles;
		editorState.activeBubbleId = bubbles[newIdx].id;
	}

	async function handleAutoDetect() {
		await editorState.runOcr();
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
				To translate text, we first need to detect speech bubbles on this page.
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
			<div class="flex flex-row items-center justify-between">
				<div class="ml-1 flex flex-row items-center gap-4">
					<Languages class="text-accent h-5 w-5" />
					<p class="font-semibold text-black">Translation Panel</p>
				</div>
				<div class="flex flex-row gap-2">
					<Button
						class="h-8 w-8 rounded-full p-2"
						variant="outline"
						onclick={handlePrev}
						disabled={totalBubbles <= 1}
					>
						<ChevronLeft class="h-4 w-4" />
					</Button>
					<Button
						class="h-8 w-8 rounded-full p-2"
						variant="outline"
						onclick={handleNext}
						disabled={totalBubbles <= 1}
					>
						<ChevronRight class="h-4 w-4" />
					</Button>
				</div>
			</div>

			<div class="flex w-full flex-col gap-3">
				<Button
					variant="ghost"
					class="border-primary-border hover:border-accent hover:text-accent hover:bg-accent/5 flex w-full flex-row gap-3 border-2"
					onclick={handleAutoDetect}
					disabled={editorState.isProcessing || totalBubbles === 0}
				>
					{#if editorState.isProcessing}
						<Loader2 class="text-accent h-4 w-4 animate-spin" />
						<p class="text-accent">Running OCR...</p>
					{:else}
						<Scan class="h-4 w-4" />
						<p>Auto-Detect Text</p>
					{/if}
				</Button>
				<GlossaryButton />
			</div>

			<Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200" />

			<div class="flex w-full flex-row justify-between px-1">
				<p class="text-sm font-semibold text-black">Speech Bubbles</p>
				<p class="text-sm font-semibold text-black">
					{totalBubbles > 0 ? activeBubbleIndex + 1 : 0} of {totalBubbles}
				</p>
			</div>

			<div class="flex flex-col gap-2 px-1">
				<p class="text-sm font-semibold text-black">Original Text (JA)</p>
				{#if editorState.activePage && activeBubbleIndex >= 0}
					<textarea
						bind:value={editorState.activePage.bubbles[activeBubbleIndex].ja_text}
						oninput={() => editorState.saveBubbles()}
						class="border-primary-border focus:outline-accent focus:ring-accent w-full resize-none rounded-lg border bg-white px-3 py-2 text-start text-sm text-black focus:ring-1"
						rows="3"
						placeholder="Enter Japanese text..."
					></textarea>
				{:else}
					<textarea
						value=""
						disabled
						class="border-primary-border w-full resize-none rounded-lg border bg-gray-50 px-3 py-2 text-start text-sm text-gray-400"
						rows="3"
						placeholder="No speech bubbles found on this page."
					></textarea>
				{/if}
			</div>

			<div class="flex flex-col gap-2 px-1">
				<p class="text-sm font-semibold text-black">Translation (EN)</p>
				{#if editorState.activePage && activeBubbleIndex >= 0}
					<textarea
						bind:value={editorState.activePage.bubbles[activeBubbleIndex].en_text}
						oninput={() => editorState.saveBubbles()}
						class="border-primary-border focus:outline-accent focus:ring-accent w-full resize-none rounded-lg border bg-white px-3 py-2 text-start text-sm text-black focus:ring-1"
						rows="3"
						placeholder="Enter English translation..."
					></textarea>
				{:else}
					<textarea
						value=""
						disabled
						class="border-primary-border w-full resize-none rounded-lg border bg-gray-50 px-3 py-2 text-start text-sm text-gray-400"
						rows="3"
						placeholder="No speech bubbles found on this page."
					></textarea>
				{/if}
			</div>

			<div>
				<Button
					class="w-full"
					onclick={() => editorState.saveBubbles()}
					disabled={totalBubbles === 0}
				>
					<p>Apply Translation</p>
				</Button>
			</div>
		</div>
	</div>
{/if}
