import React, { useReducer } from "react";
import { Watermark, WatermarkMatches, WatermarkOutputRaw, WatermarksIndexRaw, unserializeSingleWatermarkMatches } from "../types";
import { MatchRow } from "./MatchRow";
import { IconBtn } from "../../utils/IconBtn";

export interface MagnifyingContext {
    magnify?: (watermark: Watermark | null) => void;
    showMatches?: (watermark: Watermark) => void;
}

export const MagnifyingContext = React.createContext<MagnifyingContext>({});

export function MatchViewer({ all_matches }: { all_matches: WatermarkMatches[] }) {
    /*
    Component to render a list of watermark matches.
    */
    const [group_by_source, toggleGroupBySource] = useReducer((group_by_source) => !group_by_source, true);
    const [magnifying, setMagnifying] = React.useState<Watermark | null>(null);

    return (
        <MagnifyingContext.Provider value={{magnify: setMagnifying}}>
            <div className="viewer-options">
                <p>
                    <input type="checkbox" name="group-by-source" id="group-by-source" defaultChecked onChange={toggleGroupBySource} />
                    <label htmlFor="group-by-source">Group by source document</label>
                </p>
            </div>
            <div className="viewer-table">
            {all_matches.map((matches, idx) => (
                <MatchRow key={idx} matches={matches} group_by_source={group_by_source} />
            ))}
            </div>
            {magnifying && <Magnifier magnifying={magnifying} />}
        </MagnifyingContext.Provider>
    );
}

export function Magnifier({magnifying}: {magnifying: Watermark}) {
    const setMagnifying = React.useContext(MagnifyingContext).magnify!;
    return (
        <div className="magnifier" onClick={() => setMagnifying(null)} >
            <IconBtn icon="mdi:close"/>
            <img src={magnifying.image_url} alt={magnifying.name} />
            <h4>{magnifying.name} {magnifying.source && `(${magnifying.source.name})`}</h4>
        </div>
    )
}
