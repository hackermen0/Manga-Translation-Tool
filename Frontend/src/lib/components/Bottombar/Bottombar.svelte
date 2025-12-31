<script lang="ts">
	import Magnifier from './Magnifier/Magnifier.svelte';
	import Settings from './Settings/Settings.svelte';
	import { Popover } from 'bits-ui';
</script>

<div class="mx-3 flex h-full w-full flex-row justify-between px-1">
	<div class="my-auto space-x-3 text-sm text-black">
		<!-- <span>1920 x 1080 px</span>
		<span>•</span>
		<span>RGB/8</span> -->
		<Settings />
	</div>
	<div class="my-auto">
		<Magnifier />
	</div>
	<div class="my-auto space-x-3 text-sm text-gray-500">
		<span>Page 1 of 1</span>
		<span>•</span>
		<span>Auto Save: On</span>
	</div>
</div>
