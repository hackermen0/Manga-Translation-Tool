<script lang="ts">
	import { Upload, Plus, ScanText, Loader2 } from '@lucide/svelte';
	import { Button } from '$lib';
	import { imageState, zoomState, layerStateManager, editorState } from '$lib';
	import { Open } from '$lib';
	import { tick, untrack } from 'svelte';
	import BubbleOverlay from './BubbleOverlay.svelte';
	import DetectionToolbar from './Toolbar/DetectionToolbar.svelte';
	import RedrawingOverlay from './RedrawingOverlay.svelte';
	import RedrawingToolbar from './Toolbar/RedrawingToolbar.svelte';
	import TypesettingOverlay from './TypesettingOverlay.svelte';
	import TypesettingToolbar from './Toolbar/TypesettingToolbar.svelte';

	const BACKEND_URL = 'http://127.0.0.1:8000';

	let sortedLayers = $derived([...layerStateManager.layerList].sort((a, b) => a.zIndex - b.zIndex));
	let hasImages = $derived(sortedLayers.some((l) => l.imageID && imageState.images[l.imageID]));

	let scrollContainer: HTMLDivElement | undefined = $state();
	let containerWidth = $state(0);
	let containerHeight = $state(0);
	let isPanning = false;

	$effect(() => {
		const activePage = editorState.activePage;
		if (!activePage) return;

		const inpaintedUrl = activePage.inpaintedUrl;
		const originalUrl = activePage.originalUrl;
		const originalFilename = activePage.originalFilename;
		const activeSession = editorState.activeSession;

		untrack(() => {
			const showInpainted = activeSession === 'redrawing' || activeSession === 'typesetting';
			const targetURL = `${BACKEND_URL}${showInpainted && inpaintedUrl ? inpaintedUrl : originalUrl}`;
			const existingOriginalLayer = layerStateManager.layerList.find(
				(l) => l.name === 'Original Image'
			);

			if (!existingOriginalLayer) {
				const img = new Image();
				img.onload = () => {
					const newImageID = imageState.addImage({
						name: originalFilename,
						type: 'image/png',
						size: 0,
						lastModified: Date.now(),
						imageURL: targetURL,
						width: img.naturalWidth,
						height: img.naturalHeight
					});

					const newImageLayerID = layerStateManager.addLayer('Original Image', 'image');
					layerStateManager.setLayerImage(newImageLayerID, newImageID);
					layerStateManager.selectLayer(newImageLayerID);
				};
				img.src = targetURL;
			} else if (existingOriginalLayer.imageID) {
				const currentImg = imageState.images[existingOriginalLayer.imageID];
				if (currentImg && currentImg.imageURL !== targetURL) {
					const img = new Image();
					img.onload = () => {
						currentImg.imageURL = targetURL;
						currentImg.width = img.naturalWidth;
						currentImg.height = img.naturalHeight;
						currentImg.lastModified = Date.now();
					};
					img.src = targetURL;
				}
			}
		});
	});

	let canvasDimensions = $derived.by(() => {
		let maxWidth = 0;
		let maxHeight = 0;

		for (const layer of layerStateManager.layerList) {
			if (layer.imageID && imageState.images[layer.imageID]) {
				const img = imageState.images[layer.imageID];
				if (img.width > maxWidth) maxWidth = img.width;
				if (img.height > maxHeight) maxHeight = img.height;
			}
		}

		return { width: maxWidth, height: maxHeight };
	});

	let baseScale = $derived.by(() => {
		if (
			canvasDimensions.width === 0 ||
			canvasDimensions.height === 0 ||
			containerWidth === 0 ||
			containerHeight === 0
		)
			return 1;

		const widthRatio = (containerWidth - 40) / canvasDimensions.width;
		const heightRatio = (containerHeight - 40) / canvasDimensions.height;

		const fitScale = Math.min(widthRatio, heightRatio);
		return Math.min(fitScale, 1);
	});

	let displayWidth = $derived(canvasDimensions.width * baseScale * (zoomState.zoomLevel / 100));
	let displayHeight = $derived(canvasDimensions.height * baseScale * (zoomState.zoomLevel / 100));

	function handleMouseDown(e: MouseEvent) {
		const target = e.target as HTMLElement;
		if (target.closest('svg')) {
			return;
		}

		if (e.button === 2 || e.button === 1) {
			isPanning = true;
			e.preventDefault();
		}
	}

	function handleMouseMove(e: MouseEvent) {
		if (!isPanning || !scrollContainer) return;
		scrollContainer.scrollLeft -= e.movementX;
		scrollContainer.scrollTop -= e.movementY;
	}

	function handleMouseUp() {
		isPanning = false;
	}

	async function handleMouseWheel(e: WheelEvent) {
		if (!scrollContainer) return;
		if (e.ctrlKey) e.preventDefault();

		const canvasDiv = scrollContainer.firstElementChild as HTMLElement;
		let anchorX = 0.5;
		let anchorY = 0.5;

		if (canvasDiv) {
			const rect = canvasDiv.getBoundingClientRect();
			anchorX = (e.clientX - rect.left) / rect.width;
			anchorY = (e.clientY - rect.top) / rect.height;
		}

		const zoomStep = 5;
		if (e.deltaY < 0) {
			zoomState.zoomIn(zoomStep);
		} else {
			zoomState.zoomOut(zoomStep);
		}

		await tick();

		if (
			scrollContainer.scrollWidth > scrollContainer.clientWidth ||
			scrollContainer.scrollHeight > scrollContainer.clientHeight
		) {
			const newRect = canvasDiv.getBoundingClientRect();
			const containerRect = scrollContainer.getBoundingClientRect();

			const mouseXInContainer = e.clientX - containerRect.left;
			const mouseYInContainer = e.clientY - containerRect.top;

			const newPointX = anchorX * newRect.width;
			const newPointY = anchorY * newRect.height;

			scrollContainer.scrollLeft = newPointX - mouseXInContainer;
			scrollContainer.scrollTop = newPointY - mouseYInContainer;
		}
	}

	let isDraggingDivider = $state(false);

	function handleSplitDividerPointerDown(e: PointerEvent) {
		e.preventDefault();
		try {
			(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
		} catch (err) {}
		isDraggingDivider = true;
		window.addEventListener('pointermove', handleSplitDividerPointerMove);
		window.addEventListener('pointerup', handleSplitDividerPointerUp);
	}

	function handleSplitDividerPointerMove(e: PointerEvent) {
		if (!isDraggingDivider || !scrollContainer) return;
		const canvasDiv = scrollContainer.querySelector('.relative.m-auto') as HTMLElement;
		if (!canvasDiv) return;
		const rect = canvasDiv.getBoundingClientRect();
		const relativeX = e.clientX - rect.left;
		const percentage = Math.max(0, Math.min(100, (relativeX / rect.width) * 100));
		editorState.qcSplitPercentage = percentage;
	}

	function handleSplitDividerPointerUp(e: PointerEvent) {
		if (isDraggingDivider) {
			try {
				(e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
			} catch (err) {}
			isDraggingDivider = false;
			window.removeEventListener('pointermove', handleSplitDividerPointerMove);
			window.removeEventListener('pointerup', handleSplitDividerPointerUp);
		}
	}

	function handleContextMenu(e: MouseEvent) {
		e.preventDefault();
		return false;
	}
</script>

<svelte:window onmousemove={handleMouseMove} onmouseup={handleMouseUp} />

<div class="bg-secondary flex h-full w-full flex-col overflow-hidden">
	{#if hasImages}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			bind:this={scrollContainer}
			bind:clientWidth={containerWidth}
			bind:clientHeight={containerHeight}
			class="relative flex h-full w-full flex-1 cursor-grab overflow-auto active:cursor-grabbing"
			onmousedown={handleMouseDown}
			oncontextmenu={handleContextMenu}
			onwheel={handleMouseWheel}
		>
			<div
				class="relative m-auto flex-shrink-0 bg-white shadow-lg transition-all duration-75 ease-out"
				style="width: {displayWidth}px; height: {displayHeight}px;"
			>
				{#each sortedLayers as layer (layer.id)}
					{#if layer.visibility && layer.imageID && imageState.images[layer.imageID]}
						<img
							src={imageState.images[layer.imageID].imageURL}
							alt={layer.name}
							draggable="false"
							class="absolute top-1/2 left-1/2 max-h-full max-w-full object-contain"
							style="
                                    transform: translate(-50%, -50%);
                                    opacity: {layer.opacity / 100}; 
                                    pointer-events: {layer.locked ? 'none' : 'auto'};
                                    width: auto; 
                                    height: auto;
                                "
						/>
					{/if}
				{/each}

				{#if editorState.activeSession === 'detection' || editorState.activeSession === 'translation'}
					<BubbleOverlay
						intrinsicWidth={canvasDimensions.width}
						intrinsicHeight={canvasDimensions.height}
					/>
				{/if}

				{#if editorState.activeSession === 'redrawing' || editorState.activeSession === 'typesetting'}
					<RedrawingOverlay
						intrinsicWidth={canvasDimensions.width}
						intrinsicHeight={canvasDimensions.height}
					/>
				{/if}

				{#if editorState.activeSession === 'typesetting'}
					<TypesettingOverlay
						intrinsicWidth={canvasDimensions.width}
						intrinsicHeight={canvasDimensions.height}
					/>
				{/if}

				{#if editorState.activeSession === 'quality'}
					<!-- Final View Overlay containing inpainted image and typeset text -->
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						class="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden select-none"
						style="
							opacity: {editorState.qcMode === 'onion' ? editorState.qcBlendValue / 100 : 1};
							clip-path: {editorState.qcMode === 'split' ? `polygon(${editorState.qcSplitPercentage}% 0, 100% 0, 100% 100%, ${editorState.qcSplitPercentage}% 100%)` : 'none'};
						"
					>
						{#if editorState.activePage?.inpaintedUrl}
							<img
								src={`${BACKEND_URL}${editorState.activePage.inpaintedUrl}`}
								alt="Inpainted Background"
								draggable="false"
								class="absolute top-1/2 left-1/2 max-h-full max-w-full object-contain pointer-events-none"
								style="
									transform: translate(-50%, -50%);
									width: auto;
									height: auto;
								"
							/>
						{:else}
							<!-- Fallback to original image if not inpainted yet -->
							<img
								src={`${BACKEND_URL}${editorState.activePage?.originalUrl}`}
								alt="Original Background"
								draggable="false"
								class="absolute top-1/2 left-1/2 max-h-full max-w-full object-contain pointer-events-none"
								style="
									transform: translate(-50%, -50%);
									width: auto;
									height: auto;
								"
							/>
						{/if}

						<TypesettingOverlay
							intrinsicWidth={canvasDimensions.width}
							intrinsicHeight={canvasDimensions.height}
							interactive={false}
						/>
					</div>

					<!-- Split slider line divider handle -->
					{#if editorState.qcMode === 'split'}
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<div
							class="absolute top-0 bottom-0 w-1 bg-accent cursor-ew-resize z-50 flex items-center justify-center pointer-events-auto"
							style="left: {editorState.qcSplitPercentage}%; transform: translateX(-50%);"
							onpointerdown={handleSplitDividerPointerDown}
						>
							<div class="h-8 w-8 rounded-full bg-accent text-white flex items-center justify-center shadow-lg border-2 border-white select-none pointer-events-none hover:scale-110 active:scale-95 transition-transform">
								<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevrons-left-right"><path d="m9 7-5 5 5 5"/><path d="m15 7 5 5-5 5"/></svg>
							</div>
						</div>
					{/if}

					<!-- Inpainting Mask Highlight (neon pulsing overlay) -->
					{#if editorState.qcHighlightInpaint && editorState.activePage?.bubbles}
						<svg
							viewBox="0 0 {canvasDimensions.width} {canvasDimensions.height}"
							class="pointer-events-none absolute top-0 left-0 z-45 h-full w-full"
						>
							{#each editorState.activePage.bubbles as bubble (bubble.id)}
								{@const pointsString = bubble.points.map((p) => `${p.x},${p.y}`).join(' ')}
								<polygon
									points={pointsString}
									fill="rgba(255, 0, 92, 0.4)"
									stroke="rgba(255, 0, 92, 0.9)"
									stroke-width={canvasDimensions.width * 0.0025}
									class="animate-pulse"
								/>
							{/each}
						</svg>
					{/if}
				{/if}
			</div>
		</div>

		{#if editorState.activeSession === 'detection'}
			<DetectionToolbar />
		{/if}

		{#if editorState.activeSession === 'redrawing'}
			<RedrawingToolbar />
		{/if}

		{#if editorState.activeSession === 'typesetting'}
			<TypesettingToolbar />
		{/if}
	{:else}
		<div class="flex h-full flex-col items-center justify-center gap-3 text-black">
			<div
				class="flex aspect-square w-32 items-center justify-center rounded-lg border-3 border-dashed border-gray-400 text-gray-400"
			>
				<Upload size={48} />
			</div>
			<p class="text-center text-lg font-semibold">Import Manga Page</p>
			<p class="text-center text-base font-semibold text-slate-500">
				Upload a manga page to start translating
			</p>
			<div class="flex flex-row items-center justify-center gap-3">
				<Open buttonName={'Upload Image'} variant={'default'} icon={Upload} />
				<Button icon={Plus} variant={'outline'}>Create New Project</Button>
			</div>
		</div>
	{/if}
</div>
