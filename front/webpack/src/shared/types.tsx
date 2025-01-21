
// SOURCE TYPES

export interface Document {
    uid: string;
    src: string;
    type: string;
    name: string;
    metadata: { [key: string]: string; };
}

export interface ImageInfo {
    id: string;
    num: number;
    url: string;
    src?: string;
    name?: string;
    document?: Document;
    link?: string;
    metadata?: { [key: string]: string; };
    subtitle?: string | undefined;
}// CONTEXT

export interface NameProvider {
    [source_id: string]: {
        name: string;
        metadata: { [key: string]: string; };
        images: { [image_id: string]: string; };
    };
}
