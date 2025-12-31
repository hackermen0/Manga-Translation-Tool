<script>
	export let items;

	import { Accordion } from 'bits-ui';
	import { FolderClosed, FolderOpen } from '@lucide/svelte';

	import Image from './Image.svelte';
</script>

<Accordion.Root type="single" class="font-mono">
	<Accordion.Item>
		<Accordion.Header>
			<Accordion.Trigger
				class="mb-3 flex items-center gap-3 rounded border-2 border-none px-2 py-1 transition-all hover:border-2 hover:border-[#a6a1aa] [&[data-state=open]>#folder-close]:hidden [&[data-state=open]>#folder-open]:block"
			>
				<FolderClosed id="folder-close" />

				<FolderOpen id="folder-open" class="hidden" />

				<p class="text-left font-sans text-[14px]">Folder Name</p>
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
							<svelte:self items={item.items} />
						{/if}
					{/each}
				</div>
			</div>
		</Accordion.Content>
	</Accordion.Item>
</Accordion.Root>
