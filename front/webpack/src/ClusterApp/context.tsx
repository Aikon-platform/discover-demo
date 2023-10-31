import { EditorContext, EditorState, EditorAction, ImageInfo, ClusterInfo } from "./types";
import React from "react";

export const ClusterEditorContext = React.createContext<EditorContext | undefined>(undefined);

function eraseImagesMetadata(images: ImageInfo[]): ImageInfo[] {
  return images.map((image) => { return { path: image.path, raw_url: image.raw_url, id: image.id, distance: image.id + 10 } });
}

export const editorReducer = (state: EditorState, action: EditorAction) => {
  console.log("editorReducer", state, action);

  // Basic actions
  if (action.type == "edit")
    return { ...state, editing: true };

  if (action.type == "edit_cluster") {
    if (state.editingCluster == action.cluster_id)
      return state;
    return { ...state, editingCluster: action.cluster_id, image_selection: new Set<ImageInfo>() };
  }

  const action_prefix = action.type.split("_")[0];
  if (!state.editing) return state;

  switch (action_prefix) {
    case "cluster":
      const new_clusters = new Map(state.content.clusters);
      switch (action.type) {
        case "cluster_rename":
          new_clusters.set(action.cluster_id, { ...new_clusters.get(action.cluster_id!)!, name: action.name! });
          break;
        case "cluster_merge":
          // move images from cluster2 to cluster1
          const cluster1 = state.content.clusters.get(action.cluster_id)!;
          const cluster2 = state.content.clusters.get(action.other)!;
          const new_cluster1 = { ...cluster1, images: [...cluster1.images, ...eraseImagesMetadata(cluster2.images)] };
          new_clusters.delete(action.other);
          new_clusters.set(action.cluster_id, new_cluster1);
          break;
        case "cluster_delete":
          // move cluster's images to garbage cluster
          return state;
        case "cluster_ask":
          if (action.cluster_id === null) {
            return { ...state, askingCluster: null };
          }
          return { ...state, askingCluster: { not_cluster_id: action.cluster_id, for_action: action.for_action! } };
      }
      return { ...state, content: { ...state.content, clusters: new_clusters } };
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
          return { ...state, image_selection: selection };

        case "selection_invert":
          const inverted = new Set<ImageInfo>(state.content.clusters.get(state.editingCluster)!.images);
          selection.forEach(item => inverted.delete(item));
          return { ...state, image_selection: inverted };

        case "selection_all":
          const all = new Set<ImageInfo>(state.content.clusters.get(state.editingCluster)!.images);
          return { ...state, image_selection: all };

        case "selection_clear":
          return { ...state, image_selection: new Set<ImageInfo>() };

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
            image_selection: new Set<ImageInfo>(),
            askingCluster: null
          };
      }
      break;
  }
  throw new Error("Invalid action type");
}


