import React, { useReducer } from "react";
import { SimImage, SimilarityMatch } from "../types";
import { ImageDisplay } from "../../shared/ImageDisplay";
import { Icon } from "@iconify/react";
import { IconBtn } from "../../shared/IconBtn";
import { NameProviderContext, getSourceName } from "../utils/naming";
import { SimilarityHrefContext } from "./ImageSimBrowser";

interface MatchGroupProps {
    matches: SimilarityMatch[];
    grouped?: boolean;
    threshold?: number;
    wref?: SimImage;
}

export function MatchGroup({ matches, grouped, threshold, wref }: MatchGroupProps) {
    /*
    Component to render a group of watermark matches.
    */
    // expand the group or not
    const [expanded, toggleExpand] = useReducer((expanded) => !expanded, false);
    const nameProvider = React.useContext(NameProviderContext);
    const matchesRef = React.useContext(SimilarityHrefContext).matchesHref || (() => undefined);

    return (
        (!threshold || matches[0].similarity > threshold/100) &&
        <div className="column match-group">
            <div className={expanded ? "match-expanded" : "match-excerpt"}>
            <h4>{grouped && <Icon icon="mdi:folder"></Icon>} {getSourceName(nameProvider, matches[0].image.document)}</h4>
            <div className="columns is-multiline match-items">
                {matches.map((match, idx) => (
                    (expanded || idx==0) && (!threshold || match.similarity > threshold/100) && <ImageDisplay key={idx} comparison={wref} href={matchesRef(match.image)} {...match} />
                ))}
            </div>
            {matches.length > 1 && <IconBtn icon={expanded ? "mdi:close" : "mdi:animation-plus"} onClick={toggleExpand} label={expanded ? "Collapse" : `+${matches.length -1}`}/>}
            </div>
        </div>
    );
}
