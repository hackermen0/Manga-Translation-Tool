<script lang="ts">
	import { ScrollArea } from 'bits-ui';
	import { Layers, TranslationPanel } from '$lib';
	import { editorState } from '$lib';
</script>

<ScrollArea.Root class="h-full w-full">
	<ScrollArea.Viewport class="h-full w-full">
		<div class="flex flex-col gap-10 p-4">
			<Layers />
			{#if editorState.activeSession === 'translation'}
				<TranslationPanel />
			{/if}
		</div>
	</ScrollArea.Viewport>

	<ScrollArea.Scrollbar
		orientation="vertical"
		class="hover:bg-dark-10 w-2.5 p-px transition-all duration-200 hover:w-3"
	>
		<ScrollArea.Thumb class="bg-primary flex-1 rounded-full" />
	</ScrollArea.Scrollbar>

	<ScrollArea.Corner />
</ScrollArea.Root>
