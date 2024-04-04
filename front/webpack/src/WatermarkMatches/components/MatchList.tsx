import React, { useReducer } from "react";
import { MatchListProps, WatermarkOutputRaw, WatermarksIndexRaw, unserializeWatermarkOutputs } from "../types";
import { MatchRow } from "./MatchRow";

export function MatchList({ query, matches, source_index, source_url }: MatchListProps) {
    /*
    Component to render a list of watermark matches.
    */
    const all_matches = unserializeWatermarkOutputs(query, matches, source_index, source_url);
    console.log(all_matches);

    return (
        <div>
            {all_matches.map((matches, idx) => (
                <MatchRow key={idx} matches={matches} />
            ))}
        </div>
    );
}
