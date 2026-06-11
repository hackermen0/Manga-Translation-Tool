<script lang="ts">
    import { Languages, Scan, ChevronRight, ChevronLeft, Loader2, ScanText } from "@lucide/svelte";
    import { Button, GlossaryButton, editorState } from "$lib";
    import { Separator } from "bits-ui";

    let bubbles = $derived(editorState.activePage?.bubbles || []);
    let totalBubbles = $derived(bubbles.length);

    let activeBubbleIndex = $derived.by(() => {
        if (bubbles.length === 0) return -1;
        const idx = bubbles.findIndex(b => b.id === editorState.activeBubbleId);
        return idx !== -1 ? idx : 0;
    });

    let activeBubble = $derived(bubbles[activeBubbleIndex]);

    $effect(() => {
        if (bubbles.length > 0 && (editorState.activeBubbleId === null || !bubbles.some(b => b.id === editorState.activeBubbleId))) {
            editorState.activeBubbleId = bubbles[0].id;
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

    async function handleAutoDetect() {
        await editorState.runOcr();
    }

    async function handleDetectClick() {
        editorState.setActiveSession('detection');
        await editorState.detectBubbles();
    }
</script>

{#if editorState.activePage && !editorState.activePage.detected}
    <div class="h-auto p-6 border-2 border-primary-border border-dashed flex flex-col items-center justify-center text-center gap-6 rounded-lg bg-white shadow-sm ring-1 ring-accent/10">
        <div class="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center text-accent">
            <ScanText class="w-8 h-8" />
        </div>
        <div class="flex flex-col gap-2">
            <h3 class="font-bold text-black text-lg">Detection Required</h3>
            <p class="text-sm text-gray-500 max-w-[280px]">
                To translate text, we first need to detect speech bubbles on this page.
            </p>
        </div>
        <Button 
            class="w-full flex items-center justify-center gap-2 shadow-sm"
            onclick={handleDetectClick}
            disabled={editorState.isProcessing}
        >
            {#if editorState.isProcessing}
                <Loader2 class="w-4 h-4 animate-spin" />
                Detecting...
            {:else}
                <ScanText class="w-4 h-4" />
                Detect Speech Bubbles
            {/if}
        </Button>
    </div>
{:else}
    <div class="h-auto p-4 border-2 border-primary-border flex flex-col gap-5 rounded-lg ring-1 ring-accent bg-white">
        <div class="flex flex-col gap-6">
            <div class="flex flex-row justify-between items-center">
                <div class="flex flex-row gap-4 ml-1 items-center">
                    <Languages class="w-5 h-5 text-accent" />
                    <p class="font-semibold text-black">Translation Panel</p>
                </div>
                <div class="flex flex-row gap-2">
                    <Button 
                        class="rounded-full w-8 h-8 p-2" 
                        variant="outline" 
                        onclick={handlePrev}
                        disabled={totalBubbles <= 1}
                    >
                        <ChevronLeft class="w-4 h-4" />
                    </Button>
                    <Button 
                        class="rounded-full w-8 h-8 p-2" 
                        variant="outline" 
                        onclick={handleNext}
                        disabled={totalBubbles <= 1}
                    >
                        <ChevronRight class="w-4 h-4" />
                    </Button>
                </div>
            </div>

            <div class="w-full flex flex-col gap-3">
                <Button 
                    variant="ghost" 
                    class="w-full border-2 border-primary-border flex flex-row gap-3 hover:border-accent hover:text-accent hover:bg-accent/5"
                    onclick={handleAutoDetect}
                    disabled={editorState.isProcessing || totalBubbles === 0}
                >
                    {#if editorState.isProcessing}
                        <Loader2 class="w-4 h-4 animate-spin text-accent" />
                        <p class="text-accent">Running OCR...</p>
                    {:else}
                        <Scan class="w-4 h-4" />
                        <p>Auto-Detect Text</p>
                    {/if}
                </Button> 
                <GlossaryButton />
            </div>

            <Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200" />  

            <div class="flex flex-row justify-between w-full px-1">
                <p class="font-semibold text-black text-sm">Speech Bubbles</p>
                <p class="font-semibold text-black text-sm">
                    {totalBubbles > 0 ? activeBubbleIndex + 1 : 0} of {totalBubbles}
                </p>
            </div>  

            <div class="px-1 flex flex-col gap-2">
                <p class="font-semibold text-black text-sm">Original Text (JA)</p>
                {#if activeBubble}
                    <textarea 
                        bind:value={activeBubble.ja_text} 
                        oninput={() => editorState.saveBubbles()}
                        class="border-primary-border w-full rounded-lg border py-2 px-3 text-start bg-white text-black text-sm resize-none focus:outline-accent focus:ring-1 focus:ring-accent"
                        rows="3"
                        placeholder="Enter Japanese text..."
                    ></textarea>
                {:else}
                    <textarea 
                        value="" 
                        disabled 
                        class="border-primary-border w-full rounded-lg border py-2 px-3 text-start bg-gray-50 text-gray-400 text-sm resize-none"
                        rows="3"
                        placeholder="No speech bubbles found on this page."
                    ></textarea>
                {/if}
            </div>

            <div class="px-1 flex flex-col gap-2">
                <p class="font-semibold text-black text-sm">Translation (EN)</p>
                {#if activeBubble}
                    <textarea 
                        bind:value={activeBubble.en_text} 
                        oninput={() => editorState.saveBubbles()}
                        class="border-primary-border w-full rounded-lg border py-2 px-3 text-start bg-white text-black text-sm resize-none focus:outline-accent focus:ring-1 focus:ring-accent"
                        rows="3"
                        placeholder="Enter English translation..."
                    ></textarea>
                {:else}
                    <textarea 
                        value="" 
                        disabled 
                        class="border-primary-border w-full rounded-lg border py-2 px-3 text-start bg-gray-50 text-gray-400 text-sm resize-none"
                        rows="3"
                        placeholder="No speech bubbles found on this page."
                    ></textarea>
                {/if}
            </div>

            <div>
                <Button 
                    class="w-full"
                    onclick={() => editorState.saveBubbles()}
                    disabled={totalBubbles === 0}
                >
                    <p>Apply Translation</p>
                </Button>
            </div>
        </div>
    </div>
{/if}
