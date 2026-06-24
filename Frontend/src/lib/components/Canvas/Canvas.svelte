<script lang="ts">
	import { Upload, Plus, ScanText, Loader2 } from '@lucide/svelte';
	import JSZip from 'jszip';
	import { Button } from '$lib';
	import { imageState, zoomState, layerStateManager, editorState } from '$lib';
	import { Open } from '$lib';
	import { tick, untrack } from 'svelte';
	import BubbleOverlay from './BubbleOverlay.svelte';
	import DetectionToolbar from './Toolbar/DetectionToolbar.svelte';
	import RedrawingOverlay from './RedrawingOverlay.svelte';
	import HealingOverlay from './HealingOverlay.svelte';
	import RedrawingToolbar from './Toolbar/RedrawingToolbar.svelte';
	import TypesettingOverlay from './TypesettingOverlay.svelte';
	import TypesettingToolbar from './Toolbar/TypesettingToolbar.svelte';
import { findAutoSourceOffset, healPatch, applyHealResult } from '$lib/stores/HealEngine';

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

	function getBBox(points: { x: number; y: number }[]) {
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

	function autoFitFontSize(
		text: string,
		boxWidth: number,
		boxHeight: number,
		style: any
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

	function layoutHorizontal(
		ctx: CanvasRenderingContext2D,
		text: string,
		availW: number,
		fontSize: number,
		lineHeight: number
	): string[] {
		const words = text.split(/\s+/);
		const lines: string[] = [];
		let currentLine = '';
		for (const word of words) {
			const testLine = currentLine ? `${currentLine} ${word}` : word;
			const metrics = ctx.measureText(testLine);
			if (metrics.width > availW && currentLine) {
				lines.push(currentLine);
				currentLine = word;
			} else {
				currentLine = testLine;
			}
		}
		if (currentLine) lines.push(currentLine);
		return lines;
	}

	function layoutVertical(
		ctx: CanvasRenderingContext2D,
		text: string,
		availH: number,
		fontSize: number,
		lineHeight: number
	): string[] {
		const words = text.split(/\s+/);
		const lines: string[] = [];
		let currentLine = '';
		for (const word of words) {
			const testLine = currentLine ? `${currentLine} ${word}` : word;
			const metrics = ctx.measureText(testLine);
			if (metrics.width > availH && currentLine) {
				lines.push(currentLine);
				currentLine = word;
			} else {
				currentLine = testLine;
			}
		}
		if (currentLine) lines.push(currentLine);
		return lines;
	}

	interface TextLayoutLine {
		text: string;
		y: number;
	}

	interface TextLayoutChar {
		char: string;
		x: number;
		y: number;
	}

	interface TextLayoutResult {
		lines: TextLayoutLine[];
		chars: TextLayoutChar[];
	}

	function escapeHtml(text: string): string {
		return text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;')
			.replace(/'/g, '&#039;');
	}

	function tokenizeText(text: string): string[] {
		const words = text.split(/(\s+)/);
		const tokens: string[] = [];
		for (const word of words) {
			if (word.trim() === '') {
				tokens.push(word);
			} else {
				if (word.includes('-')) {
					const parts = word.split('-');
					for (let i = 0; i < parts.length; i++) {
						const isLast = i === parts.length - 1;
						tokens.push(parts[i] + (isLast ? '' : '-'));
					}
				} else {
					tokens.push(word);
				}
			}
		}
		return tokens;
	}

	function getTextLayout(
		text: string,
		boxWidth: number,
		boxHeight: number,
		style: any,
		computedFontSize: number
	): TextLayoutResult {
		const padding = Math.min(boxWidth, boxHeight) * 0.1;
		
		const container = document.createElement('div');
		container.style.position = 'absolute';
		container.style.visibility = 'hidden';
		container.style.left = '-9999px';
		container.style.top = '-9999px';
		container.style.width = `${boxWidth}px`;
		container.style.height = `${boxHeight}px`;
		container.style.padding = `${padding}px`;
		container.style.boxSizing = 'border-box';
		container.style.display = 'flex';
		container.style.alignItems = 'center';
		container.style.justifyContent = 'center';
		container.style.overflow = 'hidden';

		const textDiv = document.createElement('div');
		textDiv.style.fontFamily = `'${style.fontFamily}', 'Comic Neue', 'Comic Sans MS', sans-serif`;
		textDiv.style.fontSize = `${computedFontSize}px`;
		textDiv.style.fontWeight = style.fontWeight;
		textDiv.style.fontStyle = style.fontStyle ?? 'normal';
		textDiv.style.writingMode = style.writingMode === 'vertical' ? 'vertical-rl' : 'horizontal-tb';
		textDiv.style.textOrientation = style.writingMode === 'vertical' ? 'upright' : 'mixed';
		textDiv.style.textAlign = style.textAlign || 'center';
		textDiv.style.lineHeight = String(style.lineHeight);
		textDiv.style.letterSpacing = `${style.letterSpacing}px`;
		textDiv.style.wordBreak = 'break-word';
		textDiv.style.overflowWrap = 'break-word';
		textDiv.style.whiteSpace = 'pre-wrap';
		textDiv.style.width = '100%';
		textDiv.style.textTransform = 'uppercase';

		const isVertical = style.writingMode === 'vertical';
		const uppercaseText = text.toUpperCase();
		let html = '';

		if (isVertical) {
			for (let i = 0; i < uppercaseText.length; i++) {
				const char = uppercaseText[i];
				if (char === '\n') {
					html += '<span data-newline="true"><br/></span>';
				} else if (char === ' ') {
					html += '<span data-space="true">&nbsp;</span>';
				} else {
					html += `<span>${escapeHtml(char)}</span>`;
				}
			}
		} else {
			const tokens = tokenizeText(uppercaseText);
			for (const token of tokens) {
				if (token.includes('\n')) {
					const subparts = token.split('\n');
					for (let i = 0; i < subparts.length; i++) {
						if (i > 0) {
							html += '<span data-newline="true"><br/></span>';
						}
						if (subparts[i]) {
							html += `<span>${escapeHtml(subparts[i])}</span>`;
						}
					}
				} else if (token.trim() === '') {
					html += `<span data-space="true">${token}</span>`;
				} else {
					html += `<span>${escapeHtml(token)}</span>`;
				}
			}
		}

		textDiv.innerHTML = html;
		container.appendChild(textDiv);
		document.body.appendChild(container);

		const spans = textDiv.querySelectorAll('span');
		const containerRect = container.getBoundingClientRect();

		const linesMap = new Map<number, { text: string; spanTops: number[] }>();
		const chars: TextLayoutChar[] = [];

		// Group horizontal lines by their top coordinate (using a tolerance of 5px)
		const getGroupKey = (coord: number) => {
			for (const key of linesMap.keys()) {
				if (Math.abs(key - coord) < 5) {
					return key;
				}
			}
			return coord;
		};

		let currentLineKey = -1;

		for (const span of spans) {
			if (span.getAttribute('data-newline') === 'true') {
				currentLineKey = -1;
				continue;
			}

			const rect = span.getBoundingClientRect();
			const x = rect.left - containerRect.left;
			const y = rect.top - containerRect.top;
			const charVal = span.textContent || '';

			if (isVertical) {
				chars.push({ char: charVal, x, y });
			} else {
				const topCoord = rect.top;
				let groupKey = getGroupKey(topCoord);
				if (currentLineKey === -1 || Math.abs(groupKey - currentLineKey) >= 5) {
					currentLineKey = groupKey;
				}
				
				if (!linesMap.has(currentLineKey)) {
					linesMap.set(currentLineKey, { text: '', spanTops: [] });
				}
				const lineObj = linesMap.get(currentLineKey)!;
				lineObj.text += charVal;
				lineObj.spanTops.push(y);
			}
		}

		document.body.removeChild(container);

		const lines: TextLayoutLine[] = [];
		if (!isVertical) {
			const sortedKeys = Array.from(linesMap.keys()).sort((a, b) => a - b);
			for (const key of sortedKeys) {
				const lineObj = linesMap.get(key)!;
				const avgY = lineObj.spanTops.reduce((sum, val) => sum + val, 0) / lineObj.spanTops.length;
				lines.push({
					text: lineObj.text,
					y: avgY
				});
			}
		}

		return { lines, chars };
	}

	const loadImg = (src: string): Promise<HTMLImageElement> => {
		return new Promise((resolve, reject) => {
			const img = new Image();
			img.crossOrigin = 'anonymous';
			img.onload = () => resolve(img);
			img.onerror = (e) => reject(new Error(`Failed to load image: ${src}`));
			img.src = src;
		});
	};

	async function renderPageToCanvas(page: any, isFinalOnly: boolean = false): Promise<HTMLCanvasElement> {
		// Fetch base64 data URLs from the backend API
		const fetchBase64 = async (endpoint: string): Promise<string> => {
			const res = await fetch(`${BACKEND_URL}${endpoint}`);
			if (!res.ok) throw new Error(`Failed to fetch image data from ${endpoint}`);
			const data = await res.json();
			return data.base64;
		};

		const defaultStyle = {
			fontSize: 16,
			fontFamily: 'CC Wild Words',
			fontWeight: 'normal',
			fontColor: '#000000',
			offsetX: 0,
			offsetY: 0,
			lineHeight: 1.2,
			textAlign: 'center' as 'left' | 'center' | 'right',
			letterSpacing: 0.5,
			autoFit: true,
			fontStyle: 'normal' as 'normal' | 'italic',
			writingMode: 'horizontal' as 'horizontal' | 'vertical',
			outline: false,
			outlineColor: '#ffffff',
			outlineWidth: 2
		};

		// 1. Pre-load all required custom fonts to ensure canvas has them ready before any layout/drawing
		let fontLoadPromise = Promise.resolve();
		if (page.bubbles) {
			const fontPromises = page.bubbles
				.filter((bubble: any) => bubble.en_text?.trim())
				.map((bubble: any) => {
					const style = bubble.typeset ?? defaultStyle;
					const fontStylePart = style.fontStyle === 'italic' ? 'italic ' : '';
					const fontWeightPart = (style.fontWeight === 'bold' || style.fontWeight === 700) ? 'bold ' : '';
					const fontStr = `${fontStylePart}${fontWeightPart}16px "${style.fontFamily}"`;
					return document.fonts.load(fontStr).catch((err) => {
						console.warn(`Failed to pre-load font: ${fontStr}`, err);
					});
				});
			fontLoadPromise = Promise.all(fontPromises).then(() => {});
		}

		const [originalBase64Url, overlayBase64Url] = await Promise.all([
			fetchBase64(`/api/workspace/${editorState.workspaceId}/page/${page.pageId}/original-base64`),
			fetchBase64(`/api/workspace/${editorState.workspaceId}/page/${page.pageId}/inpainted-base64`),
			fontLoadPromise
		]);

		const [originalImg, overlayImg] = await Promise.all([
			loadImg(originalBase64Url),
			loadImg(overlayBase64Url)
		]);

		const width = originalImg.naturalWidth;
		const height = originalImg.naturalHeight;

		// 2. Prepare offscreen canvases
		const canvas = document.createElement('canvas');
		canvas.width = width;
		canvas.height = height;
		const ctx = canvas.getContext('2d')!;

		// Draw base layer (original background)
		ctx.drawImage(originalImg, 0, 0, width, height);

		// Prepare overlay canvas
		const overlayCanvas = document.createElement('canvas');
		overlayCanvas.width = width;
		overlayCanvas.height = height;
		const overlayCtx = overlayCanvas.getContext('2d')!;

		// Draw final background image onto overlay
		overlayCtx.drawImage(overlayImg, 0, 0, width, height);

		// Draw eraser strokes
		const eraserStrokes = (page.redrawingStrokes ?? []).filter(
			(s: any) => (s.type || 'eraser') === 'eraser'
		);
		for (const stroke of eraserStrokes) {
			if (stroke.points.length < 1) continue;
			overlayCtx.beginPath();
			overlayCtx.moveTo(stroke.points[0].x, stroke.points[0].y);
			for (let i = 1; i < stroke.points.length; i++) {
				overlayCtx.lineTo(stroke.points[i].x, stroke.points[i].y);
			}
			overlayCtx.lineWidth = stroke.brushSize;
			overlayCtx.strokeStyle = stroke.brushColor || '#ffffff';
			overlayCtx.lineCap = 'round';
			overlayCtx.lineJoin = 'round';
			overlayCtx.stroke();
		}

		// Draw restore strokes
		const restoreStrokes = (page.redrawingStrokes ?? []).filter(
			(s: any) => s.type === 'restore'
		);
		if (restoreStrokes.length > 0) {
			const maskCanvas = document.createElement('canvas');
			maskCanvas.width = width;
			maskCanvas.height = height;
			const maskCtx = maskCanvas.getContext('2d')!;

			for (const stroke of restoreStrokes) {
				if (stroke.points.length < 1) continue;
				maskCtx.beginPath();
				maskCtx.moveTo(stroke.points[0].x, stroke.points[0].y);
				for (let i = 1; i < stroke.points.length; i++) {
					maskCtx.lineTo(stroke.points[i].x, stroke.points[i].y);
				}
				maskCtx.lineWidth = stroke.brushSize;
				maskCtx.strokeStyle = 'white';
				maskCtx.lineCap = 'round';
				maskCtx.lineJoin = 'round';
				maskCtx.stroke();
			}

			maskCtx.globalCompositeOperation = 'source-in';
			maskCtx.drawImage(originalImg, 0, 0, width, height);

			overlayCtx.drawImage(maskCanvas, 0, 0, width, height);
		}

		// Draw heal strokes
		const healStrokes = (page.redrawingStrokes ?? []).filter(
			(s: any) => s.type === 'heal'
		);
		if (healStrokes.length > 0) {
			const origCtx = canvas.getContext('2d')!;
			const origData = origCtx.getImageData(0, 0, width, height).data;
			const overlayImageData = overlayCtx.getImageData(0, 0, width, height);
			const overlayData = overlayImageData.data;

			for (const stroke of healStrokes) {
				const radius = stroke.brushSize / 2;
				const hardness = stroke.hardness ?? 0.75;
				const sourceMode = stroke.sourceMode ?? 'auto';
				const sourceAnchor = stroke.sourceAnchor ?? null;

				for (const coords of stroke.points) {
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
							origData,
							Math.round(coords.x),
							Math.round(coords.y),
							Math.round(radius),
							width,
							height
						);
						sourceX = autoSource.sourceX;
						sourceY = autoSource.sourceY;
					}

					sourceX = Math.max(radius + 1, Math.min(width - radius - 1, sourceX));
					sourceY = Math.max(radius + 1, Math.min(height - radius - 1, sourceY));

					const result = healPatch(
						origData,
						overlayData,
						sourceX,
						sourceY,
						coords.x,
						coords.y,
						Math.round(radius),
						hardness,
						width,
						height
					);

					if (result) {
						applyHealResult(overlayImageData.data, width, result);
					}
				}
			}
			overlayCtx.putImageData(overlayImageData, 0, 0);
		}

		// 3. Typesetting overlays
		await document.fonts.ready;

		if (page.bubbles) {
			for (const bubble of page.bubbles) {
				if (!bubble.en_text?.trim()) continue;

				const style = bubble.typeset ?? defaultStyle;
				const bbox = getBBox(bubble.points);
				if (bbox.width <= 0 || bbox.height <= 0) continue;

				const computedFontSize = style.autoFit
					? autoFitFontSize(bubble.en_text, bbox.width, bbox.height, style)
					: style.fontSize;

				const padding = Math.min(bbox.width, bbox.height) * 0.1;
				const isVertical = style.writingMode === 'vertical';

				const startX = bbox.x + (style.offsetX ?? 0);
				const startY = bbox.y + (style.offsetY ?? 0);

				const layout = getTextLayout(bubble.en_text, bbox.width, bbox.height, style, computedFontSize);

				overlayCtx.save();

				// Configure font
				const fontStylePart = style.fontStyle === 'italic' ? 'italic ' : '';
				const fontWeightPart = (style.fontWeight === 'bold' || style.fontWeight === 700) ? 'bold ' : '';
				overlayCtx.font = `${fontStylePart}${fontWeightPart}${computedFontSize}px "${style.fontFamily}", "Comic Neue", "Comic Sans MS", sans-serif`;

				if (style.letterSpacing !== undefined) {
					// @ts-ignore
					overlayCtx.letterSpacing = `${style.letterSpacing}px`;
				}

				if (isVertical) {
					overlayCtx.textBaseline = 'top';
					overlayCtx.textAlign = 'left';

					for (const charObj of layout.chars) {
						if (charObj.char.trim() === '') continue; // Skip space

						const drawX = startX + charObj.x;
						const drawY = startY + charObj.y;

						if (style.outline) {
							overlayCtx.lineWidth = (style.outlineWidth ?? 2) * 2;
							overlayCtx.strokeStyle = style.outlineColor ?? '#ffffff';
							overlayCtx.lineJoin = 'round';
							overlayCtx.lineCap = 'round';
							overlayCtx.strokeText(charObj.char, drawX, drawY);
						}
						overlayCtx.fillStyle = style.fontColor;
						overlayCtx.fillText(charObj.char, drawX, drawY);
					}
				} else {
					overlayCtx.textBaseline = 'top';
					overlayCtx.textAlign = style.textAlign || 'center';

					for (const line of layout.lines) {
						let x = startX + bbox.width / 2;
						if (style.textAlign === 'left') {
							x = startX + padding;
						} else if (style.textAlign === 'right') {
							x = startX + bbox.width - padding;
						}

						const drawY = startY + line.y;

						if (style.outline) {
							overlayCtx.lineWidth = (style.outlineWidth ?? 2) * 2;
							overlayCtx.strokeStyle = style.outlineColor ?? '#ffffff';
							overlayCtx.lineJoin = 'round';
							overlayCtx.lineCap = 'round';
							overlayCtx.strokeText(line.text.trim(), x, drawY);
						}
						overlayCtx.fillStyle = style.fontColor;
						overlayCtx.fillText(line.text.trim(), x, drawY);
					}
				}

				overlayCtx.restore();
			}
		}

		// 4. Combine base layer and overlay layer based on QC mode
		if (isFinalOnly) {
			ctx.drawImage(overlayCanvas, 0, 0, width, height);
		} else {
			if (editorState.qcMode === 'onion') {
				ctx.globalAlpha = editorState.qcBlendValue / 100;
				ctx.drawImage(overlayCanvas, 0, 0, width, height);
				ctx.globalAlpha = 1.0;
			} else {
				const splitX = (editorState.qcSplitPercentage / 100) * width;
				ctx.save();
				ctx.beginPath();
				ctx.rect(splitX, 0, width - splitX, height);
				ctx.clip();
				ctx.drawImage(overlayCanvas, 0, 0, width, height);
				ctx.restore();
			}
		}

		return canvas;
	}

	async function exportCompositedPage() {
		const activePage = editorState.activePage;
		if (!activePage) return;

		try {
			const canvas = await renderPageToCanvas(activePage, false);
			const dataUrl = canvas.toDataURL('image/png');
			const link = document.createElement('a');
			link.href = dataUrl;
			link.download = `manga_page_${activePage.pageId}_export.png`;
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
		} catch (error) {
			console.error('Single page export failed:', error);
			alert('Export failed: ' + error);
		}
	}

	async function exportAllPagesAsZip() {
		const pages = editorState.pages;
		if (!pages || pages.length === 0) {
			alert('No pages available to export.');
			return;
		}

		const zip = new JSZip();

		for (const page of pages) {
			try {
				const canvas = await renderPageToCanvas(page, true);
				const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'));
				if (blob) {
					const baseName = page.originalFilename.substring(0, page.originalFilename.lastIndexOf('.')) || page.originalFilename;
					const filename = `${baseName}_translated.png`;
					zip.file(filename, blob);
				}
			} catch (err) {
				console.error(`Failed to export page ${page.pageId}:`, err);
			}
		}

		const content = await zip.generateAsync({ type: 'blob' });
		const url = URL.createObjectURL(content);
		const link = document.createElement('a');
		link.href = url;
		link.download = `manga_translation_export.zip`;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(url);
	}

	$effect(() => {
		editorState.exportHandler = exportCompositedPage;
		editorState.exportAllHandler = exportAllPagesAsZip;
		return () => {
			if (editorState.exportHandler === exportCompositedPage) {
				editorState.exportHandler = null;
			}
			if (editorState.exportAllHandler === exportAllPagesAsZip) {
				editorState.exportAllHandler = null;
			}
		};
	});
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
					<HealingOverlay
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
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						class="pointer-events-none absolute top-0 left-0 h-full w-full overflow-hidden select-none"
						style="
							opacity: {editorState.qcMode === 'onion' ? editorState.qcBlendValue / 100 : 1};
							clip-path: {editorState.qcMode === 'split'
							? `polygon(${editorState.qcSplitPercentage}% 0, 100% 0, 100% 100%, ${editorState.qcSplitPercentage}% 100%)`
							: 'none'};
						"
					>
						{#if editorState.activePage?.inpaintedUrl}
							<img
								src={`${BACKEND_URL}${editorState.activePage.inpaintedUrl}`}
								alt="Inpainted Background"
								draggable="false"
								class="pointer-events-none absolute top-1/2 left-1/2 max-h-full max-w-full object-contain"
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
								class="pointer-events-none absolute top-1/2 left-1/2 max-h-full max-w-full object-contain"
								style="
									transform: translate(-50%, -50%);
									width: auto;
									height: auto;
								"
							/>
						{/if}

						<RedrawingOverlay
							intrinsicWidth={canvasDimensions.width}
							intrinsicHeight={canvasDimensions.height}
						/>

						<HealingOverlay
							intrinsicWidth={canvasDimensions.width}
							intrinsicHeight={canvasDimensions.height}
						/>

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
							class="bg-accent pointer-events-auto absolute top-0 bottom-0 z-50 flex w-1 cursor-ew-resize items-center justify-center"
							style="left: {editorState.qcSplitPercentage}%; transform: translateX(-50%);"
							onpointerdown={handleSplitDividerPointerDown}
						>
							<div
								class="bg-accent pointer-events-none flex h-8 w-8 items-center justify-center rounded-full border-2 border-white text-white shadow-lg transition-transform select-none hover:scale-110 active:scale-95"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="16"
									height="16"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="3"
									stroke-linecap="round"
									stroke-linejoin="round"
									class="lucide lucide-chevrons-left-right"
									><path d="m9 7-5 5 5 5"></path><path d="m15 7 5 5-5 5"></path></svg
								>
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
								></polygon>
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
