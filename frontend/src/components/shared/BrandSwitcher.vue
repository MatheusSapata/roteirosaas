<template>
  <div ref="root" class="relative min-w-0 flex-1">
    <button
      type="button"
      :class="[
        'flex cursor-pointer items-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        compact
          ? 'brand-switcher-tile h-10 w-10 justify-center rounded-xl border border-sidebar-border bg-card hover:bg-sidebar-accent'
          : 'h-11 w-full justify-between gap-2 rounded-xl border border-sidebar-border px-2 text-sidebar-foreground hover:bg-sidebar-accent/40'
      ]"
      aria-label="Trocar de sistema"
      aria-haspopup="menu"
      :aria-expanded="open"
      :disabled="loading"
      @click="open = !open"
    >
      <img v-if="compact" :src="roteiroMark" alt="Roteiro Online" class="h-7 w-7 object-contain" />
      <template v-else>
        <img :src="roteiroLogo" alt="Roteiro Online" class="brand-switcher-logo" />
        <ChevronsUpDownIcon class="h-4 w-4 text-muted-foreground" aria-hidden="true" />
      </template>
    </button>

    <Transition name="brand-switcher-fade">
      <div
        v-if="open"
        :class="[
          'absolute z-50 rounded-lg border border-sidebar-border bg-popover p-1 text-popover-foreground shadow-elegant',
          compact ? 'left-full top-0 ml-3 w-48' : 'left-0 top-full mt-2 w-full'
        ]"
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
import RoteiroMark from "../../assets/Favicon.png";
import ViajeonDarkLogo from "../../assets/logo-viajeon-modoescuro.png";
import ViajeonLightLogo from "../../assets/logo-viajeon-modoclaro.png";
import {
  ChevronsUpDownIcon
} from "lucide-vue-next";
import { useThemeStore } from "../../store/useThemeStore";

defineProps<{ loading?: boolean; compact?: boolean }>();

const emit = defineEmits<{
  selectViajeon: [];
}>();

const themeStore = useThemeStore();
const root = ref<HTMLElement | null>(null);
const open = ref(false);
const roteiroLogo = computed(() => (themeStore.isDark ? RoteiroDarkLogo : RoteiroLightLogo));
const roteiroMark = RoteiroMark;
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
/* O PNG do logo tem faixas vazias em cima e embaixo: o recorte mostra só o desenho. */
.brand-switcher-logo {
  width: 104px;
  height: 31px;
  object-fit: cover;
}

.brand-switcher-fade-enter-active,
.brand-switcher-fade-leave-active {
  transition: opacity 100ms ease;
}

.brand-switcher-fade-enter-from,
.brand-switcher-fade-leave-to {
  opacity: 0;
}
</style>
