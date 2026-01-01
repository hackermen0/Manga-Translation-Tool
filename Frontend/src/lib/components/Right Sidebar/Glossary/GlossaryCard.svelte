<script>

	import { MoveRight, Trash2 } from "@lucide/svelte";
    import { Button } from "$lib";
    import { glossaryStateManager } from "$lib";

    let {id, originalGlossary, translatedGlossary} = $props()

</script>

<div class="w-full p-3 border-2 border-gray-200 rounded-lg flex flex-row justify-between items-center">
    <div class="flex flex-row gap-2">
        <p>{originalGlossary}</p>
        <MoveRight class="w-10 h-5"/>
        <p>{translatedGlossary}</p>
    </div>
    <div>
        <Button variant={"ghost"} onclick={() => glossaryStateManager.deleteGlossary(id)}>
            <Trash2/>
        </Button>
    </div>
</div>