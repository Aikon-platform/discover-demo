<script lang="ts">
    import type { TImageInfo } from "../types";
    import ImageFileDisplay from "./ImageFileDisplay.svelte";
    import ImageInfos from "./ImageInfos.svelte";

    interface Props {
        image: TImageInfo;
    }
    const { image }: Props = $props();
    let mounted = $state(false);

    $effect(() => {
        mounted = true;
    });
</script>

<div class="image-generic-outer-wrapper" style:opacity={mounted ? 1 : 0}>
    <div class="image-generic-inner-wrapper">
        <div class="image-generic-title">
            <ImageInfos {image} filenameDisplay={false} />
        </div>
        <div class="image-generic-content mb-1">
            <ImageFileDisplay {image} />
        </div>
    </div>
</div>

<style>
    .image-generic-outer-wrapper {
        transition: opacity 1s;
    }
</style>
