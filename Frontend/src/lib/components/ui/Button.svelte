<script lang="ts">
	import type { Component } from 'svelte';
	import type { IconProps } from '@lucide/svelte';
	import { Button } from 'bits-ui';
	import { cn } from '$lib/utils';

	interface Props {
		variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
		size?: 'default' | 'sm' | 'lg' | 'icon';
		class?: string;
		onclick?: (e: MouseEvent) => void;
		children?: import('svelte').Snippet;
		icon?: Component<IconProps, {}, ''>;
		disabled?: boolean;
		href?: string;
		title?: string;
	}

	let {
		variant = 'default',
		size = 'default',
		class: className = '',
		onclick,
		children,
		icon,
		disabled = false,
		href,
		...props
	}: Props = $props();

	const buttonVariants = {
		base: 'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0',
		variants: {
			default: 'bg-primary text-primary-foreground hover:bg-primary/90',
			destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
			outline: 'border border-slate-800 bg-background hover:bg-[var(--color-accent)]/70 hover:text-black',
			secondary: 'bg-[var(--color-accent)] text-black',
			ghost: 'hover:bg-[var(--color-accent)]/70 hover:text-[var(--color-accent)]-foreground',
			link: 'text-primary underline-offset-4 hover:underline'
		},
		sizes: {
			default: 'h-10 px-4 py-2',
			sm: 'h-9 rounded-md px-3',
			lg: 'h-11 rounded-md px-8',
			icon: 'h-10 w-10'
		}
	};

	const classes = $derived(
		cn(buttonVariants.base, buttonVariants.variants[variant], buttonVariants.sizes[size], className)
	);
</script>

<Button.Root class={classes} onclick={onclick} disabled={disabled} href={href} {...props}>
	{#if icon}
		{@const Icon = icon}
		<Icon class="h-4 w-4" />
	{/if}
	{#if children}
		{@render children()}
	{/if}
</Button.Root>