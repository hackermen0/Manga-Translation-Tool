<script lang="ts">
	import { editorState, historyManager } from '$lib';
	import { zoomState } from '$lib/stores/Zoom.svelte';

	let { intrinsicWidth, intrinsicHeight } = $props<{
		intrinsicWidth: number;
		intrinsicHeight: number;
	}>();

	let activeBubbleId = $state<number | null>(null);
	let activePointIndex = $state<number | null>(null);
	let isDraggingBody = $state<boolean>(false);
	let pendingSnapshot: any = null;

	let startX = 0;
	let startY = 0;
	let initialPoints: { x: number; y: number }[] = [];

	let svgElement: SVGSVGElement;

	let draftPoints = $state<{ x: number; y: number }[]>([]);

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

	function handleSvgClick(e: MouseEvent) {
		if (editorState.activeSession !== 'detection' || editorState.activeDetectionTool !== 'create')
			return;
		const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
		draftPoints = [...draftPoints, coords];
	}

	function handleSvgDoubleClick(e: MouseEvent) {
		if (
			editorState.activeSession !== 'detection' ||
			editorState.activeDetectionTool !== 'create' ||
			draftPoints.length < 3
		)
			return;

		historyManager.recordState(editorState.activePageId!);
		const newId = Math.max(0, ...editorState.activePage!.bubbles.map((b) => b.id)) + 1;
		editorState.activePage!.bubbles.push({
			id: newId,
			points: [...draftPoints],
			ja_text: '',
			en_text: ''
		});

		draftPoints = [];
		editorState.saveBubbles();
	}

	function handleVertexPointerDown(e: PointerEvent, bubbleId: number, pointIndex: number) {
		if (editorState.activeDetectionTool !== 'edit') return;
		e.stopPropagation();
		e.preventDefault();

		pendingSnapshot = historyManager.captureSnapshot(editorState.activePageId!);

		editorState.activeBubbleId = bubbleId;

		activeBubbleId = bubbleId;
		activePointIndex = pointIndex;
		isDraggingBody = false;

		startX = e.clientX;
		startY = e.clientY;

		window.addEventListener('pointermove', handlePointerMove);
		window.addEventListener('pointerup', handlePointerUp);
	}

	function handleBodyPointerDown(e: PointerEvent, bubbleId: number) {
		e.stopPropagation();
		e.preventDefault();

		editorState.activeBubbleId = bubbleId;

		if (editorState.activeDetectionTool === 'delete') {
			historyManager.recordState(editorState.activePageId!);
			editorState.activePage!.bubbles = editorState.activePage!.bubbles.filter(
				(b) => b.id !== bubbleId
			);
			editorState.saveBubbles();
			return;
		}

		if (editorState.activeDetectionTool !== 'drag') return;

		pendingSnapshot = historyManager.captureSnapshot(editorState.activePageId!);

		if (e.target instanceof Element) e.target.setPointerCapture(e.pointerId);

		activeBubbleId = bubbleId;
		isDraggingBody = true;
		activePointIndex = null;

		startX = e.clientX;
		startY = e.clientY;

		window.addEventListener('pointermove', handlePointerMove);
		window.addEventListener('pointerup', handlePointerUp);
	}

	function handlePointerMove(e: PointerEvent) {
		if (activeBubbleId === null || !editorState.activePage) return;
		e.preventDefault();

		const bubbleIndex = editorState.activePage.bubbles.findIndex((b) => b.id === activeBubbleId);
		if (bubbleIndex === -1) return;

		const bubble = editorState.activePage.bubbles[bubbleIndex];

		if (isDraggingBody) {
			const currentCoords = getIntrinsicCoordinates(e.clientX, e.clientY);
			const previousCoords = getIntrinsicCoordinates(startX, startY);

			const dx = currentCoords.x - previousCoords.x;
			const dy = currentCoords.y - previousCoords.y;

			startX = e.clientX;
			startY = e.clientY;

			for (let i = 0; i < bubble.points.length; i++) {
				const currentX = Number(bubble.points[i].x) || 0;
				const currentY = Number(bubble.points[i].y) || 0;
				bubble.points[i].x = currentX + dx;
				bubble.points[i].y = currentY + dy;
			}
		} else if (activePointIndex !== null) {
			const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
			bubble.points[activePointIndex].x = coords.x;
			bubble.points[activePointIndex].y = coords.y;
		}
	}

	function handlePointerUp(e: PointerEvent) {
		if (activeBubbleId === null) return;

		if (e.target instanceof Element && e.target.hasPointerCapture(e.pointerId))
			e.target.releasePointerCapture(e.pointerId);

		activeBubbleId = null;
		activePointIndex = null;
		isDraggingBody = false;

		window.removeEventListener('pointermove', handlePointerMove);
		window.removeEventListener('pointerup', handlePointerUp);

		if (pendingSnapshot) {
			historyManager.recordSnapshotChange(editorState.activePageId!, pendingSnapshot);
			pendingSnapshot = null;
		}

		editorState.saveBubbles();
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<svg
	bind:this={svgElement}
	viewBox="0 0 {intrinsicWidth} {intrinsicHeight}"
	class="absolute top-0 left-0 z-50 h-full w-full {editorState.activeSession === 'detection' ||
	editorState.activeSession === 'translation'
		? 'pointer-events-auto'
		: 'pointer-events-none'}"
	onclick={handleSvgClick}
	ondblclick={handleSvgDoubleClick}
>
	{#if editorState.activeSession === 'detection' && editorState.activeDetectionTool === 'create' && draftPoints.length > 0}
		<polyline
			points={draftPoints.map((p) => `${p.x},${p.y}`).join(' ')}
			fill="rgba(255, 183, 150, 0.4)"
			stroke="#22c55e"
			stroke-width={intrinsicWidth * 0.0025}
			stroke-dasharray="4"
		></polyline>
		{#each draftPoints as point}
			<circle
				cx={point.x}
				cy={point.y}
				r={intrinsicWidth * 0.004}
				fill="white"
				stroke="#22c55e"
				stroke-width="2"
			></circle>
		{/each}
	{/if}

	{#if editorState.activePage?.bubbles}
		{#each editorState.activePage.bubbles as bubble (bubble.id)}
			{@const pointsString = bubble.points.map((p) => `${p.x},${p.y}`).join(' ')}
			{@const isSelected = editorState.activeBubbleId === bubble.id}
			{@const isHovered = activeBubbleId === bubble.id}
			{@const showDeleteHighlight =
				editorState.activeSession === 'detection' &&
				editorState.activeDetectionTool === 'delete' &&
				isHovered}

			<g>
				<polygon
					points={pointsString}
					fill={showDeleteHighlight
						? 'rgba(239, 68, 68, 0.3)'
						: isSelected
							? 'rgba(34, 197, 94, 0.3)'
							: isHovered
								? 'rgba(255, 183, 150, 0.4)'
								: 'rgba(255, 183, 150, 0.2)'}
					stroke={showDeleteHighlight
						? '#ef4444'
						: isSelected
							? '#22c55e'
							: isHovered
								? '#f97316'
								: 'rgba(34, 197, 94, 0.6)'}
					stroke-width={intrinsicWidth * (isSelected ? 0.0035 : 0.0025)}
					class="transition-colors duration-150 {editorState.activeSession === 'translation'
						? 'cursor-pointer hover:fill-green-100/30'
						: editorState.activeDetectionTool === 'drag'
							? 'cursor-move'
							: editorState.activeDetectionTool === 'delete'
								? 'cursor-pointer hover:fill-red-200 hover:stroke-red-500'
								: editorState.activeDetectionTool === 'edit'
									? 'cursor-pointer'
									: ''}"
					onpointerdown={(e) => {
						if (editorState.activeSession === 'translation') {
							e.stopPropagation();
							e.preventDefault();
							editorState.activeBubbleId = bubble.id;
						} else {
							e.preventDefault();
							handleBodyPointerDown(e, bubble.id);
						}
					}}
					onpointerenter={() => {
						if (!isDraggingBody && activePointIndex === null) activeBubbleId = bubble.id;
					}}
					onpointerleave={() => {
						if (!isDraggingBody && activePointIndex === null) activeBubbleId = null;
					}}
				></polygon>

				{#if editorState.activeSession === 'detection' && editorState.activeDetectionTool === 'edit' && isSelected}
					{#each bubble.points as point, i}
						<circle
						cx={point.x}
						cy={point.y}
						r={intrinsicWidth * 0.004}
						fill="white"
						stroke="#22c55e"
						stroke-width="2"
						class="cursor-crosshair transition-transform hover:scale-150"
						style="transform-origin: {point.x}px {point.y}px;"
						onpointerdown={(e) => handleVertexPointerDown(e, bubble.id, i)}
					></circle>
					{/each}
				{/if}
			</g>
		{/each}
	{/if}
</svg>
