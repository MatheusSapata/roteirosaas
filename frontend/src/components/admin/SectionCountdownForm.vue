<template>
  <div class="countdown-shell">
    <aside class="countdown-nav">
      <button type="button" class="countdown-nav-item active">
        <span class="countdown-nav-icon">⏱</span>
        <span>
          <strong>Contador</strong>
          <small>Texto, tempo e cor</small>
        </span>
      </button>
    </aside>

    <section class="countdown-content">
      <h4 class="countdown-title">Configurações do contador</h4>
      <p class="countdown-subtitle">Configure o texto, o tipo de contagem, o tempo limite e a cor de fundo da seção.</p>

      <div class="countdown-field">
        <label class="countdown-label">
          Etiqueta acima do título
          <small>opcional</small>
          <span class="countdown-help" data-tip="Texto exibido acima do bloco principal.">?</span>
        </label>
        <input v-model="headingText" class="countdown-input" />
      </div>

      <div class="countdown-field">
        <label class="countdown-label">Texto principal <span class="countdown-help" data-tip="Mensagem principal da chamada de urgência.">?</span></label>
        <input v-model="local.label" class="countdown-input" :placeholder="viewCopy.fields.textPlaceholder" />
      </div>

      <div class="countdown-field">
        <label class="countdown-label">Cor de fundo <span class="countdown-help" data-tip="Cor de fundo aplicada ao contador.">?</span></label>
        <div class="countdown-color-row">
          <input type="color" v-model="local.backgroundColor" class="countdown-color-picker" />
          <input v-model="local.backgroundColor" class="countdown-input countdown-input-mono" placeholder="#ef4444" />
        </div>
      </div>

      <div class="countdown-field">
        <label class="countdown-label">Tipo de contagem <span class="countdown-help" data-tip="Escolha entre data fixa ou contagem por visita.">?</span></label>
        <div class="countdown-pill-row">
          <button type="button" class="countdown-pill" :class="{ active: local.countdownMode === 'fixed' }" @click="local.countdownMode = 'fixed'">
            Data e hora fixa
          </button>
          <button type="button" class="countdown-pill" :class="{ active: local.countdownMode === 'session' }" @click="local.countdownMode = 'session'">
            Tempo individual
          </button>
        </div>
      </div>

      <div v-if="local.countdownMode === 'fixed'" class="countdown-field">
        <label class="countdown-label">Data/hora alvo <span class="countdown-help" data-tip="Data final da contagem regressiva.">?</span></label>
        <input v-model="local.targetDate" type="datetime-local" class="countdown-input" />
      </div>

      <div v-else class="countdown-grid-2">
        <div class="countdown-field">
          <label class="countdown-label">Tempo por visita <span class="countdown-help" data-tip="Duração da contagem iniciada ao abrir a página.">?</span></label>
          <input v-model.number="local.sessionDuration" type="number" min="1" max="999" class="countdown-input" />
        </div>
        <div class="countdown-field">
          <label class="countdown-label">Unidade de tempo <span class="countdown-help" data-tip="Unidade usada no tempo por visita.">?</span></label>
          <select v-model="local.sessionUnit" class="countdown-input">
            <option value="minutes">Minutos</option>
            <option value="hours">Horas</option>
            <option value="days">Dias</option>
          </select>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, watch } from "vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { CountdownSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: CountdownSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: CountdownSection): void }>();
const headingDefaults = getSectionHeadingDefaults("countdown");
const t = createAdminLocalizer();

const viewCopy = {
  fields: {
    textPlaceholder: t({ pt: "Promoção por tempo limitado", es: "Promoción por tiempo limitado" })
  }
};

const buildDefaultTargetDate = () => {
  const date = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000);
  return date.toISOString().slice(0, 16);
};

const normalizeText = (value: unknown, fallback: string) => {
  if (typeof value === "string") return value;
  if (!value || typeof value !== "object") return fallback;
  const record = value as Record<string, unknown>;
  for (const key of ["pt", "es"]) {
    const candidate = record[key];
    if (typeof candidate === "string" && candidate.trim()) return candidate;
  }
  for (const candidate of Object.values(record)) {
    if (typeof candidate === "string" && candidate.trim()) return candidate;
  }
  return fallback;
};

const sanitizeSessionDuration = (value: number | undefined) => {
  if (typeof value !== "number" || Number.isNaN(value)) return 15;
  return Math.max(1, Math.min(999, Math.round(value)));
};

const local = reactive<CountdownSection>({
  type: "countdown",
  enabled: true,
  headingLabel: normalizeText(props.modelValue.headingLabel, headingDefaults.label || "Contagem regressiva"),
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  label: normalizeText(props.modelValue.label, viewCopy.fields.textPlaceholder),
  countdownMode: props.modelValue.countdownMode || "fixed",
  sessionDuration: sanitizeSessionDuration(props.modelValue.sessionDuration),
  sessionUnit: props.modelValue.sessionUnit || "minutes",
  targetDate: props.modelValue.targetDate || buildDefaultTargetDate(),
  backgroundColor: props.modelValue.backgroundColor || "#ef4444",
  textColor: props.modelValue.textColor || "#ffffff",
  layout: "flip",
  ...props.modelValue
});

const headingText = computed({
  get: () => normalizeText(local.headingLabel, headingDefaults.label || "Contagem regressiva"),
  set: value => {
    local.headingLabel = value;
  }
});

let syncing = false;
const syncFromProps = (value: CountdownSection) => {
  syncing = true;
  Object.assign(local, value);
  local.headingLabel = normalizeText(value.headingLabel, headingDefaults.label || "Contagem regressiva");
  local.label = normalizeText(value.label, viewCopy.fields.textPlaceholder);
  local.countdownMode = value.countdownMode || "fixed";
  local.sessionDuration = sanitizeSessionDuration(value.sessionDuration);
  local.sessionUnit = value.sessionUnit || "minutes";
  local.targetDate = value.targetDate || buildDefaultTargetDate();
  local.backgroundColor = value.backgroundColor || "#ef4444";
  local.textColor = value.textColor || "#ffffff";
  local.layout = "flip";
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  nextTick(() => {
    syncing = false;
  });
};

watch(
  () => props.modelValue,
  value => {
    if (!value) return;
    syncFromProps(value);
  },
  { deep: true }
);

watch(
  () => ({ ...local }),
  value => {
    if (syncing) return;
    value.sessionDuration = sanitizeSessionDuration(value.sessionDuration);
    emit("update:modelValue", value as CountdownSection);
  },
  { deep: true }
);
</script>

<style scoped>
.countdown-shell {
  display: grid;
  grid-template-columns: 178px 1fr;
  height: 100%;
  min-height: 56vh;
}

.countdown-nav {
  border-right: 1px solid #e6eee8;
  padding: 16px 12px 16px 12px;
  background: #fff;
}

.countdown-nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid #34c759;
  border-radius: 14px;
  padding: 7px 9px;
  background: #34c759;
  color: #0f172a;
  text-align: left;
}

.countdown-nav-icon {
  width: 22px;
  height: 22px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.82);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.countdown-nav-item strong {
  display: block;
  font-size: 16px;
  line-height: 0.95;
  font-weight: 700;
}

.countdown-nav-item small {
  display: block;
  font-size: 10px;
  color: rgba(7, 82, 36, 0.78);
  font-weight: 600;
}

.countdown-content {
  background: #f4f7f5;
  padding: 10px 14px;
  overflow-y: auto;
}

.countdown-title {
  margin: 0 0 2px;
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}

.countdown-subtitle {
  margin: 0 0 10px;
  color: #607284;
  font-size: 12px;
}

.countdown-field {
  margin-top: 10px;
}

.countdown-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #5f7380;
  font-size: 13px;
  font-weight: 800;
  margin-bottom: 6px;
}

.countdown-label small {
  margin-left: auto;
  text-transform: none;
  letter-spacing: 0;
  font-size: 12px;
  color: #93a29a;
  font-weight: 700;
}

.countdown-help {
  width: 16px;
  height: 16px;
  border-radius: 999px;
  border: 1px solid #c9d4ce;
  color: #8aa0ae;
  font-size: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: help;
}

.countdown-help:hover::after {
  content: attr(data-tip);
  position: absolute;
  left: 50%;
  bottom: 22px;
  transform: translateX(-50%);
  width: 220px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #07111f;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: 0;
  text-transform: none;
  z-index: 30;
  box-shadow: 0 10px 24px rgba(7, 17, 31, 0.22);
}

.countdown-input {
  width: 100%;
  border: 1px solid #c9d4ce;
  border-radius: 12px;
  padding: 10px 12px;
  background: #fff;
}

.countdown-input-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.countdown-color-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.countdown-color-picker {
  width: 44px;
  height: 38px;
  border: 1px solid #c9d4ce;
  border-radius: 10px;
  padding: 2px;
  background: #fff;
}

.countdown-pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.countdown-pill {
  border: 1px solid #cad7d1;
  border-radius: 999px;
  background: #fff;
  color: #324a3f;
  font-size: 12px;
  font-weight: 700;
  padding: 8px 12px;
}

.countdown-pill.active {
  border-color: #0b1a34;
  background: #0b1a34;
  color: #fff;
}

.countdown-grid-2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

@media (max-width: 900px) {
  .countdown-shell {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .countdown-nav {
    border-right: 0;
    border-bottom: 0;
    padding: 8px 8px 8px 16px;
    margin-bottom: 8px;
  }

  .countdown-content {
    padding: 10px;
  }

  .countdown-grid-2 {
    grid-template-columns: 1fr;
  }
}
</style>
