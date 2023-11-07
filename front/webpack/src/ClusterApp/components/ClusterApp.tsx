import { Icon } from "@iconify/react";
import React, { useReducer } from "react";
import { ClusterElement } from "./ClusterElement";
import { unserializeClusterFile, ImageInfo, serializeClusterFile, AppProps, ClusterInfo } from "../types";
import { ClusterEditorContext, editorReducer } from "../actions";
import { ClusterAskModale } from "./ClusterAskModale";
import { IconBtn } from "../../utils/IconBtn";


export function ClusterApp({ clustering_data, editing = false, editable = false, formfield, base_url }: AppProps) {
  // transform clustering_data.clusters to Map<number, ClusterInfo>
  const [editorState, dispatchEditor] = useReducer(
    editorReducer, {
    editing: editable && editing,
    editingCluster: null,
    askingCluster: null,
    content: unserializeClusterFile(clustering_data),
    base_url: base_url,
    image_selection: new Set<ImageInfo>(),
    viewer_sort: "size",
    viewer_display: "grid",
  });

  const updateFormField = () => {
    if (formfield) {
      formfield.value = JSON.stringify(serializeClusterFile(editorState.content));
    }
  };

  const save = () => {
    if (formfield) {
      updateFormField();
      formfield.form!.submit();
    }
  };

  // sort clusters by size
  const cluster_sorting = {
    "size": (a: ClusterInfo, b: ClusterInfo) => b.images.length - a.images.length,
    "id": (a: ClusterInfo, b: ClusterInfo) => a.id - b.id,
    "name": (a: ClusterInfo, b: ClusterInfo) => a.name.localeCompare(b.name)
  }[editorState.viewer_sort];
  const clusters = Array.from(editorState.content.clusters.values()).sort(cluster_sorting);

  return (
    <ClusterEditorContext.Provider value={{ state: editorState, dispatch: dispatchEditor }}>
      <div className={editorState.editing ? "cl-editor" : ""}>
        <div className="cl-editor-toolbar">
          <h2>Cluster {editorState.editing ? "Editor" : "Viewer"}</h2>
          <div className="cl-options">
            <div className="cl-option-viewer_display">
              <span>Sort by:</span>
              <select value={editorState.viewer_sort} onChange={(e) => { dispatchEditor({ type: "viewer_sort", sort: e.target.value }); } }>
                <option value="size">Size</option>
                <option value="id">ID</option>
                <option value="name">Name</option>
              </select>
            </div>
            <div className="cl-option-viewer_display">
              <span>Display:</span>
              <select value={editorState.viewer_display} onChange={(e) => { dispatchEditor({ type: "viewer_display", display: e.target.value }); } }>
                <option value="grid">Grid</option>
                <option value="rows">Rows</option>
              </select>
            </div>
          </div>
          {editable &&
            <div className="cl-editor-tools">
              {editorState.editingCluster !== null && editorState.image_selection.size > 0 &&
                <React.Fragment>
                  <IconBtn onClick={() => { dispatchEditor({ type: "cluster_ask", for_action: "selection_move", cluster_id: editorState.editingCluster! }); } } icon="mdi:folder-move" label="Move to cluster..." />
                </React.Fragment>}
              {editorState.editingCluster !== null &&
                <div className="cl-select-tools">
                  <span>Selection ({editorState.image_selection.size}):</span>
                  {editorState.image_selection.size == 0 ?
                    <IconBtn onClick={() => { dispatchEditor({ type: "selection_all" });}} icon="mdi:select-all" label="All" /> :
                    <React.Fragment>
                      <IconBtn onClick={() => { dispatchEditor({ type: "selection_clear" });}} icon="mdi:close" label="Clear" />
                      <IconBtn onClick={() => { dispatchEditor({ type: "selection_invert" });}} icon="mdi:select-inverse" label="Invert" />
                    </React.Fragment>}
                </div>}
              {editorState.editing ?
                <IconBtn onClick={save} icon="mdi:content-save" className="big" label="Save" /> :
                <IconBtn onClick={() => { dispatchEditor({ type: "viewer_edit" }); } } className="big" icon="mdi:edit" label="Edit" />}
            </div>}
        </div>
        <div className={"cl-cluster-list cl-display-" + editorState.viewer_display}>
          {clusters.map((cluster) => (
            <ClusterElement key={cluster.id} editing={editorState.editingCluster == cluster.id} info={cluster} />
          ))}
          <div className="cl-cluster cl-filler"></div>
          <div className="cl-cluster cl-filler"></div>
          <div className="cl-cluster cl-filler"></div>
          <div className="cl-cluster cl-filler"></div>
          <div className="cl-cluster cl-filler"></div>
        </div>
        {editorState.askingCluster !== null &&
          <ClusterAskModale {...editorState.askingCluster!} />}
      </div>
    </ClusterEditorContext.Provider>
  );
}
