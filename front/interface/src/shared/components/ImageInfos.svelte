<script lang="ts">
    import { ellipsis } from "../utils";
    import type { TImageInfo } from "../types";
    import { getNameProvider } from "../naming.svelte";
    import { getContext } from "svelte";

    interface Props {
        image: TImageInfo;
        isTitle?: boolean;
        prefix?: string;
        filenameDisplay?: boolean;
    }
    const { image, isTitle = false, prefix="", filenameDisplay=true }: Props = $props();
    const tag = $derived(isTitle ? "h4" : "span");
    const name_provider = getNameProvider();
    const url = $derived(name_provider.getImageLink(image));
</script>

<svelte:element class="title-identification" class:mt-2={isTitle} this={tag} title={name_provider.getImageTitle(image)}>
    <span class="tag is-light is-bold mb-3">
        {prefix || ""}
        Image #{image.num}
    </span>
    {#if filenameDisplay}
        <br/>
        <span>{ellipsis(name_provider.getImageTitle(image), 32)}</span>
    {/if}
</svelte:element>
{#if isTitle}
    <p>{name_provider.getImageDescription(image) || image.document?.name || image.subtitle || ""}</p>
{#if url}
    <p><a href={url} target="_blank">See in context</a></p>
{/if}
{/if}
