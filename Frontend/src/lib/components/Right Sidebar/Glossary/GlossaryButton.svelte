<script lang="ts">
    import { Dialog, Separator } from 'bits-ui';
    import { Button, GlossaryCard } from '$lib';
    import { BookOpen, Download, Upload, Plus } from '@lucide/svelte';

    import { glossaryStateManager } from "$lib";


    let originalGlossary = $state("");
    let translatedGlossary = $state("");

    const handleGlossaryAdd = () => {
        glossaryStateManager.addGlossary(originalGlossary, translatedGlossary)
        originalGlossary = "";
        translatedGlossary = "";
    }

    let glossaryEntries = $derived(glossaryStateManager.getLength());


</script>

<Dialog.Root>
  <Dialog.Trigger>
    {#snippet child({ props })}
      <Button {...props} class="w-full border-2 border-primary-border p-4 hover:border-transparent" variant="ghost">
        <BookOpen />
        <p>Glossary</p>
      </Button>
    {/snippet}
  </Dialog.Trigger>
  <Dialog.Portal>
    <Dialog.Overlay class="fixed inset-0 z-50 bg-black/40 data-[state=open]:animate-in data-[state=closed]:animate-out" />
    <Dialog.Content class="fixed left-1/2 top-1/2 z-50 w-[90vw] max-w-3xl -translate-x-1/2 -translate-y-1/2 rounded-lg bg-white p-6 shadow-lg data-[state=open]:animate-in data-[state=closed]:animate-out">
      <Dialog.Title class="text-lg font-semibold mb-2">
        <div class="flex flex-col gap-2">
          <p>Glossary</p>
          <div class="flex flex-row gap-2">
            <Button variant="outline" class="flex flex-row gap-2 border-2 border-primary-border hover:border-transparent">
              <Download />
              <p>Export</p>
            </Button>
            <Button variant="outline" class="flex flex-row gap-2 border-2 border-primary-border hover:border-transparent">
              <Upload />
              <p>Import</p>
            </Button>
          </div>
        </div>
        <Separator.Root orientation="horizontal" class="w-full h-[2px] shrink-0 bg-gray-200 mt-4 mb-4" />
      </Dialog.Title>

      <Dialog.Description class="text-sm text-foreground-alt mb-4 space-y-2">
        <div class="flex flex-col gap-3">
          <div class="flex flex-col gap-3">
            <p class="font-semibold">Add New Entry</p>
            <div class="flex flex-row gap-2">
              <input type="text" placeholder="Original Word" bind:value={originalGlossary} class="w-full px-3 border-2 border-gray-200 rounded-md" />
              <input type="text" placeholder="Translation" bind:value={translatedGlossary} class="w-full px-3 border-2 border-gray-200 rounded-md" />
              <Button onclick={handleGlossaryAdd}>
                <Plus />
              </Button>
            </div>
          </div>

          <Separator.Root orientation="horizontal" class="w-full h-[2px] shrink-0 bg-gray-200 mt-4 mb-4" />

          <div>
            <p class="font-semibold text-sm">Glossary Entries ({glossaryEntries})</p>
            <div class="w-full flex justify-center items-center mt-6">
              {#if glossaryEntries <= 0}
                <p class="text-gray-400">No entries yet. Add your first glossary entry above.</p>
              {:else}
                <div class="flex flex-col gap-2 w-full">
                    {#each glossaryStateManager.glossaryList as glossary (glossary.id)}
                        <GlossaryCard id={glossary.id} originalGlossary={glossary.originalText} translatedGlossary={glossary.translatedText} />
                    {/each}
                </div>
              {/if}
            </div>
          </div>
        </div>
      </Dialog.Description>

      <div class="mt-4 flex justify-end">
        <Dialog.Close class="text-sm font-medium text-primary hover:underline">Close</Dialog.Close>
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>