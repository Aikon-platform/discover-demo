import type {
    TClusterImageInfoRaw,
    TClusterImageInfo,
    TClusteringFileRaw,
    TClusteringFile,
} from "./types";

/**
 * Convert the raw image from Django to a TClusterImageInfo
 * @param image
 * @returns
 */
export function unserializeImageInfo(image: TClusterImageInfoRaw): TClusterImageInfo {
    return {
        ...image,
        id: image.path,
        num: image.id,
        url: image.raw_url,
    };
}
function serializeImageInfo(image: TClusterImageInfo): TClusterImageInfoRaw {
    return {
        ...image,
        path: image.id,
        id: image.num,
        raw_url: image.url,
    };
}

/**
 * Convert a raw clustering file from Django to a TClusteringFile
 * @param file
 * @returns
 */
export function unserializeClusterFile(file: TClusteringFileRaw): TClusteringFile {
    return {
        clusters: Object.fromEntries(
            Object.entries(file.clusters).map(([key, value]) => [
                parseInt(key),
                {
                    ...value,
                    images: value.images.map(unserializeImageInfo),
                },
            ])
        ),
        background_urls: file.background_urls,
        image_metadata_csv: file.csv_export_file,
    };
}

/**
 * Convert a TClusteringFile to a raw clustering file for Django
 * @param file
 * @returns
 */
export function serializeClusterFile(file: TClusteringFile): TClusteringFileRaw {
    return {
        clusters: Object.fromEntries(
            Object.entries(file.clusters).map(([key, value]) => [
                parseInt(key),
                {
                    ...value,
                    images: value.images.map(serializeImageInfo),
                },
            ])
        ),
        background_urls: file.background_urls,
    };
}
