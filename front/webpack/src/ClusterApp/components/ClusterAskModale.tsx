import React, { useState } from "react";
import { MiniClusterElement } from "./ClusterElement";
import { ClusterInfo } from "../types";
import { ClusterEditorContext } from "../context";
import { Icon } from "@iconify/react";
import { IconBtn } from "../../utils/IconBtn";

export function ClusterAskModale(props: { for_action: "cluster_merge" | "selection_move"; not_cluster_id: number; }) {
    const editorContext = React.useContext(ClusterEditorContext);
    const cluster = editorContext!.state.content.clusters.get(props.not_cluster_id)!;
    const [selected, setSelected] = useState<ClusterInfo | null>(null);

    const doAction = () => {
        editorContext!.dispatch({
            type: props.for_action,
            cluster_id: selected!.id,
            other: props.not_cluster_id
        });
        editorContext!.dispatch({ type: "cluster_ask", cluster_id: null });
    };
    const [action_icon, action_label] = {
        "cluster_merge": ["mdi:merge", "Merge into this cluster"],
        "selection_move": ["mdi:folder-move", "Move images to this cluster"]
    }[props.for_action];

    // sort clusters by size
    const additional_cluster = { id: -1, name: "New cluster", images: [] };
    const clusters = [
        ...editorContext!.state.content.clusters.values(),
        ...(props.for_action == "selection_move" ? [additional_cluster] : [])
    ].sort((a, b) => b.images.length - a.images.length);

    return (
        <div className="cl-modale">
            <div className="cl-modale-wrapper">
                <div className="cl-modale-content">
                    <h2>Choose target cluster</h2>
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
                        <IconBtn onClick={() => { editorContext!.dispatch({ type: "cluster_ask", cluster_id: null }); }} icon="mdi:close" label="Cancel" />
                        <IconBtn onClick={doAction} icon={action_icon} label={action_label}  disabled={selected === null} />
                    </div>
                </div>
            </div>
        </div>
    );
}
