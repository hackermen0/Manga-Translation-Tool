class EditorState {
	activeSession = $state('translation');

	setActiveSession(section: string) {
		this.activeSession = section;
	}
}

export const editorState = new EditorState();
