import internal from "stream";

// RAW TYPES

export interface WatermarksIndexRaw {
    sources: {
        [source_id: string]: {
            name: string;
            url: string;
            page_url: string;
        }
    }
    images: [
        {
            name: string;
            source: string;
            page: number;
        }
    ]
    flips: MatchTransformation[];
}

export interface WatermarkMatchRaw {
    similarity: number;
    best_source_flip: number;
    best_query_flip: number;
    query_index: number;
    source_index: number;
}

export type MatchTransformation = null | "rot90" | "rot180" | "rot270" | "hflip" | "vflip";

export interface WatermarkDetectionsRaw {
    boxes: [number, number, number, number][];
    scores: number[];
}


export interface WatermarkOutputRaw {
    matches: WatermarkMatchRaw[][];
    detection?: WatermarkDetectionsRaw;
    query_flips: MatchTransformation[];
}

// SOURCE TYPES

export interface WatermarkSource {
    id: string;
    name: string;
    url: string;
    page_url: string;
}

export interface Watermark {
    name: string;
    image_url: string;
    source?: WatermarkSource;
    id?: number;
    page?: number;
    link?: string;
}

export interface WatermarksIndex {
    sources: WatermarkSource[];
    images: Watermark[];
    flips: MatchTransformation[];
}

// QUERY TYPES

export interface QueryWatermark {
    source_url: string;
    crop_id?: number;
    bbox?: [number, number, number, number];
}

// RESULT TYPES

export interface WatermarkMatch {
    watermark: Watermark;
    similarity: number;
    transformations: MatchTransformation[];
}

export interface WatermarkMatches {
    query: Watermark;
    matches: WatermarkMatch[];
    matches_by_source: WatermarkMatch[][];
}

// PROPS

export function urlForQuery(source_url: string, crop_id: number|undefined) {
    if (crop_id !== undefined)
        return source_url.replace(/\.[^.]*$/, `+${crop_id}.jpg`);
    return source_url;
}

export function pageUrlForImage(image: Watermark) {
    if (!image.source) {
        return image.image_url;
    }
    if (!image.page) {
        return image.source.url;
    }
    return image.source.page_url.replace("{page}", image.page.toString());
}

export function unserializeWatermarkIndex(index: WatermarksIndexRaw, base_url: string): WatermarksIndex {
    const source_documents = Object.fromEntries(
        Object.entries(index.sources).map(([id, source]) => [id, { id: id, ...source }])
    );
    const source_images: Watermark[] = index.images.map((image, i) => (
        {
            id: i,
            source: source_documents[image.source],
            name: image.name,
            page: image.page,
            image_url: base_url + image.source + "/" + image.name
        }));
    source_images.forEach(image => {
        image.link = pageUrlForImage(image);
    });

    return {
        sources: Object.values(source_documents),
        images: source_images,
        flips: index.flips
    };
}

export function unserializeSingleWatermarkMatches(query_image: string, raw_matches: WatermarkOutputRaw, raw_index: WatermarksIndexRaw, base_url: string): WatermarkMatches[] {
    const index = unserializeWatermarkIndex(raw_index, base_url);
    const queries: Watermark[] = [];
    if (raw_matches.detection) {
        for (let i = 0; i < raw_matches.detection.boxes.length; i++) {
            queries.push({
                image_url: urlForQuery(query_image, i),
                name: `Query ${i+1}`,
            });
        }
    } else {
        queries.push({
            image_url: query_image,
            name: "Query",
        });
    }
    return unserializeWatermarkMatches(queries, raw_matches, index);
}

export function unserializeWatermarkSimilarity(raw_matches: WatermarkOutputRaw, raw_index: WatermarksIndexRaw, base_url: string): WatermarkMatches[] {
    const index = unserializeWatermarkIndex(raw_index, base_url);
    return unserializeWatermarkMatches(index.images, raw_matches, index);
}

export function unserializeWatermarkMatches(queries: Watermark[], raw_matches: WatermarkOutputRaw, index: WatermarksIndex): WatermarkMatches[] {
    const matches: WatermarkMatches[] = [];
    for (let i = 0; i < raw_matches.matches.length; i++) {
        const query = queries[i];
        const matches_for_query = (
            raw_matches.matches[i].map(match => {
                const source_image = index.images[match.source_index];
                return {
                    watermark: source_image,
                    similarity: match.similarity,
                    transformations: [raw_matches.query_flips[match.best_query_flip], index.flips[match.best_source_flip]]
                };
            })
        );

        const grouped_by_source: {[key: string]: WatermarkMatch[]} = {};
        const groups: WatermarkMatch[][] = [];
        matches_for_query.forEach(match => {
            if (!grouped_by_source[match.watermark.source!.id]) {
                const newgroup: WatermarkMatch[] = []
                grouped_by_source[match.watermark.source!.id] = newgroup;
                groups.push(newgroup);
            }
            grouped_by_source[match.watermark.source!.id].push(match);
        });

        matches.push({
            query,
            matches: matches_for_query,
            matches_by_source: groups
        });
    }
    return matches;
}
