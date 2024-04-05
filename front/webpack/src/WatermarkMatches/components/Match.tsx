import { Icon } from "@iconify/react";
import { WatermarkMatch } from "../types";
import { pageUrlForImage } from "../utils";
import { MagnifyingContext } from "./MatchViewer";
import React from "react";


export function Match({watermark, similarity, transformations}: WatermarkMatch) {
    /*
    Component to render a single watermark match.
    */
    const magnifyier = React.useContext(MagnifyingContext);

    return (
        <div className="match-item column">
            <img src={watermark.image_url} alt={watermark.name} className={"match-img "+transformations.join(" ")} />
            <div className="match-tools">
                <a href={pageUrlForImage(watermark)} className="match-source" target="_blank" title="See in context">
                    <Icon icon="mdi:book-open-blank-variant" />
                </a>
                <a href="javascript:void(0)" className="match-magnify" title="Magnify" onClick={() => magnifyier.magnify(watermark.image_url)}>
                    <Icon icon="mdi:arrow-expand" />
                </a>
            </div>
            <span className="similarity">{(similarity*100).toFixed(0)}%</span>
        </div>
    );
}
