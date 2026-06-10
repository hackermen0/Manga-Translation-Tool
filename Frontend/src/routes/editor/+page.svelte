<script lang="ts">
	import { Filmstrip, Topbar, Bottombar, Canvas, RSidebar } from '$lib';
	import { editorState } from '$lib';
	import { onMount } from 'svelte';

	const BACKEND_URL = "http://127.0.0.1:8000";

	onMount(async () => {
		if (editorState.workspaceId) return;

		const savedWorkspaceId = localStorage.getItem('active_manga_workspace_id');
		if (!savedWorkspaceId) return;

		console.log(`Found active session: ${savedWorkspaceId}. Restoring...`);

		try {
			const response = await fetch(`${BACKEND_URL}/api/workspace/${savedWorkspaceId}`);
			if (!response.ok) {
				if (response.status === 404) localStorage.removeItem('active_manga_workspace_id');
				throw new Error("Could not find saved workspace on server.");
			}

			const result = await response.json();
			if (result.status === 'success') {
				editorState.initWorkspace(result.workspace);
			}
		} catch (err) {
			console.error("Failed to automatically rehydrate layout workspace state:", err);
		}
	});

</script>

<div class="bg-secondary flex h-screen w-screen flex-col overflow-hidden border-2">
	
	<div class="border-primary-border bg-background-light flex-none border-b-2">
		<Topbar />
	</div>

	<div class="flex flex-1 flex-row overflow-hidden">
		
		<div class="bg-background-light border-primary-border flex-none w-[279px] overflow-y-auto border-r-2">
			<Filmstrip/>
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