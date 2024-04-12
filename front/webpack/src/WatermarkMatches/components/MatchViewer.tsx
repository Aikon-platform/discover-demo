import React, { useReducer } from "react";
import { MatchTransformation, Watermark, WatermarkMatches, WatermarkOutputRaw, WatermarksIndexRaw, unserializeSingleWatermarkMatches } from "../types";
import { MatchRow } from "./MatchRow";
import { IconBtn } from "../../utils/IconBtn";

export interface MagnifyProps {
    watermark?: Watermark;
    transformations?: MatchTransformation[];
}

export interface MagnifyingContext {
    // Context to manage focusing on a Watermark
    magnify?: ({watermark, transformations}:MagnifyProps) => void;
    matchesHref?: (watermark: Watermark) => string;
}

export const MagnifyingContext = React.createContext<MagnifyingContext>({});

export function MatchViewer({ all_matches }: { all_matches: WatermarkMatches[] }) {
    /*
    Component to render a list of watermark matches.
    */
    const [group_by_source, toggleGroupBySource] = useReducer((group_by_source) => !group_by_source, true);
    const [magnifying, setMagnifying] = React.useState<MagnifyProps | null>(null);

    return (
        <MagnifyingContext.Provider value={{magnify: setMagnifying}}>
            <div className="viewer-options">
                <p className="field">
                    <label className="checkbox">
                        <input type="checkbox" className="checkbox mr-2" name="group-by-source" id="group-by-source" defaultChecked onChange={toggleGroupBySource} />
                        Group by source document
                    </label>
                </p>
            </div>
            <div className="viewer-table">
            {all_matches.map((matches, idx) => (
                <MatchRow key={idx} matches={matches} group_by_source={group_by_source} />
            ))}
            </div>
            {magnifying && <Magnifier {...magnifying} />}
        </MagnifyingContext.Provider>
    );
}

export function Magnifier({watermark, transformations}: MagnifyProps) {
    /*
    Component to render a magnified view of a watermark.
    */
    const setMagnifying = React.useContext(MagnifyingContext).magnify!;

    return watermark && (
        <div className="magnifier" onClick={() => setMagnifying({watermark:undefined})} >
            <IconBtn icon="mdi:close"/>
            <img src={watermark.image_url} alt={watermark.name} className={"match-img "+(transformations ? transformations.join(" ") : "")} />
            <h4 className="mt-2">{watermark.source?.name || watermark.name}</h4>
            <p>{watermark.source && watermark.name}</p>
            {watermark.link && <p><a href={watermark.link} target="_blank">See in context</a></p>}
        </div>
    )
}
