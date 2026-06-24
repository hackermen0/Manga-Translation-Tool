<script lang="ts">
	import { editorState, historyManager } from '$lib';
	import {
		healPatch,
		applyHealResult,
		findAutoSourceOffset,
		type HealResult
	} from '$lib/stores/HealEngine';
	import type { RedrawingStroke } from '$lib/stores/EditorTypes';

	let { intrinsicWidth, intrinsicHeight } = $props<{
		intrinsicWidth: number;
		intrinsicHeight: number;
	}>();

	const BACKEND_URL = 'http://127.0.0.1:8000';

	// ─── Canvas References ──────────────────────────────────────────────────
	let containerDiv: HTMLDivElement;
	let displayCanvas = $state<HTMLCanvasElement | undefined>(undefined);
	let cursorCanvas = $state<HTMLCanvasElement | undefined>(undefined);

	// ─── Internal Buffers (not DOM-mounted) ─────────────────────────────────
	let originalPageCanvas: HTMLCanvasElement | null = null;
	let editOverlayCanvas: HTMLCanvasElement | null = null;
	let originalImageData: Uint8ClampedArray | null = null;
	let activeOverlayImageData: ImageData | null = null;

	// ─── Global Snapshot Tracking ───────────────────────────────────────────
	let pendingSnapshot: any = null;

	// ─── State ──────────────────────────────────────────────────────────────
	let isDrawing = $state(false);
	let cursorX = $state(0);
	let cursorY = $state(0);
	let showCursor = $state(false);
	let isReady = $state(false);
	let strokePoints: { x: number; y: number }[] = [];
	let sourceIndicatorX = $state(0);
	let sourceIndicatorY = $state(0);
	let showSourceIndicator = $state(false);

	// ─── Derived ────────────────────────────────────────────────────────────
	let isHealTool = $derived(editorState.activeRedrawingTool === 'heal');
	let isSessionActive = $derived(
		editorState.activeSession === 'redrawing' ||
			editorState.activeSession === 'typesetting' ||
			editorState.activeSession === 'quality'
	);
	let isActive = $derived(editorState.activeSession === 'redrawing' && isHealTool);

	// ─── Image Loading ──────────────────────────────────────────────────────

	let lastLoadedPageId: string | null = null;
	let lastLoadedUrl: string | null = null;

	$effect(() => {
		const page = editorState.activePage;
		if (!page || !isSessionActive) return;

		const pageId = page.pageId;
		const targetUrl = page.inpaintedUrl ?? page.originalUrl;

		if (pageId !== lastLoadedPageId || targetUrl !== lastLoadedUrl) {
			lastLoadedPageId = pageId;
			lastLoadedUrl = targetUrl;
			loadPageImage(targetUrl);
		}
	});

	function loadPageImage(imageUrl: string) {
		isReady = false;
		originalImageData = null;
		const img = new Image();
		img.crossOrigin = 'anonymous';
		img.onload = () => {
			const w = img.naturalWidth;
			const h = img.naturalHeight;

			originalPageCanvas = document.createElement('canvas');
			originalPageCanvas.width = w;
			originalPageCanvas.height = h;
			const origCtx = originalPageCanvas.getContext('2d')!;
			origCtx.drawImage(img, 0, 0);
			originalImageData = origCtx.getImageData(0, 0, w, h).data;

			editOverlayCanvas = document.createElement('canvas');
			editOverlayCanvas.width = w;
			editOverlayCanvas.height = h;
			const editCtx = editOverlayCanvas.getContext('2d')!;
			editCtx.drawImage(img, 0, 0);

			renderDisplay();
			isReady = true;
		};
		img.onerror = () => {
			console.error('HealingOverlay: Failed to load page image');
		};
		img.src = `${BACKEND_URL}${imageUrl}`;
	}

	// ─── Display Rendering ──────────────────────────────────────────────────

	function renderDisplay() {
		if (!displayCanvas || !editOverlayCanvas) return;

		const ctx = displayCanvas.getContext('2d')!;
		ctx.clearRect(0, 0, intrinsicWidth, intrinsicHeight);
		ctx.drawImage(editOverlayCanvas, 0, 0);
	}

	function resetCanvas() {
		if (!editOverlayCanvas || !originalPageCanvas) return;
		const editCtx = editOverlayCanvas.getContext('2d')!;
		editCtx.drawImage(originalPageCanvas, 0, 0);
	}

	function applyHealStroke(
		stroke: RedrawingStroke,
		originalData: Uint8ClampedArray,
		overlayImageData: ImageData
	) {
		if (!originalPageCanvas || !editOverlayCanvas) return;

		const w = originalPageCanvas.width;
		const h = originalPageCanvas.height;
		const radius = stroke.brushSize / 2;
		const hardness = stroke.hardness ?? 0.75;
		const sourceMode = stroke.sourceMode ?? 'auto';
		const sourceAnchor = stroke.sourceAnchor ?? null;

		const overlayData = overlayImageData.data;

		stroke.points.forEach((coords) => {
			let sourceX: number;
			let sourceY: number;

			if (sourceMode === 'manual' && sourceAnchor) {
				const firstPoint = stroke.points[0];
				const offsetX = sourceAnchor.x - firstPoint.x;
				const offsetY = sourceAnchor.y - firstPoint.y;
				sourceX = coords.x + offsetX;
				sourceY = coords.y + offsetY;
			} else {
				const autoSource = findAutoSourceOffset(
					originalData,
					Math.round(coords.x),
					Math.round(coords.y),
					Math.round(radius),
					w,
					h
				);
				sourceX = autoSource.sourceX;
				sourceY = autoSource.sourceY;
			}

			sourceX = Math.max(radius + 1, Math.min(w - radius - 1, sourceX));
			sourceY = Math.max(radius + 1, Math.min(h - radius - 1, sourceY));

			const result = healPatch(
				originalData,
				overlayData,
				sourceX,
				sourceY,
				coords.x,
				coords.y,
				Math.round(radius),
				hardness,
				w,
				h
			);

			if (result) {
				applyHealResult(overlayImageData.data, w, result);
			}
		});
	}

	let lastStrokesJson = '';

	$effect(() => {
		const page = editorState.activePage;
		if (!page || !isReady || !editOverlayCanvas || !originalPageCanvas || !originalImageData)
			return;

		const currentStrokesJson = JSON.stringify(page.redrawingStrokes);
		if (currentStrokesJson === lastStrokesJson) return;
		lastStrokesJson = currentStrokesJson;

		resetCanvas();

		const healStrokes = page.redrawingStrokes.filter((s) => s.type === 'heal');
		if (healStrokes.length > 0) {
			const editCtx = editOverlayCanvas.getContext('2d')!;
			const w = editOverlayCanvas.width;
			const h = editOverlayCanvas.height;
			const overlayImageData = editCtx.getImageData(0, 0, w, h);

			healStrokes.forEach((stroke) => {
				applyHealStroke(stroke, originalImageData!, overlayImageData);
			});

			editCtx.putImageData(overlayImageData, 0, 0);
		}

		renderDisplay();
	});

	// ─── Cursor HUD Rendering ───────────────────────────────────────────────

	function renderCursorHUD() {
		if (!cursorCanvas) return;

		const ctx = cursorCanvas.getContext('2d')!;
		ctx.clearRect(0, 0, intrinsicWidth, intrinsicHeight);

		if (!showCursor || !isActive) return;

		const r = editorState.brushSize / 2;
		const lineW = Math.max(1, intrinsicWidth * 0.001);

		ctx.beginPath();
		ctx.arc(cursorX, cursorY, r, 0, Math.PI * 2);
		ctx.strokeStyle = '#10b981';
		ctx.lineWidth = lineW;
		ctx.setLineDash([Math.max(2, intrinsicWidth * 0.003), Math.max(2, intrinsicWidth * 0.003)]);
		ctx.stroke();

		ctx.beginPath();
		ctx.arc(cursorX, cursorY, Math.max(1, intrinsicWidth * 0.0015), 0, Math.PI * 2);
		ctx.fillStyle = '#10b981';
		ctx.fill();

		const innerR = r * editorState.healBrushHardness;
		if (editorState.healBrushHardness < 0.95) {
			ctx.beginPath();
			ctx.arc(cursorX, cursorY, innerR, 0, Math.PI * 2);
			ctx.strokeStyle = 'rgba(16, 185, 129, 0.3)';
			ctx.lineWidth = lineW * 0.5;
			ctx.setLineDash([]);
			ctx.stroke();
		}

		ctx.setLineDash([]);

		if (showSourceIndicator && editorState.healSourceMode === 'manual') {
			const crossSize = r * 0.4;
			ctx.beginPath();
			ctx.arc(sourceIndicatorX, sourceIndicatorY, r, 0, Math.PI * 2);
			ctx.strokeStyle = '#f59e0b';
			ctx.lineWidth = lineW;
			ctx.setLineDash([Math.max(2, intrinsicWidth * 0.003), Math.max(2, intrinsicWidth * 0.003)]);
			ctx.stroke();
			ctx.setLineDash([]);

			ctx.beginPath();
			ctx.moveTo(sourceIndicatorX - crossSize, sourceIndicatorY);
			ctx.lineTo(sourceIndicatorX + crossSize, sourceIndicatorY);
			ctx.moveTo(sourceIndicatorX, sourceIndicatorY - crossSize);
			ctx.lineTo(sourceIndicatorX, sourceIndicatorY + crossSize);
			ctx.strokeStyle = '#f59e0b';
			ctx.lineWidth = lineW * 1.5;
			ctx.stroke();

			ctx.beginPath();
			ctx.moveTo(sourceIndicatorX, sourceIndicatorY);
			ctx.lineTo(cursorX, cursorY);
			ctx.strokeStyle = 'rgba(245, 158, 11, 0.4)';
			ctx.lineWidth = lineW;
			ctx.setLineDash([4, 4]);
			ctx.stroke();
			ctx.setLineDash([]);
		}
	}

	// ─── Coordinate Conversion ──────────────────────────────────────────────

	function getIntrinsicCoordinates(clientX: number, clientY: number): { x: number; y: number } {
		if (!containerDiv) return { x: 0, y: 0 };
		const rect = containerDiv.getBoundingClientRect();
		const scaleX = intrinsicWidth / rect.width;
		const scaleY = intrinsicHeight / rect.height;
		return {
			x: (clientX - rect.left) * scaleX,
			y: (clientY - rect.top) * scaleY
		};
	}

	// ─── Pointer Event Handlers ─────────────────────────────────────────────

	function handlePointerDown(e: PointerEvent) {
		if (!isActive || !isReady) return;
		if (e.target instanceof Element) e.target.setPointerCapture(e.pointerId);

		const coords = getIntrinsicCoordinates(e.clientX, e.clientY);

		if (e.ctrlKey) {
			editorState.healSourceMode = 'manual';
			editorState.healSourceAnchor = { x: coords.x, y: coords.y };
			sourceIndicatorX = coords.x;
			sourceIndicatorY = coords.y;
			showSourceIndicator = true;
			renderCursorHUD();
			return;
		}

		isDrawing = true;
		strokePoints = [coords];

		if (editOverlayCanvas) {
			const editCtx = editOverlayCanvas.getContext('2d')!;
			activeOverlayImageData = editCtx.getImageData(
				0,
				0,
				editOverlayCanvas.width,
				editOverlayCanvas.height
			);
		}

		pendingSnapshot = historyManager.captureSnapshot(editorState.activePageId!);
	}

	function handlePointerMove(e: PointerEvent) {
		if (!isActive) return;

		const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
		cursorX = coords.x;
		cursorY = coords.y;

		if (editorState.healSourceMode === 'manual' && editorState.healSourceAnchor) {
			showSourceIndicator = true;
			if (isDrawing && strokePoints.length > 0) {
				const firstPoint = strokePoints[0];
				const offsetX = editorState.healSourceAnchor.x - firstPoint.x;
				const offsetY = editorState.healSourceAnchor.y - firstPoint.y;
				sourceIndicatorX = coords.x + offsetX;
				sourceIndicatorY = coords.y + offsetY;
			} else {
				sourceIndicatorX = editorState.healSourceAnchor.x;
				sourceIndicatorY = editorState.healSourceAnchor.y;
			}
		}

		renderCursorHUD();

		if (!isDrawing) return;

		const lastPoint = strokePoints[strokePoints.length - 1];
		const dx = coords.x - lastPoint.x;
		const dy = coords.y - lastPoint.y;
		const dist = Math.sqrt(dx * dx + dy * dy);
		const stepSize = Math.max(editorState.brushSize * 0.25, 2);

		if (dist >= stepSize) {
			strokePoints.push(coords);
			applyHealAtPoint(coords.x, coords.y);
		}
	}

	function handlePointerUp(e: PointerEvent) {
		if (!isDrawing) return;
		if (e.target instanceof Element && e.target.hasPointerCapture(e.pointerId)) {
			e.target.releasePointerCapture(e.pointerId);
		}

		if (strokePoints.length > 0) {
			const lastCoord = getIntrinsicCoordinates(e.clientX, e.clientY);
			applyHealAtPoint(lastCoord.x, lastCoord.y);
		}

		isDrawing = false;
		if (strokePoints.length > 0 && editorState.activePage) {
			const newStroke = {
				points: strokePoints,
				brushSize: editorState.brushSize,
				brushColor: editorState.brushColor,
				type: 'heal' as const,
				hardness: editorState.healBrushHardness,
				sourceMode: editorState.healSourceMode,
				sourceAnchor: editorState.healSourceAnchor ? { ...editorState.healSourceAnchor } : null
			};
			editorState.activePage.redrawingStrokes.push(newStroke);

			if (pendingSnapshot) {
				historyManager.recordSnapshotChange(editorState.activePageId!, pendingSnapshot);
				pendingSnapshot = null;
			}

			lastStrokesJson = JSON.stringify(editorState.activePage.redrawingStrokes);

			editorState.saveRedrawingStrokes();
		}
		strokePoints = [];
		activeOverlayImageData = null;
	}

	// ─── Core Heal Application ──────────────────────────────────────────────

	function applyHealAtPoint(destX: number, destY: number) {
		if (!originalPageCanvas || !editOverlayCanvas) return;

		const editCtx = editOverlayCanvas.getContext('2d')!;

		const w = originalPageCanvas.width;
		const h = originalPageCanvas.height;
		const radius = editorState.brushSize / 2;

		let originalData = originalImageData;
		if (!originalData) {
			const origCtx = originalPageCanvas.getContext('2d')!;
			originalData = origCtx.getImageData(0, 0, w, h).data;
		}

		const overlayImageData = activeOverlayImageData ?? editCtx.getImageData(0, 0, w, h);
		const overlayData = overlayImageData.data;

		let sourceX: number;
		let sourceY: number;

		if (editorState.healSourceMode === 'manual' && editorState.healSourceAnchor) {
			if (strokePoints.length > 0) {
				const firstPoint = strokePoints[0];
				const offsetX = editorState.healSourceAnchor.x - firstPoint.x;
				const offsetY = editorState.healSourceAnchor.y - firstPoint.y;
				sourceX = destX + offsetX;
				sourceY = destY + offsetY;
			} else {
				sourceX = editorState.healSourceAnchor.x;
				sourceY = editorState.healSourceAnchor.y;
			}
		} else {
			const autoSource = findAutoSourceOffset(
				originalData,
				Math.round(destX),
				Math.round(destY),
				Math.round(radius),
				w,
				h
			);
			sourceX = autoSource.sourceX;
			sourceY = autoSource.sourceY;
		}

		sourceX = Math.max(radius + 1, Math.min(w - radius - 1, sourceX));
		sourceY = Math.max(radius + 1, Math.min(h - radius - 1, sourceY));

		const result = healPatch(
			originalData,
			overlayData,
			sourceX,
			sourceY,
			destX,
			destY,
			Math.round(radius),
			editorState.healBrushHardness,
			w,
			h
		);

		if (result) {
			applyHealResult(overlayImageData.data, w, result);
			editCtx.putImageData(overlayImageData, 0, 0);
			renderDisplay();
		}
	}

	function handlePointerEnter() {
		if (isActive) {
			showCursor = true;
		}
	}

	function handlePointerLeave() {
		showCursor = false;
		renderCursorHUD();
	}

	function handleKeyDown(e: KeyboardEvent) {
		if (!isActive) return;
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	bind:this={containerDiv}
	class="absolute top-0 left-0 z-39 h-full w-full"
	style="pointer-events: {isActive ? 'auto' : 'none'}; cursor: none;"
	onpointerdown={handlePointerDown}
	onpointermove={handlePointerMove}
	onpointerup={handlePointerUp}
	onpointerenter={handlePointerEnter}
	onpointerleave={handlePointerLeave}
>
	{#if isSessionActive && isReady}
		<canvas
			bind:this={displayCanvas}
			width={intrinsicWidth}
			height={intrinsicHeight}
			class="absolute top-0 left-0 h-full w-full"
			style="pointer-events: none; image-rendering: auto;"
		></canvas>
	{/if}

	{#if isActive}
		<canvas
			bind:this={cursorCanvas}
			width={intrinsicWidth}
			height={intrinsicHeight}
			class="absolute top-0 left-0 h-full w-full"
			style="pointer-events: none; image-rendering: auto;"
		></canvas>
	{/if}
</div>
