import { Appearance, Theme } from '$lib/enums/Theme';

class ThemeState {
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

export const themeState = new ThemeState();