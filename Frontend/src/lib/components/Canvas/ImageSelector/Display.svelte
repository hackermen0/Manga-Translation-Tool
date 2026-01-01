<script lang="ts">


    import { imageState } from "$lib";

    function handleInput(event: Event) {
        const target = event.target as HTMLElement;
    }

</script>

<div class="flex w-full flex-row items-center justify-center gap-1">
	<input
		type="text"
		value={`${imageState.imageIndex + 1}/${imageState.layerList.length}`}
        disabled
		class="border-primary-border h-7 w-16 rounded-lg border py-2 text-center ring-1 ring-accent"
	/>
</div>