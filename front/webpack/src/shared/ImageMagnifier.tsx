import React from "react";
import { IconBtn } from "./IconBtn";
import { MatchTransposition } from "../SimilarityApp/types";
import { ImageToDisplay } from "./ImageDisplay";
import {ImageIdentification} from "./ImageIdentification";


export interface MagnifyProps {
    image?: ImageToDisplay;
    transpositions?: MatchTransposition[];
    comparison?: ImageToDisplay;
}

export interface MagnifyingContext {
    // Context to manage focusing on a Watermark
    magnify?: ({image, transpositions, comparison}:MagnifyProps) => void;
    setComparison?: (comparison?: ImageToDisplay | undefined, setPinned?: (pinned: boolean) => void) => void;
}

export const MagnifyingContext = React.createContext<MagnifyingContext>({});

export function ImageMagnifier({ image, transpositions, comparison }: MagnifyProps) {
    /*
    Component to render a magnified view of a watermark.
    */
    const context = React.useContext(MagnifyingContext);
    const setMagnifying = context.magnify!;
    const [transf, setTransf] = React.useState<MatchTransposition[]>(transpositions || []);

    const manualTransform = (deltaRot: 0 | 90 | -90, hflip: boolean) => {
        const curRotStr = transf.find(t => t && t.startsWith("rot"));
        const prevHflip = transf.includes("hflip");
        const curRot = curRotStr ? parseInt(curRotStr.slice(3)) : 0;
        let newRot = curRot;
        if (hflip && curRot % 180) newRot += 180;
        newRot = (newRot + deltaRot + 360) % 360;
        const newTransf = [];
        if (newRot) newTransf.push(`rot${newRot}`);
        if (hflip !== prevHflip) newTransf.push("hflip");
        setTransf(newTransf as MatchTransposition[]);
    }

    React.useEffect(() => {
        setTransf(transpositions || []);
    }, [transpositions]);

    return image && (
        <div className="magnifier" onClick={() => setMagnifying({ image: undefined })}>
            <IconBtn icon="mdi:close" className="magnifier-close"/>
            <div className="magnifying-content">
                {comparison &&
                    <div className="magnifying-item" onClick={(e) => e.stopPropagation()}>
                        <div className="display-image">
                            <img src={comparison.url} alt={comparison.id} className="display-img" />
                        </div>
                        <div className="magnifying-info">
                            <ImageIdentification image={comparison} isTitle={true} prefix={"Query"}/>
                            {comparison.link && <p><a href={comparison.link} target="_blank">See in context</a></p>}
                        </div>
                    </div>
                }
                <div className="magnifying-item" onClick={(e) => e.stopPropagation()}>
                    <div className="display-image">
                        <img src={image.url} alt={image.id} className={"display-img " + (transf.join(" "))} />
                    </div>
                    <div className="magnifying-info">
                        <ImageIdentification image={image} isTitle={true}/>
                        <p className="actions my-2">
                            <IconBtn icon="mdi:rotate-left" onClick={() => manualTransform(-90, false)} />
                            <IconBtn icon="mdi:rotate-right" onClick={() => manualTransform(90, false)} />
                            <IconBtn icon="mdi:flip-horizontal" onClick={() => manualTransform(0, true)} />
                        </p>
                        {image.link && <p><a href={image.link} target="_blank">See in context</a></p>}
                    </div>
                </div>
            </div>
        </div>
    );
}
