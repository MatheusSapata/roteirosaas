import { defineStore } from "pinia";

type ThemeMode = "light" | "dark";

const STORAGE_KEY = "admin-theme";

const getInitialTheme = (): ThemeMode => {
  if (typeof window === "undefined") {
    return "light";
  }
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return stored === "dark" ? "dark" : "light";
};

export const useThemeStore = defineStore("theme", {
  state: () => ({
    mode: getInitialTheme() as ThemeMode
  }),
  getters: {
    isDark(state): boolean {
      return state.mode === "dark";
    }
  },
  actions: {
    setTheme(mode: ThemeMode) {
      this.mode = mode;
      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, mode);
      }
    },
    toggleTheme() {
      this.setTheme(this.mode === "dark" ? "light" : "dark");
    }
  }
});
