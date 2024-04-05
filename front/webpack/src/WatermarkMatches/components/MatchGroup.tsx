import { useReducer } from "react";
import { WatermarkMatch } from "../types";
import { Match } from "./Match";
import { Icon } from "@iconify/react";
import { IconBtn } from "../../utils/IconBtn";

export function MatchGroup({ matches, grouped }: { matches: WatermarkMatch[], grouped: boolean }) {
    /*
    Component to render a group of watermark matches.
    */
    // expand the group or not
    const [expanded, toggleExpand] = useReducer((expanded) => !expanded, false);

    return (
        <div className="column match-group">
            <div className={expanded ? "match-expanded" : "match-excerpt"}>
            <h4>{grouped && <Icon icon="mdi:folder"></Icon>} {matches[0].watermark.source.name}</h4>
            <div className="columns is-multiline match-items">
                {matches.map((match, idx) => (
                    (expanded || idx==0) && <Match key={idx} {...match} />
                ))}
            </div>
            {matches.length > 1 && <IconBtn icon="mdi:animation-plus" className="expand-link" onClick={toggleExpand} label={expanded ? "Collapse" : `+${matches.length -1}`}/>}
            </div>
        </div>
    );
}
