import { unserializeImageIndex } from "../shared/converters";
import type { AligningImage, Point, RawImage } from "./state.svelte";
import {
    applyTransform,
    initialMatrix,
    invertMatrix,
    isProperWarp,
    multiplyMatrix,
    type TransformMatrix,
    type TransformModel,
} from "./transform";
import type {
    TAlignedImage,
    TAlignmentResults,
    TAlignmentResultsRaw,
    TAlignTargetTransformRaw,
} from "./types";

export const MAX_KEYPOINTS = 100;

/** 3x3 rows (numpy layout) -> TransformMatrix */
function unserializeMatrix(rows: number[][]): TransformMatrix {
    const [[a, c, e], [b, d, f], [g, h, i]] = rows;
    return { a, b, c, d, e, f, g, h, i };
}

/**
 * Unserializes alignment results
 * @param raw The raw alignment results from the API
 * @param maxKeypoints Number of keypoints to keep, the ones that are inliers in the most images
 * @returns The results, with the reference image first
 */
export function unserializeAlignmentResults(
    raw: TAlignmentResultsRaw,
    maxKeypoints: number = MAX_KEYPOINTS,
): TAlignmentResults {
    const index = unserializeImageIndex(raw.index);
    const refIdx = Math.max(
        0,
        raw.images.findIndex(
            (im) => im.is_reference,
        ),
    );

    // Keep the keypoints that are inliers in the most images, in their original order
    const nKeypoints = raw.images[refIdx]?.keypoints.length ?? 0;
    const inlierCount = new Array(nKeypoints).fill(0);
    raw.images.forEach((im, i) => {
        if (i === refIdx) return;
        im.keypoints.forEach((kp, k) => {
            if (kp?.inlier) inlierCount[k]++;
        });
    });
    const kept = inlierCount
        .map((count, k) => [count, k])
        .filter(([count]) => count > 0)
        .sort((p, q) => q[0] - p[0])
        .slice(0, maxKeypoints)
        .map(([, k]) => k)
        .sort((p, q) => p - q);

    const images: TAlignedImage[] = raw.images.map((im, i) => ({
        info: index.images[i],
        toReference:
            im.transform_matrix && unserializeMatrix(im.transform_matrix),
        keypoints: kept.map((k) => {
            const kp = im.keypoints[k];
            return kp && { x: kp.x, y: kp.y, disabled: !kp.inlier };
        }),
    }));

    return {
        method: raw.parameters.method,
        transformModel: raw.parameters.target_transform as TransformModel,
        images: [images[refIdx], ...images.filter((_, i) => i !== refIdx)],
    };
}

/**
 * Builds the images of an AlignmentState from alignment results
 * @param results The unserialized results (reference first)
 * @param rawImages The loaded images, rawImages[i] for results.images[i]
 * @returns The aligning images, placed in world space through the reference
 */
export function toAligningImages(
    results: TAlignmentResults,
    rawImages: RawImage[],
): AligningImage[] {
    const ref = rawImages[0];
    const refTransform = initialMatrix(ref.width, ref.height);
    const refKeypoints = results.images[0].keypoints;

    return results.images.map((aligned, i) => {
        const image = rawImages[i];
        let transform = refTransform;
        if (i > 0) {
            transform = aligned.toReference
                ? multiplyMatrix(refTransform, aligned.toReference)
                : initialMatrix(image.width, image.height);
            if (!isProperWarp(transform, image.width, image.height)) {
                console.warn(
                    `${image.file_name}: improper alignment transform, reset`,
                );
                transform = initialMatrix(image.width, image.height);
            }
        }

        // Unmatched keypoints: reference keypoint warped into this image, disabled
        const fromRef = invertMatrix(transform);
        const toImage = fromRef && multiplyMatrix(fromRef, refTransform);
        const keypoints: Point[] = aligned.keypoints.map((kp, k) => {
            if (kp) return kp;
            const r = refKeypoints[k]!;
            return {
                ...(toImage ? applyTransform(toImage, r.x, r.y) : r),
                disabled: true,
            };
        });

        return {
            image,
            transform,
            visible: true,
            keypoints,
            opacity: 0.7,
            invertColors: false,
            hFlip: false,
        };
    });
}
