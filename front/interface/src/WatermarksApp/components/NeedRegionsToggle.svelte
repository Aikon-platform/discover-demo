<script lang="ts">
    import Icon from "@iconify/svelte";
    import { ToggleGroup } from "bits-ui";
    import { onMount } from "svelte";
    import { enforceValue, updateUrlSearchParams, isBoolean } from "../../shared/utils";

    interface Props {
        value?: boolean;
        field: HTMLInputElement;
        are_sketches_field?: HTMLInputElement;
    }

    const enforceNeedsRegionsValue = enforceValue([ "true", "false", "sketches" ], "true");
    const urlParamName = "needs_regions";
    const urlParamUpdateHook = (value: string) =>
        updateUrlSearchParams(
            enforceNeedsRegionsValue,
            urlParamName,
            isBoolean(value) ? value.toString() : value  // if it's bool, stringify it
        );

    let { value = $bindable(true), field, are_sketches_field }: Props = $props();
    let internal_value = $state(value ? "true" : "false");

    function onValueChange(newValue: string) {
        internal_value = newValue;
        urlParamUpdateHook(internal_value);
        value = internal_value == "true";
        field.checked = value;
        if (are_sketches_field) {
            are_sketches_field.checked = internal_value == "sketches";
        }
    }

    onMount(() => {
        const searchParams = new URL(window.location.href).searchParams;
        const urlValue = searchParams.get(urlParamName) || "";

        // urlValue is defined  => set form values from URL
        if (urlValue) {
            if (are_sketches_field) {
                are_sketches_field.checked = urlValue==="sketches";
            }
            internal_value = urlParamUpdateHook(urlValue);
        // no URL values => set default depending on passed props
        } else {
            internal_value = are_sketches_field?.checked
                ? "sketches"
                : field.checked ? "true" : "false";
            urlParamUpdateHook(urlValue);
        }
        value = internal_value == "true";
    });

    $inspect(are_sketches_field);
</script>

<ToggleGroup.Root value={internal_value} type="single" {onValueChange} class="columns toggle-analysis-type">
    <ToggleGroup.Item value="true" class="column is-3 has-text-centered">
        <Icon icon="mdi:image-size-select-large" />
        <span><b>Detect and crop</b> watermarks inside the full pages</span>
    </ToggleGroup.Item>
    <ToggleGroup.Item value="false" class="column is-3 has-text-centered">
        <Icon icon="mdi:fullscreen" />
        <span>Watermarks are already cropped, use <b>full images</b></span>
    </ToggleGroup.Item>
    {#if are_sketches_field}
        <ToggleGroup.Item value="sketches" class="column is-3 has-text-centered">
            <Icon icon="lucide:flower" />
            <span>Images are <b>black sketches on white background</b>, use <b>full images</b></span>
        </ToggleGroup.Item>
    {/if}
</ToggleGroup.Root>
