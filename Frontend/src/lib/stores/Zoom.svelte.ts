class ZoomState {
	zoomLevel = $state(100);
	minZoom = 25;
	maxZoom = 400;

	setZoomLevel(level: number) {
		this.zoomLevel = Math.max(this.minZoom, Math.min(this.maxZoom, level));
	}

	zoomIn(step: number = 25) {
		this.setZoomLevel(this.zoomLevel + step);
	}

	zoomOut(step: number = 25) {
		this.setZoomLevel(this.zoomLevel - step);
	}
}

export const zoomState = new ZoomState();
