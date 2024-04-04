import React from "react";
import { WatermarkMatches, WatermarkMatch } from "../types";
import { Match } from "./Match";
import { urlForQuery } from "../utils";
import { MatchGroup } from "./MatchGroup";

export function MatchRow({matches}: {matches :WatermarkMatches}) {
    /*
    Component to render a single watermark match.
    */
    const grouped_by_source = matches.matches.reduce((acc, match) => {
        if (!acc[match.watermark.source.id]) {
            acc[match.watermark.source.id] = [];
        }
        acc[match.watermark.source.id].push(match);
        return acc;
    }, {} as {[key: string]: WatermarkMatch[]});
    console.log(grouped_by_source);

    return (
        <div className="match-row columns">
            <div className="column query-col">
                <img src={ urlForQuery(matches.query)} alt="Query" />
            </div>
            {Object.keys(grouped_by_source).map(source_id => (
                <MatchGroup key={source_id} matches={grouped_by_source[source_id]} />
            ))}
        </div>
    );
}
