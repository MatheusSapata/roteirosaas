<template>
  <div ref="root" class="relative w-full">
    <button
      type="button"
      class="flex w-full cursor-pointer items-center justify-between gap-3 rounded-lg border border-sidebar-border px-3 py-2 text-sidebar-foreground transition-colors hover:bg-sidebar-accent/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      aria-label="Trocar de sistema"
      aria-haspopup="menu"
      :aria-expanded="open"
      :disabled="loading"
      @click="open = !open"
    >
      <img :src="roteiroLogo" alt="Roteiro Online" class="h-10 w-auto object-contain" />
      <svg
        viewBox="0 0 24 24"
        class="h-4 w-4 flex-shrink-0 text-muted-foreground"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="m7 15 5 5 5-5" />
        <path d="m7 9 5-5 5 5" />
      </svg>
    </button>

    <Transition name="brand-switcher-fade">
      <div
        v-if="open"
        class="absolute left-0 top-full z-50 mt-2 w-full rounded-lg border border-sidebar-border bg-popover p-1 text-popover-foreground shadow-elegant"
        role="menu"
      >
        <button
          type="button"
          class="flex w-full cursor-pointer items-center justify-start rounded-md px-3 py-3 hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          role="menuitem"
          :disabled="loading"
          @click="selectViajeon"
        >
          <img :src="viajeonLogo" alt="" class="h-auto w-[80px] max-w-full object-contain object-left" />
          <span class="sr-only">Ir para Viajeon</span>
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import RoteiroDarkLogo from "../../assets/Logo Branco - Roteiro Online.png";
import RoteiroLightLogo from "../../assets/Logo Cor - Roteiro Online.png";
import ViajeonDarkLogo from "../../assets/logo-viajeon-modoescuro.png";
import ViajeonLightLogo from "../../assets/logo-viajeon-modoclaro.png";
import { useThemeStore } from "../../store/useThemeStore";

defineProps<{ loading?: boolean }>();

const emit = defineEmits<{
  selectViajeon: [];
}>();

const themeStore = useThemeStore();
const root = ref<HTMLElement | null>(null);
const open = ref(false);
const roteiroLogo = computed(() => (themeStore.isDark ? RoteiroDarkLogo : RoteiroLightLogo));
const viajeonLogo = computed(() => (themeStore.isDark ? ViajeonDarkLogo : ViajeonLightLogo));

const selectViajeon = () => {
  open.value = false;
  emit("selectViajeon");
};

const handleDocumentClick = (event: MouseEvent) => {
  if (!root.value?.contains(event.target as Node)) open.value = false;
};

const handleEscape = (event: KeyboardEvent) => {
  if (event.key === "Escape") open.value = false;
};

onMounted(() => {
  document.addEventListener("click", handleDocumentClick);
  document.addEventListener("keydown", handleEscape);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
  document.removeEventListener("keydown", handleEscape);
});
</script>

<style scoped>
.brand-switcher-fade-enter-active,
.brand-switcher-fade-leave-active {
  transition: opacity 100ms ease;
}

.brand-switcher-fade-enter-from,
.brand-switcher-fade-leave-to {
  opacity: 0;
}
</style>
