import React from "react";
import { IconBtn } from "./IconBtn";
import { MatchTransformation } from "../SimilarityApp/types";
import { ImageInfo } from "./ImageDisplay";


export interface TooltipProps {
    image?: ImageInfo;
    transformations?: MatchTransformation[];
}

export interface TooltipContext {
    // Context to manage focusing on a Watermark
    setTooltip?: (tooltip?:TooltipProps) => void;
    getTitle?: (image: ImageInfo) => string;
    getSubtitle?: (image: ImageInfo) => string;
}

export const TooltipContext = React.createContext<TooltipContext>({});

export function ImageTooltip({ image, transformations }: TooltipProps) {
    /*
    Component to render a magnified view of a watermark.
    */
    const context = React.useContext(TooltipContext);
    const getTitle = context.getTitle || ((image: ImageInfo) => image.title);
    const getSubtitle = context.getSubtitle || ((image: ImageInfo) => image.subtitle);
    const refTooltip = React.useRef<HTMLDivElement>(null);

    const followMouse = (e: MouseEvent) => {
        if (refTooltip.current) {
            const x = e.clientX + 10;
            const y = e.clientY + 10;
            refTooltip.current.style.left = x + "px";
            refTooltip.current.style.top = y + "px";
        }
    }

    React.useEffect(() => {
        document.addEventListener("mousemove", followMouse);
        return () => document.removeEventListener("mousemove", followMouse);
    }, []);

    return image && (
        <div className="tooltip" ref={refTooltip}>
            <div className="display-image">
                <img src={image.url} alt={image.id} className={"display-img " + (transformations?.join(" "))} />
            </div>
            <h4 className="mt-2">{getTitle(image)}</h4>
            <p>{getSubtitle(image)}</p>
        </div>
    );
}
