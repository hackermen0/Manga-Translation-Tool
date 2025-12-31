
interface GlossaryState {
    id: string;
    originalText: string;
    translatedText: string;
}


class GlossaryStateManager {

    glossaries = $state<Record<string, GlossaryState>>({})
    glossaryList = $derived(Object.values(this.glossaries))

    addGlossary(originalText: string, translatedText: string) {
        const id = crypto.randomUUID()
        this.glossaries[id] = {
            id,
            originalText,
            translatedText,
        }
        this.glossaries = { ...this.glossaries }; 
    }

    deleteGlossary(id: string) {
        if (this.glossaries[id]) {
            const {[id]: _, ...rest } = this.glossaries;
            this.glossaries = rest;
        }
    }

    getLength(){
        return this.glossaryList.length
    }

}

export const glossaryStateManager = new GlossaryStateManager();