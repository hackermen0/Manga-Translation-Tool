<script lang="ts">
	export let item;

	import { Image } from '@lucide/svelte';
</script>

<button
	type="button"
	class="flex w-full cursor-pointer flex-row gap-3 rounded border-2 border-[#ffffff] px-2 py-1 text-left transition-all outline-none hover:border-2 hover:border-[#a6a1aa] focus:border-2 focus:border-accent focus:shadow-[0_0_10px_3px_rgba(214,190,248,0.7)]"
>
	<Image />
	<p class="font-sans text-[14px] text-pretty">
		{item.fileName}
	</p>
</button>
