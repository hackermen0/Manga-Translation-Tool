<script lang="ts">
	import {
		Type,
		ChevronRight,
		ChevronLeft,
		ScanText,
		Loader2,
		RotateCcw,
		AlignLeft,
		AlignCenter,
		AlignRight,
		Bold,
		Move
	} from '@lucide/svelte';
	import { Button, editorState } from '$lib';
	import { DEFAULT_TYPESET_STYLE } from '$lib/stores/Editor.svelte';
	import { Separator } from 'bits-ui';
	let fontOptions = $state([
		{ label: 'CC Wild Words', value: 'CC Wild Words', styleType: 'Comic Serif/Sans Mix', purpose: 'Standard Dialogue', tone: 'Neutral / Narrative' },
		{ label: 'Anime Ace', value: 'Anime Ace', styleType: 'Clean Comic Sans', purpose: 'Budget Standard Speech', tone: 'Casual / Friendly' },
		{ label: 'CC Lettering Black', value: 'CC Lettering Black', styleType: 'Heavy Gothic/Bold', purpose: 'Villains / Dark Artifacts', tone: 'Menacing / Authoritative' },
		{ label: 'Whiz Bang', value: 'Whiz Bang', styleType: 'Jittery / Angular', purpose: 'Screaming / Shock', tone: 'Panicked / High Energy' },
		{ label: 'Augie', value: 'Augie', styleType: 'Handwriting', purpose: 'Internal Monologue', tone: 'Intimate / Reflective' }
	]);
	let bubbles = $derived(editorState.activePage?.bubbles || []);
	let totalBubbles = $derived(bubbles.length);
	let activeBubbleIndex = $derived.by(() => {
		if (bubbles.length === 0) return -1;
		const idx = bubbles.findIndex((b) => b.id === editorState.activeBubbleId);
		return idx !== -1 ? idx : 0;
	});
	let activeBubble = $derived(bubbles[activeBubbleIndex]);
	let selectedFontMetadata = $derived(
		fontOptions.find((f) => f.value === (activeBubble?.typeset?.fontFamily || DEFAULT_TYPESET_STYLE.fontFamily))
	);
	
	let localFontsLoaded = $state(false);
	let isFontLoading = $state(false);

	async function loadLocalFonts() {
		if (!('queryLocalFonts' in window)) {
			alert('Your browser does not support the Local Font Access API. Please use a Chromium-based browser (Chrome, Edge).');
			return;
		}
		try {
			isFontLoading = true;
			// @ts-ignore
			const availableFonts = await window.queryLocalFonts();
			const uniqueFonts = new Set<string>();
			for (const fontData of availableFonts) {
				uniqueFonts.add(fontData.family);
			}
			
			const newFonts = Array.from(uniqueFonts).map(f => ({
				label: f,
				value: f,
				styleType: 'System Font',
				purpose: 'User Installed',
				tone: 'Varies'
			}));
            
			for (const nf of newFonts) {
				if (!fontOptions.find(opt => opt.value === nf.value)) {
					fontOptions.push(nf);
				}
			}
			localFontsLoaded = true;
		} catch (err: any) {
			console.error(err);
			alert('Failed to load local fonts. You may have denied permission.');
		} finally {
			isFontLoading = false;
		}
	}

	$effect(() => {
		if (
			bubbles.length > 0 &&
			(editorState.activeBubbleId === null ||
				!bubbles.some((b) => b.id === editorState.activeBubbleId))
		) {
			editorState.activeBubbleId = bubbles[0].id;
		}
	});
	// Initialize typeset styles when entering the typesetting section
	$effect(() => {
		if (editorState.activeSession === 'typesetting' && editorState.activePage?.detected) {
			editorState.initializeTypesetStyles();
		}
	});
	function handlePrev() {
		if (totalBubbles === 0) return;
		const newIdx = (activeBubbleIndex - 1 + totalBubbles) % totalBubbles;
		editorState.activeBubbleId = bubbles[newIdx].id;
	}
	function handleNext() {
		if (totalBubbles === 0) return;
		const newIdx = (activeBubbleIndex + 1) % totalBubbles;
		editorState.activeBubbleId = bubbles[newIdx].id;
	}
	function resetCurrentBubble() {
		if (!activeBubble || !editorState.activePage) return;
		editorState.activePage.bubbles[activeBubbleIndex].typeset = {
			...DEFAULT_TYPESET_STYLE
		};
		editorState.saveTypesetting();
	}
	async function handleDetectClick() {
		editorState.setActiveSession('detection');
		await editorState.detectBubbles();
	}
	function handleStyleChange() {
		editorState.saveTypesetting();
	}
</script>

{#if editorState.activePage && !editorState.activePage.detected}
	<div
		class="border-primary-border ring-accent flex h-auto flex-col items-center justify-center gap-6 rounded-lg border-2 bg-white p-6 text-center ring-1"
	>
		<div class="bg-accent/10 text-accent flex h-16 w-16 items-center justify-center rounded-full">
			<ScanText class="h-8 w-8" />
		</div>
		<div class="flex flex-col gap-2">
			<h3 class="text-lg font-bold text-black">Detection Required</h3>
			<p class="max-w-[280px] text-sm text-gray-500">
				To typeset translated text, we first need to detect speech bubbles on this page.
			</p>
		</div>
		<Button
			class="flex w-full items-center justify-center gap-2 shadow-sm"
			onclick={handleDetectClick}
			disabled={editorState.isProcessing}
		>
			{#if editorState.isProcessing}
				<Loader2 class="h-4 w-4 animate-spin" />
				Detecting...
			{:else}
				<ScanText class="h-4 w-4" />
				Detect Speech Bubbles
			{/if}
		</Button>
	</div>
{:else}
	<div
		class="border-primary-border ring-accent flex h-auto flex-col gap-5 rounded-lg border-2 bg-white p-4 ring-1"
	>
		<div class="flex flex-col gap-5">
			<!-- Header -->
			<div class="flex flex-row items-center justify-between">
				<div class="ml-1 flex flex-row items-center gap-4">
					<Type class="text-accent h-5 w-5" />
					<p class="font-semibold text-black">Typesetting Panel</p>
				</div>
				<div class="flex flex-row gap-2">
					<Button
						class="h-8 w-8 rounded-full p-2"
						variant="outline"
						onclick={handlePrev}
						disabled={totalBubbles <= 1}
					>
						<ChevronLeft class="h-4 w-4" />
					</Button>
					<Button
						class="h-8 w-8 rounded-full p-2"
						variant="outline"
						onclick={handleNext}
						disabled={totalBubbles <= 1}
					>
						<ChevronRight class="h-4 w-4" />
					</Button>
				</div>
			</div>
			<!-- Bubble Counter -->
			<div class="flex w-full flex-row justify-between px-1">
				<p class="text-sm font-semibold text-black">Speech Bubbles</p>
				<p class="text-sm font-semibold text-black">
					{totalBubbles > 0 ? activeBubbleIndex + 1 : 0} of {totalBubbles}
				</p>
			</div>
			<Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200" />
			{#if activeBubble && editorState.activePage && activeBubbleIndex >= 0}
				{@const typeset = activeBubble.typeset ?? DEFAULT_TYPESET_STYLE}
				<!-- English Text -->
				<div class="flex flex-col gap-2 px-1">
					<p class="text-sm font-semibold text-black">English Text</p>
					<textarea
						bind:value={editorState.activePage.bubbles[activeBubbleIndex].en_text}
						oninput={handleStyleChange}
						class="border-primary-border focus:outline-accent focus:ring-accent w-full resize-none rounded-lg border bg-white px-3 py-2 text-start text-sm text-black focus:ring-1"
						rows="3"
						placeholder="Enter English text..."
					></textarea>
				</div>
				<Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200" />
				<!-- Font Family -->
				<div class="flex flex-col gap-2 px-1">
					<div class="flex items-center justify-between">
						<p class="text-sm font-semibold text-black">Font Family</p>
						<Button variant="outline" size="sm" class="h-6 px-2 text-xs" onclick={loadLocalFonts} disabled={localFontsLoaded || isFontLoading}>
							{isFontLoading ? 'Loading...' : localFontsLoaded ? 'System Fonts Loaded' : 'Load System Fonts'}
						</Button>
					</div>
					<select
						value={typeset.fontFamily}
						onchange={(e) => {
							if (editorState.activePage && activeBubbleIndex >= 0) {
								if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
									editorState.activePage.bubbles[activeBubbleIndex].typeset = {
										...DEFAULT_TYPESET_STYLE
									};
								}
								editorState.activePage.bubbles[activeBubbleIndex].typeset!.fontFamily = (
									e.target as HTMLSelectElement
								).value;
								handleStyleChange();
							}
						}}
						class="border-primary-border focus:outline-accent focus:ring-accent w-full rounded-lg border bg-white px-3 py-2 text-sm text-black focus:ring-1"
					>
						{#each fontOptions as font}
							<option value={font.value} style="font-family: '{font.value}', sans-serif;"
								>{font.label}</option
							>
						{/each}
					</select>
					{#if selectedFontMetadata}
						<div class="mt-1 flex flex-col gap-1.5 rounded-lg border border-accent/20 bg-accent/5 p-3 text-xs shadow-inner">
							<div class="flex items-center justify-between">
								<span class="font-semibold text-gray-500">Style:</span>
								<span class="font-medium text-black">{selectedFontMetadata.styleType}</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="font-semibold text-gray-500">Purpose:</span>
								<span class="font-medium text-black text-right">{selectedFontMetadata.purpose}</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="font-semibold text-gray-500">Tone:</span>
								<span class="font-medium text-accent font-bold">{selectedFontMetadata.tone}</span>
							</div>
						</div>
					{/if}
				</div>
				<!-- Font Size + Auto-Fit -->
				<div class="flex flex-col gap-2 px-1">
					<div class="flex items-center justify-between">
						<p class="text-sm font-semibold text-black">Font Size</p>
						<label class="flex items-center gap-2 text-xs text-gray-500">
							<input
								type="checkbox"
								checked={typeset.autoFit}
								onchange={(e) => {
									if (editorState.activePage && activeBubbleIndex >= 0) {
										if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
											editorState.activePage.bubbles[activeBubbleIndex].typeset = {
												...DEFAULT_TYPESET_STYLE
											};
										}
										editorState.activePage.bubbles[activeBubbleIndex].typeset!.autoFit = (
											e.target as HTMLInputElement
										).checked;
										handleStyleChange();
									}
								}}
								class="accent-accent h-3.5 w-3.5 rounded"
							/>
							Auto-fit
						</label>
					</div>
					<div class="flex items-center gap-3">
						<input
							type="range"
							min="6"
							max="120"
							value={typeset.fontSize}
							disabled={typeset.autoFit}
							oninput={(e) => {
								if (editorState.activePage && activeBubbleIndex >= 0) {
									if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
										editorState.activePage.bubbles[activeBubbleIndex].typeset = {
											...DEFAULT_TYPESET_STYLE
										};
									}
									editorState.activePage.bubbles[activeBubbleIndex].typeset!.fontSize = Number(
										(e.target as HTMLInputElement).value
									);
									handleStyleChange();
								}
							}}
							class="accent-accent w-full disabled:opacity-40"
						/>
						<input
							type="number"
							min="6"
							max="120"
							value={typeset.fontSize}
							disabled={typeset.autoFit}
							oninput={(e) => {
								if (editorState.activePage && activeBubbleIndex >= 0) {
									if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
										editorState.activePage.bubbles[activeBubbleIndex].typeset = {
											...DEFAULT_TYPESET_STYLE
										};
									}
									editorState.activePage.bubbles[activeBubbleIndex].typeset!.fontSize = Number(
										(e.target as HTMLInputElement).value
									);
									handleStyleChange();
								}
							}}
							class="border-primary-border w-16 rounded-lg border bg-white px-2 py-1 text-center text-sm text-black disabled:opacity-40"
						/>
					</div>
				</div>
				<!-- Font Weight & Color Row -->
				<div class="flex flex-row gap-3 px-1 items-end">
					<!-- Font Weight Slider -->
					<div class="flex flex-1 flex-col gap-2">
						<div class="flex justify-between items-center">
							<p class="text-sm font-semibold text-black">Weight</p>
							<span class="text-xs text-accent font-bold">{typeset.fontWeight === 'bold' ? 700 : typeset.fontWeight === 'normal' ? 400 : typeset.fontWeight}</span>
						</div>
						<input
							type="range"
							min="100"
							max="900"
							step="100"
							value={typeset.fontWeight === 'bold' ? 700 : typeset.fontWeight === 'normal' ? 400 : Number(typeset.fontWeight) || 400}
							oninput={(e) => {
								if (editorState.activePage && activeBubbleIndex >= 0) {
									if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
										editorState.activePage.bubbles[activeBubbleIndex].typeset = {
											...DEFAULT_TYPESET_STYLE
										};
									}
									editorState.activePage.bubbles[activeBubbleIndex].typeset!.fontWeight = Number((e.target as HTMLInputElement).value);
									handleStyleChange();
								}
							}}
							class="accent-accent w-full"
						/>
					</div>
					<!-- Text Color -->
					<div class="flex flex-1 flex-col gap-2">
						<p class="text-sm font-semibold text-black">Text Color</p>
						<div class="flex items-center gap-2">
							<input
								type="color"
								value={typeset.fontColor}
								oninput={(e) => {
									if (editorState.activePage && activeBubbleIndex >= 0) {
										if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
											editorState.activePage.bubbles[activeBubbleIndex].typeset = {
												...DEFAULT_TYPESET_STYLE
											};
										}
										editorState.activePage.bubbles[activeBubbleIndex].typeset!.fontColor = (
											e.target as HTMLInputElement
										).value;
										handleStyleChange();
									}
								}}
								class="h-9 w-9 cursor-pointer rounded-lg border-2 border-gray-200 p-0.5"
							/>
							<span class="text-xs font-medium text-gray-500">{typeset.fontColor}</span>
						</div>
					</div>
				</div>
				<!-- Text Alignment -->
				<div class="flex flex-col gap-2 px-1">
					<p class="text-sm font-semibold text-black">Alignment</p>
					<div class="border-primary-border flex flex-row rounded-lg border-2 p-0.5">
						{#each [{ value: 'left', icon: AlignLeft }, { value: 'center', icon: AlignCenter }, { value: 'right', icon: AlignRight }] as alignOpt}
							{@const Icon = alignOpt.icon}
							<button
								onclick={() => {
									if (editorState.activePage && activeBubbleIndex >= 0) {
										if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
											editorState.activePage.bubbles[activeBubbleIndex].typeset = {
												...DEFAULT_TYPESET_STYLE
											};
										}
										editorState.activePage.bubbles[activeBubbleIndex].typeset!.textAlign =
											alignOpt.value as 'left' | 'center' | 'right';
										handleStyleChange();
									}
								}}
								class="flex flex-1 items-center justify-center rounded-md py-1.5 text-sm transition-colors {typeset.textAlign ===
								alignOpt.value
									? 'bg-accent/15 text-accent'
									: 'text-gray-500 hover:bg-gray-100'}"
							>
								<Icon class="h-4 w-4" />
							</button>
						{/each}
					</div>
				</div>
				<!-- Line Height -->
				<div class="flex flex-col gap-2 px-1">
					<div class="flex items-center justify-between">
						<p class="text-sm font-semibold text-black">Line Height</p>
						<span class="text-accent text-sm font-bold">{typeset.lineHeight.toFixed(1)}</span>
					</div>
					<input
						type="range"
						min="0.8"
						max="2.5"
						step="0.1"
						value={typeset.lineHeight}
						oninput={(e) => {
							if (editorState.activePage && activeBubbleIndex >= 0) {
								if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
									editorState.activePage.bubbles[activeBubbleIndex].typeset = {
										...DEFAULT_TYPESET_STYLE
									};
								}
								editorState.activePage.bubbles[activeBubbleIndex].typeset!.lineHeight = Number(
									(e.target as HTMLInputElement).value
								);
								handleStyleChange();
							}
						}}
						class="accent-accent w-full"
					/>
				</div>
				<!-- Letter Spacing -->
				<div class="flex flex-col gap-2 px-1">
					<div class="flex items-center justify-between">
						<p class="text-sm font-semibold text-black">Letter Spacing</p>
						<span class="text-accent text-sm font-bold">{typeset.letterSpacing.toFixed(1)}px</span>
					</div>
					<input
						type="range"
						min="-2"
						max="8"
						step="0.5"
						value={typeset.letterSpacing}
						oninput={(e) => {
							if (editorState.activePage && activeBubbleIndex >= 0) {
								if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
									editorState.activePage.bubbles[activeBubbleIndex].typeset = {
										...DEFAULT_TYPESET_STYLE
									};
								}
								editorState.activePage.bubbles[activeBubbleIndex].typeset!.letterSpacing = Number(
									(e.target as HTMLInputElement).value
								);
								handleStyleChange();
							}
						}}
						class="accent-accent w-full"
					/>
				</div>
				<Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200" />
				<!-- Position Offset -->
				<div class="flex flex-col gap-2 px-1">
					<div class="flex items-center gap-2">
						<Move class="h-4 w-4 text-gray-500" />
						<p class="text-sm font-semibold text-black">Position Offset</p>
					</div>
					<div class="flex flex-row gap-3">
						<div class="flex flex-1 flex-col gap-1">
							<label class="text-xs text-gray-500">X Offset</label>
							<input
								type="number"
								value={Math.round(typeset.offsetX)}
								oninput={(e) => {
									if (editorState.activePage && activeBubbleIndex >= 0) {
										if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
											editorState.activePage.bubbles[activeBubbleIndex].typeset = {
												...DEFAULT_TYPESET_STYLE
											};
										}
										editorState.activePage.bubbles[activeBubbleIndex].typeset!.offsetX = Number(
											(e.target as HTMLInputElement).value
										);
										handleStyleChange();
									}
								}}
								class="border-primary-border w-full rounded-lg border bg-white px-2 py-1.5 text-center text-sm text-black"
							/>
						</div>
						<div class="flex flex-1 flex-col gap-1">
							<label class="text-xs text-gray-500">Y Offset</label>
							<input
								type="number"
								value={Math.round(typeset.offsetY)}
								oninput={(e) => {
									if (editorState.activePage && activeBubbleIndex >= 0) {
										if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
											editorState.activePage.bubbles[activeBubbleIndex].typeset = {
												...DEFAULT_TYPESET_STYLE
											};
										}
										editorState.activePage.bubbles[activeBubbleIndex].typeset!.offsetY = Number(
											(e.target as HTMLInputElement).value
										);
										handleStyleChange();
									}
								}}
								class="border-primary-border w-full rounded-lg border bg-white px-2 py-1.5 text-center text-sm text-black"
							/>
						</div>
					</div>
				</div>
				<Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200" />
				<!-- Action Buttons -->
				<div class="flex flex-col gap-2">
					<Button
						variant="outline"
						class="border-primary-border flex w-full flex-row gap-2 border-2 text-accent hover:bg-accent/5 hover:border-accent"
						onclick={() => {
							if (editorState.activePage && activeBubble) {
								const currentStyle = activeBubble.typeset || DEFAULT_TYPESET_STYLE;
								for (const b of editorState.activePage.bubbles) {
									b.typeset = { ...currentStyle };
								}
								editorState.saveTypesetting();
							}
						}}
						disabled={totalBubbles === 0}
					>
						<p>Apply Style to All</p>
					</Button>
					<Button
						class="w-full"
						onclick={() => editorState.saveTypesetting()}
						disabled={totalBubbles === 0}
					>
						<p>Apply Typesetting</p>
					</Button>
					<Button
						variant="ghost"
						class="border-primary-border flex w-full flex-row gap-2 border-2 hover:border-amber-500 hover:bg-amber-50 hover:text-amber-600"
						onclick={resetCurrentBubble}
						disabled={totalBubbles === 0}
					>
						<RotateCcw class="h-4 w-4" />
						<p>Reset to Default</p>
					</Button>
				</div>
			{:else}
				<div class="flex flex-col items-center gap-3 py-6 text-center">
					<div
						class="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-gray-400"
					>
						<Type class="h-6 w-6" />
					</div>
					<p class="text-sm text-gray-500">No speech bubbles detected on this page.</p>
				</div>
			{/if}
		</div>
	</div>
{/if}
