import React from "react";
import internal from "stream";

// RAW TYPES

export interface SimilarityIndexRaw {
    sources: {
        [source_id: string]: {
            uid: string;
            src: string;
            type: string;
            metadata: { [key: string]: string };
        }
    }
    images: [
        {
            id: string;
            src: string; // e.g. iiif url
            url: string; // e.g. media url
            doc_uid: string;
            metadata?: { [key: string]: string };
        }
    ]
    flips?: MatchTransformation[];
}

export type SimpleSimilarityMatchRaw = [number, number, number] // [source_index, query_index, similarity]

export interface SimilarityMatchRaw {
    similarity: number;
    best_source_flip: number;
    best_query_flip: number;
    query_index: number;
    source_index: number;
}

export interface SimilarityOutputRaw {
    matches: SimilarityMatchRaw[][]; // matches for each query image
    query_flips: MatchTransformation[];
}

export type MatchTransformation = null | "rot90" | "rot180" | "rot270" | "hflip" | "vflip";

// SOURCE TYPES

export interface SimDocument {
    uid: string;
    src: string;
    type: string;
    name: string;
    metadata: { [key: string]: string };
}

export interface SimImage {
    id: string;
    url: string;
    src?: string;
    name?: string;
    document?: SimDocument;
    link?: string;
    metadata?: { [key: string]: string };
}

export interface SimilarityIndex {
    sources: SimDocument[];
    images: SimImage[];
    flips: MatchTransformation[];
}

// QUERY TYPES

export interface QueryImage {
    source_url: string;
    crop_id?: number;
    bbox?: [number, number, number, number];
}

// RESULT TYPES

export interface SimilarityMatch {
    image: SimImage;
    similarity: number;
    transformations: MatchTransformation[];
}

export interface SimilarityMatches {
    query: SimImage;
    matches: SimilarityMatch[];
    matches_by_document: SimilarityMatch[][];
}

// CONTEXT

export interface NameProvider {
    [source_id: string]: {
        name: string;
        metadata: { [key: string]: string };
        images: { [image_id: string]: string };
    }
}
