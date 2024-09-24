import { Icon } from "@iconify/react";
import { MatchTransformation, Watermark } from "../types";
import React from "react";
import { MagnifyingContext } from "./Magnifier";

interface WatermarkProps {
    watermark: Watermark;
    similarity?: number;
    transformations?: MatchTransformation[];
    wref?: Watermark
}

export function WatermarkDisplay({watermark, similarity, transformations, wref}: WatermarkProps) {
    /*
    Component to render a single watermark match.
    */
    const magnifyier = React.useContext(MagnifyingContext);

    return (
        <div className="match-item column">
            <div className="match-img">
                <img src={watermark.image_url} alt={watermark.name} className={"watermark "+(transformations || []).join(" ")} onClick={() => magnifyier.magnify && magnifyier.magnify({watermark, transformations, wref})} />
            </div>
            <div className="match-tools">
                {watermark.link && <a href={watermark.link} className="match-source" target="_blank" title="See in context">
                    <Icon icon="mdi:book-open-blank-variant" />
                </a>}
                {magnifyier.magnify && <a href="javascript:void(0)" className="match-magnify" title="Magnify" onClick={() => magnifyier.magnify!({watermark, transformations, wref})}>
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
