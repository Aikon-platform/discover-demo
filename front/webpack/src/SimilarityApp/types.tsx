import React from "react";
import internal from "stream";
import { Document, ImageInfo } from "../shared/types";

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
    transpositions?: MatchTransposition[];
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
    query_transpositions: MatchTransposition[];
}

export type MatchTransposition = "none" | "rot90" | "rot180" | "rot270" | "hflip" | "vflip" | "rot90 hflip" | "rot180 hflip" | "rot270 hflip";

export interface SimilarityIndex {
    sources: Document[];
    images: ImageInfo[];
    transpositions: MatchTransposition[];
}

// QUERY TYPES

export interface QueryImage {
    source_url: string;
    crop_id?: number;
    bbox?: [number, number, number, number];
}

// RESULT TYPES

export interface SimilarityMatch {
    image: ImageInfo;
    similarity: number;
    q_transposition: MatchTransposition;
    m_transposition: MatchTransposition;
}

export interface SimilarityMatches {
    query: ImageInfo;
    matches: SimilarityMatch[];
    matches_by_document: SimilarityMatch[][];
}
