import React from "react";
import { SimilarityMatch, SimilarityMatches } from "../types";
import { NameProvider } from "../../shared/types";
import { IconBtn } from "../../shared/IconBtn";
import { getImageName, getSourceName, NameProviderContext } from "../../shared/naming";

function escapeCSVCell(cell?: string | number): string {
    /*
    Escape a cell value for CSV.
    */
    if (!cell) return "";
    return cell.toString().replace(/"/g, '""');
}

function exportMatchesCSV(matches: SimilarityMatch[], nameProvider?: NameProvider): Promise<string> {
    /*
    Export a list of watermark matches to CSV.
    */
    return new Promise((resolve, reject) => {
        // get all metadata fields in matches' sources
        const metadata_fields = new Set<string>();
        matches.forEach(match => {
            Object.keys(match.image.document?.metadata || {}).forEach(key => metadata_fields.add(key));
            Object.keys(match.image.metadata || {}).forEach(key => metadata_fields.add(key));
        });
        const linted_metadata = Array.from(metadata_fields).map(s => (s.charAt(0).toUpperCase()+s.slice(1)).replace(/[\s,"'_]+/g, " "));

        const header = "Image,Source,Similarity,Document,Document URL," + linted_metadata.join(",") + "\n";
        const lines = matches.map(match => {
            const metadata = Array.from(metadata_fields).map(key => (match.image.metadata || match.image.document?.metadata || {})[key] || "");
            return [
                (nameProvider && getImageName(nameProvider, match.image)) || match.image.id,
                match.image.src || match.image.id,
                match.similarity,
                (nameProvider && getSourceName(nameProvider, match.image.document)) || match.image.document?.name,
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
    const [error, setError] = React.useState<string | null>(null);
    const nameProvider = React.useContext(NameProviderContext);

    const exportCSV = async () => {
        setExporting(true);
        try {
            const ematches = matches.matches.filter(m => !threshold || m.similarity >= threshold);
            // add query
            ematches.unshift({image: matches.query, similarity: 1, q_transposition: "none", m_transposition: "none"});
            const csv = await exportMatchesCSV(ematches, nameProvider);
            const blob = new Blob([csv], {type: "text/csv"});
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "similarity-matches.csv";
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
