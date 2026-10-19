<script lang="ts">
    import ImageFileDisplay from "../../shared/components/ImageFileDisplay.svelte";
    import type { TSimpleCluster } from "../clustering";
    import type { TSimilarityIndex } from "../types";
    interface Props {
        cluster: TSimpleCluster;
        index: TSimilarityIndex;
    }
    const { cluster, index }: Props = $props();
</script>

<div class="cl-cluster box">
    <div class="cl-anchor"></div>
    <div class="cl-props">
        <div class="cl-propcontent">
            <div class="cl-propinfo">
                <p class="cl-cluster-title">
                    <span>{cluster.id >= 0 ? `Cluster ${cluster.id}` : "Unclustered"} ({cluster.members.length})</span>
                </p>
            </div>
        </div>
    </div>
    <div class="cl-samples">
        <div class="cl-images cl-limitheight">
            {#each cluster.members as member (member)}
                <div class="cl-image card">
                    <ImageFileDisplay image={index.images[member]} />
                </div>
            {:else}
                <p>∅</p>
            {/each}
        </div>
    </div>
</div>
