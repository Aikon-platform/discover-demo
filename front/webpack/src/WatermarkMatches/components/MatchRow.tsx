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
        <div className="match-row columns is-2">
            <div className="column match-query is-2">
                <h4>Query</h4>
                <img src={ urlForQuery(matches.query)} alt="Query" />
            </div>
            <div className="column columns match-results is-10">
                {Object.keys(grouped_by_source).map(source_id => (
                    <MatchGroup key={source_id} matches={grouped_by_source[source_id]} />
                ))}
            </div>
        </div>
    );
}
