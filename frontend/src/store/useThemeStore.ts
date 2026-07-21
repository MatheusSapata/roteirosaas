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
    mode: getInitialTheme() as ThemeMode,
    domThemeActive: false
  }),
  getters: {
    isDark(state): boolean {
      return state.mode === "dark";
    }
  },
  actions: {
    syncDocumentTheme() {
      if (typeof document === "undefined" || !this.domThemeActive) return;
      const dark = this.mode === "dark";
      document.documentElement.classList.toggle("dark", dark);
      document.documentElement.dataset.theme = this.mode;
    },
    activateDocumentTheme() {
      this.domThemeActive = true;
      this.syncDocumentTheme();
    },
    deactivateDocumentTheme() {
      this.domThemeActive = false;
      if (typeof document === "undefined") return;
      document.documentElement.classList.remove("dark");
      delete document.documentElement.dataset.theme;
    },
    setTheme(mode: ThemeMode) {
      this.mode = mode;
      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, mode);
      }
      this.syncDocumentTheme();
    },
    toggleTheme() {
      this.setTheme(this.mode === "dark" ? "light" : "dark");
    }
  }
});
