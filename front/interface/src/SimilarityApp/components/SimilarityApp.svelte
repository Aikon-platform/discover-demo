<script lang="ts">
    import { onMount } from "svelte";
    import IconBtn from "../../shared/components/IconBtn.svelte";
    import ImageMagnifier, { setMagnifyingContext } from "../../shared/components/ImageMagnifier.svelte";
    import NameProvider, { setNameProvider } from "../../shared/naming.svelte";
    import { unserializeSimilarityMatrix } from "../converters";
    import type { TSimilarityIndex, TSimilarityMatches } from "../types";
    import ClusteringTool from "./ClusteringTool.svelte";
    import SimBrowser from "./SimBrowser.svelte";

    interface Props {
        source_index_url: string;
        sim_matrix_url: string;
        metadata_url?: string;
        mode?: "cluster" | "browse";
    }
    let { source_index_url, sim_matrix_url, metadata_url, mode }: Props = $props();

    let index:TSimilarityIndex = $state.raw({ sources: [], images: [], transpositions: [] });
    let matches:TSimilarityMatches[] = $state.raw([]);
    let loading = $state(true);
    // If clustering tool has been shown once, keep it hidden but active so parameters are still available
    let keep_clustering_tool = $state(mode == "cluster");

    const magnifying = $state({});
    setMagnifyingContext(magnifying);

    const name_provider = new NameProvider();
    setNameProvider(name_provider);

    onMount(() => {
        Promise.all([
            fetch(source_index_url).then(response => response.json()),
            fetch(sim_matrix_url).then(response => response.json())
        ]).then(([ raw_index, raw_matches ]) => {
            const data = unserializeSimilarityMatrix(raw_matches, raw_index);
            [ index, matches ] = [ data.index, data.matches ];
            name_provider.fetchIIIFNames(index.sources);
            loading = false;
        });

        if (metadata_url && metadata_url !== "" && metadata_url != "None") {
            name_provider.fetchMetadataNames(metadata_url);
        }
    });

    $effect(() => {
        if (mode == "cluster") {
            keep_clustering_tool = true;
        }
    });

    $inspect(name_provider.sources);
</script>

{#if loading}
    <p>Loading...</p>
{:else}
    {#if keep_clustering_tool}
    <ClusteringTool index={index!} matches={matches!} visible={mode == "cluster"}>
        {#snippet extra_toolbar_items()}
        <div class="toolbar-item toolbar-btn">
            <IconBtn icon="mdi:folder" onclick={() => mode = "browse"} label="Switch to Browse Mode" />
        </div>
        {/snippet}
    </ClusteringTool>
    {/if}
    {#if mode == "browse"}
        <SimBrowser index={index!} matches={matches!}>
            {#snippet extra_toolbar_items()}
            <div class="toolbar-item toolbar-btn">
                <IconBtn icon="mdi:graph" onclick={() => mode = "cluster"} label="Cluster the results" />
            </div>
            {/snippet}
        </SimBrowser>
    {/if}
{/if}

<ImageMagnifier {...magnifying} />
