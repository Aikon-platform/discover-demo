<script lang="ts">
    import Icon from "@iconify/svelte";
    import { ToggleGroup } from "bits-ui";
    import { onMount } from "svelte";

    interface Props {
        value: string;
        field: HTMLSelectElement;
    }

    let { value = $bindable(), field }:Props = $props();

    function onValueChange(newValue: string) {
        field.value = newValue;
    }

    onMount(() => {
        value = field.value;
    });
</script>

<ToggleGroup.Root bind:value={value} type="single" {onValueChange} class="columns toggle-analysis-type">
    <ToggleGroup.Item value="query" class="column is-3 has-text-centered">
        <Icon icon="mdi:database-search" />
        <span>I have <b>samples</b> and I want to <b>search</b> for similar watermarks in a <b>database</b></span>
    </ToggleGroup.Item>
    <ToggleGroup.Item value="indexing" class="column is-3 has-text-centered">
        <Icon icon="mdi:database-plus" />
        <span>I have a <b>database</b> of watermarks that I want to make <b>searchable</b></span>
    </ToggleGroup.Item>
    <ToggleGroup.Item value="similarity" class="column is-3 has-text-centered">
        <Icon icon="mdi:compare-horizontal" />
        <span>I have a <b>set</b> of watermarks that I want to <b>compare</b> to each other</span>
    </ToggleGroup.Item>
</ToggleGroup.Root>
