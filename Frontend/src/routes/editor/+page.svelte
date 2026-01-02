<script lang="ts">
	import { Explorer, Topbar, Bottombar, Canvas, RSidebar } from '$lib';
	import { editorState } from '$lib';

	const items = [
		{ value: '1', fileName: 'Image 1.png', type: 'image' },
		{ value: '2', fileName: 'Image 2.png', type: 'image' },
		{ value: '3', fileName: 'The biggest.png', type: 'image' },
		{ value: '4', fileName: 'Image 4.png', type: 'image' },
		{ value: '5', fileName: 'Image 5.png', type: 'image' },
		{ value: '6', fileName: 'Image 6.png', type: 'image' },
		{ value: '7', fileName: 'Image 7.png', type: 'image' },
		{ value: '8', fileName: 'Image 8.png', type: 'image' },
		{ value: '9', fileName: 'Image 9.png', type: 'image' },
		{
			value: '10',
			fileName: 'More Images',
			type: 'folder',
			items: [
				{ value: '1', fileName: 'Secret Image 1.png', type: 'image' },
				{ value: '2', fileName: 'Secret Image 2.png', type: 'image' },
				{ value: '3', fileName: 'Secret Image 3.png', type: 'image' },
				{ value: '4', fileName: 'Secret Image 4.png', type: 'image' },
				{
					value: '5',
					fileName: 'The biggest secret',
					type: 'folder',
					items: [
						{ value: '1', fileName: 'Super Secret 1.png', type: 'image' },
						{ value: '2', fileName: 'Super Secret 2.png', type: 'image' },
						{ value: '3', fileName: 'Super Secret 3.png', type: 'image' },
						{ value: '4', fileName: 'Super Secret 4.png', type: 'image' },
						{ value: '5', fileName: 'Super Secret 5.png', type: 'image' },
						{ value: '6', fileName: 'Super Secret 6.png', type: 'image' }
					]
				}
			]
		}
	];
</script>

<div class="bg-secondary flex h-screen w-screen flex-col overflow-hidden border-2">
	
	<div class="border-primary-border bg-background-light flex-none border-b-2">
		<Topbar />
	</div>

	<div class="flex flex-1 flex-row overflow-hidden">
		
		<div class="bg-background-light border-primary-border flex-none w-[279px] overflow-y-auto border-r-2">
			<Explorer items={items} />
		</div>

		<div class="flex-1 relative bg-gray-50 overflow-hidden">
			<Canvas />
		</div>

		<div class="bg-background-light border-primary-border flex-none w-[400px] overflow-y-auto border-l-2">
			<RSidebar/>
		</div>
	</div>

	<div class="bg-background-light border-primary-border flex-none h-[4rem] w-full flex-row items-center justify-center border-t-2">
		<Bottombar />
	</div>
</div>