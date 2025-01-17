import { useReducer } from "react";
import { Watermark, WatermarkMatch } from "../types";
import { WatermarkDisplay } from "./WatermarkDisplay";
import { Icon } from "@iconify/react";
import { IconBtn } from "../../shared/IconBtn";

interface MatchGroupProps {
    matches: WatermarkMatch[];
    grouped?: boolean;
    threshold?: number;
    wref?: Watermark;
}

export function MatchGroup({ matches, grouped, threshold, wref }: MatchGroupProps) {
    /*
    Component to render a group of watermark matches.
    */
    // expand the group or not
    const [expanded, toggleExpand] = useReducer((expanded) => !expanded, false);

    return (
        (!threshold || matches[0].similarity > threshold/100) &&
        <div className="column match-group">
            <div className={expanded ? "match-expanded" : "match-excerpt"}>
            <h4>{grouped && <Icon icon="mdi:folder"></Icon>} {matches[0].watermark.source?.name}</h4>
            <div className="columns is-multiline match-items">
                {matches.map((match, idx) => (
                    (expanded || idx==0) && (!threshold || match.similarity > threshold/100) && <WatermarkDisplay key={idx} wref={wref} {...match} />
                ))}
            </div>
            {matches.length > 1 && <IconBtn icon={expanded ? "mdi:close" : "mdi:animation-plus"} onClick={toggleExpand} label={expanded ? "Collapse" : `+${matches.length -1}`}/>}
            </div>
        </div>
    );
}
