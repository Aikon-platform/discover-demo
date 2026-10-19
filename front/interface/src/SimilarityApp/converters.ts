import type {
    TSimilarityIndexRaw,
    TSimilarityIndex,
    TSimpleSimilarityMatchRaw,
    TSimilarityMatches,
    TSimilarityMatchRaw,
    TSimilarityOutputRaw,
    TSimilarityMatch,
} from "./types";
import type { TImageInfo } from "../shared/types";

/**
 * Unserializes a similarity index
 * @param index The index
 * @returns The unserialized index
 */
function unserializeSimilarityIndex(index: TSimilarityIndexRaw): TSimilarityIndex {
    const source_documents = Object.fromEntries(
        Object.entries(index.sources).map(([id, source]) => [
            id,
            { name: source.metadata?.name || source.uid, ...source },
        ])
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
        transpositions: index.transpositions || ["none"],
    };
}

/**
 * Unserializes a similarity matrix
 * @param raw_matches The raw matches
 * @param index_raw The raw index
 * @returns The unserialized matches and index
 */
export function unserializeSimilarityMatrix(
    raw_matches: TSimpleSimilarityMatchRaw[],
    index_raw: TSimilarityIndexRaw
): { matches: TSimilarityMatches[]; index: TSimilarityIndex } {
    const index = unserializeSimilarityIndex(index_raw);
    const complex_matches: TSimilarityMatchRaw[][] = index.images.map(() => []);
    raw_matches.forEach(([source_index, query_index, similarity]) => {
        // Create a symmetric matrix
        complex_matches[query_index].push({
            similarity,
            best_source_flip: 0,
            best_query_flip: 0,
            query_index: query_index,
            source_index: source_index,
        });
        complex_matches[source_index].push({
            similarity,
            best_source_flip: 0,
            best_query_flip: 0,
            query_index: source_index,
            source_index: query_index,
        });
    });
    return {
        matches: unserializeImageMatches(
            complex_matches,
            index,
            index
        ),
        index,
    };
}

/**
 * Unserializes image matches
 * @param query_index The queries
 * @param raw_matches The raw matches
 * @param source_index The index
 * @returns The unserialized matches
 */
function unserializeImageMatches(
    raw_matches: TSimilarityOutputRaw,
    source_index: TSimilarityIndex,
    query_index: TSimilarityIndex
): TSimilarityMatches[] {
    const matches: TSimilarityMatches[] = [];
    for (let i = 0; i < raw_matches.length; i++) {
        const query = query_index.images[i];
        const matches_for_query = raw_matches[i]
            .map((match) => {
                const source_image = source_index.images[match.source_index];
                return {
                    image: source_image,
                    similarity: match.similarity,
                    q_transposition: query_index.transpositions[match.best_query_flip],
                    m_transposition: source_index.transpositions[match.best_source_flip],
                };
            })
            .sort((a, b) => b.similarity - a.similarity);

        const grouped_by_source: { [key: string]: TSimilarityMatch[] } = {};
        const groups: TSimilarityMatch[][] = [];
        matches_for_query.forEach((match) => {
            if (!grouped_by_source[match.image.document!.uid]) {
                const newgroup: TSimilarityMatch[] = [];
                grouped_by_source[match.image.document!.uid] = newgroup;
                groups.push(newgroup);
            }
            grouped_by_source[match.image.document!.uid].push(match);
        });

        matches.push({
            query,
            matches: matches_for_query,
            matches_by_document: groups,
        });
    }
    return matches.sort((a, b) => b.matches[0].similarity - a.matches[0].similarity);
}

/**
 * Unserializes search results
 * @param raw_index The raw index
 * @param raw_matches The raw matches
 * @returns The unserialized index and matches
 */
export function unserializeSearchResults(
    raw_index: TSimilarityIndexRaw,
    raw_matches: { query: TSimilarityIndexRaw, pairs: TSimpleSimilarityMatchRaw[] }
): { source_index: TSimilarityIndex; query_index: TSimilarityIndex; matches: TSimilarityMatches[] } {
    console.log(raw_matches, raw_index);
    const source_index = unserializeSimilarityIndex(raw_index);
    const query_index = unserializeSimilarityIndex(raw_matches.query);
    const complex_matches: TSimilarityMatchRaw[][] = query_index.images.map(() => []);
    raw_matches.pairs.forEach(([source_index, query_index, similarity]) => {
        complex_matches[query_index].push({
            similarity,
            best_source_flip: 0,
            best_query_flip: 0,
            query_index: query_index,
            source_index: source_index,
        });
    });
    const matches = unserializeImageMatches(complex_matches, source_index, query_index);
    return { source_index, query_index, matches };
}
