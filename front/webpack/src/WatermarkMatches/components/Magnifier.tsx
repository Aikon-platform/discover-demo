import React from "react";
import { IconBtn } from "../../shared/IconBtn";
import { MatchTransformation, Watermark } from "../types";

export interface MagnifyProps {
    watermark?: Watermark;
    transformations?: MatchTransformation[];
    wref?: Watermark;
}

export interface MagnifyingContext {
    // Context to manage focusing on a Watermark
    magnify?: ({watermark, transformations, wref}:MagnifyProps) => void;
    matchesHref?: (watermark: Watermark) => string;
}

export const MagnifyingContext = React.createContext<MagnifyingContext>({});

export function Magnifier({ watermark, transformations, wref }: MagnifyProps) {
    /*
    Component to render a magnified view of a watermark.
    */
    const setMagnifying = React.useContext(MagnifyingContext).magnify!;
    const [transf, setTransf] = React.useState<MatchTransformation[]>(transformations || []);

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
        setTransf(newTransf as MatchTransformation[]);
    }

    React.useEffect(() => {
        setTransf(transformations || []);
    }, [transformations]);

    return watermark && (
        <div className="magnifier">
            <IconBtn icon="mdi:close" onClick={() => setMagnifying({ watermark: undefined })}/>
            <div className="columns">
                {wref &&
                    <div className="column is-6">
                        <div className="match-img">
                            <img src={wref.image_url} alt={wref.name} className="watermark" />
                        </div>
                        <h4 className="mt-2">Query: {wref.source?.name || wref.name}</h4>
                        <p>{wref.source && wref.name}</p>
                        {wref.link && <p><a href={wref.link} target="_blank">See in context</a></p>}
                    </div>
                }
                <div className="column is-6">
                    <div className="match-img">
                        <img src={watermark.image_url} alt={watermark.name} className={"watermark " + (transf.join(" "))} />
                    </div>
                    <h4 className="mt-2">{watermark.source?.name || watermark.name}</h4>
                    <p>{watermark.source && watermark.name}</p>
                    <p className="actions">
                        <IconBtn icon="mdi:rotate-left" onClick={() => manualTransform(-90, false)} />
                        <IconBtn icon="mdi:rotate-right" onClick={() => manualTransform(90, false)} />
                        <IconBtn icon="mdi:flip-horizontal" onClick={() => manualTransform(0, true)} />
                    </p>
                    {watermark.link && <p><a href={watermark.link} target="_blank">See in context</a></p>}
                </div>
            </div>
        </div>
    );
}
