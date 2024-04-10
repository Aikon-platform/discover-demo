import React, { useReducer } from "react";
import { Watermark, WatermarkMatches, WatermarkOutputRaw, WatermarkSource, WatermarksIndex, WatermarksIndexRaw, unserializeSingleWatermarkMatches } from "../types";
import { MatchRow } from "./MatchRow";
import { IconBtn } from "../../utils/IconBtn";
import { Magnifier, MagnifyProps, MagnifyingContext } from "./MatchViewer";
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

    const [group_by_source, toggleGroupBySource] = useReducer((group_by_source) => !group_by_source, false);
    const [filter_by_source, setFilterBySource] = React.useState<WatermarkSource | null>(null);
    const [magnifying, setMagnifying] = React.useState<MagnifyProps | null>(null);
    const [page, setPage] = React.useState(1);
    const [highlit, setHighlit] = React.useState<Watermark | null>(null);

    const matches_filtered = filter_by_source ? matches.filter(match => match.query.source === filter_by_source) : matches;
    const PAGINATE_BY = 30;
    const total_pages = Math.ceil(matches_filtered.length/PAGINATE_BY);

    React.useEffect(() => {
        if (highlit && filter_by_source && highlit.source !== filter_by_source)
            setFilterBySource(null);
    }, [highlit]);

    const matchesHref = (watermark: Watermark) => {
        const watermark_index = watermark.id!;
        return `#match-${watermark_index}`;
    }
    const hashchange = () => {
        const loc = window.location.hash;
        if (loc.startsWith("#match-")) {
            const match_id = parseInt(loc.slice(7));
            const nhighlit = index.images[match_id];
            setHighlit(nhighlit);
            setPage(Math.floor(match_id/PAGINATE_BY));
            return;
        }
        setHighlit(null);
        if (loc.startsWith("#page-")) {
            setPage(parseInt(loc.slice(6)));
        }
    };
    React.useEffect(() => {
        window.addEventListener("hashchange", hashchange);
        hashchange();
        return () => window.removeEventListener("hashchange", hashchange);
    }, []);

    const toPage = (page: number) => {
        window.location.hash = `#page-${page}`;
    }
    const find_page = (watermark: Watermark | null) => {
        if (!watermark) return false;
        const actual_index = matches_filtered.findIndex(match => match.query === watermark);
        if (actual_index === -1) return false;
        return Math.floor(actual_index/PAGINATE_BY) + 1;
    }
    const actual_page = find_page(highlit) || Math.min(page, total_pages);

    return (
        <MagnifyingContext.Provider value={{magnify: setMagnifying, matchesHref}}>
            <div className="viewer-options">
                <div className="columns">
                    <div className="field column is-3">
                        <label className="checkbox is-normal">
                            <input type="checkbox" className="checkbox mr-2" name="group-by-source" id="group-by-source" checked={group_by_source} onChange={toggleGroupBySource} />
                            Group by source document
                        </label>
                    </div>
                    <div className="field column is-horizontal is-9">
                        <div className="field-label is-normal">
                            <label className="label">
                                Filter by document:
                            </label>
                        </div>
                        <div className="field-body">
                        <div className="field is-narrow">
                        <div className="control">
                            <div className="select is-fullwidth">
                                <select value={filter_by_source ? filter_by_source.id : ""} onChange={(e) => setFilterBySource((e.target.value && index.sources.find(source => source.id === e.target.value)) || null)}>
                                    <option value="">All</option>
                                    {index.sources.map(source => (
                                        <option key={source.id} value={source.id}>{source.name}</option>
                                    ))}
                                </select>
                            </div>
                            </div>
                            </div>
                        </div>
                    </div>
                </div>
                <Pagination page={actual_page} setPage={toPage} total_pages={total_pages} />
            </div>
            <div className="viewer-table">

            {matches_filtered.slice((actual_page-1)*PAGINATE_BY, (actual_page)*PAGINATE_BY).map((matches, idx) => (
                <MatchRow key={idx} matches={matches} group_by_source={group_by_source} highlit={highlit==matches.query} />
            ))}
            </div>
            <div className="mt-4"></div>
            <Pagination page={actual_page} setPage={toPage} total_pages={total_pages} />
            {magnifying && <Magnifier {...magnifying} />}
        </MagnifyingContext.Provider>
    );
}
