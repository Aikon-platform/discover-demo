import { Icon } from "@iconify/react";
import { MatchTransformation, Watermark } from "../types";
import { MagnifyingContext } from "./MatchViewer";
import React from "react";

interface WatermarkProps {
    watermark: Watermark;
    similarity?: number;
    transformations?: MatchTransformation[];
}

export function Watermark({watermark, similarity, transformations}: WatermarkProps) {
    /*
    Component to render a single watermark match.
    */
    const magnifyier = React.useContext(MagnifyingContext);

    return (
        <div className="match-item column">
            <img src={watermark.image_url} alt={watermark.name} className={"match-img "+(transformations || []).join(" ")} onClick={() => magnifyier.magnify && magnifyier.magnify({watermark, transformations})} />
            <div className="match-tools">
                {watermark.link && <a href={watermark.link} className="match-source" target="_blank" title="See in context">
                    <Icon icon="mdi:book-open-blank-variant" />
                </a>}
                {magnifyier.magnify && <a href="javascript:void(0)" className="match-magnify" title="Magnify" onClick={() => magnifyier.magnify!({watermark, transformations})}>
                    <Icon icon="mdi:arrow-expand" />
                </a>}
                {magnifyier.matchesHref && <a href={magnifyier.matchesHref(watermark)} className="match-focus" title="Show matches">
                    <Icon icon="mdi:image-search" />
                </a>}
            </div>
            {similarity && <span className="similarity">{(similarity*100).toFixed(0)}%</span>}
        </div>
    );
}
