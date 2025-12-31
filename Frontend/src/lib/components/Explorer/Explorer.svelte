<script lang="ts">
	export let items;

	import { Accordion } from 'bits-ui';
	import { ChevronRight } from '@lucide/svelte';
	import Image from './Image.svelte';
	import Folder from './Folder.svelte';
</script>

<Accordion.Root type="single" class="my-3 p-2 font-mono">
	<Accordion.Item>
		<Accordion.Header>
			<Accordion.Trigger
				class="mb-3 flex items-center gap-2 border-2 border-[#ffffff] transition-all [&[data-state=open]>svg]:rotate-90"
			>
				<ChevronRight />
				<span class="text-left font-sans text-[20px] font-semibold">Folder Name</span>
			</Accordion.Trigger>
		</Accordion.Header>

		<Accordion.Content>
			<div class="flex min-w-max flex-row gap-3 overflow-x-auto">
				<div class="ml-2.5 w-[2px] bg-black"></div>

				<div class="flex flex-col gap-2">
					{#each items as item (item.value)}
						{#if item.type === 'image'}
							<Image item={item} />
						{:else if item.type === 'folder'}
							<Folder items={item.items} />
						{/if}
					{/each}
				</div>
			</div>
		</Accordion.Content>
	</Accordion.Item>
</Accordion.Root>
