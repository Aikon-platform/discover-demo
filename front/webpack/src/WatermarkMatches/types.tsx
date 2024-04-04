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
}

export interface WatermarkMatchRaw {
    similarity: number;
    best_source_flip: number;
    best_query_flip: number;
    query_index: number;
    source_index: number;
}

type MatchTransformation = null | "rot90" | "rot180" | "rot270" | "hflip" | "vflip";

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
    id: number;
    name: string;
    source: WatermarkSource;
    image_url: string;
    page: number;
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
    transformation: MatchTransformation;
}

export interface WatermarkMatches {
    query: QueryWatermark;
    matches: WatermarkMatch[];
}

// PROPS

export interface MatchListProps {
    query: string;
    matches: WatermarkOutputRaw;
    source_index: WatermarksIndexRaw;
    source_url: string;
}

export function unserializeWatermarkOutputs(query_image: string, raw: WatermarkOutputRaw, index: WatermarksIndexRaw, base_url: string): WatermarkMatches[] {
    console.log(raw);
    const query = {
        source_url: query_image
    };
    const queries: QueryWatermark[] = [];
    if (raw.detection) {
        for (let i = 0; i < raw.detection.boxes.length; i++) {
            queries.push({
                source_url: query_image,
                bbox: raw.detection.boxes[i],
                crop_id: i
            });
        }
    } else {
        queries.push(query);
    }

    const source_documents = Object.fromEntries(
        Object.entries(index.sources).map(([id, source]) => [id, { id: id, ...source }])
    );
    const source_images = index.images.map((image, i) => (
        {id: i, source: source_documents[image.source], name: image.name,
            page: image.page, image_url: base_url + image.source + "/" + image.name
        }));

    const matches: WatermarkMatches[] = [];
    for (let i = 0; i < raw.matches.length; i++) {
        const query = queries[i];
        const matches_for_query = (
            raw.matches[i].map(match => {
                const source_image = source_images[match.source_index];
                return {
                    watermark: source_image,
                    similarity: match.similarity,
                    transformation: raw.query_flips[match.best_query_flip]
                };
            })
        );
        matches.push({
            query,
            matches: matches_for_query
        });
    }
    return matches;
}
