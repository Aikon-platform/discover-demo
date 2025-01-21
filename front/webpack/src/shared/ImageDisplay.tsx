import { Icon } from "@iconify/react";
import { MatchTransposition } from "../SimilarityApp/types";
import { ImageInfo } from "./types";
import React from "react";
import { MagnifyingContext } from "./ImageMagnifier";
import { TooltipContext } from "./ImageTooltip";

export interface ImageToDisplay {
    id: string;
    num: number;
    url: string;
    link?: string;
    title?: string;
    subtitle?: string;
}

interface ImageDisplayProps {
    image: ImageToDisplay;
    similarity?: number;
    transpositions?: MatchTransposition[];
    comparison?: ImageToDisplay;
    href?: string;
    disable_magnify?: boolean;
}

export function ImageDisplay({image, similarity, transpositions, comparison, href, disable_magnify}: ImageDisplayProps) {
    /*
    Component to render a single watermark match.
    */
    const magnifier = React.useContext(MagnifyingContext);
    const tooltip = React.useContext(TooltipContext);
    const [pinned, setPinned] = React.useState(false);

    return (
        <div className="display-item"
            onMouseEnter={() => tooltip.setTooltip && tooltip.setTooltip({image: image, transpositions})}
            onMouseLeave={() => tooltip.setTooltip && tooltip.setTooltip()}
            >
            <div className="display-image">
                <img src={image.url} alt={image.id} className={"display-img "+(transpositions || []).join(" ")}
                onClick={!disable_magnify ? (() => magnifier.magnify && magnifier.magnify({image: image, transpositions, comparison})) : undefined}
                />
            </div>
            <div className="display-tools" onClick={(e) => e.stopPropagation()}>
                {image.link && <a href={image.link} className="image-source" target="_blank" title="See in context">
                    <Icon icon="mdi:book-open-blank-variant" />
                </a>}
                {magnifier.setComparison &&
                (!pinned ?
                <a href="javascript:void(0)" className="image-pin" title="Pin as comparison">
                    <Icon icon="mdi:pin" onClick={() => magnifier.setComparison!(image, setPinned)} />
                </a> :
                <a href="javascript:void(0)" className="image-pin always-visible" title="Pin as comparison">
                    <Icon icon="mdi:pin-off" onClick={() => magnifier.setComparison!(undefined)} />
                </a>)
                }
                {magnifier.magnify && <a href="javascript:void(0)" className="image-magnify" title="Magnify" onClick={() => magnifier.magnify!({image: image, transpositions: transpositions, comparison})}>
                    <Icon icon="mdi:arrow-expand" />
                </a>}
                {href && <a href={href} className="image-focus" title="Show detail">
                    <Icon icon="mdi:image-search" />
                </a>}
            </div>
            {similarity && <span className="similarity">{similarity}</span>}
        </div>
    );
}
