import React from "react";
import { WatermarkMatch, WatermarkMatches } from "../types";
import { IconBtn } from "../../shared/IconBtn";

function escapeCSVCell(cell?: string | number): string {
    /*
    Escape a cell value for CSV.
    */
    if (!cell) return "";
    return cell.toString().replace(/"/g, '""');
}

function exportMatchesCSV(matches: WatermarkMatch[]): Promise<string> {
    /*
    Export a list of watermark matches to CSV.
    */
    return new Promise((resolve, reject) => {
        // get all metadata fields in matches' sources
        const metadata_fields = new Set<string>();
        matches.forEach(match => {
            Object.keys(match.watermark.source?.metadata || {}).forEach(key => metadata_fields.add(key));
        });

        const header = "Image,Page,Similarity,Source Label,Source URL,Page URL," + Array.from(metadata_fields).join(",") + "\n";
        const lines = matches.map(match => {
            const metadata = Array.from(metadata_fields).map(key => match.watermark.source?.metadata[key] || "");
            return [
                match.watermark.name,
                match.watermark.uid || match.watermark.id,
                match.similarity,
                match.watermark.source?.name,
                match.watermark.source?.url,
                match.watermark.link,
                ...metadata
            ].map(cell => `"${escapeCSVCell(cell)}"`).join(",");
        });
        resolve(header + lines.join("\n"));
    });
}

export function MatchCSVExporter({ matches, threshold }: { matches: WatermarkMatches, threshold?: number}) {
    /*
    Component to export a list of watermark matches to CSV.
    */
    const [exporting, setExporting] = React.useState(false);
    const [exported, setExported] = React.useState(false);
    const [error, setError] = React.useState<string | null>(null);

    const exportCSV = async () => {
        setExporting(true);
        try {
            const ematches = matches.matches.filter(m => !threshold || m.similarity > threshold/100);
            // add query
            ematches.unshift({watermark: matches.query, similarity: 1, transformations: []});
            const csv = await exportMatchesCSV(ematches);
            const blob = new Blob([csv], {type: "text/csv"});
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "watermark-matches.csv";
            a.click();
            setExported(true);
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
