import type { TImageInfo } from "../shared/types";
import { toAligningImages, unserializeAlignmentResults } from "./converters";
import type { AlignmentState, RawImage } from "./state.svelte";
import type { TAlignmentResultsRaw } from "./types";

/**
 * Load an image from its URL (direct or IIIF) to get its dimensions
 * @returns The image, or null if it could not be loaded
 */
export async function imageInfoToRawImage(
    image: Pick<TImageInfo, "id" | "url" | "name" | "src">,
): Promise<RawImage | null> {
    const imageUrl = image.url || image.src;
    if (!imageUrl) return null;

    const img = new Image();
    const loadWithTimeout = (useCrossOrigin = false): Promise<void> =>
        new Promise((resolve, reject) => {
            const timeoutId = setTimeout(() => reject(new Error("Image load timeout")), 5000);
            img.onload = () => {
                clearTimeout(timeoutId);
                resolve();
            };
            img.onerror = () => {
                clearTimeout(timeoutId);
                reject(new Error("Failed to load image"));
            };
            if (useCrossOrigin) img.crossOrigin = "anonymous";
            img.src = imageUrl;
        });

    try {
        // Try without crossOrigin first, then with it
        await loadWithTimeout(false);
    } catch {
        try {
            await loadWithTimeout(true);
        } catch (error) {
            console.error("Failed to load image:", image.id, error);
            return null;
        }
    }

    if (img.width === 0 || img.height === 0) return null;

    return {
        file_name: image.name || image.id,
        width: img.width,
        height: img.height,
        data: imageUrl,
    };
}

/**
 * Fetch the results of an alignment task and load them into the state
 * (images that cannot be loaded are skipped, unless it is the reference)
 */
export async function loadAlignmentResults(
    url: string,
    alignmentState: AlignmentState,
): Promise<void> {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Could not fetch alignment results (${response.status})`);
    }
    const results = unserializeAlignmentResults(
        (await response.json()) as TAlignmentResultsRaw,
    );

    const rawImages = await Promise.all(
        results.images.map((aligned) => imageInfoToRawImage(aligned.info)),
    );
    if (!rawImages[0]) {
        throw new Error(`Could not load reference image ${results.images[0].info.id}`);
    }
    const loaded = results.images
        .map((aligned, i) => [aligned, rawImages[i]] as const)
        .filter(([, raw]) => raw !== null);

    alignmentState.transformModel = results.transformModel;
    alignmentState.keepAspectRatio = results.keepAspectRatio;
    alignmentState.images = toAligningImages(
        { ...results, images: loaded.map(([aligned]) => aligned) },
        loaded.map(([, raw]) => raw!),
    );
    alignmentState.selected = alignmentState.images.length > 1 ? [1] : [];
}
