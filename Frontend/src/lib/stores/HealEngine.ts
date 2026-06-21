/**
 * HealEngine.ts — Client-Side Texture Synthesis Module
 *
 * Implements the mathematical behavior of Photoshop's Spot Healing Brush:
 *   Phase A: High-frequency structural extraction (Laplacian / high-pass filter)
 *   Phase B: Low-frequency color/lighting match (Poisson gradient blending)
 *   Phase C: Soft alpha weighted merge (feathered pasting)
 *
 * All operations work on raw RGBA Uint8ClampedArray pixel buffers.
 * No DOM or Svelte dependencies — pure computational module.
 */

// ─── Helpers ────────────────────────────────────────────────────────────────

/** Clamp value to [min, max] range */
function clamp(v: number, min: number, max: number): number {
    return v < min ? min : v > max ? max : v;
}

/** Get the 1D index into an RGBA pixel array for coordinates (x, y) */
function idx(x: number, y: number, stride: number): number {
    return (y * stride + x) * 4;
}

// ─── Gaussian Blur (Separable 2-Pass) ───────────────────────────────────────

/**
 * Build a 1D Gaussian kernel with the given sigma.
 * Kernel radius is ceil(3 * sigma) to capture 99.7% of the distribution.
 */
function buildGaussianKernel(sigma: number): Float32Array {
    const radius = Math.ceil(sigma * 3);
    const size = radius * 2 + 1;
    const kernel = new Float32Array(size);
    const s2 = 2 * sigma * sigma;
    let sum = 0;

    for (let i = 0; i < size; i++) {
        const x = i - radius;
        kernel[i] = Math.exp(-(x * x) / s2);
        sum += kernel[i];
    }

    // Normalize
    for (let i = 0; i < size; i++) {
        kernel[i] /= sum;
    }

    return kernel;
}

/**
 * Perform a separable 2-pass Gaussian blur on a patch of RGBA pixel data.
 * Operates in-place on the provided Float32Array (which stores signed values).
 * 
 * @param data   - Source RGBA data (Uint8ClampedArray from ImageData)
 * @param width  - Patch width
 * @param height - Patch height
 * @param sigma  - Blur radius (standard deviation)
 * @returns New Float32Array with blurred RGBA values
 */
export function gaussianBlur(
    data: Uint8ClampedArray,
    width: number,
    height: number,
    sigma: number
): Float32Array {
    const kernel = buildGaussianKernel(sigma);
    const radius = (kernel.length - 1) / 2;
    const pixelCount = width * height * 4;
    const temp = new Float32Array(pixelCount);
    const result = new Float32Array(pixelCount);

    // Horizontal pass → temp
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            let r = 0, g = 0, b = 0;
            for (let k = -radius; k <= radius; k++) {
                const sx = clamp(x + k, 0, width - 1);
                const si = idx(sx, y, width);
                const w = kernel[k + radius];
                r += data[si] * w;
                g += data[si + 1] * w;
                b += data[si + 2] * w;
            }
            const di = idx(x, y, width);
            temp[di] = r;
            temp[di + 1] = g;
            temp[di + 2] = b;
            temp[di + 3] = data[di + 3]; // Preserve alpha
        }
    }

    // Vertical pass → result
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            let r = 0, g = 0, b = 0;
            for (let k = -radius; k <= radius; k++) {
                const sy = clamp(y + k, 0, height - 1);
                const si = idx(x, sy, width);
                const w = kernel[k + radius];
                r += temp[si] * w;
                g += temp[si + 1] * w;
                b += temp[si + 2] * w;
            }
            const di = idx(x, y, width);
            result[di] = r;
            result[di + 1] = g;
            result[di + 2] = b;
            result[di + 3] = temp[di + 3];
        }
    }

    return result;
}

// ─── Phase A: High-Frequency Structural Extraction ──────────────────────────

/**
 * Extract the high-frequency texture component from a source patch.
 *
 *   Texture = Source_raw - GaussianBlur(Source_raw, σ=2.0)
 *
 * Result is stored as signed offsets centered at 128 in each channel,
 * so that it can be added to any destination color later.
 *
 * @param sourceData - Raw RGBA pixel data of the source patch
 * @param width      - Patch width
 * @param height     - Patch height
 * @param sigma      - Blur sigma for low-frequency extraction (default 2.0)
 * @returns Float32Array of signed texture offsets (centered at 0, not 128)
 */
export function extractHighFrequency(
    sourceData: Uint8ClampedArray,
    width: number,
    height: number,
    sigma: number = 2.0
): Float32Array {
    const blurred = gaussianBlur(sourceData, width, height, sigma);
    const texture = new Float32Array(width * height * 4);

    for (let i = 0; i < width * height * 4; i += 4) {
        // Signed offset: positive means brighter than average, negative means darker
        texture[i] = sourceData[i] - blurred[i];         // R
        texture[i + 1] = sourceData[i + 1] - blurred[i + 1]; // G
        texture[i + 2] = sourceData[i + 2] - blurred[i + 2]; // B
        texture[i + 3] = 255; // Full alpha for the texture layer
    }

    return texture;
}

// ─── Phase B: Poisson Gradient Blending (Simplified Membrane Equation) ──────

/**
 * Solve a simplified Poisson/membrane equation to harmonize the high-frequency
 * texture with the destination's low-frequency lighting conditions.
 *
 * The boundary pixels of the destination patch anchor the color solution.
 * Interior pixels are iteratively relaxed to satisfy:
 *   ∇²result = ∇²(texture guidance)
 * while matching boundary conditions from the destination.
 *
 * Uses Jacobi iteration for stability (no dependency ordering issues).
 *
 * @param texture      - High-frequency texture from Phase A (signed Float32Array)
 * @param destData     - Raw RGBA data of the destination patch
 * @param width        - Patch width
 * @param height       - Patch height
 * @param mask         - Float32Array alpha mask (0.0–1.0) indicating heal region
 * @param iterations   - Number of Jacobi iterations (default 20)
 * @returns Uint8ClampedArray of the blended result
 */
export function poissonBlend(
    texture: Float32Array,
    destData: Uint8ClampedArray,
    width: number,
    height: number,
    mask: Float32Array,
    iterations: number = 20
): Uint8ClampedArray {
    const size = width * height;
    const result = new Uint8ClampedArray(size * 4);

    // Initialize result with destination data
    result.set(destData);

    // Precompute the Laplacian of the guidance field (texture)
    // ∇²texture[i] = texture[i-1] + texture[i+1] + texture[i-stride] + texture[i+stride] - 4*texture[i]
    const guidanceLap = new Float32Array(size * 3); // RGB only

    for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
            const ci = (y * width + x);
            const pi = ci * 4;
            const li = ci * 3;

            // Only compute for pixels inside the mask
            if (mask[ci] < 0.01) continue;

            for (let c = 0; c < 3; c++) {
                const center = texture[pi + c];
                const left = texture[idx(x - 1, y, width) + c];
                const right = texture[idx(x + 1, y, width) + c];
                const top = texture[idx(x, y - 1, width) + c];
                const bottom = texture[idx(x, y + 1, width) + c];
                guidanceLap[li + c] = left + right + top + bottom - 4 * center;
            }
        }
    }

    // Working buffers for Jacobi iteration (RGB channels only)
    const current = new Float32Array(size * 3);
    const next = new Float32Array(size * 3);

    // Initialize current and next with destination pixel values to preserve boundary conditions
    for (let i = 0; i < size; i++) {
        const r = destData[i * 4];
        const g = destData[i * 4 + 1];
        const b = destData[i * 4 + 2];

        current[i * 3] = r;
        current[i * 3 + 1] = g;
        current[i * 3 + 2] = b;

        next[i * 3] = r;
        next[i * 3 + 1] = g;
        next[i * 3 + 2] = b;
    }

    // Jacobi iteration
    for (let iter = 0; iter < iterations; iter++) {
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const ci = y * width + x;

                // Skip pixels outside the mask (boundary conditions stay fixed)
                if (mask[ci] < 0.01) {
                    next[ci * 3] = current[ci * 3];
                    next[ci * 3 + 1] = current[ci * 3 + 1];
                    next[ci * 3 + 2] = current[ci * 3 + 2];
                    continue;
                }

                const li = ci * 3;
                const leftIdx = (y * width + (x - 1)) * 3;
                const rightIdx = (y * width + (x + 1)) * 3;
                const topIdx = ((y - 1) * width + x) * 3;
                const bottomIdx = ((y + 1) * width + x) * 3;

                for (let c = 0; c < 3; c++) {
                    // Jacobi: f[i] = (f[neighbors] - ∇²guidance) / 4
                    const neighborSum =
                        current[leftIdx + c] +
                        current[rightIdx + c] +
                        current[topIdx + c] +
                        current[bottomIdx + c];

                    next[li + c] = (neighborSum - guidanceLap[li + c]) / 4;
                }
            }
        }

        // Swap buffers
        current.set(next);
    }

    // Write result back, blending with mask
    for (let i = 0; i < size; i++) {
        const alpha = mask[i];
        if (alpha < 0.001) continue;

        const pi = i * 4;
        result[pi] = clamp(Math.round(current[i * 3] * alpha + destData[pi] * (1 - alpha)), 0, 255);
        result[pi + 1] = clamp(Math.round(current[i * 3 + 1] * alpha + destData[pi + 1] * (1 - alpha)), 0, 255);
        result[pi + 2] = clamp(Math.round(current[i * 3 + 2] * alpha + destData[pi + 2] * (1 - alpha)), 0, 255);
        result[pi + 3] = 255;
    }

    return result;
}

// ─── Phase C: Feathered Alpha Mask ──────────────────────────────────────────

/**
 * Generate a radial alpha falloff mask for a circular brush stamp.
 *
 *   α = 1.0 - clamp((d - R × hardness) / (R × (1 - hardness)), 0, 1)
 *
 * @param width    - Patch width
 * @param height   - Patch height
 * @param centerX  - Center X within the patch
 * @param centerY  - Center Y within the patch
 * @param radius   - Brush radius in pixels
 * @param hardness - Edge hardness (0.0 = fully soft, 1.0 = hard edge). Default 0.75
 * @returns Float32Array of per-pixel alpha values (0.0–1.0)
 */
export function computeAlphaMask(
    width: number,
    height: number,
    centerX: number,
    centerY: number,
    radius: number,
    hardness: number = 0.75
): Float32Array {
    const mask = new Float32Array(width * height);
    const innerRadius = radius * hardness;
    const fadeWidth = radius * (1 - hardness);

    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const dx = x - centerX;
            const dy = y - centerY;
            const d = Math.sqrt(dx * dx + dy * dy);

            if (d <= innerRadius) {
                mask[y * width + x] = 1.0;
            } else if (fadeWidth > 0) {
                mask[y * width + x] = 1.0 - clamp((d - innerRadius) / fadeWidth, 0, 1);
            } else {
                mask[y * width + x] = d <= radius ? 1.0 : 0.0;
            }
        }
    }

    return mask;
}

// ─── Auto-Source Sampling ───────────────────────────────────────────────────

/**
 * For contextual auto-spot mode: compute the average pixel values from a ring
 * perimeter 12px outside the brush radius. This provides the "clean" source
 * texture for healing.
 *
 * Samples pixels on the ring and builds a composite source patch by
 * averaging concentric ring samples from the surrounding area.
 *
 * @param originalData - Full original page pixel data
 * @param destX        - Destination center X (in image coordinates)
 * @param destY        - Destination center Y (in image coordinates)
 * @param radius       - Brush radius
 * @param imageWidth   - Full image width
 * @param imageHeight  - Full image height
 * @returns Object with sourceX, sourceY as the best offset for sampling
 */
export function findAutoSourceOffset(
    originalData: Uint8ClampedArray,
    destX: number,
    destY: number,
    radius: number,
    imageWidth: number,
    imageHeight: number
): { sourceX: number; sourceY: number } {
    const ringRadius = radius + 12;
    const sampleAngles = 16; // Sample 16 positions around the ring

    // Score each candidate direction by texture variance (lower = cleaner)
    let bestAngle = 0;
    let bestScore = Infinity;

    for (let a = 0; a < sampleAngles; a++) {
        const angle = (a / sampleAngles) * Math.PI * 2;
        const sx = Math.round(destX + Math.cos(angle) * ringRadius);
        const sy = Math.round(destY + Math.sin(angle) * ringRadius);

        // Check bounds — the entire source patch must fit within the image
        if (
            sx - radius < 0 || sx + radius >= imageWidth ||
            sy - radius < 0 || sy + radius >= imageHeight
        ) {
            continue;
        }

        // Compute a quick variance score over a small sample area
        let sumR = 0, sumG = 0, sumB = 0;
        let sumR2 = 0, sumG2 = 0, sumB2 = 0;
        let count = 0;

        const sampleRadius = Math.min(radius, 8);
        for (let dy = -sampleRadius; dy <= sampleRadius; dy += 2) {
            for (let dx = -sampleRadius; dx <= sampleRadius; dx += 2) {
                const px = sx + dx;
                const py = sy + dy;
                if (px < 0 || px >= imageWidth || py < 0 || py >= imageHeight) continue;

                const pi = idx(px, py, imageWidth);
                const r = originalData[pi];
                const g = originalData[pi + 1];
                const b = originalData[pi + 2];
                sumR += r; sumG += g; sumB += b;
                sumR2 += r * r; sumG2 += g * g; sumB2 += b * b;
                count++;
            }
        }

        if (count === 0) continue;

        // Variance = E[X²] - E[X]²
        const varR = sumR2 / count - (sumR / count) ** 2;
        const varG = sumG2 / count - (sumG / count) ** 2;
        const varB = sumB2 / count - (sumB / count) ** 2;
        const totalVar = varR + varG + varB;

        if (totalVar < bestScore) {
            bestScore = totalVar;
            bestAngle = a;
        }
    }

    const angle = (bestAngle / sampleAngles) * Math.PI * 2;
    return {
        sourceX: Math.round(destX + Math.cos(angle) * ringRadius),
        sourceY: Math.round(destY + Math.sin(angle) * ringRadius)
    };
}

// ─── Main Heal Pipeline ────────────────────────────────────────────────────

/**
 * Extract a rectangular patch of pixel data from a full image buffer.
 */
function extractPatch(
    data: Uint8ClampedArray,
    imageWidth: number,
    patchX: number,
    patchY: number,
    patchW: number,
    patchH: number
): Uint8ClampedArray {
    const patch = new Uint8ClampedArray(patchW * patchH * 4);

    for (let y = 0; y < patchH; y++) {
        const srcRow = ((patchY + y) * imageWidth + patchX) * 4;
        const dstRow = y * patchW * 4;
        patch.set(data.subarray(srcRow, srcRow + patchW * 4), dstRow);
    }

    return patch;
}

/**
 * Write a rectangular patch back into a full image buffer.
 */
function writePatch(
    data: Uint8ClampedArray,
    imageWidth: number,
    patchX: number,
    patchY: number,
    patchW: number,
    patchH: number,
    patch: Uint8ClampedArray
): void {
    for (let y = 0; y < patchH; y++) {
        const dstRow = ((patchY + y) * imageWidth + patchX) * 4;
        const srcRow = y * patchW * 4;
        data.set(patch.subarray(srcRow, srcRow + patchW * 4), dstRow);
    }
}

export interface HealResult {
    /** The patched pixel data to write into the overlay */
    patchData: Uint8ClampedArray;
    /** Patch position in image coordinates */
    patchX: number;
    patchY: number;
    /** Patch dimensions */
    patchW: number;
    patchH: number;
}

/**
 * Main entry point: Perform a single heal stamp at the given destination.
 *
 * Orchestrates the 3-phase pipeline:
 *   1. Extract high-frequency texture from source patch
 *   2. Poisson-blend texture onto destination's lighting
 *   3. Feathered alpha merge
 *
 * @param originalData  - Immutable original page pixel data (full image)
 * @param overlayData   - Current overlay pixel data (full image, will be READ for dest)
 * @param sourceX       - Source center X (image coords)
 * @param sourceY       - Source center Y (image coords)
 * @param destX         - Destination center X (image coords)
 * @param destY         - Destination center Y (image coords)
 * @param radius        - Brush radius in pixels
 * @param hardness      - Edge hardness (0.0–1.0)
 * @param imageWidth    - Full image width
 * @param imageHeight   - Full image height
 * @returns HealResult with the blended patch and its position
 */
export function healPatch(
    originalData: Uint8ClampedArray,
    overlayData: Uint8ClampedArray,
    sourceX: number,
    sourceY: number,
    destX: number,
    destY: number,
    radius: number,
    hardness: number,
    imageWidth: number,
    imageHeight: number
): HealResult | null {
    // Compute patch bounds (clamped to image)
    const patchW = radius * 2 + 2; // +2 for boundary pixels needed by Poisson
    const patchH = radius * 2 + 2;

    // Source patch bounds
    const srcPatchX = clamp(Math.round(sourceX - radius - 1), 0, imageWidth - patchW);
    const srcPatchY = clamp(Math.round(sourceY - radius - 1), 0, imageHeight - patchH);

    // Destination patch bounds
    const dstPatchX = clamp(Math.round(destX - radius - 1), 0, imageWidth - patchW);
    const dstPatchY = clamp(Math.round(destY - radius - 1), 0, imageHeight - patchH);

    // Extract source patch from the ORIGINAL (immutable) image
    const sourcePatch = extractPatch(originalData, imageWidth, srcPatchX, srcPatchY, patchW, patchH);

    // Extract destination patch from the OVERLAY (current working state)
    const destPatch = extractPatch(overlayData, imageWidth, dstPatchX, dstPatchY, patchW, patchH);

    // Center of the brush within the patch coordinate system
    const localCenterX = Math.round(destX) - dstPatchX;
    const localCenterY = Math.round(destY) - dstPatchY;

    // Phase A: Extract high-frequency texture from source
    const texture = extractHighFrequency(sourcePatch, patchW, patchH, 2.0);

    // Phase C (computed early): Generate the alpha mask
    const alphaMask = computeAlphaMask(patchW, patchH, localCenterX, localCenterY, radius, hardness);

    // Phase B: Poisson gradient blending
    // Superimpose texture onto destination's low-frequency illumination
    // Pass high-frequency source texture directly to avoid clamping/blurring artifacts
    const blendedPatch = poissonBlend(texture, destPatch, patchW, patchH, alphaMask, 20);

    return {
        patchData: blendedPatch,
        patchX: dstPatchX,
        patchY: dstPatchY,
        patchW,
        patchH
    };
}

/**
 * Apply a HealResult onto an overlay ImageData buffer.
 * Writes the patch pixels into the correct location of the full-size overlay.
 */
export function applyHealResult(
    overlayData: Uint8ClampedArray,
    imageWidth: number,
    result: HealResult
): void {
    writePatch(
        overlayData,
        imageWidth,
        result.patchX,
        result.patchY,
        result.patchW,
        result.patchH,
        result.patchData
    );
}
