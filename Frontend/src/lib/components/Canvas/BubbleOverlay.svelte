<script lang="ts">
    import { editorState } from '$lib/stores/Editor.svelte';
    import { zoomState } from '$lib/stores/Zoom.svelte'; 

    let { intrinsicWidth, intrinsicHeight } = $props<{ intrinsicWidth: number, intrinsicHeight: number }>();

    let activeBubbleId = $state<number | null>(null);
    let activePointIndex = $state<number | null>(null);
    let isDraggingBody = $state<boolean>(false);

    let startX = 0;
    let startY = 0;
    
    let initialPoints: {x: number, y: number}[] = [];
    let svgElement: SVGSVGElement;

    function handleVertexPointerDown(e: PointerEvent, bubbleId: number, pointIndex: number) {
        e.stopPropagation();
        e.preventDefault();
        
        if (e.target instanceof Element) {
            e.target.setPointerCapture(e.pointerId);
        }
        
        activeBubbleId = bubbleId;
        activePointIndex = pointIndex;
        isDraggingBody = false;
        
        startX = e.clientX;
        startY = e.clientY;

        const bubble = editorState.activePage?.bubbles.find(b => b.id === bubbleId);
        if (bubble) {
            initialPoints = [ { ...bubble.points[pointIndex] } ];
        }

        window.addEventListener('pointermove', handlePointerMove);
        window.addEventListener('pointerup', handlePointerUp);
    }

    function handleBodyPointerDown(e: PointerEvent, bubbleId: number) {
        e.stopPropagation();
        e.preventDefault();
        
        if (e.target instanceof Element) {
            e.target.setPointerCapture(e.pointerId);
        }
        
        activeBubbleId = bubbleId;
        isDraggingBody = true;
        activePointIndex = null;
        
        startX = e.clientX;
        startY = e.clientY;

        const bubble = editorState.activePage?.bubbles.find(b => b.id === bubbleId);
        if (bubble) {
            initialPoints = bubble.points.map(p => ({ ...p }));
        }

        window.addEventListener('pointermove', handlePointerMove);
        window.addEventListener('pointerup', handlePointerUp);
    }

    function handlePointerMove(e: PointerEvent) {
        if (activeBubbleId === null || !editorState.activePage) return;
        
        e.preventDefault();

        const rawDx = e.clientX - startX;
        const rawDy = e.clientY - startY;

        const scaleFactor = zoomState.zoomLevel / 100;
        const dx = rawDx / scaleFactor;
        const dy = rawDy / scaleFactor;

        const bubbleIndex = editorState.activePage.bubbles.findIndex(b => b.id === activeBubbleId);
        if (bubbleIndex === -1) return;

        if (isDraggingBody) {
            editorState.activePage.bubbles[bubbleIndex].points = initialPoints.map(p => ({
                x: p.x + dx,
                y: p.y + dy
            }));
        } else if (activePointIndex !== null) {
            editorState.activePage.bubbles[bubbleIndex].points[activePointIndex] = {
                x: initialPoints[0].x + dx,
                y: initialPoints[0].y + dy
            };
        }
    }

    function handlePointerUp(e: PointerEvent) {
        if (activeBubbleId === null) return;

        if (e.target instanceof Element && e.target.hasPointerCapture(e.pointerId)) {
            e.target.releasePointerCapture(e.pointerId);
        }

        activeBubbleId = null;
        activePointIndex = null;
        isDraggingBody = false;
        
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
            {@const pointsString = bubble.points.map(p => `${p.x},${p.y}`).join(' ')}
            {@const isHovered = activeBubbleId === bubble.id}
            
            <g 
                class="pointer-events-auto"
                onpointerenter={() => { if (!isDraggingBody && activePointIndex === null) activeBubbleId = bubble.id }}
                onpointerleave={() => { if (!isDraggingBody && activePointIndex === null) activeBubbleId = null }}
            >
                <polygon 
                    points={pointsString}
                    fill={isHovered ? "rgba(255, 183, 150, 0.4)" : "rgba(255, 183, 150, 0.2)"}
                    stroke={isHovered ? "#22c55e" : "rgba(34, 197, 94, 0.6)"}
                    stroke-width={intrinsicWidth * 0.0025}
                    class="cursor-move transition-colors duration-150"
                    onpointerdown={(e) => handleBodyPointerDown(e, bubble.id)}
                />

                {#if isHovered || activePointIndex !== null || isDraggingBody}
                    {#each bubble.points as point, i}
                        <circle 
                            cx={point.x} 
                            cy={point.y} 
                            r={intrinsicWidth * 0.004} 
                            fill="white" 
                            stroke="#22c55e" 
                            stroke-width="2" 
                            class="cursor-crosshair hover:scale-150 transition-transform origin-center" 
                            onpointerdown={(e) => handleVertexPointerDown(e, bubble.id, i)} 
                        />
                    {/each}
                {/if}
            </g>
        {/each}
    {/if}
</svg>