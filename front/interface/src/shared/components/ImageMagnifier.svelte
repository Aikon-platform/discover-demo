<script lang="ts" module>
    import { getContext, setContext } from "svelte";
    import type { TMatchTransposition, TImageInfo } from "../types";

    export interface MagnifyingContext {
        image?: TImageInfo;
        transpositions?: TMatchTransposition[];
        comparison?: TImageInfo;
    }

    export function getMagnifyingContext() {
        return getContext<MagnifyingContext>("magnify");
    }

    export function setMagnifyingContext(context: MagnifyingContext) {
        setContext("magnify", context);
    }
</script>

<script lang="ts">
    import { Dialog } from "bits-ui";
    import IconBtn from "./IconBtn.svelte";
    import ImageInfos from "./ImageInfos.svelte";

    const magnifying = $derived(getMagnifyingContext());
    const { image, comparison, transpositions } = $derived(magnifying);

    let transf = $derived<TMatchTransposition[]>(transpositions || []);

    function getOpen() {
        return image !== undefined;
    }
    function setOpen(open: boolean) {
        if (!open) magnifying.image = undefined;
    }

    function manualTransform(deltaRot: 0 | 90 | -90, hflip: boolean) {
        const curRotStr = transf.find(t => t && t.startsWith("rot")),
            prevHflip = transf.includes("hflip"),
            curRot = curRotStr ? parseInt(curRotStr.slice(3)) : 0;
        let newRot = curRot;
        if (hflip && curRot % 180) newRot += 180;
        newRot = (newRot + deltaRot + 360) % 360;
        const newTransf: TMatchTransposition[] = [];
        if (newRot) newTransf.push(`rot${newRot}` as TMatchTransposition);
        if (hflip !== prevHflip) newTransf.push("hflip");
        transf = newTransf;
    }
</script>

{#if image}
<Dialog.Root bind:open={getOpen, setOpen} onOpenChange={setOpen}>
    <Dialog.Portal>
        <div class="modal content" class:is-active={getOpen()}>
        <Dialog.Overlay class="modal-background" />
        <IconBtn icon="mdi:close" class="dialog-close" onclick={() => setOpen(false)}/>
        <Dialog.Content class="magnifier modal-content">
            <div class="magnifying-content">
                {#if comparison}
                    <!-- svelte-ignore a11y_click_events_have_key_events -->
                    <!-- svelte-ignore a11y_no_static_element_interactions -->
                    <div class="magnifying-item" onclick={(e) => e.stopPropagation()}>
                        <div class="display-image">
                            <img src={comparison.url} alt={comparison.id} class="display-img" />
                        </div>
                        <div class="magnifying-info">
                            <ImageInfos image={comparison} isTitle={true} prefix="Query"/>
                        </div>
                    </div>
                {/if}
                <!-- svelte-ignore a11y_click_events_have_key_events -->
                <!-- svelte-ignore a11y_no_static_element_interactions -->
                <div class="magnifying-item" onclick={(e) => e.stopPropagation()}>
                    <div class="display-image">
                        <img src={image.url} alt={image.id} class={"display-img " + (transf.join(" "))} />
                    </div>
                    <div class="magnifying-info">

                        <ImageInfos image={image} isTitle={true}/>
                        <p class="actions my-2">
                            <IconBtn icon="mdi:rotate-left" onclick={() => manualTransform(-90, false)} />
                            <IconBtn icon="mdi:rotate-right" onclick={() => manualTransform(90, false)} />
                            <IconBtn icon="mdi:flip-horizontal" onclick={() => manualTransform(0, true)} />
                        </p>
                    </div>
                </div>
            </div>
        </Dialog.Content>
        </div>
    </Dialog.Portal>
</Dialog.Root>
{/if}
