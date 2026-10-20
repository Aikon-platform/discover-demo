<script lang="ts">
    import { onMount } from "svelte";
    import IIIFURLItem from "./IIIFURLItem.svelte";
    import { enforceValue, enforceBooleanValue, valueOrDefault, updateUrlSearchParams, isValidHttpUrl, isString } from "../../shared/utils";

    /**
     * NOTE URL-bound parameters are:
     * - "iiif_data": string. comma-separated IIIF manifest URLs on which to run a task.
     */

    interface Props {
        field: HTMLTextAreaElement;
        value?: string[][];
    }

    let { field, value = $bindable([]) }: Props = $props();

    const paramName = "iiif_data";

    /** deduplicate URL value for `iiif_data` */
    const deduplicateUrlValue = (s: string): string => [ ...new Set(s.split(",")) ].join(",")

    /** deduplate svelte's internal form data (`value`) */
    const deduplicateInternalValue = (v: string[][]): string[][] => {
        const dedupUriArr = [ ...new Set(
            v
                .filter(el => el.length)
                .map(el => el[0])
        ) ];
        return dedupUriArr.map(el => ([ el ]));
    }

    /**
     * URL-to-Svelte serialization
     * comma separated string to `value`
     * "url1,url2" => [["url1"], ["url2"]]
     */
    const unstringifyIiifData = (s: string): string[][] =>
        deduplicateUrlValue(s)
            .split(",")
            .filter(isValidHttpUrl)
            .map(x => [ x ]);

    /**
     * Svelte-to-URL serialization
     * `value` to "," separated string
     * [["url1"], ["url2"]] => "url1,url2"
     */
    const stringifyIiifData = (d: string[][]): string =>
        deduplicateInternalValue(d)
            .filter(x => x.length)
            .map(x => x[0])
            .filter(x => isString(x) && isValidHttpUrl(x))
            .join(",");

    /** field.value is the data actually being read by the Django form => update it */
    const updateFieldValue = (newValue: string[][]) => {
        field.value = JSON.stringify(deduplicateInternalValue(newValue));
    }

    /** update URL param `iiif_data` with new URLs. */
    const updateUrlIiifData = (iiifData: string[][]): Function => {
        // stringify `iiifData` (extract urls, remove non-urls, join urls by ",")
        const iiifDataStr = stringifyIiifData(iiifData);
        return updateUrlSearchParams(
            undefined,
            paramName,
            iiifDataStr
        )
    }

    /** main hook to update value, field.value and the URL based on `newValue` */
    const updateValue = (newValue: string[][]) => {
        value = deduplicateInternalValue(newValue);
        updateFieldValue(value);
        updateUrlIiifData(value);
    }

    function readFromUrlParam() {
        const sp = (new URL(window.location.href)).searchParams;
        // 1. parse URLs in seach params
        const urlIiifUris = unstringifyIiifData(sp.get(paramName) || "");
        // 2. concat items here with `value`
        const newValue = value.concat(urlIiifUris);
        // 3. update state
        updateValue(newValue);
    }

    // fired when pre-saved items are deleted or modified
    function onChangeItem(index: number) {
        return (url: string) => {
            // copy of `value` to avoid in-place modifs.
            let newValue = [ ...value ];
            if (url == "") {
                // delete element by its index
                newValue.splice(index, 1);
            } else {
                // modify element by its index.
                newValue[index] = [ url ];
            }
            updateValue(newValue);
        }
    }

    // fired when a new item is added
    function onKeydown(e: KeyboardEvent) {
        if (e.key == "Enter") {
            e.preventDefault();
            if ((e.currentTarget as HTMLInputElement).value != "") {
                const newValue = [...value].concat([[ (e.currentTarget as HTMLInputElement).value.trim() ]]);
                updateValue(newValue);
            }
            (e.currentTarget as HTMLInputElement).value = "";
        }
    }

    // TODO fix URL binding here !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    // fired when data is pasted into the input
    function onPaste(e: ClipboardEvent) {
        const text = e.clipboardData?.getData("text/plain");
        const lines = text?.split(/\s+/);
        if (lines) {
            const newValue = [ ...value ];
            newValue.push(...lines.map(line => [ line.trim() ]).filter(line => line[0] != ""));
            updateValue(newValue);
        }
    }

    onMount(() => {
        value = JSON.parse(field.value);
        readFromUrlParam();
    });
</script>

<div>
    {#each value as url, i (i)}
        <IIIFURLItem url={url[0]} onChange={onChangeItem(i)} />
    {/each}
    <input class="input" type="text" placeholder="Type or paste URLs to append to the list above" onkeydown={onKeydown} onpaste={onPaste}/>
</div>
