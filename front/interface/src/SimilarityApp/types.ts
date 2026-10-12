import type { TImageIndexRaw, TImageIndex, TImageInfo, TMatchTransposition } from "../shared/types";

// RAW TYPES

export interface TSimilarityIndexRaw extends TImageIndexRaw {
    transpositions?: (TMatchTransposition | number)[];
}

export type TSimpleSimilarityMatchRaw = [number, number, number] // [source_index, query_index, similarity]

export interface TSimilarityMatchRaw {
    similarity: number;
    best_source_flip: number;
    best_query_flip: number;
    query_index: number;
    source_index: number;
}

export type TSimilarityOutputRaw = TSimilarityMatchRaw[][]; // matches for each query image

export interface TSimilarityIndex extends TImageIndex {
    transpositions: TMatchTransposition[];
}

// QUERY TYPES

export interface TQueryImage {
    source_url: string;
    crop_id?: number;
    bbox?: [number, number, number, number];
}

// RESULT TYPES

export interface TSimilarityMatch {
    image: TImageInfo;
    similarity: number;
    q_transposition: TMatchTransposition;
    m_transposition: TMatchTransposition;
}

export interface TSimilarityMatches {
    query: TImageInfo;
    matches: TSimilarityMatch[];
    matches_by_document: TSimilarityMatch[][];
}
