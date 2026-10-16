<script lang="ts">
    import type { TClusterImageInfo, TClusterInfo } from "../types";
    import { getEditorState } from "../state.svelte";
    import IconBtn from "../../shared/components/IconBtn.svelte";
    import Icon from "@iconify/svelte";
    import ClusterCSVExporter from "./ClusterCSVExporter.svelte";
    import ImageList from "./ImageList.svelte";
    import ClusterAlignModal from "./ClusterAlignModal.svelte";
    import { getNameProvider } from "../../shared/naming.svelte";

    interface Props {
        cluster: TClusterInfo;
        expanded?: boolean;
        editing?: boolean;
        editable?: boolean;
        dti_transformed?: boolean;
        thumbnail?: boolean;
        selected?: boolean;
    }
    let {
        cluster,
        expanded = false,
        editing = $bindable(false),
        editable = false,
        dti_transformed = $bindable(false),
        thumbnail = false,
        selected = false,
    }: Props = $props();

    let renaming = $state(false);
    let elRef = $state<HTMLDivElement>();
    let nameInput = $state<HTMLInputElement>();
    const editor_state = getEditorState();
    const name_provider = getNameProvider();

    const N_SHOWN = { grid: 8, rows: 18 };
    const n_shown = $derived(N_SHOWN[editor_state.viewer_display]);

    let images:TClusterImageInfo[] = $state([]);
    let alignInit = $state(false);
    let showAlignModal = $state(false);

    // CALLBACKS
    function onRenameSubmit(e: Event) {
        e.preventDefault();
        const val = nameInput?.value;
        if (val) {
            cluster.name = val;
        }
        renaming = false;
    }

    function askForMerge() {
        editor_state.ask_cluster("cluster_merge", cluster.id);
    }

    const scrollIntoView = () => {
        setTimeout(() => elRef?.scrollIntoView({ behavior: "smooth", block: "center" }), 100);
    };

    $effect(() => {
        if (editing) {
            scrollIntoView();
        }
    });
    $effect(() => {
        cluster.images.length;
        images = name_provider.sortImages(cluster.images);
    });
</script>

<div
    class="cl-cluster box"
    class:cl-expanded={expanded || editing}
    class:cl-selected={selected || editing}
>
    <div class="cl-anchor" bind:this={elRef}></div>
    <div class="cl-props">
        <div class="cl-propcontent">
            {#if thumbnail}
                <h3>{cluster.name}</h3>
                <p>
                    {#if cluster.id >= 0}
                        Cluster #{cluster.id}, {cluster.images.length} images
                    {/if}
                </p>
            {:else}
                <div class="cl-propinfo">
                    <div class="cl-cluster-title">
                        {#if renaming && editing}
                            <form onsubmit={onRenameSubmit}>
                                <input
                                    type="text"
                                    bind:this={nameInput}
                                    defaultValue={cluster.name}
                                    autofocus
                                />
                                <a href="javascript:void(0)" onclick={onRenameSubmit} class="btn"
                                    ><Icon icon="mdi:check-bold" /></a
                                >
                            </form>
                        {:else}
                            <span>{cluster.name}</span>
                            {#if editing}
                                <a
                                    href="javascript:void(0)"
                                    class="btn is-edit"
                                    onclick={() => {
                                        renaming = true;
                                    }}
                                    title="Rename"><Icon icon="mdi:edit" /></a
                                >
                            {/if}
                        {/if}
                    </div>
                    <p>
                        {cluster.id >= 0 &&
                            `Cluster #${cluster.id}, ${cluster.images.length} images`}
                    </p>

                    {#if editable}
                        <p>
                            {#if editing}
                                <IconBtn
                                    icon="mdi:merge"
                                    label="Merge cluster with..."
                                    onclick={askForMerge}
                                />
                                <IconBtn
                                    icon="mdi:check-bold"
                                    label="End edition"
                                    onclick={() => (editing = false)}
                                />
                            {:else}
                                <IconBtn
                                    icon="mdi:edit"
                                    label="Edit cluster"
                                    onclick={() => (editing = true)}
                                />
                            {/if}
                        </p>
                    {:else}
                        <p>
                            <ClusterCSVExporter clusters={[ cluster ]} />
                            <IconBtn
                                icon="mdi:vector-arrange-above"
                                onclick={() => ((alignInit = true), (showAlignModal = true))}
                                label="Align images"
                                class="is-small is-link"
                            />
                            <!-- {btnExpand} TODO -->
                        </p>
                    {/if}
                </div>
            {/if}<!-- thumbnail -->

            {#if !thumbnail && cluster.proto_url}
                <div class="cl-protoinfo">
                    <p>
                        {#if dti_transformed}
                            <IconBtn
                                icon="mdi:image"
                                class="is-outline"
                                label="Show images"
                                onclick={() => {
                                    dti_transformed = false;
                                }}
                            />
                        {:else}
                            <IconBtn
                                icon="mdi:panorama-variant"
                                class="is-outline"
                                label="Show protos"
                                onclick={() => {
                                    dti_transformed = true;
                                }}
                            />
                        {/if}
                    </p>
                    <div class="cl-proto">
                        <img
                            src={(editor_state.base_url || "") + cluster.proto_url}
                            alt="cl-proto"
                            class="prototype"
                        />
                        <!--{#if cluster.mask_url}-->
                        <!--    <img-->
                        <!--        src={(editor_state.base_url || "") + cluster.mask_url}-->
                        <!--        alt="mask"-->
                        <!--        class="mask"-->
                        <!--    />-->
                        <!--{/if}-->
                    </div>
                </div>
            {/if}
        </div>

        {#if editable && !editing}
            <a
                class="cl-overlay cl-hoveroptions"
                href="javascript:void(0)"
                onclick={() => (editing = true)}
            >
                <IconBtn icon="mdi:edit" label="Edit cluster" />
                <IconBtn
                    icon="mdi:merge"
                    label="Merge with..."
                    onclick={(e) => {
                        e.stopPropagation();
                        askForMerge();
                    }}
                />
            </a>
        {/if}
    </div>
    <div class="cl-samples">
        <ImageList
            selectable={editing}
            {images}
            {dti_transformed}
            limit={expanded && !editing ? undefined : n_shown}
            onexpand={() => scrollIntoView()}
            disable_all={thumbnail}
            bind:expanded
        />
    </div>
</div>

{#if alignInit}
    <ClusterAlignModal
        {cluster}
        bind:open={showAlignModal}
        onClose={() => (showAlignModal = false)}
    />
{/if}
