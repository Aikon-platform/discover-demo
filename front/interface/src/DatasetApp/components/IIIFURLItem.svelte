<script lang="ts">
    import EditableSpan from "../../shared/components/EditableSpan.svelte";
import IconBtn from "../../shared/components/IconBtn.svelte";

    interface Props {
        url: string;
        onChange: (url: string) => void;
    }

    let { url, onChange }: Props = $props();

    const onBlur = () => {
        onChange(url);
    }

    const valid = $derived(url.startsWith("http://") || url.startsWith("https://"));
</script>

<div class="urllist-item mb-2" class:valid={valid}>
    <EditableSpan bind:value={url} placeholder="URL" onblur={onBlur} onenter={onBlur} class="urllist-item-content"/>
    <div class="actions">
        <button class="delete" onclick={(e) => {onChange(""); e.preventDefault();}} />
    </div>
</div>

<style lang="scss">
    .urllist-item {
        display: flex;
        justify-content: stretch;
        align-items: center;
        width: 100%;
        background-color: var(--bulma-info-soft);
        padding: 0.5rem 1rem;
        border-radius: var(--bulma-radius);
        font-size: 0.8rem;
        :global(.urllist-item-content) {
            flex: 1;
        }
    }
    .urllist-item:not(.valid) {
        background-color: var(--bulma-danger-soft);
    }
</style>
