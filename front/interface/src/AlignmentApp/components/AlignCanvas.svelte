<script lang="ts">
    import type { AligningImage, AlignmentState } from "../state.svelte";
    import {
        applyTransform,
        identityMatrix,
        invertMatrix,
        matrixToCss,
        multiplyMatrix,
        scaleMatrix,
        translationMatrix,
        type TransformMatrix,
    } from "../transform";
    import TransformBox from "./TransformBox.svelte";
    import KeypointOverlay from "./KeypointOverlay.svelte";
    import IconBtn from "../../shared/components/IconBtn.svelte";
    import { untrack } from "svelte";

    interface Props {
        alignmentState: AlignmentState;
    }

    let { alignmentState }: Props = $props();

    // RGB mode: render each of up to 3 visible images as a R/G/B additive
    // channel instead of stacking them with opacity.
    const RGB_CHANNEL_COLORS = ["#ff0000", "#00ff00", "#0000ff"];
    let rgbMode = $state(false);
    const visibleIndices = $derived(
        alignmentState.images
            .map((_, i) => i)
            .filter((i) => alignmentState.images[i].visible),
    );
    const rgbModeAvailable = $derived(
        alignmentState.solo === null
            ? visibleIndices.length >= 2 && visibleIndices.length <= 3
            : alignmentState.solo !== 0,
    );

    // Container reference for resize observation
    let container: HTMLDivElement;

    // Resize observer
    let resizeObserver: ResizeObserver | null = null;

    // Track container dimensions
    let containerWidth = $state(0);
    let containerHeight = $state(0);

    const imageCount = $derived(alignmentState.images.length);

    // Canvas zoom/pan applied on top of the auto-fit layout, expressed
    // as a "fit-space -> screen" transform: screen = zoom * fitPoint + pan
    const MIN_ZOOM = 0.05;
    const MAX_ZOOM = 20;
    const FIT_MARGIN = 10;
    let zoom = $state(1);
    let pan = $state({ x: 0, y: 0 });
    let spaceHeld = $state(false);
    let isPanning = $state(false);
    let panStart = { x: 0, y: 0 };
    let panOrigin = { x: 0, y: 0 };

    const clampZoom = (z: number) => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, z));

    function zoomAt(clientX: number, clientY: number, factor: number) {
        if (!container) return;
        const rect = container.getBoundingClientRect();
        const mx = clientX - rect.left;
        const my = clientY - rect.top;
        const newZoom = clampZoom(zoom * factor);
        if (newZoom === zoom) return;

        // Keep the fit-space point currently under the cursor fixed on screen
        const fx = (mx - pan.x) / zoom;
        const fy = (my - pan.y) / zoom;
        pan = { x: mx - newZoom * fx, y: my - newZoom * fy };
        zoom = newZoom;
    }

    function handleWheel(e: WheelEvent) {
        e.preventDefault();
        const factor = Math.exp(-e.deltaY * 0.001);
        zoomAt(e.clientX, e.clientY, factor);
    }

    function resetView() {
        layout = computeLayout();
        zoom = 1;
        pan = { x: 0, y: 0 };
    }

    function isPanTrigger(e: PointerEvent) {
        return e.button === 1 || (e.button === 0 && spaceHeld);
    }

    function handlePointerDown(e: PointerEvent) {
        if (!isPanTrigger(e)) return;
        e.preventDefault();
        isPanning = true;
        panStart = { x: e.clientX, y: e.clientY };
        panOrigin = { ...pan };
        (e.currentTarget as Element).setPointerCapture(e.pointerId);
    }

    function handlePointerMove(e: PointerEvent) {
        if (!isPanning) return;
        pan = {
            x: panOrigin.x + (e.clientX - panStart.x),
            y: panOrigin.y + (e.clientY - panStart.y),
        };
    }

    function handlePointerUp(e: PointerEvent) {
        if (!isPanning) return;
        isPanning = false;
        (e.currentTarget as Element).releasePointerCapture(e.pointerId);
    }

    // Space key triggers hand tool
    function handleKeyDown(e: KeyboardEvent) {
        if (e.code === "Space" && !e.repeat) {
            spaceHeld = true;
        }
    }

    function handleKeyUp(e: KeyboardEvent) {
        if (e.code === "Space") {
            spaceHeld = false;
        }
    }

    // Compute relative transform for each image and centering offset
    function computeLayout() {
        const images = alignmentState.images;
        if (images.length === 0) {
            return {
                transforms: [],
                width: 0,
                height: 0,
                baseScale: 1,
                view: identityMatrix(),
            };
        }

        const inv = identityMatrix();

        const relativeTransforms = images.map((img) =>
            multiplyMatrix(inv, img.transform),
        );

        // Find bounds of all the visible images only
        let minX = Infinity;
        let minY = Infinity;
        let maxX = -Infinity;
        let maxY = -Infinity;
        let hasVisible = false;

        for (let i = 0; i < images.length; i++) {
            const img = images[i];
            const transform = relativeTransforms[i];

            if (!img.visible) continue;

            hasVisible = true;
            const corners = [
                applyTransform(transform, 0, 0),
                applyTransform(transform, img.image.width, 0),
                applyTransform(transform, img.image.width, img.image.height),
                applyTransform(transform, 0, img.image.height),
            ];

            for (const corner of corners) {
                minX = Math.min(minX, corner.x);
                minY = Math.min(minY, corner.y);
                maxX = Math.max(maxX, corner.x);
                maxY = Math.max(maxY, corner.y);
            }
        }

        // If no visible images, return identity transforms and no offset
        if (!hasVisible) {
            return {
                transforms: relativeTransforms,
                width: 0,
                height: 0,
                baseScale: 1,
                view: inv,
            };
        }

        const width = maxX - minX;
        const height = maxY - minY;
        const baseScale = Math.max(
            Math.min(
                5,
                (containerWidth - FIT_MARGIN * 2) / width,
                (containerHeight - FIT_MARGIN * 2) / height,
            ),
            0.1,
        );

        // World -> container pixels
        const view = multiplyMatrix(
            translationMatrix(containerWidth / 2, containerHeight / 2),
            multiplyMatrix(
                scaleMatrix(baseScale, baseScale),
                multiplyMatrix(
                    translationMatrix(-minX - width / 2, -minY - height / 2),
                    inv,
                ),
            ),
        );

        return {
            transforms: relativeTransforms,
            width,
            height,
            view,
            baseScale,
        };
    }

    // Update container dimensions
    function updateDimensions() {
        if (!container) return;

        const rect = container.getBoundingClientRect();
        untrack(() => {
            const invLayout = multiplyMatrix(
                scaleMatrix(1 / layout.baseScale, 1 / layout.baseScale),
                translationMatrix(-containerWidth / 2, -containerHeight / 2),
            );
            containerWidth = Math.floor(rect.width);
            containerHeight = Math.floor(rect.height);
            layout.baseScale = Math.max(
                Math.min(
                    (containerWidth - FIT_MARGIN * 2) / layout.width,
                    (containerHeight - FIT_MARGIN * 2) / layout.height,
                ),
                0.1,
            );
            layout.view = multiplyMatrix(
                translationMatrix(containerWidth / 2, containerHeight / 2),
                multiplyMatrix(
                    scaleMatrix(layout.baseScale, layout.baseScale),
                    multiplyMatrix(invLayout, layout.view),
                ),
            );
        });
    }

    // Initialize resize observer and compute layout
    $effect(() => {
        if (container) {
            updateDimensions();

            resizeObserver = new ResizeObserver(() => {
                updateDimensions();
            });
            resizeObserver.observe(container);
        }

        return () => {
            if (resizeObserver) {
                resizeObserver.disconnect();
                resizeObserver = null;
            }
        };
    });

    // Compute layout reactively
    let layout = $state(computeLayout());
    $effect(() => {
        const reactive = $state.snapshot(imageCount);
        untrack(() => {
            resetView();
        });
    });

    // User zoom/pan, applied on top of the auto-fit "world -> container pixel" view
    const zoomPan = $derived(
        multiplyMatrix(
            translationMatrix(pan.x, pan.y),
            scaleMatrix(zoom, zoom),
        ),
    );
    const view = $derived(multiplyMatrix(zoomPan, layout.view));

    const selectedImage: number | null = $derived(
        alignmentState.selected[0] ?? null,
    );

    // Only show TransformBox if the selected image is visible and not the first layer
    const showTransformBox = $derived(
        alignmentState.tool === "transform" &&
            selectedImage !== null &&
            //selectedImage !== 0 &&
            alignmentState.images[selectedImage]?.visible !== false,
    );

    function onTransformChange(selected: AligningImage, m: TransformMatrix) {
        selected.transform = m;
        selected.keypoints = selected.keypoints.map((p) => {
            return { ...p, disabled: true };
        });
    }
</script>

<svelte:window onkeydown={handleKeyDown} onkeyup={handleKeyUp} />

<div class="align-canvas-wrap">
    <div
        bind:this={container}
        class="align-canvas"
        class:pannable={spaceHeld}
        class:panning={isPanning}
        class:rgb-mode={rgbMode && rgbModeAvailable}
        onwheel={handleWheel}
        onpointerdown={handlePointerDown}
        onpointermove={handlePointerMove}
        onpointerup={handlePointerUp}
        onpointercancel={handlePointerUp}
        role="application"
    >
        <button
            class="align-canvas-background"
            aria-label="Deselect"
            onclick={() => (alignmentState.selected = [])}
        ></button>
        {#each alignmentState.images as aligningImage, i (aligningImage)}
            {#if i === 0 || (alignmentState.solo === null ? aligningImage.visible : i === alignmentState.solo)}
                <button
                    class="align-image-layer"
                    class:rgb-layer={rgbMode && rgbModeAvailable}
                    style:transform-origin="0 0"
                    style:transform={matrixToCss(
                        multiplyMatrix(view, aligningImage.transform),
                    )}
                    style:width="{aligningImage.image.width}px"
                    style:height="{aligningImage.image.height}px"
                    style:opacity={i === 0 ? 1.0 : aligningImage.opacity}
                    onclick={(e) => {
                        console.log("Clicking image", i);
                        if (alignmentState.tool === "transform") {
                            e.preventDefault();
                            console.log("Selecting image", i);
                            alignmentState.selected = [i];
                        }
                    }}
                >
                    {#if rgbMode && rgbModeAvailable}
                        {@const channelColor =
                            RGB_CHANNEL_COLORS[visibleIndices.indexOf(i)]}

                        <div
                            class="rgb-channel-bg"
                            style="background: {channelColor};"
                        ></div>
                        <div class="rgb-channel-img-wrapper">
                            <div
                                class="rgb-channel-bg"
                                style:background="#fff"
                            ></div>
                            <img
                                src={aligningImage.image.data}
                                alt={aligningImage.image.file_name}
                                class="rgb-channel-img"
                                class:flipped={aligningImage.hFlip}
                            />
                            {#if aligningImage.invertColors}
                                <div
                                    class="rgb-channel-bg"
                                    style:background="#fff"
                                    style:mix-blend-mode="difference"
                                ></div>
                            {/if}
                        </div>
                    {:else}
                        <img
                            src={aligningImage.image.data}
                            alt={aligningImage.image.file_name}
                            class:flipped={aligningImage.hFlip}
                        />
                        {#if aligningImage.invertColors}
                            <div
                                class="rgb-channel-bg"
                                style:background="#fff"
                                style:mix-blend-mode="difference"
                            ></div>
                        {/if}
                    {/if}
                </button>
            {/if}
        {/each}
        {#if showTransformBox}
            {@const selected = alignmentState.images[selectedImage!]}
            {#if selected}
                {#key selectedImage}
                    <TransformBox
                        transform={selected.transform}
                        {view}
                        width={selected.image.width}
                        height={selected.image.height}
                        transformModel={alignmentState.transformModel}
                        onChange={(m: TransformMatrix) =>
                            onTransformChange(selected, m)}
                    />
                {/key}
            {/if}
        {/if}
        {#if alignmentState.tool === "keypoints"}
            <KeypointOverlay
                {alignmentState}
                imageIndex={0}
                ghostMode
                matrix={multiplyMatrix(
                    view,
                    alignmentState.images[0].transform,
                )}
                enabled={false}
            />
        {/if}
    </div>

    <div class="align-canvas-controls">
        {#if rgbModeAvailable}
            <IconBtn
                icon="mdi:palette"
                title="RGB mode"
                class={["is-small is-white", rgbMode ? "is-link" : "is-ghost"]}
                onclick={() => (rgbMode = !rgbMode)}
            />
        {/if}
        <IconBtn
            icon="mdi:fit-to-page-outline"
            title="Reset view"
            class="is-ghost is-white is-small"
            onclick={resetView}
        />
    </div>
</div>

<style>
    .align-canvas-wrap {
        position: relative;
        display: flex;
        flex-direction: column;
        width: 100%;
        height: 100%;
        min-height: 300px;
    }

    .align-canvas {
        flex: 1 1 auto;
        width: 100%;
        min-height: 400px;
        background: #222;
        position: relative;
        overflow: hidden;
        touch-action: none;
        cursor: default;
    }

    .align-canvas-background {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        cursor: default;
    }

    .align-canvas.pannable {
        cursor: grab;
    }

    .align-canvas.panning {
        cursor: grabbing;
    }

    .align-canvas.rgb-mode {
        background: #000;
    }

    .align-canvas-controls {
        position: absolute;
        right: 0.25rem;
        top: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
        background: rgba(30, 30, 30, 0.75);
        border-radius: var(--bulma-radius, 4px);
        padding: 0.25rem;
        color: #fff;
    }

    .align-image-layer {
        position: absolute;
        top: 0;
        left: 0;
        max-width: none;
        max-height: none;
        isolation: isolate;
        padding: 0;
        margin: 0;
    }

    .flipped {
        transform: scaleX(-1);
    }

    .rgb-layer {
        mix-blend-mode: plus-lighter;
    }

    .rgb-channel-bg {
        position: absolute;
        inset: 0;
    }

    .rgb-channel-img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        max-width: none;
        max-height: none;
        mix-blend-mode: luminosity;
        background-color: #000;
    }

    .rgb-channel-img-wrapper {
        background-color: #fff;
        mix-blend-mode: multiply;
    }
</style>
