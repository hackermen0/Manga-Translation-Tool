<script lang="ts">
	import { Upload, Plus } from '@lucide/svelte';
	import { Button } from '$lib';
</script>

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
		<Button icon={Upload} variant={'default'}>Upload Image</Button>
		<Button icon={Plus} variant={'outline'}>Create New Project</Button>
	</div>
</div>
