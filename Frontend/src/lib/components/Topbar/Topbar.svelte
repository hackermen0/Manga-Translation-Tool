<script lang="ts">
	import { Button, Open } from '$lib';
	import { editorState } from '$lib/stores/Editor.svelte';
	import { Separator } from 'bits-ui';
	import {
		Languages,
		Paintbrush,
		Type,
		CheckCircle,
		Save,
		FolderOpen,
		Undo,
		Redo,
		Rocket,
		ScanText 
	} from '@lucide/svelte';

	const sections = [
		{ id: 'detection', name: 'Detection', icon: ScanText },
		{ id: 'translation', name: 'Translation', icon: Languages },
		{ id: 'redrawing', name: 'Redrawing', icon: Paintbrush },
		{ id: 'typesetting', name: 'Typesetting', icon: Type },
		{ id: 'quality', name: 'Quality Checking', icon: CheckCircle }
	];
</script>

<div class="bg-white px-4 py-2">
	<div class="flex items-center justify-between">
		<div class="flex items-center space-x-4">
			<div class="flex items-center space-x-2">
				<Open buttonName="Open" variant="ghost" size="sm" icon={FolderOpen}/>
				<Button variant="ghost" size="sm" icon={Save}>Save</Button>
				<Button variant="ghost" size="sm" icon={Rocket}>Export</Button>
			</div>

			<Separator.Root orientation="vertical" class="h-6 w-px shrink-0 bg-gray-200" />

			<div class="flex items-center space-x-1">
				<Button variant="ghost" size="sm" icon={Undo} />
				<Button variant="ghost" size="sm" icon={Redo} />
			</div>

			<Separator.Root orientation="vertical" class="h-6 w-px shrink-0 bg-gray-200" />

			<div class="flex items-center space-x-1">
				{#each sections as section}
					<Button
						variant={editorState.activeSession === section.id ? 'default' : 'ghost'}
						size="sm"
						onclick={() => editorState.setActiveSession(section.id)}
						class="flex items-center space-x-2"
						icon={section.icon}
					>
						{section.name}
					</Button>
				{/each}
			</div>
		</div>

		<div class="flex items-center space-x-2">
			<div class="text-sm font-medium text-gray-700">Manga Translator Pro</div>
		</div>
	</div>
</div>