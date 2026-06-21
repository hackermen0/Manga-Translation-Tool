<script lang="ts">
	import { editorState } from '$lib';
	import {
		healPatch,
		applyHealResult,
		findAutoSourceOffset,
		type HealResult
	} from '$lib/stores/HealEngine';
	import { onMount, tick } from 'svelte';

	let { intrinsicWidth, intrinsicHeight } = $props<{
		intrinsicWidth: number;
		intrinsicHeight: number;
	}>();

	const BACKEND_URL = 'http://127.0.0.1:8000';

	// ─── Canvas References ──────────────────────────────────────────────────
	let containerDiv: HTMLDivElement;
	let displayCanvas = $state<HTMLCanvasElement | undefined>(undefined); // Shows the composited result
	let cursorCanvas = $state<HTMLCanvasElement | undefined>(undefined); // Real-time brush HUD

	// ─── Internal Buffers (not DOM-mounted) ─────────────────────────────────
	let originalPageCanvas: HTMLCanvasElement | null = null; // Immutable background
	let editOverlayCanvas: HTMLCanvasElement | null = null; // Dynamic edit layer

	// ─── Undo Stack ─────────────────────────────────────────────────────────
	let undoStack: ImageData[] = [];
	const MAX_UNDO = 30;

	// ─── State ──────────────────────────────────────────────────────────────
	let isDrawing = $state(false);
	let cursorX = $state(0);
	let cursorY = $state(0);
	let showCursor = $state(false);
	let isReady = $state(false);
	let strokePoints: { x: number; y: number }[] = [];

	// Source indicator for manual mode
	let sourceIndicatorX = $state(0);
	let sourceIndicatorY = $state(0);
	let showSourceIndicator = $state(false);

	// ─── Derived ────────────────────────────────────────────────────────────
	let isHealTool = $derived(editorState.activeRedrawingTool === 'heal');
	let isActive = $derived(
		(editorState.activeSession === 'redrawing') && isHealTool
	);

	// ─── Image Loading ──────────────────────────────────────────────────────

	let lastLoadedPageId: string | null = null;

	$effect(() => {
		const page = editorState.activePage;
		if (!page || !isActive) return;

		const pageId = page.pageId;
		const inpaintedUrl = page.inpaintedUrl;
		const originalUrl = page.originalUrl;

		// Reload when page changes
		if (pageId !== lastLoadedPageId) {
			lastLoadedPageId = pageId;
			loadPageImage(inpaintedUrl ?? originalUrl);
		}
	});

	function loadPageImage(imageUrl: string) {
		isReady = false;
		const img = new Image();
		img.crossOrigin = 'anonymous';
		img.onload = () => {
			const w = img.naturalWidth;
			const h = img.naturalHeight;

			// Create immutable original buffer
			originalPageCanvas = document.createElement('canvas');
			originalPageCanvas.width = w;
			originalPageCanvas.height = h;
			const origCtx = originalPageCanvas.getContext('2d')!;
			origCtx.drawImage(img, 0, 0);

			// Create dynamic edit overlay (starts as a copy of the original)
			editOverlayCanvas = document.createElement('canvas');
			editOverlayCanvas.width = w;
			editOverlayCanvas.height = h;
			const editCtx = editOverlayCanvas.getContext('2d')!;
			editCtx.drawImage(img, 0, 0);

			// Clear undo stack for new page
			undoStack = [];

			// Render initial display
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

	// ─── Cursor HUD Rendering ───────────────────────────────────────────────

	function renderCursorHUD() {
		if (!cursorCanvas) return;

		const ctx = cursorCanvas.getContext('2d')!;
		ctx.clearRect(0, 0, intrinsicWidth, intrinsicHeight);

		if (!showCursor || !isActive) return;

		const r = editorState.brushSize / 2;
		const lineW = Math.max(1, intrinsicWidth * 0.001);

		// Destination brush circle
		ctx.beginPath();
		ctx.arc(cursorX, cursorY, r, 0, Math.PI * 2);
		ctx.strokeStyle = '#10b981'; // emerald-500
		ctx.lineWidth = lineW;
		ctx.setLineDash([Math.max(2, intrinsicWidth * 0.003), Math.max(2, intrinsicWidth * 0.003)]);
		ctx.stroke();

		// Center dot
		ctx.beginPath();
		ctx.arc(cursorX, cursorY, Math.max(1, intrinsicWidth * 0.0015), 0, Math.PI * 2);
		ctx.fillStyle = '#10b981';
		ctx.fill();

		// Hardness inner ring
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

		// Source indicator in manual mode
		if (showSourceIndicator && editorState.healSourceMode === 'manual') {
			// Source crosshair
			const crossSize = r * 0.4;
			ctx.beginPath();
			ctx.arc(sourceIndicatorX, sourceIndicatorY, r, 0, Math.PI * 2);
			ctx.strokeStyle = '#f59e0b'; // amber-500
			ctx.lineWidth = lineW;
			ctx.setLineDash([Math.max(2, intrinsicWidth * 0.003), Math.max(2, intrinsicWidth * 0.003)]);
			ctx.stroke();
			ctx.setLineDash([]);

			// Cross inside source circle
			ctx.beginPath();
			ctx.moveTo(sourceIndicatorX - crossSize, sourceIndicatorY);
			ctx.lineTo(sourceIndicatorX + crossSize, sourceIndicatorY);
			ctx.moveTo(sourceIndicatorX, sourceIndicatorY - crossSize);
			ctx.lineTo(sourceIndicatorX, sourceIndicatorY + crossSize);
			ctx.strokeStyle = '#f59e0b';
			ctx.lineWidth = lineW * 1.5;
			ctx.stroke();

			// Connecting line from source to dest
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

	// ─── Undo Support ───────────────────────────────────────────────────────

	function pushUndoSnapshot() {
		if (!editOverlayCanvas) return;
		const ctx = editOverlayCanvas.getContext('2d')!;
		const snapshot = ctx.getImageData(0, 0, editOverlayCanvas.width, editOverlayCanvas.height);
		undoStack.push(snapshot);
		if (undoStack.length > MAX_UNDO) {
			undoStack.shift();
		}
	}

	export function undoLastHeal(): boolean {
		if (undoStack.length === 0 || !editOverlayCanvas) return false;
		const snapshot = undoStack.pop()!;
		const ctx = editOverlayCanvas.getContext('2d')!;
		ctx.putImageData(snapshot, 0, 0);
		renderDisplay();
		return true;
	}

	// ─── Pointer Event Handlers ─────────────────────────────────────────────

	function handlePointerDown(e: PointerEvent) {
		if (!isActive || !isReady) return;
		if (e.target instanceof Element) e.target.setPointerCapture(e.pointerId);

		const coords = getIntrinsicCoordinates(e.clientX, e.clientY);

		// Ctrl+Click: Set manual source anchor
		if (e.ctrlKey) {
			editorState.healSourceMode = 'manual';
			editorState.healSourceAnchor = { x: coords.x, y: coords.y };
			sourceIndicatorX = coords.x;
			sourceIndicatorY = coords.y;
			showSourceIndicator = true;
			renderCursorHUD();
			return; // Don't start a stroke
		}

		// Begin heal stroke
		isDrawing = true;
		strokePoints = [coords];

		// Push undo snapshot before modifications
		pushUndoSnapshot();
	}

	function handlePointerMove(e: PointerEvent) {
		if (!isActive) return;

		const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
		cursorX = coords.x;
		cursorY = coords.y;

		// Update source indicator position in manual mode (lockstep offset)
		if (editorState.healSourceMode === 'manual' && editorState.healSourceAnchor) {
			showSourceIndicator = true;
			// In manual mode during drag, the source moves in lockstep
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

		// Collect stroke points (subsample for performance)
		const lastPoint = strokePoints[strokePoints.length - 1];
		const dx = coords.x - lastPoint.x;
		const dy = coords.y - lastPoint.y;
		const dist = Math.sqrt(dx * dx + dy * dy);
		const stepSize = Math.max(editorState.brushSize * 0.25, 2);

		if (dist >= stepSize) {
			strokePoints.push(coords);
			// Apply heal stamp at this point immediately for feedback
			applyHealAtPoint(coords.x, coords.y);
		}
	}

	function handlePointerUp(e: PointerEvent) {
		if (!isDrawing) return;
		if (e.target instanceof Element && e.target.hasPointerCapture(e.pointerId)) {
			e.target.releasePointerCapture(e.pointerId);
		}

		// Apply final heal at last position
		if (strokePoints.length > 0) {
			const lastCoord = getIntrinsicCoordinates(e.clientX, e.clientY);
			applyHealAtPoint(lastCoord.x, lastCoord.y);
		}

		isDrawing = false;
		strokePoints = [];
		renderDisplay();
	}

	// ─── Core Heal Application ──────────────────────────────────────────────

	function applyHealAtPoint(destX: number, destY: number) {
		if (!originalPageCanvas || !editOverlayCanvas) return;

		const origCtx = originalPageCanvas.getContext('2d')!;
		const editCtx = editOverlayCanvas.getContext('2d')!;

		const w = originalPageCanvas.width;
		const h = originalPageCanvas.height;
		const radius = editorState.brushSize / 2;

		// Get pixel data from immutable original
		const originalData = origCtx.getImageData(0, 0, w, h).data;
		// Get pixel data from current edit overlay
		const overlayImageData = editCtx.getImageData(0, 0, w, h);
		const overlayData = overlayImageData.data;

		let sourceX: number;
		let sourceY: number;

		if (editorState.healSourceMode === 'manual' && editorState.healSourceAnchor) {
			// Manual source: lockstep offset from anchor
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
			// Auto-spot mode: find best source from surrounding ring
			const autoSource = findAutoSourceOffset(
				new Uint8ClampedArray(originalData),
				Math.round(destX),
				Math.round(destY),
				Math.round(radius),
				w,
				h
			);
			sourceX = autoSource.sourceX;
			sourceY = autoSource.sourceY;
		}

		// Clamp source coordinates
		sourceX = Math.max(radius + 1, Math.min(w - radius - 1, sourceX));
		sourceY = Math.max(radius + 1, Math.min(h - radius - 1, sourceY));

		// Run the 3-phase heal pipeline
		const result = healPatch(
			new Uint8ClampedArray(originalData),
			new Uint8ClampedArray(overlayData),
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
			// Apply the healed patch to the overlay
			applyHealResult(overlayImageData.data, w, result);
			editCtx.putImageData(overlayImageData, 0, 0);
			renderDisplay();
		}
	}

	// ─── Pointer Enter/Leave ────────────────────────────────────────────────

	function handlePointerEnter() {
		if (isActive) {
			showCursor = true;
		}
	}

	function handlePointerLeave() {
		showCursor = false;
		renderCursorHUD();
	}

	// ─── Keyboard Events (Shift for hardness) ───────────────────────────────

	function handleKeyDown(e: KeyboardEvent) {
		if (!isActive) return;

		// Shift+drag changes hardness — we just track shift state
		// The actual hardness change happens during pointer move
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	bind:this={containerDiv}
	class="absolute top-0 left-0 z-41 h-full w-full"
	style="pointer-events: {isActive ? 'auto' : 'none'}; cursor: none;"
	onpointerdown={handlePointerDown}
	onpointermove={handlePointerMove}
	onpointerup={handlePointerUp}
	onpointerenter={handlePointerEnter}
	onpointerleave={handlePointerLeave}
>
	<!-- Display canvas: shows the healed result -->
	{#if isActive && isReady}
		<canvas
			bind:this={displayCanvas}
			width={intrinsicWidth}
			height={intrinsicHeight}
			class="absolute top-0 left-0 h-full w-full"
			style="pointer-events: none; image-rendering: auto;"
		></canvas>
	{/if}

	<!-- Cursor HUD canvas: brush circle, source indicator -->
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
