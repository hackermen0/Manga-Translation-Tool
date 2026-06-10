<script lang="ts">
    import { editorState } from '$lib/stores/Editor.svelte';

    let { intrinsicWidth, intrinsicHeight } = $props<{ intrinsicWidth: number, intrinsicHeight: number }>();

    let activeId = $state<number | null>(null);
    let mode = $state<'drag' | 'tl' | 'tr' | 'bl' | 'br' | null>(null);

    let startX = 0;
    let startY = 0;
    let initialBbox = { x1: 0, y1: 0, x2: 0, y2: 0 };
    let svgElement: SVGSVGElement;

    function getSVGPoint(e: PointerEvent) {
        const point = svgElement.createSVGPoint();
        point.x = e.clientX;
        point.y = e.clientY;
        return point.matrixTransform(svgElement.getScreenCTM()!.inverse());
    }

    function handlePointerDown(e: PointerEvent, id: number, interactionMode: typeof mode) {
        e.stopPropagation();
        e.preventDefault();
        
        activeId = id;
        mode = interactionMode;
        
        const pt = getSVGPoint(e);
        startX = pt.x;
        startY = pt.y;

        const bubble = editorState.activePage?.bubbles.find(b => b.id === id);
        if (bubble) {
            initialBbox = { ...bubble.bbox };
        }

        window.addEventListener('pointermove', handlePointerMove);
        window.addEventListener('pointerup', handlePointerUp);
    }

    function handlePointerMove(e: PointerEvent) {
        if (!activeId || !mode || !editorState.activePage) return;

        const pt = getSVGPoint(e);
        const dx = pt.x - startX;
        const dy = pt.y - startY;

        const bubbleIndex = editorState.activePage.bubbles.findIndex(b => b.id === activeId);
        if (bubbleIndex === -1) return;

        const b = editorState.activePage.bubbles[bubbleIndex];
        const newBbox = { ...initialBbox };

        if (mode === 'drag') {
            newBbox.x1 += dx;
            newBbox.x2 += dx;
            newBbox.y1 += dy;
            newBbox.y2 += dy;
        } else if (mode === 'tl') {
            newBbox.x1 = Math.min(newBbox.x1 + dx, newBbox.x2 - 20);
            newBbox.y1 = Math.min(newBbox.y1 + dy, newBbox.y2 - 20);
        } else if (mode === 'tr') {
            newBbox.x2 = Math.max(newBbox.x2 + dx, newBbox.x1 + 20);
            newBbox.y1 = Math.min(newBbox.y1 + dy, newBbox.y2 - 20);
        } else if (mode === 'bl') {
            newBbox.x1 = Math.min(newBbox.x1 + dx, newBbox.x2 - 20);
            newBbox.y2 = Math.max(newBbox.y2 + dy, newBbox.y1 + 20);
        } else if (mode === 'br') {
            newBbox.x2 = Math.max(newBbox.x2 + dx, newBbox.x1 + 20);
            newBbox.y2 = Math.max(newBbox.y2 + dy, newBbox.y1 + 20);
        }

        editorState.activePage.bubbles[bubbleIndex].bbox = newBbox;
    }

    function handlePointerUp() {
        activeId = null;
        mode = null;
        window.removeEventListener('pointermove', handlePointerMove);
        window.removeEventListener('pointerup', handlePointerUp);
    }
</script>

<svg 
    bind:this={svgElement}
    viewBox="0 0 {intrinsicWidth} {intrinsicHeight}" 
    class="absolute top-0 left-0 w-full h-full pointer-events-none z-50"
>
    {#if editorState.activePage?.bubbles}
        {#each editorState.activePage.bubbles as bubble (bubble.id)}
            {@const width = bubble.bbox.x2 - bubble.bbox.x1}
            {@const height = bubble.bbox.y2 - bubble.bbox.y1}
            {@const isHovered = activeId === bubble.id}
            
            <g 
                class="pointer-events-auto"
                onpointerenter={() => { if (!mode) activeId = bubble.id }}
                onpointerleave={() => { if (!mode) activeId = null }}
            >
                <rect 
                    x={bubble.bbox.x1} 
                    y={bubble.bbox.y1} 
                    {width} 
                    {height} 
                    fill={isHovered ? "rgba(59, 130, 246, 0.2)" : "transparent"}
                    stroke={isHovered ? "#3b82f6" : "rgba(59, 130, 246, 0.5)"}
                    stroke-width={intrinsicWidth * 0.002}
                    class="cursor-move transition-colors duration-150"
                    onpointerdown={(e) => handlePointerDown(e, bubble.id, 'drag')}
                />

                {#if isHovered || mode}
                    {@const r = intrinsicWidth * 0.005}
                    <circle cx={bubble.bbox.x1} cy={bubble.bbox.y1} {r} fill="white" stroke="#3b82f6" stroke-width="8" class="cursor-nwse-resize" onpointerdown={(e) => handlePointerDown(e, bubble.id, 'tl')} />
                    <circle cx={bubble.bbox.x2} cy={bubble.bbox.y1} {r} fill="white" stroke="#3b82f6" stroke-width="8" class="cursor-nesw-resize" onpointerdown={(e) => handlePointerDown(e, bubble.id, 'tr')} />
                    <circle cx={bubble.bbox.x1} cy={bubble.bbox.y2} {r} fill="white" stroke="#3b82f6" stroke-width="8" class="cursor-nesw-resize" onpointerdown={(e) => handlePointerDown(e, bubble.id, 'bl')} />
                    <circle cx={bubble.bbox.x2} cy={bubble.bbox.y2} {r} fill="white" stroke="#3b82f6" stroke-width="8" class="cursor-nwse-resize" onpointerdown={(e) => handlePointerDown(e, bubble.id, 'br')} />
                {/if}
            </g>
        {/each}
    {/if}
</svg>