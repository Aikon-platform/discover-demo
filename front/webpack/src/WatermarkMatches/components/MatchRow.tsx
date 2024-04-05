import React from "react";
import { WatermarkMatches, WatermarkMatch } from "../types";
import { Watermark } from "./Watermark";
import { MatchGroup } from "./MatchGroup";

interface MatchRowProps {
    matches: WatermarkMatches;
    group_by_source: boolean;
    highlit?: boolean;
}

export function MatchRow({matches, group_by_source, highlit}: MatchRowProps) {
    /*
    Component to render a single watermark match.
    */
    const [showAll, toggleShowAll] = React.useReducer((showAll) => !showAll, false);
    const groups = group_by_source ? matches.matches_by_source : [matches.matches];
    const scrollRef = React.useRef<HTMLDivElement>(null);

    if (highlit) {
        setTimeout(
            () => scrollRef.current?.scrollIntoView({behavior: "smooth", block: "center"}),
            100
        );
    }

    return (
        <div className={"match-row columns is-2 " + (highlit?"highlit":"")} ref={scrollRef}>
            <div className="column match-query is-2">
                <h4>{matches.query.name}</h4>
                <div className="columns is-multiline match-items is-centered">
                    <Watermark watermark={matches.query} />
                </div>
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
