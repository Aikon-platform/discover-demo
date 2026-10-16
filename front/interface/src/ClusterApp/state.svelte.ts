import type {
    TEditorState,
    TClusteringFile,
    TClusterImageInfo,
    TActionRequiringAsk,
    TClusterInfo,
} from "./types";
import { getContext, setContext } from "svelte";
import { SvelteSet } from "svelte/reactivity";
import NameProvider from "../shared/naming.svelte";
import { parseImageMetadataCSV, type TImageAlignMetadata } from "./align";

/**
 * Erase the original cluster-specific metadata from the images
 * (i.e. the transformed prototype url, and the distance to the cluster center)
 * @param images
 * @returns
 */
function eraseImagesMetadata(images: TClusterImageInfo[]): TClusterImageInfo[] {
    return images.map((image) => {
        const { tsf_url, ...rest } = image;
        return { ...rest, distance: image.num + 10 };
    });
}

export default class ClusterEditorState implements TEditorState {
    content: TClusteringFile;

    editing: boolean = $state(false);
    editingCluster: number | null = $state(null);
    askingCluster: { exclude_cluster_id: number; for_action: TActionRequiringAsk } | null =
        $state(null);

    base_url: string;
    image_selection: SvelteSet<string> = $state(new SvelteSet());

    viewer_sort: "size" | "id" | "name" = $state("id");
    viewer_display: "grid" | "rows" = $state("grid");
    name_provider: NameProvider;

    image_metadata_csv?: string;
    private image_metadata: Promise<Map<number, TImageAlignMetadata> | null> | null = null;

    constructor(data: TClusteringFile, base_url?: string) {
        this.content = $state(
            {
                clusters: data.clusters,
                background_urls: data.background_urls,
            }
        );
        this.name_provider = new NameProvider();
        this.base_url = base_url || "";
        this.image_metadata_csv = data.image_metadata_csv;
    }

    /**
     * Lazily fetch and parse the image metadata csv (once, unless it fails)
     * @returns The metadata by image_id, or null if there is no csv
     * @throws If the csv cannot be fetched or parsed
     */
    get_image_metadata(): Promise<Map<number, TImageAlignMetadata> | null> {
        if (!this.image_metadata_csv) return Promise.resolve(null);
        if (!this.image_metadata) {
            const url = this.base_url + this.image_metadata_csv;
            this.image_metadata = fetch(url)
                .then((response) => {
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    return response.text();
                })
                .then(parseImageMetadataCSV)
                .catch((error) => {
                    this.image_metadata = null;
                    throw error;
                });
        }
        return this.image_metadata;
    }

    select_images(action: "all" | "none" | "invert" | "toggle", image?: TClusterImageInfo) {
        switch (action) {
            case "all":
                this.image_selection = new SvelteSet(
                    this.content.clusters[this.editingCluster!]!.images.map((image) => image.id)
                );
                break;
            case "none":
                this.image_selection.clear();
                break;
            case "invert":
                this.image_selection = new SvelteSet(
                    this.content.clusters[this.editingCluster!]!
                        .images.filter((image) => !this.image_selection.has(image.id))
                        .map((image) => image.id)
                );
                break;
            case "toggle":
                if (image) {
                    this.image_selection.has(image.id)
                        ? this.image_selection.delete(image.id)
                        : this.image_selection.add(image.id);
                }
                break;
        }
    }

    ask_cluster(action: TActionRequiringAsk, cluster_id: number) {
        this.askingCluster = { exclude_cluster_id: cluster_id, for_action: action };
    }

    ask_cluster_choice(cluster_id: number) {
        switch (this.askingCluster?.for_action) {
            case "cluster_merge":
                this.merge_clusters(this.askingCluster.exclude_cluster_id, cluster_id);
                break;
            case "selection_move":
                this.move_images(this.askingCluster.exclude_cluster_id, cluster_id);
                break;
        }
        this.askingCluster = null;
    }

    merge_clusters(cluster1_id: number, cluster2_id: number) {
        const cluster1 = this.content.clusters[cluster1_id]!;
        const cluster2 = this.content.clusters[cluster2_id]!;
        const new_cluster1 = {
            ...cluster1,
            images: [...cluster1.images, ...eraseImagesMetadata(cluster2.images)],
        };
        delete this.content.clusters[cluster2_id];
        this.content.clusters[cluster1_id] = new_cluster1;
        this.editingCluster = cluster1_id;
    }

    move_images(cluster1_id: number, cluster2_id: number) {
        const orig_cluster = this.content.clusters[cluster1_id]!;

        // remove image obsolete metadata inside selection
        const new_images = eraseImagesMetadata(orig_cluster.images.filter((image) => this.image_selection.has(image.id)));

        // remove images from current cluster
        orig_cluster.images = orig_cluster.images.filter((image) => !this.image_selection.has(image.id));

        let new_cluster: TClusterInfo;

        if (cluster2_id == -1) {
            // create a new cluster
            const new_id = Math.max(...Object.keys(this.content.clusters).map(Number)) + 1;
            new_cluster = {
                id: new_id,
                name: "Cluster " + new_id,
                images: new_images,
            };
        } else {
            // add images to existing cluster
            new_cluster = { ...this.content.clusters[cluster2_id]! };
            new_cluster.images.push(...new_images);
        }

        this.content.clusters = {
            ...this.content.clusters,
            [new_cluster.id]: new_cluster,
        };
        this.editingCluster = null;
        this.image_selection.clear();
        this.askingCluster = null;
    }
}

export function getEditorState() {
    return getContext<ClusterEditorState>("editor_state");
}

export function setEditorState(state: ClusterEditorState) {
    setContext("editor_state", state);
}
