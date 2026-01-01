<script lang="ts">

	import { Languages, Scan, ChevronRight, ChevronLeft} from "@lucide/svelte";
    import { Button, GlossaryButton } from "$lib";

    import { Separator } from "bits-ui";

    let pages = 10;
    let pageNumber = $state(1);
    let originalText = "こんにちは";
    let translatedText = "Hello";


</script>

<div class="h-auto p-4 border-2 border-primary-border flex flex-col gap-5 rounded-lg ring-1 ring-accent">
    <div class="flex flex-col gap-6">
        <div class="flex flex-row justify-between">
            <div class="flex flex-row gap-4 ml-1">
                <Languages />
                <p class="font-semibold text-black">Translation Panel</p>
            </div>
            <div class="flex flex-row gap-4">
                <Button class="rounded-full w-8 h-8 p-2" variant="outline" onclick={() => {pageNumber--}}>
                    <ChevronLeft/>
                </Button>
                <Button class="rounded-full w-8 h-8 p-2" variant="outline" onclick={() => {pageNumber++}}>
                    <ChevronRight/>
                </Button>
            </div>
        </div>
            <div class="w-full flex flex-col gap-3">
                <Button variant={"ghost"} class="w-full border-2 border-primary-border flex flex-row gap-3 hover:border-transparent">
                    <Scan/>
                    <p>Auto-Detect Text</p>
                </Button> 
                <GlossaryButton/>
            </div>
        <Separator.Root orientation="horizontal" class="h-[2px] w-full shrink-0 bg-gray-200"/>  
        <div class="flex flex-row justify-between w-full px-1">
            <p class="font-semibold text-black text-sm">Speech Bubbles</p>
            <p class="font-semibold text-black text-sm">{pageNumber} of {pages}</p>
        </div>  
        <div class="px-1 flex flex-col gap-2">
            <p class="font-semibold text-black text-sm">Original Text</p>
            <input value={originalText} type="text" class="border-primary-border w-full rounded-lg border py-2 px-3 text-start">
        </div>
        <div class="px-1 flex flex-col gap-2">
            <p class="font-semibold text-black text-sm">Translation</p>
            <input value={translatedText} type="text" class="border-primary-border w-full rounded-lg border py-2 px-3 text-start">
        </div>
        <div>
            <Button class="w-full">
                <p>Apply Translation</p>
            </Button>
        </div>
    </div>
</div>


