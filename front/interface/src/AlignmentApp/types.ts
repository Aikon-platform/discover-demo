import type { TSimilarityIndexRaw } from "../SimilarityApp/types";
import type { TImageInfo } from "../shared/types";
import type { Point } from "./state.svelte";
import type { TransformMatrix, TransformModel } from "./transform";

// Raw output of the API alignment task (api/app/alignment/alignment.py)

export type TAlignTargetTransformRaw =
    | "scale"
    | "scalexy"
    | "scale+rotate"
    | "scalexy+rotate"
    | "affine"
    | "homographic";

export interface TAlignKeypointRaw {
    x: number;
    y: number;
    /** RANSAC inlier flag */
    inlier: boolean;
}

export interface TAlignedImageRaw {
    image_id: string;
    /** 3x3 rows, image pixels -> reference pixels (null if not estimated) */
    transform_matrix: number[][] | null;
    /** Same order as the reference keypoints, null where unmatched */
    keypoints: (TAlignKeypointRaw | null)[];
    is_reference?: boolean | null;
}

export interface TAlignmentResultsRaw {
    parameters: {
        method: string;
        target_transform: TAlignTargetTransformRaw;
        reference_image: string;
    };
    /** images[i] describes index.images[i] */
    index: TSimilarityIndexRaw;
    images: TAlignedImageRaw[];
}

// Unserialized results

export interface TAlignedImage {
    info: TImageInfo;
    /** Image pixels -> reference pixels (identity for the reference, null if not estimated) */
    toReference: TransformMatrix | null;
    /** Shared across images, null where unmatched; RANSAC outliers are disabled */
    keypoints: (Point | null)[];
}

export interface TAlignmentResults {
    method: string;
    transformModel: TransformModel;
    /** Reference first */
    images: TAlignedImage[];
}
