<script lang="ts">
    import { AlignmentState } from "../state.svelte";
    import AlignCandidates from "./AlignCandidates.svelte";
    import AlignCanvas from "./AlignCanvas.svelte";
    import AlignKeypoints from "./AlignKeypoints.svelte";
    import AlignLayers from "./AlignLayers.svelte";
    import IconBtn from "../../shared/components/IconBtn.svelte";
    import { loadAlignmentResults } from "../loader";

    interface Props {
        alignmentState?: AlignmentState;
        /** URL of alignment task results to load on mount */
        alignment_url?: string;
    }

    let { alignmentState, alignment_url }: Props = $props();

    if (!alignmentState) {
        alignmentState = new AlignmentState();
    }

    $inspect(alignmentState.transformModel);

    let loading = $state(!!alignment_url);
    let loadError: string | null = $state(null);
    if (alignment_url) {
        loadAlignmentResults(alignment_url, alignmentState)
            .catch((e) => {
                console.error(e);
                loadError = `${e}`;
            })
            .finally(() => (loading = false));
    }

    // Open the candidates modal by default so the user picks images first;
    // it can be reopened at any time from the toolbar.
    let showCandidates = $state(
        alignmentState.images.length === 0 && !alignment_url,
    );
    let showKeypoints = $derived(alignmentState.tool === "keypoints");

    // Resizable panel state
    let sidebarWidth = $state(400);
    let keypointsWidth = $state(700);
    let startX = $state(0);
    let startWidth = $state(0);
    let activeHandle = $state<"sidebar" | "keypoints" | null>(null);

    function startResize(handle: "sidebar" | "keypoints", e: MouseEvent) {
        activeHandle = handle;
        startX = e.clientX;
        startWidth = handle === "sidebar" ? sidebarWidth : keypointsWidth;
        e.preventDefault();
    }

    function stopResize() {
        activeHandle = null;
    }

    function handleResize(e: MouseEvent) {
        if (!activeHandle) return;
        const delta = e.clientX - startX;
        if (activeHandle === "sidebar") {
            const newWidth = startWidth + delta;
            if (newWidth >= 150 && newWidth <= 600) {
                sidebarWidth = newWidth;
            }
        } else if (activeHandle === "keypoints") {
            const newWidth = startWidth - delta;
            if (newWidth >= 200 && newWidth <= 700) {
                keypointsWidth = newWidth;
            }
        }
    }
</script>

<div class="alignment-app-root">
    <div class="alignment-toolbar">
        <IconBtn
            icon="mdi:image-plus"
            label="Select images"
            class="is-link is-light"
            onclick={() => (showCandidates = true)}
        />
        {#if loading}
            <span class="ml-3">Loading alignment results…</span>
        {:else if loadError}
            <span class="ml-3 has-text-danger">{loadError}</span>
        {/if}
    </div>

    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
        class="alignment-layout"
        onmousemove={handleResize}
        onmouseup={stopResize}
        onmouseleave={stopResize}
        role="region"
    >
        <div
            class="alignment-sidebar"
            style="width: {sidebarWidth}px; flex: 0 0 {sidebarWidth}px;"
        >
            <AlignLayers {alignmentState} />
            {#if alignmentState.tool === "keypoints"}
                <AlignCanvas {alignmentState} />
            {/if}
        </div>
        <button
            class="resize-handle"
            aria-label="Resize panel"
            onmousedown={(e) => startResize("sidebar", e)}
        ></button>
        <div class="alignment-main">
            <div class="align-canvas-toolbar">
                <div class="buttons has-addons">
                    <IconBtn
                        icon="mdi:cursor-move"
                        label="Transform"
                        class={[
                            "is-small",
                            alignmentState.tool === "transform"
                                ? "is-link"
                                : "",
                        ]}
                        onclick={() => (alignmentState.tool = "transform")}
                    />
                    <IconBtn
                        icon="mdi:vector-point"
                        label="Keypoints"
                        class={[
                            "is-small",
                            alignmentState.tool === "keypoints"
                                ? "is-link"
                                : "",
                        ]}
                        onclick={() => (alignmentState.tool = "keypoints")}
                    />
                </div>
                <div class="toolbar-separator"></div>
                <div class="select is-small">
                    <select
                        bind:value={alignmentState.transformModel}
                        onchange={() => alignmentState.resync(true)}
                        title="Transform model"
                    >
                        <option value="scale">Uniform Scale</option>
                        <option value="scalexy">Non-Uniform Scale</option>
                        <option value="scale+rotate">Uniform Scale + Rotate</option>
                        <option value="scalexy+rotate">Non-Uniform Scale + Rotate</option>
                        <option value="affine">Affine</option>
                        <option value="homographic">Homography</option>
                    </select>
                </div>
                <span class="toolbar-hint">
                    {#if alignmentState.tool === "keypoints"}
                        Keypoints: click: add / drag · ctrl+click: remove ·
                        shift+click: disable
                    {/if}
                </span>
            </div>
            {#if alignmentState.tool === "transform"}
                <AlignCanvas {alignmentState} />
            {:else}
                <AlignKeypoints {alignmentState} target="reference" />
            {/if}
        </div>
        {#if showKeypoints}
            <button
                class="resize-handle"
                onmousedown={(e) => startResize("keypoints", e)}
                aria-label="Resize panel"
            ></button>
            <div
                class="alignment-keypoints"
                style="width: {keypointsWidth}px; flex: 0 0 {keypointsWidth}px;"
            >
                <AlignKeypoints {alignmentState} target="selected" />
            </div>
        {/if}
    </div>
</div>

<AlignCandidates
    {alignmentState}
    bind:open={showCandidates}
    onClose={() => (showCandidates = false)}
/>

<style>
    .alignment-app-root {
        display: flex;
        flex-direction: column;
        height: 88vh;
        min-height: 500px;
        width: 100%;
    }

    .alignment-toolbar {
        flex: none;
        display: flex;
        align-items: center;
        padding: 0.5rem 0;
    }

    .alignment-layout {
        flex: 1 1 auto;
        display: flex;
        flex-direction: row;
        min-height: 0;
        border: 1px solid var(--bulma-border, #dbdbdb);
        border-radius: var(--bulma-radius-large, 6px);
        overflow: hidden;
    }

    .alignment-sidebar {
        height: 100%;
        overflow: hidden;
        border-right: 1px solid var(--bulma-border, #dbdbdb);
        background: var(--bulma-scheme-main, #fff);
        min-width: 150px;
        max-width: 500px;
        display: flex;
        flex-direction: column;
        height: 100%;
        justify-content: stretch;
    }

    .alignment-main {
        flex: 1 1 auto;
        height: 100%;
        min-width: 0;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    .alignment-keypoints {
        height: 100%;
        overflow: hidden;
        border-left: 1px solid var(--bulma-border, #dbdbdb);
        background: var(--bulma-scheme-main, #fff);
        min-width: 200px;
        max-width: 70%;
    }

    .resize-handle {
        width: 8px;
        height: 100%;
        background: var(--bulma-border, #dbdbdb);
        cursor: col-resize;
        flex: 0 0 8px;
        transition: background-color 0.2s;
        user-select: none;
        margin: 0;
        padding: 0;
        min-width: 8px;
        border-radius: 0;
    }

    .resize-handle:hover,
    .resize-handle:active {
        background: var(--bulma-primary, #00d1b2);
    }

    :global(.aligner-viewer) {
        width: 100%;
    }

    .align-canvas-toolbar {
        flex: none;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.375rem 0.5rem;
        border-bottom: 1px solid var(--bulma-border, #dbdbdb);
        background: var(--bulma-scheme-main, #fff);
        min-width: 0;
    }

    .align-canvas-toolbar .buttons {
        flex-wrap: nowrap;
        margin-bottom: 0;
    }

    .align-canvas-toolbar :global(.buttons .button) {
        margin-bottom: 0;
    }

    .toolbar-separator {
        align-self: stretch;
        width: 1px;
        background: var(--bulma-border, #dbdbdb);
    }

    .toolbar-hint {
        flex: 1 1 auto;
        min-width: 0;
        text-align: right;
        font-size: 0.75rem;
        color: var(--bulma-text-weak, #666);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
</style>
