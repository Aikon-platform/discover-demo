import { SimilarityIndexRaw, SimilarityIndex, SimpleSimilarityMatchRaw, SimilarityMatches, SimilarityMatchRaw, SimilarityOutputRaw, SimilarityMatch } from "../types";
import { ImageInfo } from "../../shared/types";


// PROPS

export function unserializeSimilarityIndex(index: SimilarityIndexRaw): SimilarityIndex {
    const source_documents = Object.fromEntries(
        Object.entries(index.sources).map(([id, source]) => [id, { name: source.metadata?.name || source.uid, ...source }])
    );
    const source_images: ImageInfo[] = index.images.map((image, i) => (
        {
            id: image.id,
            num: i,
            src: image.src,
            url: image.url,
            document: source_documents[image.doc_uid],
            metadata: image.metadata || {}
        }));

    return {
        sources: Object.values(source_documents),
        images: source_images,
        transpositions: index.transpositions || ["none"]
    };
}

export function unserializeSimilarityMatrix(raw_matches: SimpleSimilarityMatchRaw[], index_raw: SimilarityIndexRaw): { matches: SimilarityMatches[]; index: SimilarityIndex; } {
    const index = unserializeSimilarityIndex(index_raw);
    const complex_matches: SimilarityMatchRaw[][] = index.images.map(() => []);
    raw_matches.forEach(([source_index, query_index, similarity]) => {
        // Create a symmetric matrix
        complex_matches[query_index].push({ similarity, best_source_flip: 0, best_query_flip: 0, query_index: query_index, source_index: source_index });
        complex_matches[source_index].push({ similarity, best_source_flip: 0, best_query_flip: 0, query_index: source_index, source_index: query_index });
    });
    return { matches: unserializeImageMatches(index.images, { matches: complex_matches, query_transpositions: index.transpositions }, index), index };
}

export function unserializeImageMatches(queries: ImageInfo[], raw_matches: SimilarityOutputRaw, index: SimilarityIndex): SimilarityMatches[] {
    const matches: SimilarityMatches[] = [];
    for (let i = 0; i < raw_matches.matches.length; i++) {
        const query = queries[i];
        const matches_for_query = (
            raw_matches.matches[i].map(match => {
                const source_image = index.images[match.source_index];
                return {
                    image: source_image,
                    similarity: match.similarity,
                    q_transposition: raw_matches.query_transpositions[match.best_query_flip],
                    m_transposition: index.transpositions[match.best_source_flip]
                };
            }).sort((a, b) => b.similarity - a.similarity)
        );

        const grouped_by_source: { [key: string]: SimilarityMatch[]; } = {};
        const groups: SimilarityMatch[][] = [];
        matches_for_query.forEach(match => {
            if (!grouped_by_source[match.image.document!.uid]) {
                const newgroup: SimilarityMatch[] = [];
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
