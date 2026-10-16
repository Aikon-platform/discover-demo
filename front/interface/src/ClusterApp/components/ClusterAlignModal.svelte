<script lang="ts">
    import { Dialog } from "bits-ui";
    import { AlignmentState } from "../../AlignmentApp/state.svelte";
    import AlignmentApp from "../../AlignmentApp/components/AlignmentApp.svelte";
    import type { TClusterInfo } from "../types";
    import { getEditorState } from "../state.svelte";
    import { loadClusterAligningImages } from "../align";

    interface Props {
        cluster: TClusterInfo;
        open: boolean;
        onClose: () => void;
    }

    let { cluster, open = $bindable(), onClose }: Props = $props();

    const editor_state = getEditorState();

    // Create alignment state for this modal
    const alignmentState = new AlignmentState();

    let imagesLoaded = $state(false);
    let metadataError = $state<string | null>(null);

    // Load the prototype and images of the cluster, prefilled with the DTI transforms if available
    async function loadImagesFromCluster() {
        if (imagesLoaded) return;
        imagesLoaded = true;
        alignmentState.images = [];
        metadataError = null;

        let metadata = null;
        try {
            metadata = await editor_state.get_image_metadata();
        } catch (error) {
            console.error("Could not load image metadata:", error);
            metadataError = `Could not prefill the alignment from the image metadata: ${error}`;
        }
        const { images, prefilled } = await loadClusterAligningImages(
            cluster,
            editor_state.base_url,
            metadata,
        );
        if (prefilled) {
            alignmentState.transformModel = prefilled === "projective" ? "homographic" : "affine";
        }
        alignmentState.images = images;
        alignmentState.selected = images.length > 1 ? [1] : [];
        alignmentState.resync();
    }

    function handleClose() {
        alignmentState.images = [];
        imagesLoaded = false;
        onClose();
    }

    // Load images when modal opens
    $effect(() => {
        if (open && !imagesLoaded) {
            loadImagesFromCluster();
        }
    });
</script>

<Dialog.Root bind:open>
    <Dialog.Portal>
        <div class="modal" class:is-active={open}>
            <Dialog.Overlay class="modal-background" onclick={handleClose} />
            <Dialog.Content class="modal-card cluster-align-modal">
                {#snippet child({ props })}
                    <div {...props}>
                        {#if metadataError}
                            <div class="notification is-warning is-light mb-0">{metadataError}</div>
                        {/if}
                        <AlignmentApp {alignmentState} />
                    </div>
                {/snippet}
            </Dialog.Content>
        </div>
    </Dialog.Portal>
</Dialog.Root>

<style>
    .cluster-align-modal {
        width: min(1600px, 92vw);
        max-height: 85vh;
        display: flex;
        flex-direction: column;
    }
</style>
