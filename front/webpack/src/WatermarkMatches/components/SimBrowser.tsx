import React, { useReducer } from "react";
import { Watermark, WatermarkMatches, WatermarkOutputRaw, WatermarksIndex, WatermarksIndexRaw, unserializeSingleWatermarkMatches } from "../types";
import { MatchRow } from "./MatchRow";
import { IconBtn } from "../../utils/IconBtn";
import { Magnifier, MagnifyingContext } from "./MatchViewer";
import { Pagination } from "./Pagination";

export interface SimBrowserProps {
    index: WatermarksIndex;
    matches: WatermarkMatches[];
}

export function WatermarkSimBrowser({ matches, index }: SimBrowserProps) {
    /*
    Component to render a list of watermark matches.
    */
    //

    const [group_by_source, toggleGroupBySource] = useReducer((group_by_source) => !group_by_source, true);
    const [magnifying, setMagnifying] = React.useState<Watermark | null>(null);
    const [page, setPage] = React.useState(0);
    const [highlit, setHighlit] = React.useState<Watermark | null>(null);

    const PAGINATE_BY = 30;
    const total_pages = Math.ceil(matches.length/PAGINATE_BY);

    const matchesHref = (watermark: Watermark) => {
        const watermark_index = matches.findIndex(match => match.query === watermark);
        return `#match-${watermark_index}`;
    }
    const hashchange = () => {
        const loc = window.location.hash;
        if (loc.startsWith("#match-")) {
            const match_id = parseInt(loc.slice(7));
            setHighlit(matches[match_id].query);
            setPage(Math.floor(match_id/PAGINATE_BY));
            return;
        }
        setHighlit(null);
        if (loc.startsWith("#page-")) {
            setPage(parseInt(loc.slice(6))-1);
        }
    };
    React.useEffect(() => {
        window.addEventListener("hashchange", hashchange);
        hashchange();
        return () => window.removeEventListener("hashchange", hashchange);
    }, []);

    const toPage = (page: number) => {
        window.location.hash = `#page-${page+1}`;
    }

    return (
        <MagnifyingContext.Provider value={{magnify: setMagnifying, matchesHref}}>
            <div className="viewer-options">
                <p className="field">
                    <label className="checkbox">
                        <input type="checkbox" className="checkbox mr-2" name="group-by-source" id="group-by-source" defaultChecked onChange={toggleGroupBySource} />
                        Group by source document
                    </label>
                </p>
                <Pagination page={page} setPage={toPage} total_pages={total_pages} />
            </div>
            <div className="viewer-table">

            {matches.slice(page*PAGINATE_BY, (page+1)*PAGINATE_BY).map((matches, idx) => (
                <MatchRow key={idx} matches={matches} group_by_source={group_by_source} highlit={highlit==matches.query} />
            ))}
            </div>
            <div className="mt-4"></div>
            <Pagination page={page} setPage={toPage} total_pages={total_pages} />
            {magnifying && <Magnifier magnifying={magnifying} />}
        </MagnifyingContext.Provider>
    );
}
