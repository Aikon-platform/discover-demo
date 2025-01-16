import { Icon } from "@iconify/react";
import { MatchTransformation, SimImage } from "../SimilarityApp/types";
import React from "react";
import { MagnifyingContext } from "./ImageMagnifier";
import { TooltipContext } from "./ImageTooltip";

export interface ImageInfo {
    id: string;
    url: string;
    link?: string;
    title?: string;
    subtitle?: string;
}

interface ImageDisplayProps {
    image: ImageInfo;
    similarity?: number;
    transformations?: MatchTransformation[];
    comparison?: ImageInfo;
    href?: string;
    disable_magnify?: boolean;
}

export function ImageDisplay({image, similarity, transformations, comparison, href, disable_magnify}: ImageDisplayProps) {
    /*
    Component to render a single watermark match.
    */
    const magnifier = React.useContext(MagnifyingContext);
    const tooltip = React.useContext(TooltipContext);

    return (
        <div className="display-item"
            onMouseEnter={() => tooltip.setTooltip && tooltip.setTooltip({image: image, transformations})}
            onMouseLeave={() => tooltip.setTooltip && tooltip.setTooltip()}
            >
            <div className="display-image">
                <img src={image.url} alt={image.id} className={"display-img "+(transformations || []).join(" ")}
                onClick={!disable_magnify ? (() => magnifier.magnify && magnifier.magnify({image: image, transformations, comparison: comparison})) : undefined}
                />
            </div>
            <div className="display-tools">
                {image.link && <a href={image.link} className="match-source" target="_blank" title="See in context">
                    <Icon icon="mdi:book-open-blank-variant" />
                </a>}
                {magnifier.magnify && <a href="javascript:void(0)" className="match-magnify" title="Magnify" onClick={() => magnifier.magnify!({image: image, transformations, comparison: comparison})}>
                    <Icon icon="mdi:arrow-expand" />
                </a>}
                {href && <a href={href} className="match-focus" title="Show matches">
                    <Icon icon="mdi:image-search" />
                </a>}
            </div>
            {similarity && <span className="similarity">{(similarity*100).toFixed(0)}%</span>}
        </div>
    );
}
