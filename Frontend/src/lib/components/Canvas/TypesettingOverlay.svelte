<script lang="ts">
	import { editorState, historyManager } from '$lib';
	import { DEFAULT_TYPESET_STYLE } from '$lib/stores/Editor.svelte';
	import type { TypesetStyle } from '$lib/stores/Editor.svelte';
	let { intrinsicWidth, intrinsicHeight, interactive = true } = $props<{
		intrinsicWidth: number;
		intrinsicHeight: number;
		interactive?: boolean;
	}>();
	let svgElement: SVGSVGElement;
	let pendingSnapshot: any = null;

	// Auto-fit: calculate max font size that fits text inside a bounding box
	function autoFitFontSize(
		text: string,
		boxWidth: number,
		boxHeight: number,
		style: TypesetStyle
	): number {
		if (!text.trim() || boxWidth <= 0 || boxHeight <= 0) return 12;
		const canvas = document.createElement('canvas');
		const ctx = canvas.getContext('2d')!;
		const padding = Math.min(boxWidth, boxHeight) * 0.1;
		const availW = boxWidth - padding * 2;
		const availH = boxHeight - padding * 2;
		if (availW <= 0 || availH <= 0) return 8;

		const isVertical = style.writingMode === 'vertical';
		const limitLength = isVertical ? availH : availW;
		const limitThickness = isVertical ? availW : availH;

		let lo = 6;
		let hi = Math.min(boxWidth, boxHeight);
		let bestSize = lo;
		for (let iter = 0; iter < 20; iter++) {
			const mid = Math.floor((lo + hi) / 2);
			if (mid <= lo) break;
			const fontStr = `${style.fontStyle === 'italic' ? 'italic ' : ''}${style.fontWeight === 'bold' ? 'bold ' : ''}${mid}px "${style.fontFamily}", sans-serif`;
			ctx.font = fontStr;
			// Word-wrap the text
			const words = text.split(/\s+/);
			const lines: string[] = [];
			let currentLine = '';
			for (const word of words) {
				const testLine = currentLine ? `${currentLine} ${word}` : word;
				const metrics = ctx.measureText(testLine);
				if (metrics.width > limitLength && currentLine) {
					lines.push(currentLine);
					currentLine = word;
				} else {
					currentLine = testLine;
				}
			}
			if (currentLine) lines.push(currentLine);
			const totalThickness = lines.length * mid * style.lineHeight;
			if (totalThickness <= limitThickness && lines.every((l) => ctx.measureText(l).width <= limitLength)) {
				bestSize = mid;
				lo = mid;
			} else {
				hi = mid;
			}
		}
		return bestSize;
	}
	// Compute bounding box from polygon points
	function getBBox(points: { x: number; y: number }[]) {
		if (!points || points.length === 0) return { x: 0, y: 0, width: 0, height: 0, cx: 0, cy: 0 };
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
			height: maxY - minY,
			cx: (minX + maxX) / 2,
			cy: (minY + maxY) / 2
		};
	}
	// Dragging state
	let dragBubbleId: number | null = $state(null);
	let dragStartX = 0;
	let dragStartY = 0;
	let dragStartOffsetX = 0;
	let dragStartOffsetY = 0;
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
	function handleTextPointerDown(e: PointerEvent, bubbleId: number) {
		e.stopPropagation();
		e.preventDefault();
		editorState.activeBubbleId = bubbleId;

		if (editorState.activeTypesettingTool !== 'drag') return;

		const bubble = editorState.activePage?.bubbles.find((b) => b.id === bubbleId);
		if (!bubble) return;

		pendingSnapshot = historyManager.captureSnapshot(editorState.activePageId!);

		if (!bubble.typeset) {
			bubble.typeset = { ...DEFAULT_TYPESET_STYLE };
		}

		dragBubbleId = bubbleId;
		const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
		dragStartX = coords.x;
		dragStartY = coords.y;
		dragStartOffsetX = bubble.typeset.offsetX ?? 0;
		dragStartOffsetY = bubble.typeset.offsetY ?? 0;
		window.addEventListener('pointermove', handleDragMove);
		window.addEventListener('pointerup', handleDragUp);
	}
	function handleDragMove(e: PointerEvent) {
		if (dragBubbleId === null || !editorState.activePage) return;
		e.preventDefault();
		const bubble = editorState.activePage.bubbles.find((b) => b.id === dragBubbleId);
		if (!bubble || !bubble.typeset) return;
		const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
		bubble.typeset.offsetX = dragStartOffsetX + (coords.x - dragStartX);
		bubble.typeset.offsetY = dragStartOffsetY + (coords.y - dragStartY);
	}
	function handleDragUp() {
		dragBubbleId = null;
		window.removeEventListener('pointermove', handleDragMove);
		window.removeEventListener('pointerup', handleDragUp);
		if (pendingSnapshot) {
			historyManager.recordSnapshotChange(editorState.activePageId!, pendingSnapshot);
			pendingSnapshot = null;
		}
		editorState.saveTypesetting();
	}
	function handleBubbleClick(e: PointerEvent, bubbleId: number) {
		e.stopPropagation();
		e.preventDefault();
		editorState.activeBubbleId = bubbleId;
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<svg
	bind:this={svgElement}
	data-typesetting-overlay-interactive={interactive}
	viewBox="0 0 {intrinsicWidth} {intrinsicHeight}"
	class="typesetting-overlay-svg {interactive ? 'pointer-events-auto' : 'pointer-events-none'} absolute top-0 left-0 z-50 h-full w-full"
>
	{#if editorState.activePage?.bubbles}
		{#each editorState.activePage.bubbles as bubble (bubble.id)}
			{@const bbox = getBBox(bubble.points)}
			{@const style = bubble.typeset ?? DEFAULT_TYPESET_STYLE}
			{@const isSelected = editorState.activeBubbleId === bubble.id}
			{@const pointsString = bubble.points.map((p) => `${p.x},${p.y}`).join(' ')}
			{@const computedFontSize = style.autoFit
				? autoFitFontSize(bubble.en_text, bbox.width, bbox.height, style)
				: style.fontSize}
			{@const padding = Math.min(bbox.width, bbox.height) * 0.1}
			<g>
				<!-- Bubble boundary outline -->
				<polygon
					points={pointsString}
					fill={isSelected && interactive ? 'rgba(99, 102, 241, 0.08)' : 'transparent'}
					stroke={isSelected && interactive ? '#6366f1' : 'rgba(156, 163, 175, 0.4)'}
					stroke-width={intrinsicWidth * (isSelected && interactive ? 0.002 : 0.0012)}
					stroke-dasharray={isSelected && interactive ? 'none' : `${intrinsicWidth * 0.005}`}
					class="{interactive ? 'cursor-pointer' : ''} transition-colors duration-150"
					onpointerdown={interactive ? (e) => handleBubbleClick(e, bubble.id) : null}
				></polygon>
				<!-- Text rendered inside the bubble via foreignObject -->
				{#if bubble.en_text?.trim()}
					<foreignObject 
						x={bbox.x + (style.offsetX ?? 0)} 
						y={bbox.y + (style.offsetY ?? 0)} 
						width={bbox.width} 
						height={bbox.height}
					>
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<div
							class="typeset-text-container"
							style="
								width: 100%;
								height: 100%;
								display: flex;
								align-items: center;
								justify-content: center;
								overflow: hidden;
								pointer-events: {interactive ? 'auto' : 'none'};
								cursor: {interactive ? (editorState.activeTypesettingTool === 'drag' ? 'move' : 'pointer') : 'default'};
								padding: {padding}px;
								box-sizing: border-box;
								border: {editorState.activeTypesettingTool === 'drag' 
									? (isSelected ? '1.5px dashed #6366f1' : '1px dashed rgba(156, 163, 175, 0.5)') 
									: '1px dashed transparent'};
								border-radius: 4px;
								background-color: {isSelected && editorState.activeTypesettingTool === 'drag' ? 'rgba(99, 102, 241, 0.04)' : 'transparent'};
								transition: border-color 0.15s, background-color 0.15s;
							"
							onpointerdown={interactive ? (e) => handleTextPointerDown(e, bubble.id) : null}
						>
							<div
								class="typeset-text"
								style="
									font-family: '{style.fontFamily}', 'Comic Neue', 'Comic Sans MS', sans-serif;
									font-size: {computedFontSize}px;
									font-weight: {style.fontWeight};
									font-style: {style.fontStyle ?? 'normal'};
									writing-mode: {style.writingMode === 'vertical' ? 'vertical-rl' : 'horizontal-tb'};
									text-orientation: {style.writingMode === 'vertical' ? 'upright' : 'mixed'};
									color: {style.fontColor};
									text-align: {style.textAlign};
									line-height: {style.lineHeight};
									letter-spacing: {style.letterSpacing}px;
									word-break: break-word;
									overflow-wrap: break-word;
									white-space: pre-wrap;
									user-select: none;
									width: 100%;
									text-transform: uppercase;
									text-shadow: {style.outline ? `-1px -1px 0 ${style.outlineColor ?? '#ffffff'}, 1px -1px 0 ${style.outlineColor ?? '#ffffff'}, -1px 1px 0 ${style.outlineColor ?? '#ffffff'}, 1px 1px 0 ${style.outlineColor ?? '#ffffff'}, 0 0 4px ${style.outlineColor ?? '#ffffff'}, 0 0 4px ${style.outlineColor ?? '#ffffff'}` : 'none'};
								"
							>
								{bubble.en_text}
							</div>
						</div>
					</foreignObject>
				{/if}
			</g>
		{/each}
	{/if}
</svg>
