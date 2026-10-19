<script lang="ts">
    import { onMount } from "svelte";
    import IconBtn from "../../shared/components/IconBtn.svelte";
    import ImageMagnifier, { setMagnifyingContext } from "../../shared/components/ImageMagnifier.svelte";
    import NameProvider, { setNameProvider } from "../../shared/naming.svelte";
    import { unserializeSearchResults } from "../converters";
    import type { TSimilarityIndex, TSimilarityMatches } from "../types";
    import SimBrowser from "./SimBrowser.svelte";

    interface Props {
        source_index_url: string;
        query_result_url: string;
        metadata_url?: string;
    }
    const { source_index_url, query_result_url, metadata_url }: Props = $props();

    let source_index: TSimilarityIndex = $state({ sources: [], images: [], transpositions: [] });
    let query_index: TSimilarityIndex = $state({ sources: [], images: [], transpositions: [] });
    let matches: TSimilarityMatches[] = $state([]);
    let loading = $state(true);

    const magnifying = $state({});
    setMagnifyingContext(magnifying);

    const name_provider = new NameProvider();
    setNameProvider(name_provider);

    onMount(() => {
        Promise.all([
            fetch(source_index_url).then(response => response.json()),
            fetch(query_result_url).then(response => response.json())
        ]).then(([ raw_index, raw_matches ]) => {
            console.log(raw_index, raw_matches);
            const data = unserializeSearchResults(raw_index, raw_matches);
            [ source_index, query_index, matches ] = [ data.source_index, data.query_index, data.matches ];
            name_provider.fetchIIIFNames(source_index.sources);
            loading = false;
        });

        if (metadata_url && metadata_url !== "" && metadata_url != "None") {
            name_provider.fetchMetadataNames(metadata_url);
        }
    });
</script>

{#if loading}
    <p>Loading...</p>
{:else}
    <SimBrowser index={source_index!} matches={matches!} />
{/if}

<ImageMagnifier {...magnifying} />
