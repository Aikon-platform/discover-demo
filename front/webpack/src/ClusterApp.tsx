import { useEffect, useReducer, useState } from "react";
import { ClusterElement, ClusterProps, ClusterInfo, ImageInfo, MiniClusterElement } from "./ClusterElement";
import React from "react";

interface ClusteringFile {
  clusters: ClusterInfo[];
  background_urls: string[];
}

interface AppProps {
  // The parameters as passed to initClusterViewer
  clustering_data: ClusteringFile;
  base_url: string;
  editing?: boolean;
  editable?: boolean;
  formfield?: HTMLInputElement;
}

type ActionRequiringAsk = "cluster_merge" | "selection_move";

interface EditorState {
  editing: boolean;
  editingCluster: number | null;
  askingCluster: {not_cluster_id: number, for_action: ActionRequiringAsk} | null;
  content: ClusteringFile;
  base_url: string;
  image_selection: Set<ImageInfo>;
}

type EditorAction =
 { type: "cluster_rename", cluster_id: number, name: string } |
 { type: "cluster_merge", cluster_id: number, other: number } |
 { type: "cluster_delete", cluster_id: number } |
 { type: "cluster_ask", cluster_id: number | null, for_action?: ActionRequiringAsk } |
 { type: "edit" } |
 { type: "edit_cluster", cluster_id: number | null } |
 { type: "selection_change", images: ImageInfo[], selected:boolean } |
 { type: "selection_invert" } |
 { type: "selection_clear" } |
 { type: "selection_move", cluster_id: number | null, other?: number } |
 { type: "selection_all" };

interface EditorContext {
  state: EditorState;
  dispatch: React.Dispatch<EditorAction>;
}

export const ClusterEditorContext = React.createContext<EditorContext | undefined>(undefined);

const editorReducer = (state: EditorState, action: EditorAction) => {
  console.log("editorReducer", state, action);

  // Basic actions
  if (action.type == "edit")
    return {...state, editing: true};

  if (action.type == "edit_cluster") {
    if (state.editingCluster == action.cluster_id)
      return state;
    return {...state, editingCluster: action.cluster_id, image_selection: new Set<ImageInfo>()};
  }
  
  const action_prefix = action.type.split("_")[0];
  if (!state.editing) return state;
  
  switch (action_prefix) {
    case "cluster":
      switch (action.type) {
        case "cluster_rename":
          return {
            ...state,
            content: {
              ...state.content,
              clusters: state.content.clusters.map((cluster) => {
                if (cluster.id == action.cluster_id) {
                  return {...cluster, name: action.name!};
                }
                return cluster;
              })
            }
          };
        case "cluster_merge":
          // move images from cluster2 to cluster1
          return state;
        case "cluster_delete":
          // move cluster's images to garbage cluster
          return state;
        case "cluster_ask":
          if (action.cluster_id === null) {
            return {...state, askingCluster: null};
          }
          return {...state, askingCluster: {not_cluster_id: action.cluster_id, for_action: action.for_action!}};
      }
      break;

    case "selection":
      const selection = new Set<ImageInfo>(state.image_selection);
      if (state.editingCluster === null) {
        return state;
      }
      switch (action.type) {
        case "selection_change":
          for (const image of action.images) {
            if (action.selected) {
              selection.add(image);
            } else {
              selection.delete(image);
            }
          }
          console.log("selection_change", selection);
          return {...state, image_selection: selection};

        case "selection_invert":
          const inverted = new Set<ImageInfo>(state.content.clusters.find((cluster) => cluster.id == state.editingCluster)!.images);
          selection.forEach(item => inverted.delete(item));
          return {...state, image_selection: inverted};

        case "selection_clear":
          return {...state, image_selection: new Set<ImageInfo>()};

        case "selection_move":
          if (action.cluster_id === null) {
            return {...state, askingCluster: null};
          }
          // remove image obsolete metadata inside selection
          const new_images = Array.from(selection).map((image) => {return {path: image.path, raw_url: image.raw_url, id: image.id, distance: image.id+1000}});
          // remove images from current cluster
          const orig_cluster = state.content.clusters.find((cluster) => cluster.id == state.editingCluster)!;
          const new_orig_cluster = {...orig_cluster, images: orig_cluster.images.filter((image) => !selection.has(image))};
          let new_cluster: ClusterInfo;

          if (action.cluster_id == -1) {
            const new_id = state.content.clusters.reduce((max, cluster) => Math.max(max, cluster.id), 0) + 1;
            new_cluster = {
              id: new_id,
              name: "Cluster " + new_id,
              images: new_images
            };
          } else {
            new_cluster = state.content.clusters.find((cluster) => cluster.id == action.cluster_id)!;
            new_cluster.images.push(...new_images);
          }

          const new_clusters = state.content.clusters.filter((cluster) => cluster.id != state.editingCluster && cluster.id != action.cluster_id);
          console.log("selection_move", new_orig_cluster, new_cluster, new_clusters);
          new_clusters.push(new_orig_cluster);
          new_clusters.push(new_cluster);
          
          return {
            ...state, 
            content: {...state.content, clusters: new_clusters}, 
            editingCluster: null, 
            image_selection: new Set<ImageInfo>(), 
            askingCluster: null
          };
      }
      break;
  }
  throw new Error("Invalid action type");
}

function ClusterAskModale(props: {for_action: "cluster_merge" | "selection_move", not_cluster_id: number}) {
  const editorContext = React.useContext(ClusterEditorContext);
  const cluster = editorContext!.state.content.clusters.find((cluster) => cluster.id == props.not_cluster_id)!;
  const [selected, setSelected] = useState<ClusterInfo | null>(null);

  const doAction = () => {
    editorContext!.dispatch({
      type: props.for_action,
      cluster_id: selected!.id,
      other: props.not_cluster_id
    });
    editorContext!.dispatch({type: "cluster_ask", cluster_id: null});
  };
  const action_name = {
    "cluster_merge": "Merge",
    "selection_move": "Move"
  }[props.for_action];

  // sort clusters by size
  const additional_cluster = {id: -1, name: "New cluster", images: []};
  const clusters = [
    ...editorContext!.state.content.clusters.sort((a, b) => b.images.length - a.images.length),
    additional_cluster
  ];

  return (
    <div className="cl-modale">
      <div className="cl-modale-wrapper">
      <div className="cl-modale-content">
      <h2>Choose target cluster</h2>
      <div className="cl-ask-select">
        <div className="cl-ask-list">
          {clusters.map((cluster) => (cluster.id != props.not_cluster_id &&
            <div key={cluster.id} className="cl-ask-cluster">
              <MiniClusterElement info={cluster} selected={selected?.id == cluster.id} onClick={() => setSelected(cluster)}/>
            </div>
          ))}
        </div>
        <div className="cl-ask-buttons">
          <button onClick={() => {editorContext!.dispatch({type: "cluster_ask", cluster_id: null})}}>Cancel</button>
          <button onClick={doAction} disabled={selected === null}>{action_name}</button>
        </div>
      </div>
      </div>
      </div>
    </div>
  );
}

export default function ClusterApp({ clustering_data, editing=false, editable=false, formfield, base_url }: AppProps) {
  const [editorState, dispatchEditor] = useReducer(
    editorReducer, {
      editing: editable && editing, 
      editingCluster: null, 
      askingCluster: null,
      content: clustering_data, 
      base_url: base_url, 
      image_selection: new Set<ImageInfo>()});

  const updateFormField = () => {
    if (formfield) {
      formfield.value = JSON.stringify(editorState.content);
    }
  }

  const save = () => {
    if (formfield) {
      updateFormField();
      formfield.form!.submit();
    }
  }

  // sort clusters by size
  const clusters = editorState.content.clusters.sort((a, b) => b.images.length - a.images.length);

  return (
    <ClusterEditorContext.Provider value={{state: editorState, dispatch: dispatchEditor}}>
    <div className={editorState.editing ? "cl-editor" : ""}>
      <div className="cl-editor-toolbar">
        <h1>Cluster {editorState.editing ? "Editor" : "Viewer"}</h1>
        {editable && 
          <div className="cl-editor-tools">
            {editorState.editingCluster !== null && editorState.image_selection.size > 0 &&
            <React.Fragment>
              <button onClick={() => {dispatchEditor({type: "cluster_ask", for_action: "selection_move", cluster_id: editorState.editingCluster! })}}>Move to cluster...</button>
              <button onClick={() => {dispatchEditor({type: "selection_clear"})}}>Clear selection</button>
            </React.Fragment>
            }
            {editorState.editingCluster !== null && 
            <React.Fragment>
              <button onClick={() => {dispatchEditor({type: "selection_invert"})}}>Invert selection</button>
            </React.Fragment>
            }
            {editorState.editing ? 
            <button onClick={save}>Save changes</button> : 
            <button onClick={() => {dispatchEditor({type: "edit"})}}>Edit</button>}
          </div>
      }
      </div>        
      <div className="cl-cluster-list">
      {clusters.map((cluster) => (
        <ClusterElement key={cluster.id} editing={editorState.editingCluster == cluster.id} info={cluster} />
      ))}
      </div>
      {editorState.askingCluster !== null &&
        <ClusterAskModale {...editorState.askingCluster!} />}
    </div>
    </ClusterEditorContext.Provider>
  );
}
