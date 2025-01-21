import React from "react";
import { SimilarityIndex, SimilarityMatches } from "../types";
import { NameProvider } from "../../shared/types";
import { ImageInfo } from "../../shared/types";
import { ImageMagnifier, MagnifyingContext, MagnifyProps } from "../../shared/ImageMagnifier";
import { fetchIIIFNames, getImageName, getSourceName, NameProviderContext } from "../../shared/naming";
import { IconBtn } from "../../shared/IconBtn";
import { ImageSimBrowser } from "./ImageSimBrowser";
import { ClusteringTool } from "./ClusteringTool";
import { ImageTooltip, TooltipContext, TooltipProps } from "../../shared/ImageTooltip";

export interface SimilarityProps {
    index: SimilarityIndex;
    matches: SimilarityMatches[];
    mode?: SimilarityMode;
}

export type SimilarityMode = "cluster" | "browse";

export function SimilarityApp(props: SimilarityProps) {

    const [nameProvider, setContext] = React.useState<NameProvider>({});
    const [magnifying, setMagnifying] = React.useState<MagnifyProps | null>(null);
    const [mode, setMode] = React.useState<SimilarityMode>(props.mode || "cluster");
    const [tooltip, setTooltip] = React.useState<TooltipProps | undefined>(undefined);

    React.useEffect(() => {
        fetchIIIFNames(props.index.sources, (ncontext: NameProvider) => setContext({ ...nameProvider, ...ncontext }));
    }, []);

    const addtitional_toolbar = (
        <div className="toolbar-item toolbar-btn">
            {mode != "browse" && <IconBtn icon="mdi:folder" onClick={() => setMode("browse")} label="Switch to Browse Mode" />}
            {mode != "cluster" && <IconBtn icon="mdi:graph" onClick={() => setMode("cluster")} label="Cluster the results" />}
        </div>
    )

    return (
    <NameProviderContext.Provider value={nameProvider}>
        <TooltipContext.Provider value={{ setTooltip }}>
            <MagnifyingContext.Provider value={{ magnify: setMagnifying }}>
                {mode === "browse" && <ImageSimBrowser index={props.index} matches={props.matches} extra_toolbar_items={addtitional_toolbar} />}
                <ClusteringTool index={props.index} matches={props.matches} visible={mode == "cluster"} extra_toolbar_items={addtitional_toolbar} />
                {magnifying && <ImageMagnifier {...magnifying} />}
                {tooltip && <ImageTooltip {...tooltip} />}
            </MagnifyingContext.Provider>
        </TooltipContext.Provider>
    </NameProviderContext.Provider>)
}
