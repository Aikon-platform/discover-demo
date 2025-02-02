import { EditorContext, EditorState, EditorAction, ClusterImageInfo, ClusterInfo } from "./types";
import React from "react";

/*
  This file contains the reducer for the ClusterEditor app.
  It is the main function that updates the state of the app.
*/

export const ClusterEditorContext = React.createContext<EditorContext | undefined>(undefined);

function eraseImagesMetadata(images: ClusterImageInfo[]): ClusterImageInfo[] {
  return images.map((image) => {
    const { tsf_url, ...rest } = image;
    return { ...rest, distance: image.num + 10 };
  });
}

export const editorReducer = (state: EditorState, action: EditorAction) : EditorState => {
  const action_prefix = action.type.split("_")[0];
  if (!state.editing && action_prefix != "viewer") return state;

  switch (action_prefix) {
    // VIEWER ACTIONS
    case "viewer":
      return handleViewerAction(state, action);
    // CLUSTER ACTIONS
    case "cluster":
      return handleClusterAction(state, action);

    // SELECTION ACTIONS
    case "selection":
      return handleSelectionAction(state, action);
  }
  throw new Error("Invalid action type " + action.type);
}

function handleViewerAction(state: EditorState, action: EditorAction): EditorState {
  /*
  Handle actions that are not cluster-specific.
  */
  switch (action.type) {
    case "viewer_sort":
      return { ...state, viewer_sort: action.sort as "size" | "id" | "name" };

    case "viewer_display":
      return { ...state, viewer_display: action.display as "grid" | "rows" };

    case "viewer_edit":
      return { ...state, editing: true, editingCluster: null, image_selection: new Set<ClusterImageInfo>() };

    case "viewer_end_edit":
      return { ...state, editing: false, editingCluster: null, image_selection: new Set<ClusterImageInfo>() };

    case "viewer_focus":
      return { ...state, editingCluster: action.cluster_id, image_selection: new Set<ClusterImageInfo>() };
  }
  throw new Error("Invalid action type " + action.type);
}

function handleClusterAction(state: EditorState, action: EditorAction): EditorState {
  /*
  Handle actions that are cluster-specific.
  */
  const new_clusters = new Map(state.content.clusters);

  switch (action.type) {
    case "cluster_rename":
      new_clusters.set(action.cluster_id, { ...new_clusters.get(action.cluster_id!)!, name: action.name! });
      return { ...state, content: { ...state.content, clusters: new_clusters } };

    case "cluster_merge":
      // move images from cluster2 to cluster1
      const cluster1 = state.content.clusters.get(action.cluster_id)!;
      const cluster2 = state.content.clusters.get(action.other)!;
      const new_cluster1 = { ...cluster1, images: [...cluster1.images, ...eraseImagesMetadata(cluster2.images)] };
      new_clusters.delete(action.other);
      new_clusters.set(action.cluster_id, new_cluster1);
      return { ...state, content: { ...state.content, clusters: new_clusters }, editingCluster: cluster1.id, askingCluster: null };

    case "cluster_ask":
      return {
        ...state,
        askingCluster: (action.cluster_id === null ? null :
          { not_cluster_id: action.cluster_id, for_action: action.for_action! })
        };
  }
  throw new Error("Invalid action type " + action.type);
}

function handleSelectionAction(state: EditorState, action: EditorAction): EditorState {
  /*
  Handle actions that are selection-specific.
  */
  const selection = new Set<ClusterImageInfo>(state.image_selection);
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
      return { ...state, image_selection: selection };

    case "selection_invert":
      const inverted = new Set<ClusterImageInfo>(state.content.clusters.get(state.editingCluster)!.images);
      selection.forEach(item => inverted.delete(item));
      return { ...state, image_selection: inverted };

    case "selection_all":
      const all = new Set<ClusterImageInfo>(state.content.clusters.get(state.editingCluster)!.images);
      return { ...state, image_selection: all };

    case "selection_clear":
      return { ...state, image_selection: new Set<ClusterImageInfo>() };

    case "selection_move":
      if (action.cluster_id === null) {
        return { ...state, askingCluster: null };
      }
      // remove image obsolete metadata inside selection
      const new_images = eraseImagesMetadata(Array.from(selection));
      // remove images from current cluster
      const orig_cluster = state.content.clusters.get(state.editingCluster)!;
      const new_orig_cluster = { ...orig_cluster, images: orig_cluster.images.filter((image) => !selection.has(image)) };
      let new_cluster: ClusterInfo;

      if (action.cluster_id == -1) {
        const new_id = Math.max(...state.content.clusters.keys()) + 1;
        new_cluster = {
          id: new_id,
          name: "Cluster " + new_id,
          images: new_images
        };
      } else {
        new_cluster = { ...state.content.clusters.get(action.cluster_id)! };
        new_cluster.images.push(...new_images);
      }

      const new_clusters = new Map(state.content.clusters)
      new_clusters.set(new_orig_cluster.id, new_orig_cluster);
      new_clusters.set(new_cluster.id, new_cluster);

      return {
        ...state,
        content: { ...state.content, clusters: new_clusters },
        editingCluster: null,
        image_selection: new Set<ClusterImageInfo>(),
        askingCluster: null
      };
  }
  throw new Error("Invalid action type "+action.type);
}
