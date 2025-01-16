import React, { useReducer } from "react";
import { ClusterElement } from "./ClusterElement";
import { ClusterImageInfo, serializeClusterFile, ClusterAppProps, ClusterInfo } from "../types";
import { ClusterEditorContext, editorReducer } from "../actions";
import { ClusterAskModale } from "./ClusterAskModale";
import { IconBtn } from "../../shared/IconBtn";
import { ClusterCSVExporter } from "./ClusterExporter";

/*
  This file contains the main React component for the ClusterEditor app.
*/

export function ClusterApp({ clustering_data, viewer_sort="size", editing = false, editable = false, formfield, base_url }: ClusterAppProps) {
  const [editorState, dispatchEditor] = useReducer(
    editorReducer, {
    editing: editable && editing,
    editingCluster: null,
    askingCluster: null,
    content: clustering_data,
    base_url: base_url,
    image_selection: new Set<ClusterImageInfo>(),
    viewer_sort: viewer_sort,
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
    dispatchEditor({ type: "viewer_end_edit" });
  };

  // sort clusters
  const cluster_sorting = {
    "size": (a: ClusterInfo, b: ClusterInfo) => b.images.length - a.images.length,
    "id": (a: ClusterInfo, b: ClusterInfo) => a.id - b.id,
    "name": (a: ClusterInfo, b: ClusterInfo) => a.name.localeCompare(b.name)
  }[editorState.viewer_sort];
  const clusters = Array.from(editorState.content.clusters.values()).sort(cluster_sorting);


  return (
    <ClusterEditorContext.Provider value={{ state: editorState, dispatch: dispatchEditor }}>
      <div className={editorState.editing ? "cl-editor" : ""}>
        <div className="toolbar cl-editor-toolbar">
          <div className="toolbar-content">
            <h2>Cluster {editorState.editing ? "Editor" : "Viewer"}</h2>
            <div className="toolbar-item">
              <label className="label">Sort by:</label>
              <div className="field is-narrow">
                <div className="select">
                  <select value={editorState.viewer_sort} onChange={(e) => { dispatchEditor({ type: "viewer_sort", sort: e.target.value }); } }>
                    <option value="size">Size</option>
                    <option value="id">ID</option>
                    <option value="name">Name</option>
                  </select>
                </div>
              </div>
            </div>
            <div className="toolbar-item">
              <label className="label">Display:</label>
              <div className="field is-narrow">
                <div className="select">
                  <select value={editorState.viewer_display} onChange={(e) => { dispatchEditor({ type: "viewer_display", display: e.target.value }); } }>
                    <option value="grid">Grid</option>
                    <option value="rows">Rows</option>
                  </select>
                </div>
              </div>
            </div>
            {editable &&
              <div className="toolbar-content cl-editor-tools">
                {editorState.editingCluster !== null &&
                  <div className="toolbar-item cl-select-tools">
                    <label className="label">Selection ({editorState.image_selection.size}):</label>
                    <div className="field">
                    {editorState.image_selection.size == 0 ?
                      <IconBtn onClick={() => { dispatchEditor({ type: "selection_all" });}} icon="mdi:select-all" label="All" /> :
                      <React.Fragment>
                        <IconBtn onClick={() => { dispatchEditor({ type: "selection_clear" });}} icon="mdi:close" label="Clear" />
                        <IconBtn onClick={() => { dispatchEditor({ type: "selection_invert" });}} icon="mdi:select-inverse" label="Invert" />
                      </React.Fragment>}
                    </div>
                  </div>}
                {editorState.editingCluster !== null && editorState.image_selection.size > 0 &&
                  <div className="toolbar-item toolbar-btn">
                    <label className="label">Actions on selection:</label>
                    <IconBtn onClick={() => { dispatchEditor({ type: "cluster_ask", for_action: "selection_move", cluster_id: editorState.editingCluster! }); } } icon="mdi:folder-move" label="Move to cluster..." />
                  </div>}
                <div className="toolbar-item toolbar-btn">
                {editorState.editing ?
                  <IconBtn onClick={save} icon="mdi:content-save" className="big is-link" label={formfield ? "Save" : "Apply"} /> :
                  <IconBtn onClick={() => { dispatchEditor({ type: "viewer_edit" }); } } className="big is-link" icon="mdi:edit" label="Edit" />}
                </div>
                <div className="toolbar-item toolbar-btn">
                  <ClusterCSVExporter clusters={clusters} />
                </div>
              </div>}
          </div>
        </div>
        <div className={"cl-cluster-list cl-display-" + editorState.viewer_display}>
          {clusters.map((cluster) => (
            <ClusterElement key={cluster.id} editing={editorState.editingCluster == cluster.id} info={cluster} />
          ))}
          <div className="cl-cluster box cl-filler"></div>
          <div className="cl-cluster box cl-filler"></div>
          <div className="cl-cluster box cl-filler"></div>
          <div className="cl-cluster box cl-filler"></div>
          <div className="cl-cluster box cl-filler"></div>
        </div>
        {editorState.askingCluster !== null &&
          <ClusterAskModale {...editorState.askingCluster!} />}
      </div>
    </ClusterEditorContext.Provider>
  );
}
