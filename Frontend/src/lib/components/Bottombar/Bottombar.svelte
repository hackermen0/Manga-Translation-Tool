<script lang="ts">
	import Magnifier from './Magnifier/Magnifier.svelte';
	import Settings from './Settings/Settings.svelte';
	import { editorState } from '$lib/stores/Editor.svelte';
	let currentPageNumber = $derived.by(() => {
		if (editorState.pages.length === 0 || !editorState.activePageId) return 0;
		const index = editorState.pages.findIndex(p => p.pageId === editorState.activePageId);
		return index !== -1 ? index + 1 : 0;
	});
</script>

<div class="px-4 flex h-full w-full flex-row justify-between">
	<div class="my-auto space-x-3 text-sm text-black">
		<Settings />
	</div>
	<div class="my-auto">
		<Magnifier />
	</div>
	<div class="my-auto space-x-3 text-sm text-gray-500">
		<span>Page {currentPageNumber} of {editorState.pages.length}</span>
		<span>•</span>
		<span>Auto Save: On</span>
	</div>
</div>