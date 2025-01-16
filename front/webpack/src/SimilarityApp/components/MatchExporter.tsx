import React from "react";
import { SimilarityMatch, SimilarityMatches } from "../types";
import { IconBtn } from "../../shared/IconBtn";

function escapeCSVCell(cell?: string | number): string {
    /*
    Escape a cell value for CSV.
    */
    if (!cell) return "";
    return cell.toString().replace(/"/g, '""');
}

function exportMatchesCSV(matches: SimilarityMatch[]): Promise<string> {
    /*
    Export a list of watermark matches to CSV.
    */
    return new Promise((resolve, reject) => {
        // get all metadata fields in matches' sources
        console.log(matches);
        const metadata_fields = new Set<string>();
        matches.forEach(match => {
            Object.keys(match.image.document?.metadata || {}).forEach(key => metadata_fields.add(key));
        });

        const header = "Image,Source,Similarity,Document,Document URL," + Array.from(metadata_fields).join(",") + "\n";
        const lines = matches.map(match => {
            const metadata = Array.from(metadata_fields).map(key => match.image.document?.metadata[key] || "");
            return [
                match.image.id,
                match.image.url || match.image.id,
                match.similarity,
                match.image.document?.name,
                match.image.document?.src,
                ...metadata
            ].map(cell => `"${escapeCSVCell(cell)}"`).join(",");
        });
        resolve(header + lines.join("\n"));
    });
}

export function MatchCSVExporter({ matches, threshold }: { matches: SimilarityMatches, threshold?: number}) {
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
            ematches.unshift({image: matches.query, similarity: 1, transformations: []});
            console.log(ematches);
            const csv = await exportMatchesCSV(ematches);
            const blob = new Blob([csv], {type: "text/csv"});
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "similarity-matches.csv";
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
