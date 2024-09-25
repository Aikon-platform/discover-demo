import React, { useReducer } from "react";
import { WatermarkMatches } from "../types";
import { MatchRow } from "./MatchRow";
import { Magnifier, MagnifyProps, MagnifyingContext } from "./Magnifier";

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
