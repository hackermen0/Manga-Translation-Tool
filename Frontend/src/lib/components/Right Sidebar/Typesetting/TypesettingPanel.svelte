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
		Move,
		Italic
	} from '@lucide/svelte';
	import { Button, editorState, historyManager } from '$lib';
	import { DEFAULT_TYPESET_STYLE } from '$lib/stores/Editor.svelte';
	import { Separator } from 'bits-ui';
	let fontOptions = $state([
		{
			label: 'CC Wild Words',
			value: 'CC Wild Words',
			styleType: 'Comic Serif/Sans Mix',
			purpose: 'Standard Dialogue',
			tone: 'Neutral / Narrative'
		},
		{
			label: 'Manga Temple',
			value: 'Manga Temple',
			styleType: 'Classic Manga Sans',
			purpose: 'Standard Dialogue',
			tone: 'Traditional / Narrative'
		},
		{
			label: 'Anime Ace',
			value: 'Anime Ace',
			styleType: 'Clean Comic Sans',
			purpose: 'Budget Standard Speech',
			tone: 'Casual / Friendly'
		},
		{
			label: 'Komika Hands',
			value: 'Komika Hands',
			styleType: 'Clean Dialogue Sans',
			purpose: 'Modern Speech / Thoughts',
			tone: 'Friendly / Energetic'
		},
		{
			label: 'Komika Axis',
			value: 'Komika Axis',
			styleType: 'Heavy Rounded Comic',
			purpose: 'Exclamations / Main Dialogue',
			tone: 'Impactful / Confident'
		},
		{
			label: 'Creative Block BB',
			value: 'Creative Block BB',
			styleType: 'Square Comic Sans',
			purpose: 'Heroic Dialogue / Main Story',
			tone: 'Bold / Energetic'
		},
		{
			label: 'Badaboom BB',
			value: 'Badaboom BB',
			styleType: 'Action SFX Display',
			purpose: 'Screaming / Sound Effects',
			tone: 'Excited / High Impact'
		},
		{
			label: 'Damn Noisy Kids',
			value: 'Damn Noisy Kids',
			styleType: 'Jittery SFX',
			purpose: 'Angry Shouting / SFX',
			tone: 'Aggressive / Loud'
		},
		{
			label: 'Feast of Flesh BB',
			value: 'Feast of Flesh BB',
			styleType: 'Distressed Horror Display',
			purpose: 'Demons / Threatening Speech / SFX',
			tone: 'Scary / Creepy / Menacing'
		},
		{
			label: 'CC Lettering Black',
			value: 'CC Lettering Black',
			styleType: 'Heavy Gothic/Bold',
			purpose: 'Villains / Dark Artifacts',
			tone: 'Menacing / Authoritative'
		},
		{
			label: 'Whiz Bang',
			value: 'Whiz Bang',
			styleType: 'Jittery / Angular',
			purpose: 'Screaming / Shock',
			tone: 'Panicked / High Energy'
		},
		{
			label: 'Catholic School Girls',
			value: 'Catholic School Girls',
			styleType: 'Chalkboard Handwriting',
			purpose: 'Side Notes / Whispers / Flashbacks',
			tone: 'Cute / Playful'
		},
		{
			label: 'Kid Kosmic',
			value: 'Kid Kosmic',
			styleType: 'Blocky Comic Handwriting',
			purpose: 'Internal Thoughts / Child Characters',
			tone: 'Whimsical / Innocent'
		},
		{
			label: 'Augie',
			value: 'Augie',
			styleType: 'Handwriting',
			purpose: 'Internal Monologue',
			tone: 'Intimate / Reflective'
		}
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
		fontOptions.find(
			(f) => f.value === (activeBubble?.typeset?.fontFamily || DEFAULT_TYPESET_STYLE.fontFamily)
		)
	);

	let localFontsLoaded = $state(false);
	let isFontLoading = $state(false);

	async function loadLocalFonts() {
		if (!('queryLocalFonts' in window)) {
			alert(
				'Your browser does not support the Local Font Access API. Please use a Chromium-based browser (Chrome, Edge).'
			);
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

			const newFonts = Array.from(uniqueFonts).map((f) => ({
				label: f,
				value: f,
				styleType: 'System Font',
				purpose: 'User Installed',
				tone: 'Varies'
			}));

			for (const nf of newFonts) {
				if (!fontOptions.find((opt) => opt.value === nf.value)) {
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
	let stylePendingSnapshot: any = null;
	let typingTimeout: any = null;

	function startStyleChange() {
		if (!stylePendingSnapshot && editorState.activePageId) {
			stylePendingSnapshot = historyManager.captureSnapshot(editorState.activePageId);
		}
	}

	function endStyleChange() {
		if (stylePendingSnapshot && editorState.activePageId) {
			historyManager.recordSnapshotChange(editorState.activePageId, stylePendingSnapshot);
			stylePendingSnapshot = null;
		}
	}

	function handleTextFocus() {
		startStyleChange();
	}

	function handleTextInput() {
		if (typingTimeout) clearTimeout(typingTimeout);
		typingTimeout = setTimeout(() => {
			if (!stylePendingSnapshot || !editorState.activePageId) return;
			const currentSnapshot = historyManager.captureSnapshot(editorState.activePageId);
			if (
				currentSnapshot &&
				JSON.stringify(currentSnapshot) !== JSON.stringify(stylePendingSnapshot)
			) {
				historyManager.pushSnapshot(stylePendingSnapshot);
				stylePendingSnapshot = currentSnapshot;
			}
		}, 1000);
		handleStyleChange();
	}

	function handleTextBlur() {
		if (typingTimeout) clearTimeout(typingTimeout);
		endStyleChange();
	}

	function resetCurrentBubble() {
		if (!activeBubble || !editorState.activePage) return;
		historyManager.recordState(editorState.activePageId!);
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
						onfocus={handleTextFocus}
						oninput={handleTextInput}
						onblur={handleTextBlur}
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
						<Button
							variant="outline"
							size="sm"
							class="h-6 px-2 text-xs"
							onclick={loadLocalFonts}
							disabled={localFontsLoaded || isFontLoading}
						>
							{isFontLoading
								? 'Loading...'
								: localFontsLoaded
									? 'System Fonts Loaded'
									: 'Load System Fonts'}
						</Button>
					</div>
					<select
						value={typeset.fontFamily}
						onchange={(e) => {
							if (editorState.activePage && activeBubbleIndex >= 0) {
								startStyleChange();
								if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
									editorState.activePage.bubbles[activeBubbleIndex].typeset = {
										...DEFAULT_TYPESET_STYLE
									};
								}
								editorState.activePage.bubbles[activeBubbleIndex].typeset!.fontFamily = (
									e.target as HTMLSelectElement
								).value;
								handleStyleChange();
								endStyleChange();
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
						<div
							class="border-accent/20 bg-accent/5 mt-1 flex flex-col gap-1.5 rounded-lg border p-3 text-xs shadow-inner"
						>
							<div class="flex items-center justify-between">
								<span class="font-semibold text-gray-500">Style:</span>
								<span class="font-medium text-black">{selectedFontMetadata.styleType}</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="font-semibold text-gray-500">Purpose:</span>
								<span class="text-right font-medium text-black">{selectedFontMetadata.purpose}</span
								>
							</div>
							<div class="flex items-center justify-between">
								<span class="font-semibold text-gray-500">Tone:</span>
								<span class="text-accent font-medium">{selectedFontMetadata.tone}</span>
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
										startStyleChange();
										if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
											editorState.activePage.bubbles[activeBubbleIndex].typeset = {
												...DEFAULT_TYPESET_STYLE
											};
										}
										editorState.activePage.bubbles[activeBubbleIndex].typeset!.autoFit = (
											e.target as HTMLInputElement
										).checked;
										handleStyleChange();
										endStyleChange();
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
							onpointerdown={startStyleChange}
							onchange={endStyleChange}
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
							onfocus={handleTextFocus}
							onblur={handleTextBlur}
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
									handleTextInput();
								}
							}}
							class="border-primary-border w-16 rounded-lg border bg-white px-2 py-1 text-center text-sm text-black disabled:opacity-40"
						/>
					</div>
				</div>
				<!-- Font Weight & Color Row -->
				<div class="flex flex-row items-end gap-3 px-1">
					<!-- Font Weight Slider -->
					<div class="flex flex-1 flex-col gap-2">
						<div class="flex items-center justify-between">
							<p class="text-sm font-semibold text-black">Weight</p>
							<span class="text-accent text-xs font-bold"
								>{typeset.fontWeight === 'bold'
									? 700
									: typeset.fontWeight === 'normal'
										? 400
										: typeset.fontWeight}</span
							>
						</div>
						<input
							type="range"
							min="100"
							max="900"
							step="100"
							value={typeset.fontWeight === 'bold'
								? 700
								: typeset.fontWeight === 'normal'
									? 400
									: Number(typeset.fontWeight) || 400}
							onpointerdown={startStyleChange}
							onchange={endStyleChange}
							oninput={(e) => {
								if (editorState.activePage && activeBubbleIndex >= 0) {
									if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
										editorState.activePage.bubbles[activeBubbleIndex].typeset = {
											...DEFAULT_TYPESET_STYLE
										};
									}
									editorState.activePage.bubbles[activeBubbleIndex].typeset!.fontWeight = Number(
										(e.target as HTMLInputElement).value
									);
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
								onpointerdown={startStyleChange}
								onchange={endStyleChange}
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
				<!-- Text Border Section -->
				<div class="flex flex-col gap-3 px-1">
					<div class="flex items-center justify-between">
						<p class="text-sm font-semibold text-black">Text Border</p>
						<label class="flex cursor-pointer items-center gap-2 text-xs text-gray-500 select-none">
							<input
								type="checkbox"
								checked={typeset.outline ?? false}
								onchange={(e) => {
									if (editorState.activePage && activeBubbleIndex >= 0) {
										startStyleChange();
										if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
											editorState.activePage.bubbles[activeBubbleIndex].typeset = {
												...DEFAULT_TYPESET_STYLE
											};
										}
										editorState.activePage.bubbles[activeBubbleIndex].typeset!.outline = (
											e.target as HTMLInputElement
										).checked;
										handleStyleChange();
										endStyleChange();
									}
								}}
								class="accent-accent h-4 w-4 rounded"
							/>
							Enable border
						</label>
					</div>

					{#if typeset.outline}
						<div class="flex flex-row gap-4">
							<!-- Border Size Slider -->
							<div class="flex flex-1 flex-col gap-1.5">
								<div class="flex items-center justify-between">
									<span class="text-xs font-semibold text-gray-500">Border Size</span>
									<span class="text-accent text-xs font-bold">{typeset.outlineWidth ?? 2}px</span>
								</div>
								<div class="flex items-center gap-2">
									<input
										type="range"
										min="1"
										max="15"
										step="0.5"
										value={typeset.outlineWidth ?? 2}
										onpointerdown={startStyleChange}
										onchange={endStyleChange}
										oninput={(e) => {
											if (editorState.activePage && activeBubbleIndex >= 0) {
												if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
													editorState.activePage.bubbles[activeBubbleIndex].typeset = {
														...DEFAULT_TYPESET_STYLE
													};
												}
												editorState.activePage.bubbles[activeBubbleIndex].typeset!.outlineWidth = Number(
													(e.target as HTMLInputElement).value
												);
												handleStyleChange();
											}
										}}
										class="accent-accent w-full"
									/>
								</div>
							</div>

							<!-- Border Color Picker -->
							<div class="flex flex-col gap-1.5">
								<span class="text-xs font-semibold text-gray-500">Border Color</span>
								<div class="flex items-center gap-2">
									<input
										type="color"
										value={typeset.outlineColor ?? '#ffffff'}
										onpointerdown={startStyleChange}
										onchange={endStyleChange}
										oninput={(e) => {
											if (editorState.activePage && activeBubbleIndex >= 0) {
												if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
													editorState.activePage.bubbles[activeBubbleIndex].typeset = {
														...DEFAULT_TYPESET_STYLE
													};
												}
												editorState.activePage.bubbles[activeBubbleIndex].typeset!.outlineColor = (
													e.target as HTMLInputElement
												).value;
												handleStyleChange();
											}
										}}
										class="h-8 w-8 cursor-pointer rounded-lg border border-gray-200 p-0.5"
									/>
									<span class="text-xs font-medium text-gray-500"
										>{typeset.outlineColor ?? '#ffffff'}</span
									>
								</div>
							</div>
						</div>
					{/if}
				</div>
				<!-- Alignment & Style Formatting -->
				<div class="flex flex-row gap-3 px-1">
					<!-- Alignment -->
					<div class="flex flex-1 flex-col gap-2">
						<p class="text-sm font-semibold text-black">Alignment</p>
						<div
							class="border-primary-border flex h-10 flex-row items-center rounded-lg border-2 bg-gray-50 p-0.5"
						>
							{#each [{ value: 'left', icon: AlignLeft }, { value: 'center', icon: AlignCenter }, { value: 'right', icon: AlignRight }] as alignOpt}
								{@const Icon = alignOpt.icon}
								<button
									onclick={() => {
										if (editorState.activePage && activeBubbleIndex >= 0) {
											startStyleChange();
											if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
												editorState.activePage.bubbles[activeBubbleIndex].typeset = {
													...DEFAULT_TYPESET_STYLE
												};
											}
											editorState.activePage.bubbles[activeBubbleIndex].typeset!.textAlign =
												alignOpt.value as 'left' | 'center' | 'right';
											handleStyleChange();
											endStyleChange();
										}
									}}
									class="flex h-full flex-1 items-center justify-center rounded-md text-sm transition-colors {typeset.textAlign ===
									alignOpt.value
										? 'bg-accent/15 text-accent font-bold'
										: 'text-gray-500 hover:bg-gray-200'}"
									title="Align {alignOpt.value}"
								>
									<Icon class="h-4 w-4" />
								</button>
							{/each}
						</div>
					</div>

					<!-- Formatting -->
					<div class="flex w-20 flex-col gap-2">
						<p class="text-center text-sm font-semibold text-black">Style</p>
						<div
							class="border-primary-border flex h-10 flex-row items-center justify-center rounded-lg border-2 bg-gray-50 p-0.5"
						>
							<button
								onclick={() => {
									if (editorState.activePage && activeBubbleIndex >= 0) {
										startStyleChange();
										if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
											editorState.activePage.bubbles[activeBubbleIndex].typeset = {
												...DEFAULT_TYPESET_STYLE
											};
										}
										const current =
											editorState.activePage.bubbles[activeBubbleIndex].typeset!.fontStyle;
										editorState.activePage.bubbles[activeBubbleIndex].typeset!.fontStyle =
											current === 'italic' ? 'normal' : 'italic';
										handleStyleChange();
										endStyleChange();
									}
								}}
								class="flex h-full w-full items-center justify-center rounded-md text-sm transition-colors {typeset.fontStyle ===
								'italic'
									? 'bg-accent/15 text-accent font-bold'
									: 'text-gray-500 hover:bg-gray-200'}"
								title="Italic"
							>
								<Italic class="h-4 w-4" />
							</button>
						</div>
					</div>
				</div>

				<!-- Writing Mode -->
				<div class="flex flex-col gap-2 px-1">
					<p class="text-sm font-semibold text-black">Writing Mode</p>
					<div class="border-primary-border flex flex-row rounded-lg border-2 bg-gray-50 p-0.5">
						<button
							onclick={() => {
								if (editorState.activePage && activeBubbleIndex >= 0) {
									startStyleChange();
									if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
										editorState.activePage.bubbles[activeBubbleIndex].typeset = {
											...DEFAULT_TYPESET_STYLE
										};
									}
									editorState.activePage.bubbles[activeBubbleIndex].typeset!.writingMode =
										'horizontal';
									handleStyleChange();
									endStyleChange();
								}
							}}
							class="flex-1 rounded-md py-1.5 text-xs font-semibold transition-colors {(typeset.writingMode ??
								'horizontal') === 'horizontal'
								? 'bg-accent text-white shadow-sm'
								: 'text-gray-500 hover:bg-gray-100'}"
						>
							Horizontal (Standard)
						</button>
						<button
							onclick={() => {
								if (editorState.activePage && activeBubbleIndex >= 0) {
									startStyleChange();
									if (!editorState.activePage.bubbles[activeBubbleIndex].typeset) {
										editorState.activePage.bubbles[activeBubbleIndex].typeset = {
											...DEFAULT_TYPESET_STYLE
										};
									}
									editorState.activePage.bubbles[activeBubbleIndex].typeset!.writingMode =
										'vertical';
									handleStyleChange();
									endStyleChange();
								}
							}}
							class="flex-1 rounded-md py-1.5 text-xs font-semibold transition-colors {(typeset.writingMode ??
								'horizontal') === 'vertical'
								? 'bg-accent text-white shadow-sm'
								: 'text-gray-500 hover:bg-gray-100'}"
						>
							Vertical (Manga)
						</button>
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
						onpointerdown={startStyleChange}
						onchange={endStyleChange}
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
						onpointerdown={startStyleChange}
						onchange={endStyleChange}
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
						<label class="flex flex-1 flex-col gap-1 text-xs text-gray-500">
							<span>X Offset</span>
							<input
								type="number"
								value={Math.round(typeset.offsetX)}
								onfocus={handleTextFocus}
								onblur={handleTextBlur}
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
										handleTextInput();
									}
								}}
								class="border-primary-border w-full rounded-lg border bg-white px-2 py-1.5 text-center text-sm text-black"
							/>
						</label>
						<label class="flex flex-1 flex-col gap-1 text-xs text-gray-500">
							<span>Y Offset</span>
							<input
								type="number"
								value={Math.round(typeset.offsetY)}
								onfocus={handleTextFocus}
								onblur={handleTextBlur}
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
										handleTextInput();
									}
								}}
								class="border-primary-border w-full rounded-lg border bg-white px-2 py-1.5 text-center text-sm text-black"
							/>
						</label>
					</div>
				</div>
				<Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200" />
				<!-- Action Buttons -->
				<div class="flex flex-col gap-2">
					<Button
						variant="outline"
						class="border-primary-border text-accent hover:bg-accent/5 hover:border-accent flex w-full flex-row gap-2 border-2"
						onclick={() => {
							if (editorState.activePage && activeBubble) {
								historyManager.recordState(editorState.activePageId!);
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
