<script lang="ts">
	import { editorState } from '$lib/stores/Editor.svelte';
	import type { RedrawingStroke } from '$lib/stores/Editor.svelte';

	let { intrinsicWidth, intrinsicHeight } = $props<{
		intrinsicWidth: number;
		intrinsicHeight: number;
	}>();

	let svgElement: SVGSVGElement;
	let isDrawing = $state(false);
	let currentStrokePoints = $state<{ x: number; y: number }[]>([]);

	let cursorX = $state(0);
	let cursorY = $state(0);
	let showCursor = $state(false);

	const BACKEND_URL = 'http://127.0.0.1:8000';

	let originalImageUrl = $derived.by(() => {
		if (!editorState.activePage) return '';
		return `${BACKEND_URL}${editorState.activePage.originalUrl}`;
	});

	let isDrawingTool = $derived(
		editorState.activeRedrawingTool === 'eraser' || editorState.activeRedrawingTool === 'restore'
	);

	let eraserStrokes = $derived(
		(editorState.activePage?.redrawingStrokes ?? []).filter(
			(s) => (s.type || 'eraser') === 'eraser'
		)
	);
	let restoreStrokes = $derived(
		(editorState.activePage?.redrawingStrokes ?? []).filter((s) => s.type === 'restore')
	);

	function getIntrinsicCoordinates(clientX: number, clientY: number) {
		const ctm = svgElement.getScreenCTM();
		if (!ctm) {
			const rect = svgElement.getBoundingClientRect();
			const rawX = clientX - rect.left;
			const rawY = clientY - rect.top;
			const scaleX = intrinsicWidth / rect.width;
			const scaleY = intrinsicHeight / rect.height;
			return { x: rawX * scaleX, y: rawY * scaleY };
		}
		const inverseCTM = ctm.inverse();
		const pt = new DOMPoint(clientX, clientY);
		const svgPt = pt.matrixTransform(inverseCTM);
		return { x: svgPt.x, y: svgPt.y };
	}

	function handlePointerDown(e: PointerEvent) {
		if (editorState.activeSession !== 'redrawing' || !isDrawingTool) return;
		if (e.target instanceof Element) e.target.setPointerCapture(e.pointerId);

		isDrawing = true;
		const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
		currentStrokePoints = [coords];
	}

	function handlePointerMove(e: PointerEvent) {
		if (editorState.activeSession === 'redrawing' && isDrawingTool) {
			const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
			cursorX = coords.x;
			cursorY = coords.y;
		}

		if (!isDrawing) return;
		const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
		currentStrokePoints = [...currentStrokePoints, coords];
	}

	function handlePointerUp(e: PointerEvent) {
		if (!isDrawing) return;
		if (e.target instanceof Element && e.target.hasPointerCapture(e.pointerId)) {
			e.target.releasePointerCapture(e.pointerId);
		}

		isDrawing = false;
		if (currentStrokePoints.length > 0 && editorState.activePage) {
			editorState.activePage.redrawingStrokes.push({
				points: currentStrokePoints,
				brushSize: editorState.brushSize,
				brushColor: editorState.brushColor,
				type: editorState.activeRedrawingTool as 'eraser' | 'restore'
			});
			editorState.saveRedrawingStrokes();
		}
		currentStrokePoints = [];
	}

	function handlePointerEnter() {
		if (editorState.activeSession === 'redrawing' && isDrawingTool) {
			showCursor = true;
		}
	}

	function handlePointerLeave() {
		showCursor = false;
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<svg
	bind:this={svgElement}
	viewBox="0 0 {intrinsicWidth} {intrinsicHeight}"
	class="absolute top-0 left-0 z-40 h-full w-full {editorState.activeSession === 'redrawing' &&
	isDrawingTool
		? 'pointer-events-auto'
		: 'pointer-events-none'}"
	style="cursor: none;"
	onpointerdown={handlePointerDown}
	onpointermove={handlePointerMove}
	onpointerup={handlePointerUp}
	onpointerenter={handlePointerEnter}
	onpointerleave={handlePointerLeave}
>
	<defs>
		<clipPath id="restore-clip">
			{#each restoreStrokes as stroke}
				{#if stroke.points.length > 0}
					<polyline
						points={stroke.points.map((p) => `${p.x},${p.y}`).join(' ')}
						fill="none"
						stroke="white"
						stroke-width={stroke.brushSize}
						stroke-linecap="round"
						stroke-linejoin="round"
					></polyline>
				{/if}
			{/each}
			{#if isDrawing && editorState.activeRedrawingTool === 'restore' && currentStrokePoints.length > 0}
				<polyline
					points={currentStrokePoints.map((p) => `${p.x},${p.y}`).join(' ')}
					fill="none"
					stroke="white"
					stroke-width={editorState.brushSize}
					stroke-linecap="round"
					stroke-linejoin="round"
				></polyline>
			{/if}
		</clipPath>
	</defs>

	{#each eraserStrokes as stroke}
		{#if stroke.points.length > 0}
			<polyline
				points={stroke.points.map((p) => `${p.x},${p.y}`).join(' ')}
				fill="none"
				stroke={stroke.brushColor || '#ffffff'}
				stroke-width={stroke.brushSize}
				stroke-linecap="round"
				stroke-linejoin="round"
			></polyline>
		{/if}
	{/each}

	{#if editorState.activeSession === 'redrawing' && isDrawing && editorState.activeRedrawingTool === 'eraser' && currentStrokePoints.length > 0}
		<polyline
			points={currentStrokePoints.map((p) => `${p.x},${p.y}`).join(' ')}
			fill="none"
			stroke={editorState.brushColor}
			stroke-width={editorState.brushSize}
			stroke-linecap="round"
			stroke-linejoin="round"
		></polyline>
	{/if}

	{#if restoreStrokes.length > 0 || (editorState.activeSession === 'redrawing' && isDrawing && editorState.activeRedrawingTool === 'restore')}
		<image
			href={originalImageUrl}
			x="0"
			y="0"
			width={intrinsicWidth}
			height={intrinsicHeight}
			clip-path="url(#restore-clip)"
			preserveAspectRatio="none"
		></image>
	{/if}

	{#if showCursor && editorState.activeSession === 'redrawing' && isDrawingTool}
		<circle
			cx={cursorX}
			cy={cursorY}
			r={editorState.brushSize / 2}
			fill="none"
			stroke={editorState.activeRedrawingTool === 'restore' ? '#3b82f6' : '#333333'}
			stroke-width={Math.max(1, intrinsicWidth * 0.001)}
			stroke-dasharray="{Math.max(2, intrinsicWidth * 0.003)} {Math.max(2, intrinsicWidth * 0.003)}"
			style="pointer-events: none;"
		></circle>
		<circle
			cx={cursorX}
			cy={cursorY}
			r={Math.max(1, intrinsicWidth * 0.0015)}
			fill={editorState.activeRedrawingTool === 'restore' ? '#3b82f6' : '#333333'}
			style="pointer-events: none;"
		></circle>
	{/if}
</svg>
