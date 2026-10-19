<script lang="ts">
    import Icon from "@iconify/svelte";
    import ImageInfos from "../../shared/components/ImageInfos.svelte";
    import type { TSimilarityMatch } from "../types";
    import IconBtn from "../../shared/components/IconBtn.svelte";
    import ImageFileDisplay from "../../shared/components/ImageFileDisplay.svelte";
    import type { TImageInfo } from "../../shared/types";
    import { matchesHRef } from "./SimBrowser.svelte";

    interface Props {
        matches: TSimilarityMatch[];
        grouped?: boolean;
        threshold?: number;
        wref?: TImageInfo;
    }

    const { matches, grouped, threshold, wref }: Props = $props();

    let expanded = $state(false);
</script>

{#if !threshold || matches[0].similarity >= threshold}
<div class="match-group">
    <div class={expanded ? "match-expanded" : "match-excerpt"}>
        <p>
            {#if grouped}
                <Icon icon="mdi:folder"></Icon>
                {matches[0].image.document?.name || matches[0].image.document?.uid}
            {:else}
                <ImageInfos image={matches[0].image} />
            {/if}
        </p>
        <div class="columns is-multiline match-items">
            {#each matches as match, idx (match.image.id)}
                {#if (expanded || idx == 0) && (!threshold || match.similarity >= threshold)}
                    <ImageFileDisplay comparison={wref} href={matchesHRef(match.image)} {...match} disable_pin />
                {/if}
            {/each}
        </div>
        {#if matches.length > 1}
            <IconBtn
                icon={expanded ? "mdi:close" : "mdi:animation-plus"}
                onclick={() => (expanded = !expanded)}
                label={expanded ? "Collapse" : `+${matches.length - 1}`}
            />
        {/if}
    </div>
</div>
{/if}
