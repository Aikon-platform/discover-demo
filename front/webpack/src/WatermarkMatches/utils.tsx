import { QueryWatermark, Watermark } from "./types";

export function pageUrlForImage(image: Watermark) {
    return image.source.page_url.replace("{page}", image.page.toString());
}

export function urlForQuery(query: QueryWatermark) {
    if (query.crop_id !== undefined)
        return query.source_url.replace(/\.[^.]*$/, `+${query.crop_id}.jpg`);
    return query.source_url;
}
