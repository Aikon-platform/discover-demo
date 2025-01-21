/*
 Types for the cluster app
 It also includes a util function to serialize/deserialize the clustering file.
*/

import { ImageInfo } from "../shared/types";

// RAW TYPES

export interface ClusterImageInfoRaw {
    path: string;
    raw_url: string;
    tsf_url?: string;
    distance?: number;
    id: number;
    name?: string;
}

export interface ClusterInfoRaw {
    id: number;
    name: string;
    proto_url?: string;
    mask_url?: string;
    images: ClusterImageInfoRaw[];
}

export interface ClusteringFileRaw {
    clusters: { [key: string]: ClusterInfoRaw };
    background_urls: string[];
}

// TYPES

export interface ClusterImageInfo extends ImageInfo {
    tsf_url?: string; // transformed url (for DTI)
    distance?: number; // distance to center (for DTI)
}

export interface ClusterInfo {
    id: number;
    name: string;
    proto_url?: string;
    mask_url?: string;
    images: ClusterImageInfo[];
}

export interface ClusterProps {
    info: ClusterInfo;
    editing: boolean;
}

export interface ClusteringFile {
    clusters: Map<number, ClusterInfo>;
    background_urls: string[];
}

export interface ClusterAppProps {
    clustering_data: ClusteringFile;
    base_url?: string;
    editing?: boolean;
    editable?: boolean;
    formfield?: HTMLInputElement;
    viewer_sort?: "size" | "id" | "name";
}

export type ActionRequiringAsk = "cluster_merge" | "selection_move";

export interface EditorState {
    editing: boolean;
    editingCluster: number | null;
    askingCluster: { not_cluster_id: number, for_action: ActionRequiringAsk } | null;
    content: ClusteringFile;
    base_url?: string;
    image_selection: Set<ClusterImageInfo>;
    viewer_sort: "size" | "id" | "name";
    viewer_display: "grid" | "rows";
}

export type EditorAction =
    { type: "cluster_rename", cluster_id: number, name: string } |
    { type: "cluster_merge", cluster_id: number, other: number } |
    { type: "cluster_delete", cluster_id: number } |
    { type: "cluster_ask", cluster_id: number | null, for_action?: ActionRequiringAsk } |
    { type: "viewer_edit" } |
    { type: "viewer_end_edit" } |
    { type: "viewer_focus", cluster_id: number | null } |
    { type: "viewer_sort", sort: string } |
    { type: "viewer_display", display: string } |
    { type: "selection_change", images: ClusterImageInfo[], selected: boolean } |
    { type: "selection_invert" } |
    { type: "selection_clear" } |
    { type: "selection_move", cluster_id: number | null, other?: number } |
    { type: "selection_all" };

export interface EditorContext {
    state: EditorState;
    dispatch: React.Dispatch<EditorAction>;
}

export function unserializeImageInfo(image: ClusterImageInfoRaw): ClusterImageInfo {
    return {
        ...image,
        id: image.path,
        num: image.id,
        url: image.raw_url,
    };
}

function serializeImageInfo(image: ClusterImageInfo): ClusterImageInfoRaw {
    return {
      ...image,
      path: image.id,
      id: image.num,
      raw_url: image.url
    };
}

export function unserializeClusterFile(file: ClusteringFileRaw): ClusteringFile {
  return {
    clusters: new Map(Object.entries(file.clusters).map(([key, value]) => [parseInt(key), {
      ...value,
      images: value.images.map(unserializeImageInfo)
    }])),
    background_urls: file.background_urls
  };
}

export function serializeClusterFile(file: ClusteringFile): ClusteringFileRaw {
  return {
    clusters: Object.fromEntries(Array.from(file.clusters.entries()).map(([key, value]) => [key.toString(), {
      ...value,
      images: value.images.map(serializeImageInfo)
    }])),
    background_urls: file.background_urls
  };
}
export interface EditorContext {
  state: EditorState;
  dispatch: React.Dispatch<EditorAction>;
}
