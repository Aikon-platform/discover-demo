/*
 Alignment of the images of a cluster, prefilled from the DTI affine or projective
 transforms of the clustering's image metadata csv (cluster_by_path.csv)
*/

import { parseCSVLine } from "../shared/utils";
import type { AligningImage, RawImage } from "../AlignmentApp/state.svelte";
import { imageInfoToRawImage } from "../AlignmentApp/loader";
import {
    initialMatrix,
    invertMatrix,
    isProperWarp,
    multiplyMatrix,
    type TransformMatrix,
} from "../AlignmentApp/transform";
import type { TClusterInfo } from "./types";

/** Maximum number of cluster images loaded for alignment (closest to the prototype first) */
export const MAX_ALIGN_IMAGES = 20;

/**
 * DTI spatial transform, image -> prototype in normalized coordinates ([-1, 1]):
 * - affine (F.affine_grid): align_corners=False on both sides
 * - projective (kornia homography_warp): image grid with align_corners=True,
 *   sampled in the prototype with align_corners=False
 */
export type TDTITransformKind = "affine" | "projective";

export interface TImageAlignMetadata {
    cluster_id: number;
    toPrototype?: { kind: TDTITransformKind; matrix: TransformMatrix };
}

/** Csv columns of each transform kind (DTI transformation names and their aliases) */
const TRANSFORM_COLUMNS: Record<TDTITransformKind, string[]> = {
    affine: ["matrix_affine", "matrix_aff"],
    projective: ["matrix_projective", "matrix_proj", "matrix_homography"],
};

/** "[a, c, e, b, d, f, g, h, i]" (flattened 3x3 or 2x3 rows) -> TransformMatrix */
function parseMatrix(value: string | undefined): TransformMatrix | undefined {
    if (!value) return undefined;
    let flat: unknown;
    try {
        flat = JSON.parse(value);
    } catch {
        return undefined;
    }
    if (!Array.isArray(flat) || (flat.length !== 9 && flat.length !== 6)) return undefined;
    if (!flat.every((x) => typeof x === "number" && Number.isFinite(x))) return undefined;
    const [a, c, e, b, d, f, g = 0, h = 0, i = 1] = flat as number[];
    return { a, b, c, d, e, f, g, h, i };
}

/**
 * Parse the image metadata csv
 * (header like "image_id,path,cluster_name,cluster_id,matrix_color,matrix_affine,dist_cluster_0")
 * @returns The metadata by image_id (TClusterImageInfo.num)
 * @throws If the csv has both affine and projective transforms (ambiguous composition)
 */
export function parseImageMetadataCSV(text: string): Map<number, TImageAlignMetadata> {
    const lines = text.split(/\r?\n/).filter((line) => line.trim() !== "");
    const result = new Map<number, TImageAlignMetadata>();
    if (lines.length === 0) return result;

    const header = parseCSVLine(lines[0]);
    const idCol = header.indexOf("image_id");
    const clusterCol = header.indexOf("cluster_id");
    if (idCol < 0 || clusterCol < 0) return result;

    const transformCols = (Object.keys(TRANSFORM_COLUMNS) as TDTITransformKind[])
        .map((kind) => [kind, header.findIndex((h) => TRANSFORM_COLUMNS[kind].includes(h))] as const)
        .filter(([, col]) => col >= 0);
    if (transformCols.length > 1) {
        throw new Error("Image metadata has both affine and projective transforms");
    }
    const [kind, transformCol] = transformCols[0] ?? [];

    for (const line of lines.slice(1)) {
        const fields = parseCSVLine(line);
        const id = parseInt(fields[idCol]);
        if (isNaN(id)) continue;
        const matrix = kind && parseMatrix(fields[transformCol!]);
        result.set(id, {
            cluster_id: parseInt(fields[clusterCol]),
            toPrototype: matrix ? { kind, matrix } : undefined,
        });
    }
    return result;
}

/** Pixels of a width x height image -> torch normalized coordinates */
function normalizationMatrix(width: number, height: number, alignCorners = false): TransformMatrix {
    if (alignCorners) {
        // Pixel centers (at x + 0.5) span [-1, 1]
        const sx = 2 / (width - 1);
        const sy = 2 / (height - 1);
        return { a: sx, b: 0, c: 0, d: sy, e: -sx / 2 - 1, f: -sy / 2 - 1, g: 0, h: 0, i: 1 };
    }
    return { a: 2 / width, b: 0, c: 0, d: 2 / height, e: -1, f: -1, g: 0, h: 0, i: 1 };
}

/**
 * Load the prototype and images of a cluster as aligning images. Images are placed
 * in the prototype frame through their DTI transform when the metadata has one
 * (for the same cluster, as images moved to another cluster were fitted to another prototype)
 * @param cluster The cluster to align
 * @param base_url The url the cluster's relative urls are relative to
 * @param metadata The image metadata, if available
 * @returns The aligning images (prototype first, if any) and the kind of the prefilled transforms, if any
 */
export async function loadClusterAligningImages(
    cluster: TClusterInfo,
    base_url: string,
    metadata: Map<number, TImageAlignMetadata> | null,
): Promise<{ images: AligningImage[]; prefilled: TDTITransformKind | null }> {
    const clusterImages = [...cluster.images]
        .sort((a, b) => (a.distance ?? Infinity) - (b.distance ?? Infinity))
        .slice(0, MAX_ALIGN_IMAGES);

    const [proto, ...rawImages] = await Promise.all([
        cluster.proto_url
            ? imageInfoToRawImage({
                  id: cluster.proto_url,
                  url: base_url + cluster.proto_url,
                  name: `${cluster.name} (prototype)`,
              })
            : Promise.resolve(null),
        ...clusterImages.map((image) =>
            imageInfoToRawImage({ ...image, url: base_url + image.url }),
        ),
    ]);

    const loaded = clusterImages
        .map((image, k) => [image, rawImages[k]] as const)
        .filter((pair): pair is readonly [(typeof pair)[0], RawImage] => pair[1] !== null);
    const ref = proto ?? loaded[0]?.[1];
    if (!ref) return { images: [], prefilled: null };

    // Normalized prototype coordinates -> world space
    const refInv = invertMatrix(normalizationMatrix(ref.width, ref.height))!;
    const fromPrototype = multiplyMatrix(initialMatrix(ref.width, ref.height), refInv);

    let prefilled: TDTITransformKind | null = null;
    const toAligning = (image: RawImage, transform: TransformMatrix): AligningImage => ({
        image,
        transform,
        visible: true,
        keypoints: [],
        opacity: 0.7,
        invertColors: false,
        hFlip: false,
    });

    const images = loaded.map(([info, image]) => {
        const meta = metadata?.get(info.num);
        let transform = initialMatrix(image.width, image.height);
        const toPrototype = meta?.cluster_id === cluster.id ? meta.toPrototype : undefined;
        if (toPrototype) {
            const normalize = normalizationMatrix(
                image.width,
                image.height,
                toPrototype.kind === "projective",
            );
            const warp = multiplyMatrix(
                fromPrototype,
                multiplyMatrix(toPrototype.matrix, normalize),
            );
            if (isProperWarp(warp, image.width, image.height)) {
                transform = warp;
                prefilled = toPrototype.kind;
            } else {
                console.warn(`${image.file_name}: improper ${toPrototype.kind} transform, reset`);
            }
        }
        return toAligning(image, transform);
    });

    if (proto) images.unshift(toAligning(proto, initialMatrix(proto.width, proto.height)));
    return { images, prefilled };
}
