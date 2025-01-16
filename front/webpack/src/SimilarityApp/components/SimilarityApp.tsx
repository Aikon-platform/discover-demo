import React from "react";
import { NameProvider, SimilarityIndex, SimilarityMatches, SimImage } from "../types";
import { ImageMagnifier, MagnifyingContext, MagnifyProps } from "../../shared/ImageMagnifier";
import { fetchIIIFNames, getImageName, getSourceName, NameProviderContext } from "../utils/naming";
import { IconBtn } from "../../shared/IconBtn";
import { ImageSimBrowser } from "./ImageSimBrowser";
import { ClusteringTool } from "./ClusteringTool";
import { ImageTooltip, TooltipContext, TooltipProps } from "../../shared/ImageTooltip";

export interface SimilarityProps {
    index: SimilarityIndex;
    matches: SimilarityMatches[];
}

export type SimilarityMode = "cluster" | "browse";

export function SimilarityApp(props: SimilarityProps) {

    const [nameProvider, setContext] = React.useState<NameProvider>({});
    const [magnifying, setMagnifying] = React.useState<MagnifyProps | null>(null);
    const [mode, setMode] = React.useState<SimilarityMode>("cluster");
    const [tooltip, setTooltip] = React.useState<TooltipProps | undefined>(undefined);

    React.useEffect(() => {
        fetchIIIFNames(props.index.sources, (ncontext: NameProvider) => setContext({ ...nameProvider, ...ncontext }));
    }, []);

    const getTitle = (image: SimImage) => {
        return getSourceName(nameProvider, image.document) || image.document?.name || image.id;
    }

    const getSubtitle = (image: SimImage) => {
        return getImageName(nameProvider, image);
    }

    const addtitional_toolbar = (
        <div className="field column is-horizontal">
            {mode != "browse" && <IconBtn icon="mdi:folder" onClick={() => setMode("browse")} label="Switch to Browse Mode" />}
            {mode != "cluster" && <IconBtn icon="mdi:graph" onClick={() => setMode("cluster")} label="Cluster the results" />}
        </div>
    )

    return (
    <NameProviderContext.Provider value={nameProvider}>
        <TooltipContext.Provider value={{ getTitle, getSubtitle, setTooltip }}>
            <MagnifyingContext.Provider value={{ magnify: setMagnifying, getTitle, getSubtitle }}>
                {mode === "browse" && <ImageSimBrowser index={props.index} matches={props.matches} addtitional_toolbar={addtitional_toolbar} />}
                <ClusteringTool index={props.index} matches={props.matches} visible={mode == "cluster"} additional_toolbar={addtitional_toolbar} />
                {magnifying && <ImageMagnifier {...magnifying} />}
                {tooltip && <ImageTooltip {...tooltip} />}
            </MagnifyingContext.Provider>
        </TooltipContext.Provider>
    </NameProviderContext.Provider>)
}
