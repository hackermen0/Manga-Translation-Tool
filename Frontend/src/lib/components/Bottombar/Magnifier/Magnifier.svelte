<script lang="ts">
	import Display from './Display.svelte';
	import { Button } from '$lib';
	import { ZoomIn, ZoomOut } from '@lucide/svelte';
	import { zoomState } from '$lib';
</script>

<div class="flex flex-row items-center justify-center gap-4">
	<Button icon={ZoomOut} variant="ghost" onclick={() => zoomState.zoomOut()} />
	<div>
		<Display minZoom={zoomState.minZoom} maxZoom={zoomState.maxZoom} />
	</div>
	<Button icon={ZoomIn} variant="ghost" onclick={() => zoomState.zoomIn()} />
</div>
