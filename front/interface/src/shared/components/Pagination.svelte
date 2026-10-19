<script lang="ts">
    import Icon from "@iconify/svelte";
import { Pagination } from "bits-ui";

    interface Props {
        page: number;
        total_pages: number;
    }
    let { page = $bindable(), total_pages }: Props = $props();
</script>

<Pagination.Root bind:page count={total_pages} class="pagination">
    {#snippet children({ pages, range })}
    <Pagination.PrevButton class="pagination-ctrl button">
        <Icon icon="mdi:chevron-left" />
    </Pagination.PrevButton>
    {#each pages as page (page.key)}
        {#if page.type === "page"}
            <Pagination.Page {page} class="pagination-ctrl button" />
        {/if}
        {#if page.type === "ellipsis"}
            <div>...</div>
        {/if}
    {/each}
    <Pagination.NextButton class="pagination-ctrl button">
        <Icon icon="mdi:chevron-right" />
    </Pagination.NextButton>
    {/snippet}
</Pagination.Root>
