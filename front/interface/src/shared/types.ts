// SOURCE TYPES

export type TPrimitive = string | number | boolean;

export interface TDocument {
    uid: string;
    src: string;
    type: string;
    name: string;
    metadata?: Record<string, string>;
}

export interface TImageInfo {
    id: string;
    num: number;
    url: string;

    src?: string;
    name?: string;
    document?: TDocument;
    link?: string;
    metadata?: Record<string, string>;
    subtitle?: string | undefined;
}

export type TMatchTransposition =
    | "none"
    | "rot90"
    | "rot180"
    | "rot270"
    | "hflip"
    | "vflip"
    | "rot90 hflip"
    | "rot180 hflip"
    | "rot270 hflip";

export interface TImageIndexRaw {
    sources: {
        [source_id: string]: {
            uid: string;
            src: string;
            type: string;
            metadata: { [key: string]: string };
        };
    };
    images: [
        {
            id: string;
            src: string; // e.g. iiif url
            url: string; // e.g. media url
            doc_uid: string;
            metadata?: { [key: string]: string };
        },
    ];
}

export interface TImageIndex {
    sources: TDocument[];
    images: TImageInfo[];
}
