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

    let fileInput: HTMLElement;
    let { buttonName, variant, size, icon }: Props = $props();
    
    let isUploading = $state(false);
    const BACKEND_URL = "http://127.0.0.1:8000";

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
                
                const firstPage = editorState.pages[0];
                if (firstPage) {
                    const img = new Image();
                    img.onload = () => {
                        const newImageID = imageState.addImage({
                            name: firstPage.originalFilename,
                            type: "image/png",
                            size: 0,
                            lastModified: Date.now(),
                            imageURL: `${BACKEND_URL}${firstPage.originalUrl}`,
                            width: img.naturalWidth,
                            height: img.naturalHeight
                        });

                        const originalLayer = layerStateManager.layerList.find(l => l.name === 'Original Image');
                        
                        if (originalLayer) {
                            layerStateManager.setLayerImage(originalLayer.id, newImageID);
                            layerStateManager.selectLayer(originalLayer.id);
                        } else {
                            const newImageLayerID = layerStateManager.addLayer(firstPage.originalFilename, "image");
                            layerStateManager.setLayerImage(newImageLayerID, newImageID);
                            layerStateManager.selectLayer(newImageLayerID);
                        }
                    };
                    img.src = `${BACKEND_URL}${firstPage.originalUrl}`;
                }
            }

        } catch (error) {
            console.error("Failed to upload chapter files:", error);
            alert("Error uploading files to the backend server.");
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