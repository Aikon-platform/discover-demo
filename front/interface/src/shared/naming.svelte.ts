import { getContext, setContext } from "svelte";
import type { TDocument, TImageInfo } from "./types";

/**
 * This module defines a class that handles the mapping [imageId -> name]
 */


/**
 * Metadata for an image, or a source.
 * Recursive interface to allow various document structures.
 */
interface TImageMetadata {
    name?: string;
    description?: string;
    url?: string;
    metadata?: Record<string, any>;
    source?: TImageMetadata;
}

interface TNameProvider {
    sortImages: (images: TImageInfo[]) => TImageInfo[];
    getImageTitle: (image: TImageInfo, ellipsis?: boolean) => string;
    getImageDescription: (image?: TImageInfo) => string;
    getImageMetadata: (image?: TImageInfo) => Record<string, any>;
    getImageLink: (image: TImageInfo) => string | undefined;
    fetchIIIFNames: (documents: TDocument[]) => Promise<any>;
    fetchMetadataNames: (metadata_url: string) => Promise<void>;
}

export default class NameProvider implements TNameProvider {
    mapping: Record<string, string> = $state.raw({});
    sources: Record<string, TImageMetadata> = $state.raw({});

    constructor(sources?: Record<string, TImageMetadata>, mapping?: Record<string, string>) {
        this.sources = sources || {};
        this.mapping = mapping || {};
    }

    /**
     * Resolve the key for an image.
     * @param image The image.
     * @returns The key.
     */
    private resolveKey(image: TImageInfo): string {
        return this.mapping[image.src || image.id] || this.mapping[image.id] || image.src || image.id;
    }

    /**
     * Look for a field in the sources, including in recursive sources.
     * @param key The key.
     * @param field The field.
     * @returns The value of the field.
     */
    private resolveField<K extends keyof TImageMetadata>(key: string, field: K): TImageMetadata[K] {
        if (this.sources[key]?.[field]) return this.sources[key][field];
        return undefined;
    }

    /**
     * Get the title of an image, to be displayed.
     * @param image The image.
     * @param ellipsis Whether to truncate the name.
     * @returns The name of the image.
     */
    getImageTitle(image: TImageInfo, ellipsis = false): string {
        const key = this.resolveKey(image);
        let name: string = this.resolveField(key, "name") || key;
        if (ellipsis) {
            name = name.split(".").slice(0, -1).join(".");
            if (name.length >= 16) {
                name = name.slice(0, 5) + "..." + name.slice(-10);
            }
        }
        return name;
    }

    /**
     * Get the description of an image (usually, name of source).
     * @param source The source.
     * @returns The name of the source.
     */
    getImageDescription(image?: TImageInfo): string {
        if (image === undefined) return "";
        const description = this.resolveField(this.resolveKey(image), "description");
        if (description) return description;
        if (image.document) return this.resolveField(image.document.uid, "name") || "";
        return "";
    }

    /**
     * Get the metadata of an image.
     * @param image The image.
     * @returns The metadata of the image.
     */
    getImageMetadata(image?: TImageInfo): Record<string, any> {
        if (image === undefined) return {};
        let metadata = {
            ...image.metadata,
            ...this.resolveField(this.resolveKey(image), "metadata")
        };
        if (image.document) metadata = {
            ...metadata,
            ...image.document.metadata,
            ...this.resolveField(image.document.uid, "metadata") || {}
        };
        return metadata;
    }

    getImageLink(image: TImageInfo) {
        if (image.link) return image.link;
        const resolved = this.resolveField(this.resolveKey(image), "url");
        if (resolved) return resolved;
        // CUDL IIIF specific hook
        if (image.document?.name.startsWith("cudllibcamacuk")) {
            const url = image.document.src.replace("/iiif/", "/view/");
            return `${url}/${image.metadata?.page}`;
        }
        return undefined;
    }

    /**
     * Fetch the names of the sources from a IIIF manifest.
     * Known sources are ignored.
     * @param documents The sources.
     * @returns A promise that resolves when the names are fetched.
     */
    fetchIIIFNames(documents: TDocument[]) {
        return new Promise(async (resolve, reject) => {
            for (const source of documents) {
                if (this.sources[source.uid]) continue;
                fetch(source.src)
                    .then((response) => response.json())
                    .then((manifest) => {
                        // extract title and other metadata
                        if (manifest.metadata === undefined) return source;
                        const metadata = Object.fromEntries(
                            manifest.metadata.map(
                                ({
                                    label,
                                    value,
                                }: {
                                    label: string;
                                    value: string;
                                }) => [label.toLowerCase(), value]
                            )
                        );
                        if (metadata.title === undefined)
                            metadata.title = source.name;

                        if (metadata.classmark !== undefined)
                            metadata.title =
                                metadata.classmark + " " + metadata.title;

                        // extract image names?
                        const canvases =
                            manifest.sequences && manifest.sequences[0]?.canvases;
                        const image_labels: Record<string, string> =
                            canvases &&
                            Object.fromEntries(
                                canvases.map((canvas: any) => {
                                    const label: string =
                                        canvas.label ||
                                        canvas.title ||
                                        (canvas.images && canvas.images[0].label) ||
                                        canvas["@id"] ||
                                        canvas.id;
                                    const id: string =
                                        (canvas.images &&
                                            canvas.images[0].resource &&
                                            canvas.images[0].resource["@id"]) ||
                                        canvas["@id"] ||
                                        canvas.id;
                                    return [id, label];
                                })
                            );

                        const document_source = {
                            description: metadata.title,
                            metadata,
                            images: image_labels,
                        };

                        const image_sources = Object.fromEntries(
                            Object.entries(image_labels).map(([id, label]) => [
                                id,
                                {
                                    name: label,
                                    metadata,
                                    source: document_source,
                                },
                            ])
                        );

                        this.sources = {
                            ...this.sources,
                            ...image_sources,
                        }

                        // no need for mapping, image_sources is already referenced with image id

                        this.sources[source.uid] = document_source;
                    });
                // slow down the requests
                await new Promise((resolve) => setTimeout(resolve, 300));
            }
        });
    }

    fetchMetadataNames(metadata_url: string): Promise<void> {
        return fetch(metadata_url).then(response => response.json()).then(data => {
            const sources: Record<string, { name: string; description: string, [key: string]: any }> = data["sources"];
            const mapping: Record<string, string> = data["mapping"];

            this.sources = {
                ...this.sources,
                ...sources,
            }

            this.mapping = {
                ...this.mapping,
                ...mapping,
            }
        });
    }

    /**
     * Sort images by source and then by name.
     * @param images The images to sort.
     * @returns The sorted images.
     */
    sortImages(images: TImageInfo[]) {
        const sortfn = (a: TImageInfo, b: TImageInfo) => {
            const source_a = this.getImageDescription(a);
            const source_b = this.getImageDescription(b);
            if (source_a === source_b) {
                return this.getImageTitle(a).localeCompare(
                    this.getImageTitle(b)
                );
            }
            return (source_a || "").localeCompare(source_b || "");
        };
        return images.sort(sortfn);
    }
}

const no_name_provider: TNameProvider = {
    sortImages: (images: TImageInfo[]) => images,
    getImageTitle: (image: TImageInfo) => image.name || image.id,
    getImageDescription: (image?: TImageInfo) => image?.document?.name || image?.document?.uid || "",
    getImageMetadata: (image?: TImageInfo) => {return {}},
    getImageLink: (image?: TImageInfo) => undefined,
    fetchIIIFNames: async (documents: TDocument[]) => {},
    fetchMetadataNames: async (metadata_url: string) => {},
}

export function getNameProvider(): TNameProvider {
    return getContext<NameProvider>("name_provider") || no_name_provider;
}

export function setNameProvider(name_provider: NameProvider) {
    setContext("name_provider", name_provider);
}
