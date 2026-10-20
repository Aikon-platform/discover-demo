<script lang="ts">
    import { onMount } from "svelte";
    import { Tabs, Toggle } from "bits-ui";
    import JSZip from "jszip";
    import Icon from "@iconify/svelte";

    import IIIFURLListInput from "./IIIFURLListInput.svelte";
    import { preprocessImage } from "../imageHelpers";
    import IconBtn from "../../shared/components/IconBtn.svelte";
    import { enforceValue, enforceBooleanValue, unquote, updateUrlSearchParams, maybeBooleanToBoolean } from "../../shared/utils";

    /**
     * NOTE URL-bound parameters are:
     * - "dataset_type": TDatasetValue. has no effect if dataset_reuse=true
     * - "dataset_reuse": boolean
     *
     */

    type TDatasetValue = "zip"|"iiif"|"pdf"|"images"|""

    const EMPTY_FILE = "No file selected";

    interface Props {
        form: HTMLElement;
        ready: boolean;
    }
    let { form, ready = $bindable() }: Props = $props();
    const form_id = $props.id();

    const dataset_reuse_field = form.querySelector("#id_reuse_dataset") as HTMLInputElement;
    const dataset_reuse_target_field = form.querySelector("#id_dataset") as HTMLInputElement;

    // `switch_field` represents the internal state sent to Django
    // `tab` represents the user-exposed / svelte side data
    // the notable difference is that, if tab==="images", images are zipped in svelte-side
    // `switch_field.value` is set to "zip" while `tab` is kept to "images", and a zip of
    // images is sent to Django.
    const switch_field = form.querySelector("#id_format") as HTMLInputElement;
    const defaultTab = "pdf";
    let tab: TDatasetValue = $state("");  // set in `onMount`

    const iiif_field = form.querySelector("#id_iiif_manifests") as HTMLTextAreaElement;
    const zip_field = form.querySelector("#id_zip_file") as HTMLInputElement;
    const pdf_field = form.querySelector("#id_pdf_file") as HTMLInputElement;
    const parent_html_form = zip_field.form!;

    // checkbox: reuse existing dataset.
    let dataset_reuse_value = $state(dataset_reuse_field.checked);
    const defaultDatasetReuse = false;
    // which dataset to reuse
    let dataset_reuse_target_value = $state(dataset_reuse_target_field.value);

    let iiif_value = $state<string[][]>([]);
    let zip_file_name = $state(EMPTY_FILE);
    let pdf_file_name = $state(EMPTY_FILE);
    let image_files: { name: string; blob: Blob }[] = $state([]);
    const image_zipper = new JSZip();

    let dragover = $state(false);

    const enforceSwitchFieldValue = enforceValue([ "zip", "iiif", "images", "pdf" ], defaultTab)
    const enforceDatasetReuseValue = enforceBooleanValue(defaultDatasetReuse);

    function addImages(files: File[]) {
        files.forEach((file) => {
            preprocessImage(file, 2048, (blob) => {
                if (blob) {
                    // make file name unique
                    const prev_names = image_files.map(f => f.name);
                    let filename = file.name;
                    if (prev_names.includes(filename)) {
                        // Generate a unique name
                        const ext = file.name.split('.').pop() || '';
                        const name = file.name.slice(0, -ext.length - 1);
                        let counter = 1;
                        while (prev_names.includes(filename)) {
                            filename = `${name}+${counter}.${ext}`;
                            counter++;
                        }
                    }
                    image_zipper.file(filename, blob);
                    image_files = [ ...image_files, { name: filename, blob: blob }];
                }
            });
        });
        tab = "images";
    }

    function removeImage(index: number) {
        return () => {
            const file = image_files[index];
            image_zipper.remove(file.name);
            image_files.splice(index, 1);
        };
    }

    function onDrop(e: DragEvent) {
        e.preventDefault();
        e.stopPropagation();
        dragover = false;
        const files = e.dataTransfer?.files;
        if (files) {
            // based on the mime type
            if (files[0].type.startsWith("image/")) {
                addImages(Array.from(files).filter((file) => file.type.startsWith("image/")));
            }
            if (files[0].type.startsWith("application/zip")) {
                zip_field.files = files;
                zip_file_name = files[0].name;
                tab = "zip";
            }
            if (files[0].type.startsWith("application/pdf")) {
                pdf_field.files = files;
                pdf_file_name = files[0].name;
                tab = "pdf";
            }
        }
    }

    function onTabChange(value: string) {
        updateUrlSearchParams(enforceSwitchFieldValue, "dataset_type", value)
        switch_field.value = value == "images" ? "zip" : value;
    }

    function onDatasetReuseChange(value: boolean) {
        dataset_reuse_field.checked = value;
        updateUrlSearchParams(enforceDatasetReuseValue, "dataset_reuse", value);
    }

    $effect(() => {
        dataset_reuse_target_field.value = dataset_reuse_target_value;
    });

    $effect(() => {
        ready = dataset_reuse_value ? dataset_reuse_target_value != "" :
            (tab == "images" && image_files.length > 0) ||
            (tab == "zip" && zip_file_name !== EMPTY_FILE) ||
            (tab == "iiif" && iiif_value.length > 0) ||
            (tab == "pdf" && pdf_file_name !== EMPTY_FILE);
    });

    onMount(() => {
        const urlSearchParams = new URLSearchParams(window.location.search);
        const urlDatasetType = urlSearchParams.get("dataset_type");

        // if `dataset_type` is defined in the URL, use it to set `tab`. otherwise, tab is set using a default.
        // implicitly, `switch_field.value` is also updated.
        const rawTab = urlDatasetType?.length
            ? urlDatasetType
            : defaultTab;
        // validate tab, and if `urlDatasetType` and sync tab and URL param.
        tab = updateUrlSearchParams(enforceSwitchFieldValue, "dataset_type", rawTab) as TDatasetValue  // validate and update value if necessary
        // synchronize switch_field (internal django value) with URL param
        switch_field.value = tab;

        // set dataset_reuse_value from URL, if possible.
        const urlDatasetReuse = maybeBooleanToBoolean(urlSearchParams.get("dataset_reuse"));
        dataset_reuse_value = updateUrlSearchParams(enforceDatasetReuseValue, "dataset_reuse", urlDatasetReuse);

        zip_file_name = zip_field.files?.[0]?.name ?? EMPTY_FILE;
        zip_field.onchange = () => {
            zip_file_name = zip_field.files?.[0]?.name ?? EMPTY_FILE;
        };

        pdf_file_name = pdf_field.files?.[0]?.name ?? EMPTY_FILE;
        pdf_field.onchange = () => {
            pdf_file_name = pdf_field.files?.[0]?.name ?? EMPTY_FILE;
        };

        if (parent_html_form) {
            parent_html_form.onsubmit = (event) => {
                if (tab !== "zip") zip_field.files = null;
                if (tab !== "pdf") pdf_field.files = null;

                if (tab == "images") {
                    event.preventDefault();
                    image_zipper.generateAsync({ type: "blob" }).then((blob) => {
                        const dataTransfer = new DataTransfer();
                        dataTransfer.items.add(
                            new File([ blob ], "dataset.zip", { type: "application/zip" })
                        );
                        zip_field.files = dataTransfer.files;
                        parent_html_form.submit();
                    });
                }
            };
        }
        return () => {
            zip_field.onchange = null;
            pdf_field.onchange = null;
            parent_html_form.onsubmit = null;
        };
    });
</script>

<div class="dataset-compose-form is-relative">
    <div class="dataset-reuse-toggle">
        <Toggle.Root bind:pressed={dataset_reuse_value} onPressedChange={onDatasetReuseChange}>
            <span class="mr-2">Reuse existing dataset</span>
            <Icon icon="mdi:sync" />
        </Toggle.Root>
    </div>
    {#if dataset_reuse_value}
        <div class="is-flex is-flex-direction-column is-align-items-start"> 
            <div class="m-1">
                <div class="select">
                    <select bind:value={dataset_reuse_target_value}>
                        <option value="">Use dataset from</option>
                        {#each dataset_reuse_target_field.children as option}
                            {#if option instanceof HTMLOptionElement && option.value != ""}
                                <option value={option.value}>{option.text}</option>
                            {/if}
                        {/each}
                    </select>
                </div>
            </div>
            <div class="m-1">
                <a class="button" 
                    style={dataset_reuse_target_value ? '' : "cursor: not-allowed; opacity: 0.5"}
                    href={dataset_reuse_target_value ? `/datasets/${dataset_reuse_target_value}/view` : undefined}
                >
                    <span class="iconify iconify--mdi" data-icon="mdi:eye"></span>
                    View dataset
                </a>
            </div>
        </div>
    {:else}
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div
            ondrop={onDrop}
            ondragover={(e) => {
                e.preventDefault();
                e.stopPropagation();
                dragover = true;
            }}
            ondragleave={(e) => {
                e.preventDefault();
                e.stopPropagation();
                dragover = false;
            }}
            class="has-background-light"
        >
            <div class="top-notification notification py-3 px-4">
                <span class="iconify" data-icon="mdi:info-outline"></span> You can drag and drop files
                here
            </div>
            {#if dragover}
                <div class="notification dropper is-info is-overlay">Drop files here</div>
            {/if}
            <Tabs.Root bind:value={tab} onValueChange={onTabChange}>
                <Tabs.List class="columns gap-2">
                    <div class="column is-3">
                        <Tabs.Trigger value="images" class="">Image files</Tabs.Trigger>
                    </div>
                    <div class="column is-3">
                        <Tabs.Trigger value="zip" class="">Zip file</Tabs.Trigger>
                    </div>
                    <div class="column is-3">
                        <Tabs.Trigger value="iiif" class="">IIIF manifests</Tabs.Trigger>
                    </div>
                    <div class="column is-3">
                        <Tabs.Trigger value="pdf" class="">PDF file</Tabs.Trigger>
                    </div>
                </Tabs.List>

                <Tabs.Content value="images">
                    <ul class="columns is-mobile is-multiline list-invisible">
                        {#each image_files as file, i (file)}
                            <li class="column is-3 is-flex">
                                <div class="image-generic-outer-wrapper" style="opacity: 1;">
                                    <div class="image-generic-inner-wrapper">
                                        <div class="image-generic-title">
                                            <IconBtn icon="mdi:delete" onclick={removeImage(i)} />
                                            <span class="title-identification" title={file.name}
                                                ><span class="tag is-light is-bold mb-3"
                                                    >Image #{i}</span
                                                >
                                                <span class="is-size-7">{file.name}</span>
                                            </span>
                                        </div>
                                        <div class="image-generic-content mb-1">
                                            <img
                                                src={URL.createObjectURL(file.blob)}
                                                alt={file.name}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </li>
                        {/each}
                    </ul>
                    <div class="file has-name is-fullwidth" id="id_pdf_file-wrapper">
                        <label for="{form_id}-img-input" class="file-label">
                            <span class="file-cta">
                                <span class="file-icon">
                                    <span class="iconify" data-icon="mdi:upload"></span>
                                </span>
                                <span class="file-label">Select files...</span>
                            </span>
                            <span class="file-name">Images ({image_files.length})</span>
                            <input
                                type="file"
                                id="{form_id}-img-input"
                                accept="image/*"
                                onchange={(e) =>
                                    addImages(
                                        Array.from((e.target as HTMLInputElement).files ?? [])
                                    )}
                                class="file-input"
                                style="display: none;"
                                multiple
                            />
                        </label>
                    </div>
                </Tabs.Content>
                <Tabs.Content value="zip">
                    <div class="file has-name is-fullwidth" id="id_zip_file-wrapper">
                        <label for={zip_field.id} class="file-label">
                            <span class="file-cta">
                                <span class="file-icon">
                                    <span class="iconify" data-icon="mdi:upload"></span>
                                </span>
                                <span class="file-label">Select a file...</span>
                            </span>
                            <span class="file-name">{zip_file_name}</span>
                        </label>
                    </div>
                </Tabs.Content>
                <Tabs.Content value="iiif">
                    <IIIFURLListInput field={iiif_field} bind:value={iiif_value} />
                </Tabs.Content>
                <Tabs.Content value="pdf">
                    <div class="file has-name is-fullwidth" id="id_pdf_file-wrapper">
                        <label for={pdf_field.id} class="file-label">
                            <span class="file-cta">
                                <span class="file-icon">
                                    <span class="iconify" data-icon="mdi:upload"></span>
                                </span>
                                <span class="file-label">Select a file...</span>
                            </span>
                            <span class="file-name">{pdf_file_name}</span>
                        </label>
                    </div>
                </Tabs.Content>
            </Tabs.Root>
        </div>
    {/if}
</div>
