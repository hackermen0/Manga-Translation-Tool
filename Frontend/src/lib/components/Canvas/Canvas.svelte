<script lang="ts">
	import { Upload, Plus, ChevronRight, ChevronLeft } from '@lucide/svelte';
	import Display from './ImageSelector/Display.svelte';
	import { Button } from '$lib';
	import { imageState } from '$lib';
	import { Open } from '$lib';

	let images = $derived(imageState.layerList);
	let imageIndex = $derived(imageState.imageIndex);
	let imagesLength = $derived(imageState.layerList.length);

	$effect(() => console.log(images));

	
</script>

<div>
	{#if images.length > 0}

	<div>
		<img src={images[imageIndex].imageURL} alt={images[imageIndex].name}/>
		<div class="flex flex-row">
			<Button icon={ChevronLeft} onclick={() => imageState.decrementIndex()} disabled={imageIndex == 0}></Button>
			<Display/>
			<Button icon={ChevronRight} onclick={() => imageState.incrementIndex()} disabled={imageIndex == imagesLength - 1}></Button>
		</div>
	</div>
		

	{:else}
	<div class="flex flex-col gap-3 text-black">
		<div
			class="mx-auto flex aspect-square w-32 items-center justify-center rounded-lg border-3 border-dashed border-gray-400 text-gray-400"
		>
			<Upload size={48} />
		</div>
		<p class="text-center text-lg font-semibold">Import Manga Page</p>
		<p class="text-center text-base font-semibold text-slate-500">
			Upload a manga page to start translating
		</p>
		<div class="flex flex-row items-center justify-center gap-3">
			<Open buttonName={"Upload Image"} variant={"default"} icon={Upload}/>
			<Button icon={Plus} variant={'outline'}>Create New Project</Button>
		</div>
	</div>
	{/if}
</div>