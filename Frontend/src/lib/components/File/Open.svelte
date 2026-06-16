<script lang="ts" module>
	import type { Component } from 'svelte';
	import type { IconProps } from '@lucide/svelte';

	interface Props {
		buttonName?: string;
		variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
		size?: 'default' | 'sm' | 'lg' | 'icon';
		icon?: Component<IconProps, {}, ''>;
	}
</script>

<script lang="ts">
	import { Button, imageState, layerStateManager } from '$lib';
	import { editorState } from '$lib/stores/Editor.svelte';
	import { FolderOpen, Plus, Loader2 } from '@lucide/svelte';

	let fileInput = $state<HTMLInputElement | null>(null);
	let { buttonName, variant, size, icon }: Props = $props();

	let isUploading = $state(false);
	let dropdownOpen = $state(false);
	let dropdownRef = $state<HTMLDivElement | null>(null);
	let isLoadingWorkspaces = $state(false);

	interface WorkspaceMetadata {
		workspace_id: string;
		name: string;
		pages_count: number;
	}

	let workspaces = $state<WorkspaceMetadata[]>([]);
	const BACKEND_URL = 'http://127.0.0.1:8000';

	// Modal state for naming new workspace
	let showNameModal = $state(false);
	let workspaceNameInput = $state('');
	let selectedFilesList = $state<File[]>([]);

	async function fetchWorkspaces() {
		isLoadingWorkspaces = true;
		try {
			const response = await fetch(`${BACKEND_URL}/api/workspace`);
			if (response.ok) {
				const data = await response.json();
				workspaces = data.workspaces || [];
			}
		} catch (err) {
			console.error('Failed to fetch workspaces:', err);
		} finally {
			isLoadingWorkspaces = false;
		}
	}

	function toggleDropdown(e: MouseEvent) {
		e.stopPropagation();
		dropdownOpen = !dropdownOpen;
		if (dropdownOpen) {
			fetchWorkspaces();
		}
	}

	function handleWindowClick(e: MouseEvent) {
		if (dropdownOpen && dropdownRef && !dropdownRef.contains(e.target as Node)) {
			dropdownOpen = false;
		}
	}

	async function selectWorkspace(workspaceId: string) {
		dropdownOpen = false;
		if (editorState.workspaceId === workspaceId) return;

		try {
			const response = await fetch(`${BACKEND_URL}/api/workspace/${workspaceId}`);
			if (!response.ok) {
				throw new Error(`Load failed with status: ${response.status}`);
			}
			const result = await response.json();
			if (result.status === 'success') {
				editorState.initWorkspace(result.workspace);
			}
		} catch (error) {
			console.error('Failed to load workspace:', error);
			alert('Error loading the workspace.');
		}
	}

	function triggerNewWorkspace(e: MouseEvent) {
		e.stopPropagation();
		dropdownOpen = false;
		if (fileInput) {
			fileInput.click();
		}
	}

	function handleFileSelection(event: Event) {
		const target = event.target as HTMLInputElement;
		const files = target.files;

		if (!files || files.length === 0) return;

		selectedFilesList = Array.from(files);
		workspaceNameInput = '';
		showNameModal = true;
		target.value = '';
	}

	function cancelCreation() {
		showNameModal = false;
		selectedFilesList = [];
		workspaceNameInput = '';
	}

	async function handleCreateWorkspace() {
		if (selectedFilesList.length === 0) return;
		if (!workspaceNameInput.trim()) return;

		isUploading = true;
		const nameToUse = workspaceNameInput.trim();

		try {
			const formData = new FormData();
			selectedFilesList.forEach((file) => {
				formData.append('files', file);
			});
			formData.append('name', nameToUse);

			const response = await fetch(`${BACKEND_URL}/api/workspace/create`, {
				method: 'POST',
				body: formData
			});

			if (!response.ok) {
				throw new Error(`Upload failed with status: ${response.status}`);
			}

			const result = await response.json();

			if (result.status === 'success') {
				editorState.initWorkspace(result.workspace);

				showNameModal = false;
				selectedFilesList = [];
				workspaceNameInput = '';
			}
		} catch (error) {
			console.error('Failed to upload chapter files:', error);
			alert('Error uploading files to the backend server.');
		} finally {
			isUploading = false;
		}
	}

	function focusInput(node: HTMLInputElement) {
		node.focus();
	}
</script>

<svelte:window onclick={handleWindowClick} />

<input
	bind:this={fileInput}
	type="file"
	id="manga_image"
	accept="image/png, image/jpeg, image/webp"
	multiple
	class="hidden"
	onchange={handleFileSelection}
	disabled={isUploading}
/>

<div class="relative inline-block text-left" bind:this={dropdownRef}>
	<Button variant={variant} size={size} icon={icon} onclick={toggleDropdown} disabled={isUploading}>
		{isUploading ? 'Uploading...' : buttonName}
	</Button>

	{#if dropdownOpen}
		<div
			class="absolute left-0 z-50 mt-2 flex w-72 origin-top-left flex-col gap-1 overflow-hidden rounded-xl border border-gray-100 bg-white py-2 text-black shadow-2xl ring-1 ring-black/5 transition-all duration-200"
		>
			<div
				class="flex items-center justify-between border-b border-gray-100 px-4 py-2 text-xs font-semibold tracking-wider text-gray-500 uppercase"
			>
				<span>Select Workspace</span>
				{#if isLoadingWorkspaces}
					<Loader2 class="h-3 w-3 animate-spin text-gray-400" />
				{/if}
			</div>

			<div class="max-h-60 overflow-y-auto py-1">
				{#if isLoadingWorkspaces && workspaces.length === 0}
					<div class="flex items-center gap-2 px-4 py-3 text-sm text-gray-400">
						<Loader2 class="text-primary h-4 w-4 animate-spin" />
						<span>Loading workspaces...</span>
					</div>
				{:else if workspaces.length === 0}
					<div class="px-4 py-3 text-sm text-gray-400 italic">No workspaces found.</div>
				{:else}
					{#each workspaces as ws}
						<button
							class="flex w-full items-center justify-between border-l-4 px-4 py-2.5 text-left text-sm transition-all duration-150 hover:bg-gray-50 {editorState.workspaceId ===
							ws.workspace_id
								? 'bg-primary/5 text-primary border-primary font-semibold'
								: 'border-transparent text-gray-700 hover:text-gray-900'}"
							onclick={() => selectWorkspace(ws.workspace_id)}
						>
							<span class="truncate pr-2">{ws.name}</span>
							<span
								class="shrink-0 rounded-full border border-gray-200 bg-gray-100 px-1.5 py-0.5 text-xs text-gray-400"
							>
								{ws.pages_count}
								{ws.pages_count === 1 ? 'page' : 'pages'}
							</span>
						</button>
					{/each}
				{/if}
			</div>

			<div class="mt-1 border-t border-gray-100 pt-1">
				<button
					class="text-primary flex w-full cursor-pointer items-center gap-2 px-4 py-2.5 text-left text-sm font-semibold transition-all duration-150 hover:bg-gray-50"
					onclick={triggerNewWorkspace}
				>
					<Plus class="text-primary h-4 w-4" />
					New Workspace...
				</button>
			</div>
		</div>
	{/if}
</div>

{#if showNameModal}
	<div
		class="animate-in fade-in fixed inset-0 z-[100] flex items-center justify-center bg-black/50 duration-200"
	>
		<div
			class="animate-in zoom-in-95 w-[90vw] max-w-md rounded-2xl border border-gray-100 bg-white p-6 text-black shadow-2xl duration-200"
		>
			<h3 class="mb-2 text-lg font-bold text-gray-900">Name Your Workspace</h3>
			<p class="mb-4 text-sm text-gray-500">
				Please enter a name for the new workspace with the {selectedFilesList.length} selected image{selectedFilesList.length ===
				1
					? ''
					: 's'}.
			</p>

			<input
				use:focusInput
				type="text"
				bind:value={workspaceNameInput}
				placeholder="e.g., Chapter 1"
				class="focus:ring-primary mb-5 w-full rounded-xl border border-gray-300 bg-white px-3 py-2.5 text-black focus:ring-2 focus:outline-none"
				onkeydown={(e) => {
					if (e.key === 'Enter') handleCreateWorkspace();
				}}
				disabled={isUploading}
			/>

			<div class="flex justify-end gap-3">
				<Button variant="outline" size="sm" onclick={cancelCreation} disabled={isUploading}>
					Cancel
				</Button>
				<Button
					variant="default"
					size="sm"
					onclick={handleCreateWorkspace}
					disabled={!workspaceNameInput.trim() || isUploading}
				>
					{#if isUploading}
						<Loader2 class="h-4 w-4 shrink-0 animate-spin" />
						Creating...
					{:else}
						Create
					{/if}
				</Button>
			</div>
		</div>
	</div>
{/if}
