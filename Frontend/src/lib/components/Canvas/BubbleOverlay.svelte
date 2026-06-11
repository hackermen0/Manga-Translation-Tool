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
    
    // Draft points for 'Create' mode
    let draftPoints = $state<{x: number, y: number}[]>([]);

    // --- MATH: Converts physical screen clicks to precise SVG mapping ---
    function getIntrinsicCoordinates(clientX: number, clientY: number) {
        const rect = svgElement.getBoundingClientRect();
        const rawX = clientX - rect.left;
        const rawY = clientY - rect.top;
        const scaleX = intrinsicWidth / rect.width;
        const scaleY = intrinsicHeight / rect.height;
        return { x: rawX * scaleX, y: rawY * scaleY };
    }

    // --- CREATE MODE ---
    function handleSvgClick(e: MouseEvent) {
        if (editorState.activeSession !== 'detection' || editorState.activeDetectionTool !== 'create') return;
        const coords = getIntrinsicCoordinates(e.clientX, e.clientY);
        draftPoints = [...draftPoints, coords];
    }

    function handleSvgDoubleClick(e: MouseEvent) {
        if (editorState.activeSession !== 'detection' || editorState.activeDetectionTool !== 'create' || draftPoints.length < 3) return;
        
        const newId = Math.max(0, ...editorState.activePage!.bubbles.map(b => b.id)) + 1;
        editorState.activePage!.bubbles.push({
            id: newId,
            points: [...draftPoints],
            ja_text: "",
            en_text: ""
        });
        
        draftPoints = [];
        editorState.saveBubbles(); // Save new bubble
    }

    // --- EDIT MODE (Points) ---
    function handleVertexPointerDown(e: PointerEvent, bubbleId: number, pointIndex: number) {
        if (editorState.activeDetectionTool !== 'edit') return;
        e.stopPropagation();
        e.preventDefault();
        
        if (e.target instanceof Element) e.target.setPointerCapture(e.pointerId);
        
        activeBubbleId = bubbleId;
        activePointIndex = pointIndex;
        isDraggingBody = false;
        
        startX = e.clientX;
        startY = e.clientY;

        const bubble = editorState.activePage?.bubbles.find(b => b.id === bubbleId);
        if (bubble) initialPoints = [ { ...bubble.points[pointIndex] } ];

        window.addEventListener('pointermove', handlePointerMove);
        window.addEventListener('pointerup', handlePointerUp);
    }

    // --- DRAG MODE (Body) ---
    function handleBodyPointerDown(e: PointerEvent, bubbleId: number) {
        e.stopPropagation();
        e.preventDefault();
        
        // Handle Delete Tool immediately
        if (editorState.activeDetectionTool === 'delete') {
            editorState.activePage!.bubbles = editorState.activePage!.bubbles.filter(b => b.id !== bubbleId);
            editorState.saveBubbles();
            return;
        }

        if (editorState.activeDetectionTool !== 'drag') return;
        
        if (e.target instanceof Element) e.target.setPointerCapture(e.pointerId);
        
        activeBubbleId = bubbleId;
        isDraggingBody = true;
        activePointIndex = null;
        
        startX = e.clientX;
        startY = e.clientY;

        const bubble = editorState.activePage?.bubbles.find(b => b.id === bubbleId);
        if (bubble) initialPoints = bubble.points.map(p => ({ ...p }));

        window.addEventListener('pointermove', handlePointerMove);
        window.addEventListener('pointerup', handlePointerUp);
    }

    // --- MOVEMENT TRACKING ---
    function handlePointerMove(e: PointerEvent) {
        if (activeBubbleId === null || !editorState.activePage) return;
        e.preventDefault();

        const dx = (e.clientX - startX) / (zoomState.zoomLevel / 100);
        const dy = (e.clientY - startY) / (zoomState.zoomLevel / 100);

        const bubbleIndex = editorState.activePage.bubbles.findIndex(b => b.id === activeBubbleId);
        if (bubbleIndex === -1) return;

        if (isDraggingBody) {
            editorState.activePage.bubbles[bubbleIndex].points = initialPoints.map(p => ({ x: p.x + dx, y: p.y + dy }));
        } else if (activePointIndex !== null) {
            editorState.activePage.bubbles[bubbleIndex].points[activePointIndex] = { x: initialPoints[0].x + dx, y: initialPoints[0].y + dy };
        }
    }

    function handlePointerUp(e: PointerEvent) {
        if (activeBubbleId === null) return;

        if (e.target instanceof Element && e.target.hasPointerCapture(e.pointerId)) e.target.releasePointerCapture(e.pointerId);

        activeBubbleId = null;
        activePointIndex = null;
        isDraggingBody = false;
        
        window.removeEventListener('pointermove', handlePointerMove);
        window.removeEventListener('pointerup', handlePointerUp);

        editorState.saveBubbles(); // Save after any drag/edit is completed
    }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<svg 
    bind:this={svgElement}
    viewBox="0 0 {intrinsicWidth} {intrinsicHeight}" 
    class="absolute top-0 left-0 w-full h-full z-50 {editorState.activeSession === 'detection' ? 'pointer-events-auto' : 'pointer-events-none'}"
    onclick={handleSvgClick}
    ondblclick={handleSvgDoubleClick}
>
    {#if editorState.activeDetectionTool === 'create' && draftPoints.length > 0}
        <polyline 
            points={draftPoints.map(p => `${p.x},${p.y}`).join(' ')}
            fill="rgba(255, 183, 150, 0.4)"
            stroke="#22c55e"
            stroke-width={intrinsicWidth * 0.0025}
            stroke-dasharray="4"
        />
        {#each draftPoints as point}
            <circle cx={point.x} cy={point.y} r={intrinsicWidth * 0.004} fill="white" stroke="#22c55e" stroke-width="2" />
        {/each}
    {/if}

    {#if editorState.activePage?.bubbles}
        {#each editorState.activePage.bubbles as bubble (bubble.id)}
            {@const pointsString = bubble.points.map(p => `${p.x},${p.y}`).join(' ')}
            {@const isHovered = activeBubbleId === bubble.id}
            
            <g>
                <polygon 
                    points={pointsString}
                    fill={isHovered || editorState.activeDetectionTool === 'delete' ? "rgba(255, 183, 150, 0.4)" : "rgba(255, 183, 150, 0.2)"}
                    stroke={isHovered || editorState.activeDetectionTool === 'delete' ? "#22c55e" : "rgba(34, 197, 94, 0.6)"}
                    stroke-width={intrinsicWidth * 0.0025}
                    class="transition-colors duration-150 {editorState.activeDetectionTool === 'drag' ? 'cursor-move' : editorState.activeDetectionTool === 'delete' ? 'cursor-pointer hover:fill-red-200 hover:stroke-red-500' : ''}"
                    onpointerdown={(e) => handleBodyPointerDown(e, bubble.id)}
                    onpointerenter={() => { if (!isDraggingBody && activePointIndex === null) activeBubbleId = bubble.id }}
                    onpointerleave={() => { if (!isDraggingBody && activePointIndex === null) activeBubbleId = null }}
                />

                {#if editorState.activeDetectionTool === 'edit' && (isHovered || activePointIndex !== null)}
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