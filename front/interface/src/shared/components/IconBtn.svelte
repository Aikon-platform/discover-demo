<script lang="ts">
    import Icon from "@iconify/svelte";
    import { Button } from "bits-ui";
    import type { ClassValue } from "svelte/elements";

    interface Props {
        icon: string;
        label?: string;
        onclick?: (e: MouseEvent) => void;
        disabled?: boolean;
        class?: ClassValue;
    }
    const { icon, label, onclick, disabled, class: className }: Props = $props();
</script>

<Button.Root class={[ className || "is-link is-light mr-2", "button", disabled ? "disabled" : "" ]} onclick={onclick} disabled={disabled}>
    <Icon icon={icon} />
    {#if label}
        <span>{label}</span>
    {/if}
</Button.Root>
