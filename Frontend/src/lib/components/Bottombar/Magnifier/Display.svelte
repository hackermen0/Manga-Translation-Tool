<script lang="ts">
	let { minZoom, maxZoom } = $props();
	import { zoomState } from '$lib';

	function handleInput(event: Event) {
		const target = event.target as HTMLInputElement;
		const value = parseInt(target.value) || 0;

		const clampedValue = Math.max(minZoom, Math.min(maxZoom, value));
		zoomState.setZoomLevel(clampedValue);

		if (clampedValue !== value) {
			target.value = clampedValue.toString();
		}
	}
</script>

<div class="flex w-full flex-row items-center justify-center gap-1">
	<input
		type="number"
		value={zoomState.zoomLevel}
		oninput={handleInput}
		class="border-primary-border h-7 w-16 rounded-lg border py-2 text-center ring-1 ring-accent"
		min={minZoom}
		max={maxZoom}
	/>
	<p class="text-slate-500">%</p>
</div>
