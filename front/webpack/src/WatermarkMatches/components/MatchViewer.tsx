import React, { useReducer } from "react";
import { WatermarkOutputRaw, WatermarksIndexRaw, unserializeWatermarkOutputs } from "../types";
import { MatchRow } from "./MatchRow";
import { IconBtn } from "../../utils/IconBtn";

export interface MatchViewerProps {
    query: string;
    matches: WatermarkOutputRaw;
    source_index: WatermarksIndexRaw;
    source_url: string;
}

export interface MagnifyingContext {
    magnify: (url: string | null) => void;
}

export const MagnifyingContext = React.createContext<MagnifyingContext>({
    magnify: (url: string | null) => {}
});

export function MatchViewer({ query, matches, source_index, source_url }: MatchViewerProps) {
    /*
    Component to render a list of watermark matches.
    */
    const all_matches = unserializeWatermarkOutputs(query, matches, source_index, source_url);
    console.log(all_matches);

    const [group_by_source, toggleGroupBySource] = useReducer((group_by_source) => !group_by_source, true);
    const [magnifying, setMagnifying] = React.useState<string | null>(null);

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
            {magnifying &&
                <div className="magnifier" onClick={() => setMagnifying(null)} >
                    <IconBtn icon="mdi:close"/>
                    <img src={magnifying} alt={magnifying} />
                </div>}
        </MagnifyingContext.Provider>
    );
}
