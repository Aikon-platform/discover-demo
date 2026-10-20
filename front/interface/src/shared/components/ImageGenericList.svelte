<script lang="ts">
    import type { TImageInfo } from "../types";
    import ImageGeneric from "./ImageGeneric.svelte";

    /**
     * an array of images displayed as a bulma `columns` inside an invisible `html:ul`
     */

    interface Props {
        image_array: TImageInfo[];
    }
    const { image_array }: Props = $props();
</script>

<ul class="columns is-mobile is-multiline list-invisible">
    {#each image_array as image (image.id)}
        <li class="column is-one-fourth is-flex">
            <ImageGeneric {image}/>
        </li>
    {/each}
</ul>
