import React from "react";
import { WatermarkMatches, WatermarkMatch } from "../types";
import { Match } from "./Match";
import { urlForQuery } from "../utils";
import { MatchGroup } from "./MatchGroup";
import { MagnifyingContext } from "./MatchViewer";

interface MatchRowProps {
    matches: WatermarkMatches;
    group_by_source: boolean;
}

export function MatchRow({matches, group_by_source}: MatchRowProps) {
    /*
    Component to render a single watermark match.
    */
    const groups: WatermarkMatch[][] = [];
    if (group_by_source) {
        const grouped_by_source: {[key: string]: WatermarkMatch[]} = {};
        matches.matches.forEach(match => {
            if (!grouped_by_source[match.watermark.source.id]) {
                const newgroup: WatermarkMatch[] = []
                grouped_by_source[match.watermark.source.id] = newgroup;
                groups.push(newgroup);
            }
            grouped_by_source[match.watermark.source.id].push(match);
        });
    } else {
        matches.matches.forEach(match => {
            groups.push([match]);
        });
    }
    const [showAll, toggleShowAll] = React.useReducer((showAll) => !showAll, false);
    const magnifier = React.useContext(MagnifyingContext);

    return (
        <div className="match-row columns is-2">
            <div className="column match-query is-2">
                <h4>Query</h4>
                <img src={urlForQuery(matches.query)} alt="Query" onClick={() => magnifier.magnify(urlForQuery(matches.query))} />
                {groups.length > 5 && <p><a href="javascript:void(0)" onClick={toggleShowAll}>{showAll ? "Show only 5 best" : `Show all ${groups.length} results`}</a></p>}
            </div>
            <div className="column columns match-results is-10">
                {groups.slice(0, showAll ? groups.length : 5).map((grouped_by_source, k) => (
                    <MatchGroup key={k} matches={grouped_by_source} grouped={group_by_source} />
                ))}
            </div>
        </div>
    );
}
