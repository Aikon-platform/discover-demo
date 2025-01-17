import React, { useState } from "react";
import { MiniClusterElement } from "./ClusterElement";
import { ClusterInfo } from "../types";
import { ClusterEditorContext } from "../actions";
import { IconBtn } from "../../shared/IconBtn";
import { MagnifyingContext } from "../../shared/ImageMagnifier";

/*
  This file contains the React component that displays a modale to ask the user
  to choose a target cluster for some action.
*/

export function ClusterAskModale(props: { for_action: "cluster_merge" | "selection_move"; not_cluster_id: number; }) {
    const editorContext = React.useContext(ClusterEditorContext);
    const cluster = editorContext!.state.content.clusters.get(props.not_cluster_id)!;
    const selection = editorContext!.state.image_selection;
    const [selected, setSelected] = useState<ClusterInfo | null>(null);
    const magnifyingContext = React.useContext(MagnifyingContext);

    const doAction = () => {
        editorContext!.dispatch({
            type: props.for_action,
            cluster_id: selected!.id,
            other: props.not_cluster_id
        });
        editorContext!.dispatch({ type: "cluster_ask", cluster_id: null });
    };
    let action_icon: string, action_title: string, action_label: string, action_cluster: ClusterInfo;
    if (props.for_action == "cluster_merge") {
        action_icon = "mdi:merge";
        action_label = "Merge whole clusters";
        action_title = "Select target cluster to merge with:";
        action_cluster = { ...cluster, name: "Selected cluster: "+cluster.name };
    } else {
        action_icon = "mdi:folder-move";
        action_title = "Select target cluster to move images:";
        action_label = "Move selected images to...";
        action_cluster = { id: -1, name: "Selected images", images: Array.from(selection) };
    }

    // sort clusters and add one last new cluster
    const additional_cluster = { id: -1, name: "New cluster", images: [] };
    const cluster_sorting = {
        "size": (a: ClusterInfo, b: ClusterInfo) => b.images.length - a.images.length,
        "id": (a: ClusterInfo, b: ClusterInfo) => a.id - b.id,
        "name": (a: ClusterInfo, b: ClusterInfo) => a.name.localeCompare(b.name)
    }[editorContext!.state.viewer_sort];
    const clusters = [
        ...Array.from(editorContext!.state.content.clusters.values()).sort(cluster_sorting),
        ...(props.for_action == "selection_move" ? [additional_cluster] : [])
    ];

    return (
        <MagnifyingContext.Provider value={{ ...magnifyingContext, magnify: undefined, setComparison: undefined }}>
        <div className="cl-modale" onClick={() => editorContext!.dispatch({ type: "cluster_ask", cluster_id: null })}>
            <div className="cl-modale-wrapper">
                <div className="cl-modale-content" onClick={(e) => e.stopPropagation()}>
                    <div className="cl-modale-header">
                        <h2 className="cl-modale-title">{action_title}</h2>
                        <div className="cl-ask-cluster">
                            <MiniClusterElement info={action_cluster} selected={true} limit={10} />
                        </div>
                    </div>
                    <div className="cl-ask-select">
                        <div className="cl-ask-list">
                            {clusters.map((cluster) => (cluster.id != props.not_cluster_id &&
                                <div key={cluster.id} className="cl-ask-cluster">
                                    <MiniClusterElement info={cluster} selected={selected?.id == cluster.id} onClick={() => setSelected(cluster)} />
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="cl-modale-actions">
                        <p>
                            <IconBtn onClick={() => { editorContext!.dispatch({ type: "cluster_ask", cluster_id: null }); }} icon="mdi:close" label="Cancel" className="is-outline" />
                            <IconBtn onClick={doAction} icon={action_icon} label={action_label}  disabled={selected === null} />
                        </p>
                    </div>
                </div>
            </div>
        </div>
        </MagnifyingContext.Provider>
    );
}
