import { useReducer } from "react";
import { WatermarkMatch } from "../types";
import { Match } from "./Match";

export function MatchGroup({ matches }: { matches: WatermarkMatch[] }) {
    /*
    Component to render a group of watermark matches.
    */
    // expand the group or not
    const [expanded, toggleExpand] = useReducer((expanded) => !expanded, false);

    return (
        <div className="column match-group">
            <h4>{matches[0].watermark.source.name}</h4>
            <div className="match-group-items">
                {matches.map((match, idx) => (
                    (expanded || idx==0) ? <Match key={idx} {...match} /> : null
                ))}
            </div>
            {matches.length > 1 ? <a href="javascript:void(0)" className="expand-link" onClick={toggleExpand}>{expanded ? "Collapse" : "Expand"} {matches.length -1} from same source</a> : null}
        </div>
    );
}
