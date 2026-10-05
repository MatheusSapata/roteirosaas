<template>
  <div ref="root" class="tip-root">
    <button type="button" class="tip-trigger" :aria-label="triggerLabel" :title="triggerLabel" :aria-expanded="open" @click="open = !open">
      <TravelIcon v-if="currentKey" :name="currentKey" :size="16" />
      <span v-else-if="modelValue" class="tip-emoji">{{ modelValue }}</span>
      <span v-else class="tip-empty">+</span>
    </button>
    <div v-if="open" class="tip-pop" role="listbox" :aria-label="t({ pt: 'Escolher ícone', es: 'Elegir ícono' })">
      <button
        v-for="key in keys"
        :key="key"
        type="button"
        role="option"
        class="tip-opt"
        :class="{ 'is-on': key === currentKey }"
        :aria-selected="key === currentKey"
        :title="icons[key].label"
        @click="pick(key)"
      >
        <TravelIcon :name="key" :size="18" />
      </button>
      <button v-if="allowClear" type="button" class="tip-clear" @click="clear">{{ t({ pt: "Sem ícone", es: "Sin ícono" }) }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import TravelIcon from "../../shared/TravelIcon.vue";
import { ICON_PREFIX, TRAVEL_ICONS, TRAVEL_ICON_KEYS, travelIconKey, type TravelIconKey } from "../../../utils/travelIcons";
import { createAdminLocalizer } from "../../../utils/adminI18n";

const props = withDefaults(defineProps<{ modelValue?: string | null; allowClear?: boolean }>(), { modelValue: "", allowClear: true });
const t = createAdminLocalizer();
const emit = defineEmits<{ (event: "update:modelValue", value: string): void }>();
const icons = TRAVEL_ICONS;
const keys = TRAVEL_ICON_KEYS;
const open = ref(false);
const root = ref<HTMLElement | null>(null);
const currentKey = computed(() => travelIconKey(props.modelValue));
const triggerLabel = computed(() =>
  currentKey.value ? `${t({ pt: "Ícone", es: "Ícono" })}: ${TRAVEL_ICONS[currentKey.value].label}` : t({ pt: "Escolher ícone", es: "Elegir ícono" })
);
const pick = (key: TravelIconKey) => {
  emit("update:modelValue", `${ICON_PREFIX}${key}`);
  open.value = false;
};
const clear = () => {
  emit("update:modelValue", "");
  open.value = false;
};
const onDocDown = (event: MouseEvent) => {
  if (open.value && root.value && !root.value.contains(event.target as Node)) open.value = false;
};
const onKey = (event: KeyboardEvent) => {
  if (event.key === "Escape") open.value = false;
};
onMounted(() => {
  document.addEventListener("mousedown", onDocDown);
  document.addEventListener("keydown", onKey);
});
onBeforeUnmount(() => {
  document.removeEventListener("mousedown", onDocDown);
  document.removeEventListener("keydown", onKey);
});
</script>

<style scoped>
.tip-root {
  position: relative;
  display: inline-flex;
}
.tip-trigger {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--card);
  color: var(--primary);
  cursor: pointer;
}
.tip-emoji {
  font-size: 14px;
}
.tip-empty {
  font-weight: 700;
  color: var(--muted-foreground);
}
.tip-pop {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 60;
  display: grid;
  grid-template-columns: repeat(6, 36px);
  gap: 4px;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--popover, var(--card));
  box-shadow: var(--shadow-elegant, 0 18px 40px -20px rgba(0, 0, 0, 0.4));
}
.tip-opt {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--foreground);
  cursor: pointer;
}
.tip-opt:hover {
  background: var(--accent);
}
.tip-opt.is-on {
  background: var(--primary);
  color: var(--primary-foreground);
}
.tip-clear {
  grid-column: 1 / -1;
  padding: 6px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--muted-foreground);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
</style>
