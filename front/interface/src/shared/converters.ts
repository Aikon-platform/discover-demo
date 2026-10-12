import type { TImageIndex, TImageIndexRaw, TImageInfo } from "./types";

/**
 * Unserializes an image index
 * @param index The index
 * @returns The unserialized index
 */
export function unserializeImageIndex(index: TImageIndexRaw): TImageIndex {
    const source_documents = Object.fromEntries(
        Object.entries(index.sources).map(([id, source]) => [
            id,
            { name: source.metadata?.name || source.uid, ...source },
        ]),
    );
    const source_images: TImageInfo[] = index.images.map((image, i) => ({
        id: image.id,
        num: i,
        src: image.src,
        url: image.url,
        document: source_documents[image.doc_uid],
        metadata: image.metadata || {},
    }));

    return {
        sources: Object.values(source_documents),
        images: source_images,
    };
}
