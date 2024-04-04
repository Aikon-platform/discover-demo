import { WatermarkMatch } from "../types";
import { pageUrlForImage } from "../utils";


export function Match({watermark, similarity, transformation}: WatermarkMatch) {
    /*
    Component to render a single watermark match.
    */
    return (
        <div className="match-col column">
            <a href={pageUrlForImage(watermark)} className="column query-col" target="_blank">
                <img src={watermark.image_url} alt={watermark.name} />
            </a>
        </div>
    );
}
