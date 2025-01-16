import { ClusterInfo, ClusteringFile, ImageInfo } from "../../ClusterApp/types";
import { SimilarityIndex, SimilarityMatches, SimImage } from "../types";

export interface Edge {
    source: number;
    target: number;
    weight: number;
}

interface RCluster {
    id: number;
    merged?: RCluster;
}

interface Graph {
    edges: Edge[];
}

export interface Cluster {
    id: number;
    members: number[];
}

export function connectedComponents(graph: Graph, threshold: number, graph_size: number): Cluster[] {
    const clusters = new Map<number, RCluster>();
    for (const edge of graph.edges) {
        if (edge.weight < threshold) continue;
        let cluster = clusters.get(edge.source) || clusters.get(edge.target) || { id: edge.source };
        while (cluster?.merged) cluster = cluster.merged;
        let cluster2 = clusters.get(edge.target);
        while (cluster2?.merged) cluster2 = cluster2.merged;
        if (cluster2 && cluster !== cluster2) cluster2.merged = cluster;
        clusters.set(edge.source, cluster);
        clusters.set(edge.target, cluster);
    }
    const fclusters = new Map<number, Cluster>();
    const residual = new Array<number>();
    for (let i = 0; i < graph_size; i++) {
        let cluster = clusters.get(i);
        while (cluster?.merged) cluster = cluster.merged;
        if (!cluster) {
            residual.push(i);
            continue;
        }
        if (!fclusters.has(cluster.id)) fclusters.set(cluster.id, { id: fclusters.size, members: [] });
        fclusters.get(cluster.id)!.members.push(i);
    }
    if (residual.length > 0) fclusters.set(-1, { id: -1, members: residual });
    return Array.from(fclusters.values());
}

export function graphFromSimilarityMatches(index: SimilarityIndex, matches: SimilarityMatches[]): Graph {
    const edges: Edge[] = [];
    const map_index = new Map<SimImage, number>();
    for (const [i, image] of index.images.entries()) {
        map_index.set(image, i);
    }

    for (const match of matches) {
        const query_index = map_index.get(match.query)!;
        for (const source of match.matches) {
            const source_index = map_index.get(source.image)!;
            edges.push({ source: query_index, target: source_index, weight: source.similarity });
        }
    }
    return { edges };
}

export function convertToClusteringFile(index: SimilarityIndex, matches: SimilarityMatches[], clusters: Cluster[]): ClusteringFile {
    const cluster_map = new Map<number, Cluster>();
    for (const cluster of clusters) {
        cluster_map.set(cluster.id, cluster);
    }
    const cluster_info = new Map<number, ClusterInfo>();
    for (const [id, cluster] of cluster_map) {
        const images: ImageInfo[] = cluster.members.map((i) => {
            const image = index.images[i];
            return {
                ...image,
                id: i,
                raw_url: image.url,
                path: image.url,
                name: image.name || "",
            };
        });
        const pid = (id >= 0 ? id : cluster_map.size + 1);
        cluster_info.set(pid, { id: pid, name: (id >= 0 ? `Cluster ${id+1}` : "Unclustered"), images });
    }
    return { clusters: cluster_info, background_urls: index.sources.map((s) => s.src) };
}
