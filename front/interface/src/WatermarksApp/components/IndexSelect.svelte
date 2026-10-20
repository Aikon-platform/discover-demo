<script lang="ts">
    import { ToggleGroup } from "bits-ui";
    import { onMount } from "svelte";
    import { enforceValue, updateUrlSearchParams } from "../../shared/utils";

    /**
     * NOTE url-bound parameters are:
     * - `watermark_index`: the watermark index to select.
     *
     * NOTE: `value` is the internal value: the Index's UUID.
     * the URL facing value is the watermark index's name, which is human-readable.
     */

    interface Props {
        options: HTMLLabelElement[];
        value: string;
    }

    let { options, value = $bindable() }:Props = $props();

    const options_detailed = $derived(options.map(option => ({
        label: Array.from(option.childNodes).filter(node => (node as any).tagName !== "INPUT").map(node => (node as any).outerHTML || node.textContent).join(""),
        input: option.querySelector("input") as HTMLInputElement,
    })));

    const urlParamName = "watermark_index";
    // `id` is the name of the Watermark index. see `watermarks/forms.py` for more info.
    const allowedIndexValues = $derived(options_detailed.map(o => o.input.id));
    const enforceIndexValue = $derived(enforceValue(allowedIndexValues, ""));
    // no need for `updateIndexSearchParam` to be derived since `enforceIndexValue  will be invoked when `updateIndexSearchParam` is called.
    const updateIndexSearchParam = (v: string) => updateUrlSearchParams(enforceIndexValue, urlParamName, v);

    function onValueChange(newValue: string) {
        let indexName = "";
        options_detailed.forEach(({ input }) => {
            if (input.value === newValue) {
                input.checked = true;
                // update the URL.
                indexName = input.id;
                updateIndexSearchParam(indexName);
            } else {
                input.checked = false;
            }
        });
    }

    onMount(() => {
        // read from URL
        const urlSearchParams = new URLSearchParams(window.location.search);
        // the human readable name of the index.
        let urlIndexValue = urlSearchParams.get(urlParamName) || "";

        // if the URL is defined, set form data from URL.
        if (urlIndexValue) {
            urlIndexValue = updateIndexSearchParam(urlIndexValue);
            options_detailed.forEach(({ input }) => {
                if (input.id === urlIndexValue) {
                    input.checked = input.id === urlIndexValue;
                    value = input.value;
                }
            })
        // otherwise, set form data from props
        } else {
            options_detailed.forEach(({ input }) => {
                if (input.checked) {
                    value = input.value;
                }
            });
        }
    });
</script>

<ToggleGroup.Root bind:value={value} type="single" {onValueChange} orientation="vertical" class="dataset-compose-form">
    {#each options_detailed as { input, label }}
        <ToggleGroup.Item value={input.value} class="search-index-option">
            {@html label}
        </ToggleGroup.Item>
    {:else}
        <ToggleGroup.Item value="" class="search-index-option">No index available</ToggleGroup.Item>
    {/each}
</ToggleGroup.Root>
