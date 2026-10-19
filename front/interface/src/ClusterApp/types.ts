/*
 Types for the cluster app
 It also includes a util function to serialize/deserialize the clustering file.
*/

import type { SvelteMap } from "svelte/reactivity";
import type { TImageInfo } from "../shared/types";

// RAW TYPES

export interface TClusterImageInfoRaw {
    path: string;
    raw_url: string;
    tsf_url?: string;
    distance?: number;
    id: number;
    name?: string;
}

export interface TClusterInfoRaw {
    id: number;
    name: string;
    proto_url?: string;
    mask_url?: string;
    images: TClusterImageInfoRaw[];
}

export interface TClusteringFileRaw {
    clusters: Record<string, TClusterInfoRaw>;
    background_urls: string[];
}

// TYPES

export interface TClusterImageInfo extends TImageInfo {
    tsf_url?: string; // transformed url (for DTI)
    distance?: number; // distance to center (for DTI)
}

export interface TClusterInfo {
    id: number;
    name: string;
    proto_url?: string;
    mask_url?: string;
    images: TClusterImageInfo[];
}

export interface TClusterProps {
    info: TClusterInfo;
    editing: boolean;
}

export interface TClusteringFile {
    clusters: Record<number, TClusterInfo>;
    background_urls: string[];
}

export type TActionRequiringAsk = "cluster_merge" | "selection_move";

export interface TEditorState {
    editing: boolean;
    editingCluster: number | null;
    askingCluster: {
        exclude_cluster_id: number;
        for_action: TActionRequiringAsk;
    } | null;
    content: TClusteringFile;
    base_url?: string;
    image_selection: Set<string>;
    viewer_sort: "size" | "id" | "name";
    viewer_display: "grid" | "rows";
}

export type TEditorAction =
    | { type: "cluster_rename"; cluster_id: number; name: string }
    | { type: "cluster_merge"; cluster_id: number; other: number }
    | { type: "cluster_delete"; cluster_id: number }
    | {
          type: "cluster_ask";
          cluster_id: number | null;
          for_action?: TActionRequiringAsk;
      }
    | { type: "viewer_edit" }
    | { type: "viewer_end_edit" }
    | { type: "viewer_focus"; cluster_id: number | null }
    | { type: "viewer_sort"; sort: string }
    | { type: "viewer_display"; display: string }
    | {
          type: "selection_change";
          images: TClusterImageInfo[];
          selected: boolean;
      }
    | { type: "selection_invert" }
    | { type: "selection_clear" }
    | { type: "selection_move"; cluster_id: number | null; other?: number }
    | { type: "selection_all" };
