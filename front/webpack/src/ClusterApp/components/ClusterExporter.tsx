import React from "react";
import { IconBtn } from "../../shared/IconBtn";
import { ClusterInfo } from "../types";
import { getImageName, getSourceName, NameProviderContext } from "../../shared/naming";
import { NameProvider } from "../../shared/types";

function escapeCSVCell(cell?: string | number): string {
    /*
    Escape a cell value for CSV.
    */
    if (!cell) return "";
    return cell.toString().replace(/"/g, '""');
}

function exportClustersCSV(clusters: ClusterInfo[], nameProvider?: NameProvider): Promise<string> {
    /*
    Export a list of clusters to CSV.
    */
    return new Promise((resolve, reject) => {
        // get all metadata fields in matches' sources
        const metadata_fields = new Set<string>();
        clusters.forEach(cluster => {
            cluster.images.forEach(image => {
                Object.keys(image.document?.metadata || {}).forEach(key => metadata_fields.add(key));
                Object.keys(image.metadata || {}).forEach(key => metadata_fields.add(key));
            });
        });
        const linted_metadata = Array.from(metadata_fields).map(s => (s.charAt(0).toUpperCase()+s.slice(1)).replace(/[\s,"'_]+/g, " "));

        const header = "Cluster,Cluster Name,Image,Source,Document,Document URL," + linted_metadata.join(",") + "\n";
        const lines = clusters.map(cluster => {
            return cluster.images.map(image => {
                const metadata = Array.from(metadata_fields).map(key => (image.metadata || image.document?.metadata || {})[key] || "");
                return [
                    cluster.id,
                    cluster.name,
                    (nameProvider && getImageName(nameProvider, image)) || image.id,
                    image.src || image.id,
                    (nameProvider && getSourceName(nameProvider, image.document)) || image.document?.name,
                    image.document?.src,
                    ...metadata
                ].map(cell => `"${escapeCSVCell(cell)}"`).join(",");
            }).join("\n");
        });
        resolve(header + lines.join("\n"));
    });
}

export function ClusterCSVExporter({ clusters, threshold }: { clusters: ClusterInfo[], threshold?: number}) {
    /*
    Component to export a list of watermark matches to CSV.
    */
    const [exporting, setExporting] = React.useState(false);
    const [error, setError] = React.useState<string | null>(null);
    const nameProvider = React.useContext(NameProviderContext);

    const exportCSV = async () => {
        setExporting(true);
        try {
            const csv = await exportClustersCSV(clusters, nameProvider);
            const blob = new Blob([csv], {type: "text/csv"});
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "similarity-clusters.csv";
            a.click();
        } catch (e: any) {
            setError(e.toString());
        } finally {
            setExporting(false);
        }
    }

    return (
        <div className="match-exporter">
            <IconBtn icon="mdi:download" onClick={exportCSV} disabled={exporting} label="Export to CSV" />
            {error && <span className="has-text-danger">{error}</span>}
        </div>
    );
}
