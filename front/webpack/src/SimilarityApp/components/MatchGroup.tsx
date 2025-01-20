import React, { useReducer } from "react";
import { SimilarityMatch } from "../types";
import { ImageInfo } from "../../shared/types";
import { ImageDisplay } from "../../shared/ImageDisplay";
import { Icon } from "@iconify/react";
import { IconBtn } from "../../shared/IconBtn";
import { NameProviderContext, getImageName, getSourceName } from "../../shared/naming";
import { SimilarityHrefContext } from "./ImageSimBrowser";

interface MatchGroupProps {
    matches: SimilarityMatch[];
    grouped?: boolean;
    threshold?: number;
    wref?: ImageInfo;
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
        (!threshold || matches[0].similarity >= threshold) &&
        <div className="column match-group">
            <div className={expanded ? "match-expanded" : "match-excerpt"}>
            <p>{grouped ?
                <React.Fragment>
                    <Icon icon="mdi:folder"></Icon>
                    {getSourceName(nameProvider, matches[0].image.document)}
                </React.Fragment> :
                <span>Image #{matches[0].image.num}: {getImageName(nameProvider, matches[0].image) || matches[0].image.name}</span>
                }</p>
            <div className="columns is-multiline match-items">
                {matches.map((match, idx) => (
                    (expanded || idx==0) && (!threshold || match.similarity >= threshold) && <ImageDisplay key={idx} comparison={wref} href={matchesRef(match.image)} {...match} />
                ))}
            </div>
            {matches.length > 1 && <IconBtn icon={expanded ? "mdi:close" : "mdi:animation-plus"} onClick={toggleExpand} label={expanded ? "Collapse" : `+${matches.length -1}`}/>}
            </div>
        </div>
    );
}
