<script lang="ts">
	import { editorState, historyManager } from '$lib';
	import { DEFAULT_TYPESET_STYLE } from '$lib/stores/Editor.svelte';
	import type { TypesetStyle, MangaBubble } from '$lib/stores/Editor.svelte';
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
		if (handleBubbleAction(e, bubbleId)) return;

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
	let hoveredBubbleId = $state<number | null>(null);
	let activeVertexBubbleId = $state<number | null>(null);
	let activePointIndex = $state<number | null>(null);
	let vertexDragStartX = 0;
	let vertexDragStartY = 0;

	function handleBubbleAction(e: PointerEvent, bubbleId: number) {
		e.stopPropagation();
		e.preventDefault();
		editorState.activeBubbleId = bubbleId;

		if (editorState.activeTypesettingTool === 'delete') {
			historyManager.recordState(editorState.activePageId!);
			editorState.activePage!.bubbles = editorState.activePage!.bubbles.filter(
				(b) => b.id !== bubbleId
			);
			if (editorState.activeBubbleId === bubbleId) {
				editorState.activeBubbleId = editorState.activePage!.bubbles[0]?.id ?? null;
			}
			editorState.saveBubbles();
			editorState.saveTypesetting();
			return true;
		}

		return false;
	}

	function handleBubbleClick(e: PointerEvent, bubbleId: number) {
		handleBubbleAction(e, bubbleId);
	}
	let isDrawing = $state(false);
	let drawStartX = $state(0);
	let drawStartY = $state(0);
	let drawCurrentX = $state(0);
	let drawCurrentY = $state(0);

	function handleBubbleDblClick(e: MouseEvent, bubbleId: number) {
		e.stopPropagation();
		e.preventDefault();
		editorState.activeBubbleId = bubbleId;
	}

	function handleVertexPointerDown(e: PointerEvent, bubbleId: number, pointIndex: number) {
		if (editorState.activeTypesettingTool !== 'edit') return;
		e.stopPropagation();
		e.preventDefault();

		pendingSnapshot = historyManager.captureSnapshot(editorState.activePageId!);

		editorState.activeBubbleId = bubbleId;

		activeVertexBubbleId = bubbleId;
		activePointIndex = pointIndex;

		const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
		vertexDragStartX = coords.x;
		vertexDragStartY = coords.y;

		window.addEventListener('pointermove', handleVertexPointerMove);
		window.addEventListener('pointerup', handleVertexPointerUp);
	}

	function handleVertexPointerMove(e: PointerEvent) {
		if (activeVertexBubbleId === null || activePointIndex === null || !editorState.activePage) return;
		e.preventDefault();

		const bubble = editorState.activePage.bubbles.find((b) => b.id === activeVertexBubbleId);
		if (!bubble) return;

		const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
		bubble.points[activePointIndex].x = coords.x;
		bubble.points[activePointIndex].y = coords.y;
	}

	function handleVertexPointerUp(e: PointerEvent) {
		if (activeVertexBubbleId === null) return;

		activeVertexBubbleId = null;
		activePointIndex = null;

		window.removeEventListener('pointermove', handleVertexPointerMove);
		window.removeEventListener('pointerup', handleVertexPointerUp);

		if (pendingSnapshot) {
			historyManager.recordSnapshotChange(editorState.activePageId!, pendingSnapshot);
			pendingSnapshot = null;
		}

		editorState.saveBubbles();
		editorState.saveTypesetting();
	}

	function handleSvgPointerDown(e: PointerEvent) {
		if (!interactive || editorState.activeTypesettingTool !== 'text' || !editorState.activePage) return;
		e.preventDefault();

		const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
		isDrawing = true;
		drawStartX = coords.x;
		drawStartY = coords.y;
		drawCurrentX = coords.x;
		drawCurrentY = coords.y;

		window.addEventListener('pointermove', handleSvgPointerMove);
		window.addEventListener('pointerup', handleSvgPointerUp);
	}

	function handleSvgPointerMove(e: PointerEvent) {
		if (!isDrawing) return;
		const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
		drawCurrentX = coords.x;
		drawCurrentY = coords.y;
	}

	function handleSvgPointerUp(e: PointerEvent) {
		if (!isDrawing) return;
		isDrawing = false;
		window.removeEventListener('pointermove', handleSvgPointerMove);
		window.removeEventListener('pointerup', handleSvgPointerUp);

		if (!editorState.activePage) return;

		let x1 = Math.min(drawStartX, drawCurrentX);
		let y1 = Math.min(drawStartY, drawCurrentY);
		let x2 = Math.max(drawStartX, drawCurrentX);
		let y2 = Math.max(drawStartY, drawCurrentY);
		let w = x2 - x1;
		let h = y2 - y1;

		// If click instead of drag, use default size
		if (w < 10 && h < 10) {
			w = 150;
			h = 80;
			x1 = Math.max(0, Math.min(drawStartX - w / 2, intrinsicWidth - w));
			y1 = Math.max(0, Math.min(drawStartY - h / 2, intrinsicHeight - h));
			x2 = x1 + w;
			y2 = y1 + h;
		}

		const points = [
			{ x: x1, y: y1 },
			{ x: x2, y: y1 },
			{ x: x2, y: y2 },
			{ x: x1, y: y2 }
		];

		historyManager.recordState(editorState.activePageId!);
		const page = editorState.activePage;
		const newId = Math.max(...page.bubbles.map((b) => b.id), 0) + 1;

		const newBubble: MangaBubble = {
			id: newId,
			points,
			ja_text: '',
			en_text: '',
			is_sfx: false,
			typeset: { ...DEFAULT_TYPESET_STYLE }
		};

		page.bubbles.push(newBubble);
		editorState.activeBubbleId = newId;

		// Switch tool back to select so they can interact with the new bubble
		editorState.setTypesettingTool('select');
		editorState.saveBubbles();
		editorState.saveTypesetting();
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<svg
	bind:this={svgElement}
	data-typesetting-overlay-interactive={interactive}
	viewBox="0 0 {intrinsicWidth} {intrinsicHeight}"
	class="typesetting-overlay-svg {interactive ? 'pointer-events-auto' : 'pointer-events-none'} absolute top-0 left-0 z-50 h-full w-full"
	style={interactive && editorState.activeTypesettingTool === 'text' ? 'cursor: crosshair;' : ''}
	onpointerdown={handleSvgPointerDown}
>
	{#if isDrawing}
		{@const px = Math.min(drawStartX, drawCurrentX)}
		{@const py = Math.min(drawStartY, drawCurrentY)}
		{@const pw = Math.abs(drawCurrentX - drawStartX)}
		{@const ph = Math.abs(drawCurrentY - drawStartY)}
		<rect
			x={px}
			y={py}
			width={pw}
			height={ph}
			fill="rgba(99, 102, 241, 0.1)"
			stroke="#6366f1"
			stroke-width={intrinsicWidth * 0.002}
			stroke-dasharray={`${intrinsicWidth * 0.005}`}
			rx="4"
		></rect>
	{/if}

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
					fill={interactive && editorState.activeTypesettingTool === 'delete' && hoveredBubbleId === bubble.id
						? 'rgba(239, 68, 68, 0.15)'
						: (isSelected && interactive ? 'rgba(99, 102, 241, 0.08)' : 'transparent')}
					stroke={interactive && editorState.activeTypesettingTool === 'delete' && hoveredBubbleId === bubble.id
						? '#ef4444'
						: (isSelected && interactive ? '#6366f1' : 'rgba(156, 163, 175, 0.4)')}
					stroke-width={intrinsicWidth * (isSelected && interactive ? 0.002 : 0.0012)}
					stroke-dasharray={isSelected && interactive ? 'none' : `${intrinsicWidth * 0.005}`}
					class="{interactive ? (editorState.activeTypesettingTool === 'delete' ? 'cursor-pointer hover:fill-red-200/30' : (editorState.activeTypesettingTool === 'edit' ? 'cursor-default' : 'cursor-pointer')) : ''} transition-colors duration-150"
					onpointerdown={interactive ? (e) => handleBubbleClick(e, bubble.id) : null}
					ondblclick={interactive ? (e) => handleBubbleDblClick(e, bubble.id) : null}
					onpointerenter={() => {
						if (interactive) hoveredBubbleId = bubble.id;
					}}
					onpointerleave={() => {
						if (interactive) hoveredBubbleId = null;
					}}
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
								cursor: {interactive 
									? (editorState.activeTypesettingTool === 'drag' 
										? 'move' 
										: (editorState.activeTypesettingTool === 'edit' 
											? 'default' 
											: (editorState.activeTypesettingTool === 'delete' 
												? 'pointer' 
												: 'pointer'))) 
									: 'default'};
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
							ondblclick={interactive ? (e) => handleBubbleDblClick(e, bubble.id) : null}
							onpointerenter={() => {
								if (interactive) hoveredBubbleId = bubble.id;
							}}
							onpointerleave={() => {
								if (interactive) hoveredBubbleId = null;
							}}
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
									-webkit-text-stroke: {style.outline ? `${style.outlineWidth ?? 2}px ${style.outlineColor ?? '#ffffff'}` : 'none'};
									paint-order: stroke fill;
								"
							>
								{bubble.en_text}
							</div>
						</div>
					</foreignObject>
				{/if}

				<!-- Polygon edit handles -->
				{#if interactive && editorState.activeTypesettingTool === 'edit' && isSelected}
					{#each bubble.points as point, i}
						<circle
							cx={point.x}
							cy={point.y}
							r={intrinsicWidth * 0.004}
							fill="white"
							stroke="#6366f1"
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
