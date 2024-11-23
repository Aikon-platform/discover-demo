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
    document?: SimDocument;
    link?: string;
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

// PROPS

export function unserializeSimilarityIndex(index: SimilarityIndexRaw): SimilarityIndex {
    const source_documents = Object.fromEntries(
        Object.entries(index.sources).map(([id, source]) => [id, { name: source.metadata?.name || source.uid, ...source }])
    );
    const source_images: SimImage[] = index.images.map((image, i) => (
        {
            id: image.id,
            src: image.src,
            url: image.url,
            document: source_documents[image.doc_uid]
        }));

    return {
        sources: Object.values(source_documents),
        images: source_images,
        flips: index.flips || [null]
    };
}

export function unserializeSimilarityMatrix(raw_matches: SimpleSimilarityMatchRaw[], index_raw: SimilarityIndexRaw): { matches: SimilarityMatches[], index: SimilarityIndex } {
    const index = unserializeSimilarityIndex(index_raw);
    const complex_matches: SimilarityMatchRaw[][] = index.images.map(() => []);
    raw_matches.forEach(([source_index, query_index, similarity]) => {
        // Create a symmetric matrix
        complex_matches[query_index].push({ similarity, best_source_flip: 0, best_query_flip: 0, query_index, source_index });
        complex_matches[source_index].push({ similarity, best_source_flip: 0, best_query_flip: 0, query_index, source_index });
    });
    return { matches: unserializeImageMatches(index.images, { matches: complex_matches, query_flips: index.flips }, index), index };
}

export function unserializeImageMatches(queries: SimImage[], raw_matches: SimilarityOutputRaw, index: SimilarityIndex): SimilarityMatches[] {
    const matches: SimilarityMatches[] = [];
    for (let i = 0; i < raw_matches.matches.length; i++) {
        const query = queries[i];
        const matches_for_query = (
            raw_matches.matches[i].map(match => {
                const source_image = index.images[match.source_index];
                return {
                    image: source_image,
                    similarity: match.similarity,
                    transformations: [raw_matches.query_flips[match.best_query_flip], index.flips[match.best_source_flip]]
                };
            }).sort((a, b) => b.similarity - a.similarity)
        );

        const grouped_by_source: { [key: string]: SimilarityMatch[] } = {};
        const groups: SimilarityMatch[][] = [];
        matches_for_query.forEach(match => {
            if (!grouped_by_source[match.image.document!.uid]) {
                const newgroup: SimilarityMatch[] = []
                grouped_by_source[match.image.document!.uid] = newgroup;
                groups.push(newgroup);
            }
            grouped_by_source[match.image.document!.uid].push(match);
        });

        matches.push({
            query,
            matches: matches_for_query,
            matches_by_document: groups
        });
    }
    return matches.sort((a, b) => b.matches[0].similarity - a.matches[0].similarity);
}
