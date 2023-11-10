/*
 Types for the cluster app
 It also includes a util function to serialize/deserialize the clustering file.
*/

export interface ImageInfo {
    path: string;
    raw_url: string;
    tsf_url?: string;
    distance: number;
    id: number;
}

export interface ClusterInfo {
    id: number;
    name: string;
    proto_url?: string;
    mask_url?: string;
    images: ImageInfo[];
}

export interface ClusterProps {
    info: ClusterInfo;
    editing: boolean;
}

export interface ClusteringFile {
    clusters: Map<number, ClusterInfo>;
    background_urls: string[];
}

export interface AppProps {
    clustering_data: any;
    base_url: string;
    editing?: boolean;
    editable?: boolean;
    formfield?: HTMLInputElement;
}

export type ActionRequiringAsk = "cluster_merge" | "selection_move";

export interface EditorState {
    editing: boolean;
    editingCluster: number | null;
    askingCluster: { not_cluster_id: number, for_action: ActionRequiringAsk } | null;
    content: ClusteringFile;
    base_url: string;
    image_selection: Set<ImageInfo>;
    viewer_sort: "size" | "id" | "name";
    viewer_display: "grid" | "rows";
}

export type EditorAction =
    { type: "cluster_rename", cluster_id: number, name: string } |
    { type: "cluster_merge", cluster_id: number, other: number } |
    { type: "cluster_delete", cluster_id: number } |
    { type: "cluster_ask", cluster_id: number | null, for_action?: ActionRequiringAsk } |
    { type: "viewer_edit" } |
    { type: "viewer_focus", cluster_id: number | null } |
    { type: "viewer_sort", sort: string } |
    { type: "viewer_display", display: string } |
    { type: "selection_change", images: ImageInfo[], selected: boolean } |
    { type: "selection_invert" } |
    { type: "selection_clear" } |
    { type: "selection_move", cluster_id: number | null, other?: number } |
    { type: "selection_all" };

export interface EditorContext {
    state: EditorState;
    dispatch: React.Dispatch<EditorAction>;
}

export function unserializeClusterFile(file: { clusters: { [key: string]: ClusterInfo; }; background_urls: string[]; }): ClusteringFile {
  return {
    clusters: new Map(Object.entries(file.clusters).map(([key, value]) => [parseInt(key), value])),
    background_urls: file.background_urls
  };
}

export function serializeClusterFile(file: ClusteringFile): { clusters: { [key: string]: ClusterInfo; }; background_urls: string[]; } {
  return {
    clusters: Object.fromEntries(file.clusters.entries()),
    background_urls: file.background_urls
  };
}
export interface EditorContext {
  state: EditorState;
  dispatch: React.Dispatch<EditorAction>;
}

