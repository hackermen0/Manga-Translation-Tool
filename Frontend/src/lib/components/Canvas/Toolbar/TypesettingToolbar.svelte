<script lang="ts">
	import { Scissors, MousePointer2, Move } from '@lucide/svelte';
	import { editorState, DEFAULT_TYPESET_STYLE } from '$lib/stores/Editor.svelte';
	import type { MangaBubble, Point } from '$lib/stores/Editor.svelte';

	let isSplitting = $state(false);
	let splitText1 = $state('');
	let splitText2 = $state('');
	let splitDirection = $state<'vertical' | 'horizontal'>('vertical');

	let activeBubble = $derived(
		editorState.activePage?.bubbles.find((b) => b.id === editorState.activeBubbleId)
	);

	function getBBox(points: Point[]) {
		if (!points || points.length === 0) return { x: 0, y: 0, width: 0, height: 0 };
		const xs = points.map((p) => p.x);
		const ys = points.map((p) => p.y);
		const minX = Math.min(...xs);
		const minY = Math.min(...ys);
		const maxX = Math.max(...xs);
		const maxY = Math.max(...ys);
		return {
			x: minX,
			y: minY,
			width: maxX - minX,
			height: maxY - minY
		};
	}

	function handleStartSplit() {
		if (!activeBubble) return;
		const text = activeBubble.en_text || '';
		const lines = text.split('\n');
		if (lines.length >= 2) {
			const mid = Math.ceil(lines.length / 2);
			splitText1 = lines.slice(0, mid).join('\n');
			splitText2 = lines.slice(mid).join('\n');
		} else {
			const words = text.split(/\s+/);
			const mid = Math.ceil(words.length / 2);
			splitText1 = words.slice(0, mid).join(' ');
			splitText2 = words.slice(mid).join(' ');
		}
		splitDirection = 'vertical';
		isSplitting = true;
	}

	async function handleConfirmSplit() {
		if (!activeBubble || !editorState.activePage) return;

		const page = editorState.activePage;
		const bbox = getBBox(activeBubble.points);

		let points1: Point[] = [];
		let points2: Point[] = [];

		if (splitDirection === 'vertical') {
			// Top half
			points1 = [
				{ x: bbox.x, y: bbox.y },
				{ x: bbox.x + bbox.width, y: bbox.y },
				{ x: bbox.x + bbox.width, y: bbox.y + bbox.height / 2 },
				{ x: bbox.x, y: bbox.y + bbox.height / 2 }
			];
			// Bottom half
			points2 = [
				{ x: bbox.x, y: bbox.y + bbox.height / 2 },
				{ x: bbox.x + bbox.width, y: bbox.y + bbox.height / 2 },
				{ x: bbox.x + bbox.width, y: bbox.y + bbox.height },
				{ x: bbox.x, y: bbox.y + bbox.height }
			];
		} else {
			// Left half
			points1 = [
				{ x: bbox.x, y: bbox.y },
				{ x: bbox.x + bbox.width / 2, y: bbox.y },
				{ x: bbox.x + bbox.width / 2, y: bbox.y + bbox.height },
				{ x: bbox.x, y: bbox.y + bbox.height }
			];
			// Right half
			points2 = [
				{ x: bbox.x + bbox.width / 2, y: bbox.y },
				{ x: bbox.x + bbox.width, y: bbox.y },
				{ x: bbox.x + bbox.width, y: bbox.y + bbox.height },
				{ x: bbox.x + bbox.width / 2, y: bbox.y + bbox.height }
			];
		}

		const originalId = activeBubble.id;
		const newId = Math.max(...page.bubbles.map((b) => b.id), 0) + 1;

		const bubble1: MangaBubble = {
			id: originalId,
			points: points1,
			ja_text: activeBubble.ja_text,
			en_text: splitText1,
			typeset: activeBubble.typeset ? { ...activeBubble.typeset } : { ...DEFAULT_TYPESET_STYLE }
		};

		const bubble2: MangaBubble = {
			id: newId,
			points: points2,
			ja_text: '',
			en_text: splitText2,
			typeset: activeBubble.typeset ? { ...activeBubble.typeset } : { ...DEFAULT_TYPESET_STYLE }
		};

		const index = page.bubbles.findIndex((b) => b.id === originalId);
		if (index !== -1) {
			page.bubbles.splice(index, 1, bubble1, bubble2);
			editorState.activeBubbleId = bubble1.id;
		}

		isSplitting = false;
		await editorState.saveTypesetting();
		await editorState.saveBubbles();
	}
</script>

{#if editorState.activeSession === 'typesetting'}
	<div class="absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 z-50">
		<!-- Popover options overlay -->
		{#if isSplitting && activeBubble}
			<div class="bg-white/95 backdrop-blur-md border border-gray-200 rounded-xl shadow-2xl p-4 w-80 flex flex-col gap-3 mb-2 animate-in fade-in slide-in-from-bottom-2 duration-200 select-none">
				<p class="font-semibold text-sm text-black">Split Speech Bubble</p>
				
				<!-- Bubble 1 Text -->
				<div class="flex flex-col gap-1">
					<span class="text-[10px] font-bold uppercase text-gray-400">Bubble 1 (Top/Left)</span>
					<textarea
						bind:value={splitText1}
						class="border-gray-200 w-full resize-none rounded-lg border bg-white px-2 py-1.5 text-xs text-black focus:outline-accent focus:ring-1 focus:ring-accent"
						rows="2"
						placeholder="Text for first bubble..."
					></textarea>
				</div>

				<!-- Bubble 2 Text -->
				<div class="flex flex-col gap-1">
					<span class="text-[10px] font-bold uppercase text-gray-400">Bubble 2 (Bottom/Right)</span>
					<textarea
						bind:value={splitText2}
						class="border-gray-200 w-full resize-none rounded-lg border bg-white px-2 py-1.5 text-xs text-black focus:outline-accent focus:ring-1 focus:ring-accent"
						rows="2"
						placeholder="Text for second bubble..."
					></textarea>
				</div>

				<!-- Split Direction -->
				<div class="flex flex-col gap-1">
					<span class="text-[10px] font-bold uppercase text-gray-400">Split Direction</span>
					<div class="flex flex-row gap-2 border border-gray-200 rounded-lg p-0.5 bg-gray-50">
						<button
							onclick={() => splitDirection = 'vertical'}
							class="flex-1 py-1 text-xs font-medium rounded-md transition-colors {splitDirection === 'vertical' ? 'bg-accent text-white shadow-sm' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'}"
						>
							Top / Bottom
						</button>
						<button
							onclick={() => splitDirection = 'horizontal'}
							class="flex-1 py-1 text-xs font-medium rounded-md transition-colors {splitDirection === 'horizontal' ? 'bg-accent text-white shadow-sm' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'}"
						>
							Left / Right
						</button>
					</div>
				</div>

				<!-- Action Buttons -->
				<div class="flex flex-row gap-2 mt-1">
					<button
						onclick={handleConfirmSplit}
						class="flex-1 py-1.5 bg-accent text-white text-xs font-semibold rounded-lg hover:bg-accent/90 transition-colors shadow-sm cursor-pointer"
					>
						Confirm
					</button>
					<button
						onclick={() => isSplitting = false}
						class="flex-1 py-1.5 border border-gray-200 text-gray-600 text-xs font-semibold rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
					>
						Cancel
					</button>
				</div>
			</div>
		{/if}

		<!-- Main Toolbar Bar -->
		<div class="bg-white px-3 py-2 rounded-xl shadow-2xl border border-gray-200 flex flex-row items-center gap-2">
			<button 
				onclick={() => editorState.setTypesettingTool('select')}
				class="p-2 rounded-lg transition-colors {editorState.activeTypesettingTool === 'select' ? 'bg-accent/15 text-accent' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'}"
				title="Select Bubble / Edit Text"
			>
				<MousePointer2 class="w-5 h-5" />
			</button>

			<button 
				onclick={() => editorState.setTypesettingTool('drag')}
				class="p-2 rounded-lg transition-colors {editorState.activeTypesettingTool === 'drag' ? 'bg-accent/15 text-accent' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'}"
				title="Move Text Position"
			>
				<Move class="w-5 h-5" />
			</button>

			<div class="w-px h-6 bg-gray-300 my-auto mx-1"></div>

			<button 
				onclick={handleStartSplit}
				class="p-2 rounded-lg transition-colors flex items-center gap-2 {isSplitting ? 'bg-accent/15 text-accent' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'}"
				title="Split Selected Bubble"
				disabled={!activeBubble}
			>
				<Scissors class="w-5 h-5" />
				<span class="text-xs font-medium pr-1">Split Bubble</span>
			</button>
			{#if !activeBubble}
				<span class="text-[10px] text-gray-400 italic px-2">Select a bubble on canvas to split</span>
			{/if}
		</div>
	</div>
{/if}
