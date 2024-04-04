import { Icon } from "@iconify/react";
import { WatermarkMatch } from "../types";
import { pageUrlForImage } from "../utils";


export function Match({watermark, similarity, transformation}: WatermarkMatch) {
    /*
    Component to render a single watermark match.
    */
    return (
        <div className="match-item">
            <img src={watermark.image_url} alt={watermark.name} className={"match-img "+transformation} />
            <a href={pageUrlForImage(watermark)} className="match-source" target="_blank">
                <Icon icon="mdi:book-open-blank-variant" />
            </a>
            <span className="similarity">{(similarity*100).toFixed(0)}%</span>
        </div>
    );
}
