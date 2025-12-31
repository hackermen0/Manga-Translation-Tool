import { Appearance, Theme } from '$lib/enums/Theme';

class themeState {
  appearance = $state<Appearance>(Appearance.Light);
  theme = $state<Theme>(Theme.Purple);

  setAppearance(appearance: Appearance) {
    this.appearance = appearance;
  }

  setTheme(theme: Theme) {
    this.theme = theme;
    const daisyTheme = `light-${theme.toLowerCase()}`;
    document.documentElement.setAttribute('data-theme', daisyTheme);
  }
}

export default new themeState();