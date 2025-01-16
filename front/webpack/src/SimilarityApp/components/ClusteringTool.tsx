import React from "react";
import { NameProvider, SimilarityIndex, SimilarityMatches } from "../types";
import { fetchIIIFNames, NameProviderContext } from "../utils/naming";
import { ImageMagnifier, MagnifyingContext, MagnifyProps } from "../../shared/ImageMagnifier";
import { Cluster, connectedComponents, convertToClusteringFile, graphFromSimilarityMatches } from "../utils/clustering";
import { ImageDisplay } from "../../shared/ImageDisplay";
import { IconBtn } from "../../shared/IconBtn";
import { ClusterApp } from "../../ClusterApp";
import { ClusterElement } from "../../ClusterApp/components/ClusterElement";
import { BasicImageList } from "../../ClusterApp/components/ImageLists";


export function ClusteringTool({ matches, index, visible, additional_toolbar}: { matches: SimilarityMatches[], index: SimilarityIndex, visible: boolean, additional_toolbar?: React.ReactNode }) {

    const [threshold, setThreshold] = React.useState(80);
    const graph = graphFromSimilarityMatches(index, matches);
    const [clusters, setClusters] = React.useState(connectedComponents(graph, threshold/100, index.images.length));
    const [isFinal, setFinal] = React.useState(false);


    React.useEffect(() => {
        setClusters(connectedComponents(graph, threshold/100, index.images.length));
    }, [threshold]);

    if (!visible) {
        return null;
    }

    return (
        <React.Fragment>
            <div className="viewer-options">
                <div className="columns">
                    {additional_toolbar}
                    {!isFinal &&
                    <div className="field column is-horizontal">
                        <div className="field-label is-normal">
                            <label className="label is-expanded">
                                Threshold:
                            </label>
                        </div>
                        <div className="field-body">
                            <div className="field">
                                <div className="control">
                                    <input type="range" min="30" max="100" value={threshold} onChange={(e) => setThreshold(parseInt(e.target.value))} />
                                    <span className="m-3">{threshold}%</span>
                                </div>
                            </div>
                        </div>
                    </div>}
                    <div className="field column is-horizontal">
                        {isFinal ?
                        <IconBtn icon="mdi:autorenew" onClick={() => setFinal(false)} label="Redo automatic clustering" /> :
                        <IconBtn icon="mdi:content-save" onClick={() => setFinal(true)} label="Apply clustering" />}
                    </div>
                </div>
            </div>
            <div className="viewer-table cluster-viewer">
                {isFinal ?
                <ClusterApp clustering_data={convertToClusteringFile(index, matches, clusters)} editable={true}/> :
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
        </React.Fragment>
    );
}

function ClusterMiniElement ({cluster, index}: {cluster: Cluster, index: SimilarityIndex}) {
    const n_shown = 20;
    const [expanded, setExpanded] = React.useState(false);
    const btnMore = (cluster.members.length > n_shown &&
        <a className="cl-more card" href="javascript:void(0)" onClick={() => {setExpanded(!expanded);}}>
        {expanded ? "–" : "+"}{cluster.members.length - n_shown}
        </a>
    );
    const images = cluster.members.map((i) => index.images[i]);

    return (
    <div className={"cl-cluster box"}>
    <div className="cl-anchor"></div>
    <div className="cl-props">
      <div className="cl-propcontent">
        <div className="cl-propinfo">
          <p className="cl-cluster-title">
          <span>{cluster.id >= 0 ? `Cluster ${cluster.id}` : "Unclustered"}</span>
          </p>
        </div>
      </div>
    </div>
    <div className="cl-samples">
        <div className="cl-images">
        {images.slice(0, n_shown).map((image, i) => (
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
