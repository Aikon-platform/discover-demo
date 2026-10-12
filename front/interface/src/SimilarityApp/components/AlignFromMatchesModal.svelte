<script lang="ts">
    import { Dialog } from "bits-ui";
    import {
        AlignmentState,
        type AligningImage,
    } from "../../AlignmentApp/state.svelte";
    import type { TSimilarityMatches } from "../types";
    import {
        applyTransform,
        initialMatrix,
    } from "../../AlignmentApp/transform";
    import { imageInfoToRawImage } from "../../AlignmentApp/loader";
    import AlignmentApp from "../../AlignmentApp/components/AlignmentApp.svelte";

    interface Props {
        matches: TSimilarityMatches;
        open: boolean;
        onClose: () => void;
        threshold?: number;
    }

    let {
        matches,
        open = $bindable(),
        onClose,
        threshold = 0,
    }: Props = $props();

    // Create alignment state for this modal
    const alignmentState = new AlignmentState();

    // Track if images have been loaded
    let previousThreshold = $state(0);
    let imagesLoaded = $state(false);

    // Load images from matches into alignment state
    async function loadImagesFromMatches() {
        if (imagesLoaded && previousThreshold === threshold) return;
        imagesLoaded = true;
        previousThreshold = threshold;

        // Get up to 20 matches (query + 20 results)
        // + Prepare the expected transposition
        const imagesToLoad = [
            [matches.query, "none", "none"] as const,
            ...matches.matches
                .filter((m) => m.similarity >= threshold)
                .slice(0, 20)
                .map(
                    (m) =>
                        [
                            m.image,
                            m.m_transposition,
                            m.q_transposition,
                        ] as const,
                ),
        ];
        console.log(imagesToLoad)

        // Clear existing images
        alignmentState.images = [];

        // Load each image
        for (const [img, m_transp, q_transp] of imagesToLoad) {
            try {
                const rawImage = await imageInfoToRawImage(img);
                if (rawImage) {
                    const aligningImage: AligningImage = {
                        image: rawImage,
                        // TODO use m_transp & q_transp to preload transform
                        transform: initialMatrix(
                            rawImage.width,
                            rawImage.height,
                        ),
                        visible: true,
                        keypoints:
                            alignmentState.images.length > 0
                                ? alignmentState.images[0].keypoints.map((p) =>
                                      applyTransform(
                                          alignmentState.images[0].transform,
                                          p.x,
                                          p.y,
                                      ),
                                  )
                                : [],
                        opacity: 0.7,
                        invertColors: false,
                        hFlip:
                            m_transp.includes("hflip") !==
                            q_transp.includes("hflip"),
                    };
                    alignmentState.images = [
                        ...alignmentState.images,
                        aligningImage,
                    ];
                }
            } catch (error) {
                console.error("Failed to load image:", img.id, error);
            }
        }

        alignmentState.resync();
    }

    // Handle close - clean up images
    function handleClose() {
        // Revoke object URLs if needed
        for (const aligningImage of alignmentState.images) {
            if (typeof aligningImage.image.data === "string") {
                // Only revoke if it's an object URL we created
                if (aligningImage.image.data.startsWith("blob:")) {
                    URL.revokeObjectURL(aligningImage.image.data);
                }
            }
        }
        alignmentState.images = [];
        imagesLoaded = false;
        onClose();
    }

    // Load images when modal opens
    $effect(() => {
        if (open && (!imagesLoaded || previousThreshold !== threshold)) {
            loadImagesFromMatches();
        }
    });
</script>

<Dialog.Root bind:open>
    <Dialog.Portal>
        <div class="modal" class:is-active={open}>
            <Dialog.Overlay class="modal-background" onclick={handleClose} />
            <Dialog.Content class="modal-card align-from-matches-modal">
                {#snippet child({ props })}
                    <div {...props}>
                        <AlignmentApp {alignmentState} />
                    </div>
                {/snippet}
            </Dialog.Content>
        </div>
    </Dialog.Portal>
</Dialog.Root>

<style>
    .align-from-matches-modal {
        width: min(1600px, 92vw);
        max-height: 85vh;
        display: flex;
        flex-direction: column;
    }
</style>
