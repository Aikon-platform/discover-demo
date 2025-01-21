import React, { useReducer } from "react";
import { SimilarityMatches, SimilarityIndex } from "../types";
import { NameProvider } from "../../shared/types";
import { ImageInfo, Document } from "../../shared/types";
import { MatchRow } from "./MatchRow";
import { ImageMagnifier, MagnifyProps, MagnifyingContext } from "../../shared/ImageMagnifier";
import { Pagination } from "./Pagination";
import { fetchIIIFNames, getSourceName, NameProviderContext } from "../../shared/naming";
import { SimilarityProps } from "./SimilarityApp";

interface SimilarityHref {
    matchesHref?: (watermark: ImageInfo) => string;
}

export const SimilarityHrefContext = React.createContext<SimilarityHref>({});

export function ImageSimBrowser({ index, matches, extra_toolbar_items }: { index: SimilarityIndex, matches: SimilarityMatches[], extra_toolbar_items?: React.ReactNode }) {
    /*
    Component to render a list of watermark matches.
    */

    const [group_by_source, toggleGroupBySource] = useReducer((group_by_source) => !group_by_source, false);
    const [filter_by_source, setFilterBySource] = React.useState<Document | null>(null);
    const [page, setPage] = React.useState(1);
    const [highlit, setHighlit] = React.useState<ImageInfo | null>(null);
    const minThreshold = Math.min(...matches.map(match => Math.min(...match.matches.map(m => m.similarity))));
    const maxThreshold = Math.max(...matches.map(match => Math.max(...match.matches.map(m => m.similarity))));
    const [threshold, setThreshold] = React.useState(minThreshold + 0.5*(maxThreshold-minThreshold));
    const nameProvider = React.useContext(NameProviderContext);

    const matches_filtered = filter_by_source ? matches.filter(match => match.query.document === filter_by_source) : matches;
    const PAGINATE_BY = 30;
    const total_pages = Math.ceil(matches_filtered.length / PAGINATE_BY);

    const hashchange = () => {
        const loc = window.location.hash;
        if (loc.startsWith("#match-")) {
            const match_id = parseInt(loc.slice(7));
            const nhighlit = index.images[match_id];
            setHighlit(nhighlit);
            setPage(Math.floor(match_id / PAGINATE_BY));
            return;
        }
        setHighlit(null);
        if (loc.startsWith("#page-")) {
            setPage(parseInt(loc.slice(6)));
        }
    };

    const matchesHref = (watermark: ImageInfo) => {
        const watermark_index = watermark.num!;
        return `#match-${watermark_index}`;
    }

    const toPage = (page: number) => {
        window.location.hash = `#page-${page}`;
    }

    const find_page = (watermark: ImageInfo | null) => {
        if (!watermark) return false;
        const actual_index = matches_filtered.findIndex(match => match.query === watermark);
        if (actual_index === -1) return false;
        return Math.floor(actual_index / PAGINATE_BY) + 1;
    }
    const actual_page = find_page(highlit) || Math.min(page, total_pages);


    React.useEffect(() => {
        if (highlit && filter_by_source && highlit.document !== filter_by_source)
            setFilterBySource(null);
    }, [highlit]);

    React.useEffect(() => {
        window.addEventListener("hashchange", hashchange);
        hashchange();
        return () => window.removeEventListener("hashchange", hashchange);
    }, []);

    return (
        <SimilarityHrefContext.Provider value={{matchesHref}}>
            <div className="toolbar">
                <div className="toolbar-content">
                    {extra_toolbar_items}
                    <div className="toolbar-item">
                        <label className="label is-expanded">
                            Similarity threshold:
                        </label>
                        <div className="field">
                            <input type="range" min={minThreshold} max={maxThreshold} step={0.01} value={threshold} onChange={(e) => setThreshold(parseFloat(e.target.value))} />
                            <span className="m-3">{threshold.toPrecision(4)}</span>
                        </div>
                    </div>
                    {index.sources.length > 1 &&
                    <React.Fragment>
                    <div className="toolbar-item">
                        <label className="checkbox is-normal">
                            <input type="checkbox" className="checkbox mr-2" name="group-by-source" id="group-by-source" checked={group_by_source} onChange={toggleGroupBySource} />
                            Group by source document
                        </label>
                    </div>
                    <div className="toolbar-item">
                        <label className="label">
                            Filter by document:
                        </label>
                        <div className="field is-narrow">
                            <div className="select is-fullwidth">
                                <select value={filter_by_source ? filter_by_source.uid : ""} onChange={(e) => setFilterBySource((e.target.value && index.sources.find(source => source.uid === e.target.value)) || null)}>
                                    <option value="">All</option>
                                    {index.sources.map(source => (
                                        <option key={source.uid} value={source.uid}>{getSourceName(nameProvider, source)}</option>
                                    ))}
                                </select>
                        </div>
                        </div>
                    </div>
                    </React.Fragment>}
                </div>
                <Pagination page={actual_page} setPage={toPage} total_pages={total_pages} />
            </div>
            <div className="viewer-table">

                {matches_filtered.slice((actual_page - 1) * PAGINATE_BY, (actual_page) * PAGINATE_BY).map((matches, idx) => (
                    <MatchRow key={idx} matches={matches} group_by_source={group_by_source} highlit={highlit == matches.query} threshold={threshold} />
                ))}
            </div>
            <div className="mt-4"></div>
            <Pagination page={actual_page} setPage={toPage} total_pages={total_pages} />
        </SimilarityHrefContext.Provider>
    );
}
