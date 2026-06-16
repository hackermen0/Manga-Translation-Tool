<script lang="ts">
	import { Button, Open, historyManager } from '$lib';
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
		ScanText,
		Loader2
	} from '@lucide/svelte';

	const sections = [
		{ id: 'detection', name: 'Detection', icon: ScanText },
		{ id: 'translation', name: 'Translation', icon: Languages },
		{ id: 'redrawing', name: 'Redrawing', icon: Paintbrush },
		{ id: 'typesetting', name: 'Typesetting', icon: Type },
		{ id: 'quality', name: 'Quality Checking', icon: CheckCircle }
	];

	let isExportingAll = $state(false);

	async function handleExportAll() {
		if (!editorState.exportAllHandler) {
			alert('Export functionality is not ready yet. Please ensure the canvas has loaded the page.');
			return;
		}
		isExportingAll = true;
		try {
			await editorState.exportAllHandler();
		} catch (error) {
			console.error('Export all failed:', error);
			alert('Failed to export all pages: ' + (error instanceof Error ? error.message : String(error)));
		} finally {
			isExportingAll = false;
		}
	}
</script>

<div class="bg-white px-4 py-2">
	<div class="flex items-center justify-between">
		<div class="flex items-center space-x-4">
			<div class="flex items-center space-x-2">
				<Open buttonName="Open" variant="ghost" size="sm" icon={FolderOpen}/>
				<Button variant="ghost" size="sm" icon={Save}>Save</Button>
				<Button
					variant="ghost"
					size="sm"
					onclick={handleExportAll}
					disabled={isExportingAll}
				>
					{#if isExportingAll}
						<Loader2 class="h-4 w-4 animate-spin shrink-0" />
						Exporting...
					{:else}
						<Rocket class="h-4 w-4 shrink-0" />
						Export
					{/if}
				</Button>
			</div>

			<Separator.Root orientation="vertical" class="h-6 w-px shrink-0 bg-gray-200" />

			<div class="flex items-center space-x-1">
				<Button
					variant="ghost"
					size="sm"
					icon={Undo}
					onclick={() => historyManager.undo()}
					disabled={!historyManager.canUndo}
					title="Undo (Ctrl+Z)"
				/>
				<Button
					variant="ghost"
					size="sm"
					icon={Redo}
					onclick={() => historyManager.redo()}
					disabled={!historyManager.canRedo}
					title="Redo (Ctrl+Y)"
				/>
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

		<div class="flex items-center space-x-3">
			{#if editorState.workspaceName}
				<span class="text-xs font-semibold text-primary bg-primary/10 border border-primary/20 px-2.5 py-1 rounded-full">
					Workspace: {editorState.workspaceName}
				</span>
			{/if}
			<div class="text-sm font-medium text-gray-700">Manga Translator Pro</div>
		</div>
	</div>
</div>