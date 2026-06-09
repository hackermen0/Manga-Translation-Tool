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
    import { Button } from '$lib';
    import { editorState } from '$lib/stores/Editor.svelte';

    let fileInput: HTMLElement;
    let { buttonName, variant, size, icon }: Props = $props();
    
    let isUploading = $state(false);

    let handleFileSelection = async (event: Event) => {
        const target = event.target as HTMLInputElement;
        const files = target.files;

        if (!files || files.length === 0) return;

        isUploading = true;

        try {
            const formData = new FormData();
            
            Array.from(files).forEach((file) => {
                formData.append('files', file);
            });

            const response = await fetch('http://127.0.0.1:8000/api/workspace/create', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed with status: ${response.status}`);
            }

            const result = await response.json();

            if (result.status === 'success') {
                console.log("Workspace initialized successfully:", result.workspace);
                
                editorState.initWorkspace(result.workspace);
                
                // (Optional) You can hook your layerStateManager here if you want to 
                // instantly load the first page's URL into the original layer right after upload.
            }

        } catch (error) {
            console.error("Failed to upload chapter files:", error);
            alert("Error uploading files to the backend server. Make sure FastAPI is running!");
        } finally {
            isUploading = false;
            target.value = "";
        }
    }
</script>

<input
    bind:this={fileInput}
    type="file"
    id="manga_image"
    accept="image/png, image/jpeg, image/webp"
    multiple
    class="hidden"
    onchange="{handleFileSelection}"
    disabled={isUploading}
/>

<Button 
    variant={variant} 
    size={size} 
    icon={icon} 
    onclick={() => fileInput.click()}
    disabled={isUploading}
>
    {isUploading ? 'Uploading...' : buttonName}
</Button>