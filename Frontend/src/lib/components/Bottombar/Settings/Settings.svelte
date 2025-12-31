<script lang="ts">
    import { Button } from "$lib";
    import { Settings, ChevronRight } from "@lucide/svelte";
    import { Popover, Separator } from 'bits-ui';
    import { themeState } from "$lib";
    import { capitalize } from "$lib/utils";
    import { Appearance, Theme } from "$lib/enums/Theme";

    let themes = [
        {name: "purple", color: "bg-accent-purple"},
        {name: "green", color: "bg-accent-green"},
        {name: "blue", color: "bg-accent-blue"},
        {name: "red", color: "bg-accent-red"},
        {name: "yellow", color: "bg-accent-yellow"},
        {name: "pink", color: "bg-accent-pink"},
    ]

    const themeColorMap: Record<Theme, string> = {
        purple: "bg-accent-purple",
        green: "bg-accent-green",
        blue: "bg-accent-blue",
        red: "bg-accent-red",
        yellow: "bg-accent-yellow",
        pink: "bg-accent-pink"
    };
    
</script>


<div>
    <Popover.Root>
			<Popover.Trigger>
                    <Button variant={"ghost"}>
                        <Settings/>
                    </Button>
    		</Popover.Trigger>
            <Popover.Portal>
                <Popover.Content class="bg-background-light border-2 border-primary-border z-10 p-4 rounded-lg min-w-80">
                    <div class="flex flex-col gap-2">
                        <div>
                            <span class="font-semibold">Settings</span>
                        </div>
                        <Separator.Root orientation={"horizontal"} class="w-full h-[2px] shrink-0 bg-gray-200"/>
                        <div class="flex flex-col gap-2 w-full">
                            <span class="font-semibold">Appearance</span>
                            <div>
                                <Popover.Root>
                                    <Popover.Trigger class="w-full">
                                        <Button class="flex flex-row justify-between w-full m-0" variant={"ghost"}>
                                            <span>{capitalize(themeState.appearance)}</span> 
                                            <ChevronRight/>
                                        </Button>
                                    </Popover.Trigger>
                                    <Popover.Portal>
                                        <Popover.Content class="bg-background-light border-2 border-primary-border z-10 p-4 w-full rounded-lg translate-x-54 translate-y-24">
                                            <div class="flex flex-col gap-3">
                                                <Button variant={`${themeState.appearance === 'system' ? 'secondary' : 'ghost'}`} onclick={() => themeState.setAppearance(Appearance.System)}>System</Button>
                                                <Button variant={`${themeState.appearance === 'light' ? 'secondary' : 'ghost'}`} onclick={() => themeState.setAppearance(Appearance.Light)}>Light</Button>
                                                <Button variant={`${themeState.appearance === 'dark' ? 'secondary' : 'ghost'}`} onclick={() => themeState.setAppearance(Appearance.Dark)}>Dark</Button>
                                            </div>
                                        </Popover.Content>
                                    </Popover.Portal>
                                </Popover.Root>
                            </div>
                        </div>
                        <Separator.Root orientation={"horizontal"} class="w-full h-[2px] shrink-0 bg-gray-200"/>
                        <div class="flex flex-col gap-2 w-full">
                            <span class="font-semibold">Theme</span>
                                <Popover.Root>
                                        <Popover.Trigger class="w-full">
                                            <Button class="flex flex-row justify-between w-full m-0" variant={"ghost"}>
                                                <div class={`w-8 h-8 rounded-full border-2 border-gray-300 ${themeColorMap[themeState.theme as keyof typeof themeColorMap]}`}></div>
                                                <ChevronRight/>
                                            </Button>
                                        </Popover.Trigger>
                                        <Popover.Portal>
                                            <Popover.Content class="bg-background-light border-2 border-primary-border z-10 p-4 w-full rounded-lg translate-x-72 translate-y-24">
                                                <div class="grid grid-cols-3 gap-3">
                                                    {#each themes as theme}
                                                        <Button
                                                            variant={themeState.theme === theme.name ? 'outline' : 'ghost'}
                                                            class={"hover:bg-gray-200"}
                                                            onclick={() => themeState.setTheme(theme.name as Theme)}
                                                        >
                                                            <div class={`w-8 h-8 rounded-full border-2 border-gray-300 ${theme.color}`}></div>
                                                        </Button>
                                                    {/each}
                                                </div>
                                            </Popover.Content>
                                        </Popover.Portal>
                                </Popover.Root>
                        </div>
                    </div>
                </Popover.Content>
            </Popover.Portal>
	</Popover.Root>
</div>