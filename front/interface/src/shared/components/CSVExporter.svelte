<script lang="ts">
    import IconBtn from "../../shared/components/IconBtn.svelte";

    interface Props {
        iterRows: () => AsyncGenerator<(string | number)[]>;
        filename: string;
    }
    const { iterRows, filename }: Props = $props();

    let exporting = $state(false);
    let error = $state<string | null>(null);

    // UTIL FUNCTIONS

    /**
     * Escape a cell value for CSV.
     */
    function escapeCSVCell(cell?: string | number): string {
        if (!cell) return "";
        return cell.toString().replace(/"/g, '""');
    }

    /**
     * Export a list of clusters to CSV.
     */
    async function exportDataCSV(): Promise<string> {
        const iter = iterRows();

        const lines = [];
        for await (const row of iter) {
            lines.push(row.map((cell) => `"${escapeCSVCell(cell)}"`).join(","));
        }
        return lines.join("\n");
    }

    // ACTIONS

    const exportDownloadCSV = async () => {
        exporting = true;
        try {
            const csv = await exportDataCSV();
            const blob = new Blob([ csv ], { type: "text/csv" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            a.click();
        } catch (e: any) {
            error = e.toString();
        } finally {
            exporting = false;
        }
    };
</script>

<div class="match-exporter">
    <IconBtn
        icon="mdi:download"
        onclick={exportDownloadCSV}
        disabled={exporting}
        label="Export to CSV"
    />
    {#if error}
        <span class="has-text-danger">{error}</span>
    {/if}
</div>
