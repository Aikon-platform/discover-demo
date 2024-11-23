import React, { useEffect } from "react";
import { SimilarityMatches, SimilarityMatch } from "../types";
import { ImageDisplay } from "./ImageDisplay";
import { MatchGroup } from "./MatchGroup";
import { MatchCSVExporter } from "./MatchExporter";

interface MatchRowProps {
    matches: SimilarityMatches;
    group_by_source: boolean;
    highlit?: boolean;
    threshold?: number;
}

export function MatchRow({matches, group_by_source, highlit, threshold}: MatchRowProps) {
    /*
    Component to render a single watermark match.
    */
    const [showAll, toggleShowAll] = React.useReducer((showAll) => !showAll, false);
    const groups = group_by_source ? matches.matches_by_document : matches.matches.map(m => [m]);
    const scrollRef = React.useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (highlit) {
            scrollRef.current?.scrollIntoView({behavior: "smooth", block: "center"});
        }
    }, [highlit]);

    return (
        <div className={"match-row columns " + (highlit?"highlit":"")} ref={scrollRef}>
            <div className="column match-query">
                <h4>{matches.query.document?.name || matches.query.id}</h4>
                <div className="columns is-multiline match-items is-centered">
                    <ImageDisplay image={matches.query} />
                </div>
                {groups.length > 5 && <p><a href="javascript:void(0)" onClick={toggleShowAll}>{showAll ? "Show only 5 best" : `Show all results`}</a></p>}
                <MatchCSVExporter matches={matches} threshold={threshold} />
            </div>
            <div className="column columns match-results">
                {groups.slice(0, showAll ? groups.length : 5).map((grouped_by_source, k) => (
                    <MatchGroup key={k} matches={grouped_by_source} grouped={group_by_source} threshold={threshold} wref={matches.query} />
                ))}
            </div>
        </div>
    );
}
