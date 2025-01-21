import React from "react";
import { SimilarityIndex, SimilarityMatches } from "../types";
import { NameProvider } from "../../shared/types";
import { fetchIIIFNames, NameProviderContext } from "../../shared/naming";
import { ImageMagnifier, MagnifyingContext, MagnifyProps } from "../../shared/ImageMagnifier";
import { Cluster, connectedComponents, convertToClusteringFile, graphFromSimilarityMatches } from "../utils/clustering";
import { ImageDisplay, ImageToDisplay } from "../../shared/ImageDisplay";
import { IconBtn } from "../../shared/IconBtn";
import { ClusterApp } from "../../ClusterApp";
import { ClusterElement } from "../../ClusterApp/components/ClusterElement";
import { BasicImageList } from "../../ClusterApp/components/ImageLists";

interface Pinned {
    pinnedImage?: ImageToDisplay;
    setPinned?: (pinned: boolean) => void;
}

export function ClusteringTool({ matches, index, visible, extra_toolbar_items}: { matches: SimilarityMatches[], index: SimilarityIndex, visible: boolean, extra_toolbar_items?: React.ReactNode }) {

    const minThreshold = Math.min(...matches.map(match => Math.min(...match.matches.map(m => m.similarity))));
    const maxThreshold = Math.max(...matches.map(match => Math.max(...match.matches.map(m => m.similarity))));
    const [threshold, setThreshold] = React.useState(minThreshold + 0.8*(maxThreshold-minThreshold));
    const graph = graphFromSimilarityMatches(index, matches);
    const [clusters, setClusters] = React.useState(connectedComponents(graph, threshold, index.images.length));
    const [isFinal, setFinal] = React.useState(false);
    const [pinnedImage, setPinnedImage] = React.useState<Pinned>({});
    const magnifyingContext = React.useContext(MagnifyingContext);

    React.useEffect(() => {
        setClusters(connectedComponents(graph, threshold, index.images.length));
    }, [threshold]);

    if (!visible) {
        return null;
    }


    const setMagnifying = (props: MagnifyProps) => {
        magnifyingContext.magnify &&
        magnifyingContext.magnify({
            ...props,
            comparison: pinnedImage.pinnedImage || props.comparison,
        });
    };

    const setComparison = (image?: ImageToDisplay, setPinned?: (pinned: boolean) => void) => {
        try {
            pinnedImage.setPinned && pinnedImage.setPinned(false);
        } catch (e) {
        }
        setPinned && setPinned(true);
        setPinnedImage({pinnedImage: image, setPinned: setPinned});
    }

    return (
    <MagnifyingContext.Provider value={{ ...magnifyingContext, magnify: setMagnifying, setComparison: setComparison }}>
            <div className="toolbar">
                <div className="toolbar-content">
                    {extra_toolbar_items}
                    {!isFinal &&
                    <div className="toolbar-item">
                        <label className="label is-expanded">
                            Clustering threshold:
                        </label>
                        <div className="field">
                            <div className="control">
                            <input type="range" min={minThreshold} max={maxThreshold} step={0.001} value={threshold} onChange={(e) => setThreshold(parseFloat(e.target.value))} />
                            </div>
                            <div className="control">
                                <input type="number" className="input" value={threshold} onChange={(e) => setThreshold(parseFloat(e.target.value))} />
                            </div>
                        </div>
                    </div>}
                    <div className="toolbar-item toolbar-btn">
                        {isFinal ?
                        <IconBtn icon="mdi:autorenew" onClick={() => setFinal(false)} label="Redo automatic clustering" /> :
                        <IconBtn className="is-link" icon="mdi:check-bold" onClick={() => setFinal(true)} label="Apply clustering" />}
                    </div>
                </div>
            </div>
            <div className="viewer-table cluster-viewer">
                {isFinal ?
                <ClusterApp clustering_data={convertToClusteringFile(index, matches, clusters)} editable={true} viewer_sort="id"/> :
                <div className={"cl-cluster-list cl-display-grid"}>
                {clusters.map((cluster, idx) => (
                    <ClusterMiniElement key={idx} cluster={cluster} index={index}/>
                ))}
                <div className="cl-cluster box cl-filler"></div>
                <div className="cl-cluster box cl-filler"></div>
                <div className="cl-cluster box cl-filler"></div>
                <div className="cl-cluster box cl-filler"></div>
                <div className="cl-cluster box cl-filler"></div>
                </div>}
            </div>
            <div className="mt-4"></div>
        </MagnifyingContext.Provider>
    );
}

function ClusterMiniElement ({cluster, index}: {cluster: Cluster, index: SimilarityIndex}) {
    const n_shown = 11;
    const [expanded, setExpanded] = React.useState(false);
    const btnMore = (cluster.members.length > n_shown &&
        <a className="cl-more cl-placeholder card" href="javascript:void(0)" onClick={() => {setExpanded(!expanded);}}>
        {expanded ? "–" : "+"}{cluster.members.length - n_shown}
        </a>
    );
    const images = cluster.members.map((i) => index.images[i]);

    return (
    <div className="cl-cluster box">
    <div className="cl-anchor"></div>
    <div className="cl-props">
      <div className="cl-propcontent">
        <div className="cl-propinfo">
          <p className="cl-cluster-title">
          <span>{cluster.id >= 0 ? `Cluster ${cluster.id}` : "Unclustered"} ({images.length})</span>
          </p>
        </div>
      </div>
    </div>
    <div className="cl-samples">
        <div className="cl-images cl-limitheight">
        {images.slice(0, expanded ? undefined : n_shown).map((image, i) => (
             <div className="cl-image card" key={i}>
                <ImageDisplay image={image} />
            </div>
        ))}
        {images.length === 0 && <p>∅</p>}
        {btnMore}
        </div>
    </div>
  </div>);
}
