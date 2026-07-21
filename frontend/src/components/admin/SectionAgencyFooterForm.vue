<template>
  <div class="footer-proto-body">
    <aside class="tabs">
      <button type="button" class="tab active">
        <span class="tab-icon">⚙</span>
        <span>Geral<small>Rodapé da agência</small></span>
      </button>
    </aside>

    <section class="editor">
      <div class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Rodapé com dados da agência</h2>
            <p class="section-desc">Os dados abaixo vêm automaticamente das configurações da agência.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="info-box">
            <p class="info-text">
              {{ viewCopy.info.description }}
              <span class="info-strong">{{ viewCopy.info.configs }}</span>
              {{ viewCopy.info.details }}
            </p>
            <ul class="info-list">
              <li>{{ viewCopy.info.listAddress }}</li>
              <li>{{ viewCopy.info.listSocial }}</li>
            </ul>
          </div>

          <div class="field">
            <label>Cor de fundo <span class="help" data-tip="Cor principal do fundo do rodapé.">?</span></label>
            <div class="color-row">
              <input type="color" v-model="local.backgroundColor" class="color-picker" />
              <input
                v-model="local.backgroundColor"
                placeholder="#2d2d2d"
                class="mono-input"
              />
            </div>
            <p class="field-hint">
              {{ viewCopy.colors.helper }}
              <span class="mono">#2d2d2d</span>
              {{ viewCopy.colors.helperHighlight }}
            </p>
          </div>

          <div class="check-box">
            <label class="inline-check">
              <input type="checkbox" v-model="local.showCadastur" />
              {{ viewCopy.cadastur.label }}
            </label>
            <p class="check-hint">{{ viewCopy.cadastur.helper }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";
import type { AgencyFooterSection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";

const props = defineProps<{ modelValue: AgencyFooterSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: AgencyFooterSection): void }>();
const t = createAdminLocalizer();

const viewCopy = {
  info: {
    description: t({
      pt: "Os campos são preenchidos automaticamente usando as informações cadastradas em",
      es: "Los campos se completan automáticamente usando la información registrada en"
    }),
    configs: t({ pt: "Configurações > Agência", es: "Configuraciones > Agencia" }),
    details: t({
      pt: ". Nome, CNPJ, endereço, contatos e redes sociais são exibidos somente se estiverem completos.",
      es: ". Nombre, CNPJ, dirección, contactos y redes sociales se muestran solo si están completos."
    }),
    listAddress: t({ pt: "Preencha o CEP, endereço e contatos no painel para ativar o mapa e os textos.", es: "Completa el CEP, dirección y contactos para habilitar el mapa y los textos." }),
    listSocial: t({ pt: "Os ícones das redes aparecem apenas quando a agência possui links cadastrados.", es: "Los íconos de redes solo aparecen cuando la agencia tiene enlaces registrados." })
  },
  colors: {
    helper: t({ pt: "Por padrão usamos a cor fixa", es: "Por defecto usamos el color fijo" }),
    helperHighlight: t({ pt: ", independente da cor de botões. Ajuste aqui se quiser outro fundo.", es: ", independientemente del color de botones. Ajusta aquí si quieres otro fondo." })
  },
  cadastur: {
    label: t({ pt: "Exibir selo Cadastur", es: "Mostrar sello Cadastur" }),
    helper: t({
      pt: "Habilite para mostrar o selo usando automaticamente o CPF/CNPJ salvo em Configurações da Agência.",
      es: "Activa para mostrar el sello usando automáticamente el CPF/CNPJ guardado en Configuraciones de la Agencia."
    })
  }
};

const DEFAULT_FOOTER_BG = "#2d2d2d";

const local = reactive<AgencyFooterSection>({
  ...props.modelValue,
  type: "agency_footer",
  enabled: props.modelValue.enabled ?? true,
  fullWidth: props.modelValue.fullWidth ?? true,
  displayVariant: "auto",
  showCadastur: props.modelValue.showCadastur !== false,
  backgroundColor: props.modelValue.backgroundColor || DEFAULT_FOOTER_BG
});

let syncing = false;
const syncFromProps = (value: AgencyFooterSection) => {
  syncing = true;
  Object.assign(local, value);
  local.displayVariant = "auto";
  local.fullWidth = value.fullWidth ?? true;
  local.showCadastur = value.showCadastur !== false;
  local.enabled = value.enabled ?? true;
  local.backgroundColor = value.backgroundColor || DEFAULT_FOOTER_BG;
  syncing = false;
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
  () => ({ ...local, displayVariant: "auto" }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as AgencyFooterSection);
  },
  { deep: true }
);
</script>

<style scoped>
.footer-proto-body { display: grid; grid-template-columns: 178px 1fr; min-height: 0; height: 100%; align-items: stretch; }
.tabs { border-right: 1px solid #e6eee8; padding: 16px 12px 16px 12px; display: flex; flex-direction: column; gap: 8px; background: #fff; }
.tab { display: flex; align-items: center; gap: 10px; border: 1px solid #34c759; border-radius: 14px; padding: 7px 9px; background: #34c759; color: #0f172a; text-align: left; }
.tab-icon { width: 22px; height: 22px; border-radius: 8px; background: rgba(255,255,255,.82); display: inline-flex; align-items: center; justify-content: center; font-size: 12px; }
.tab > span { display: flex; flex-direction: column; gap: 1px; font-size: 15px; font-weight: 700; line-height: 1.15; }
.tab > span small { font-size: 12px; font-weight: 600; color: rgba(15, 23, 42, 0.55); }

.editor { padding: 0; background: #edf1ef; min-width: 0; min-height: 100%; }
.section-card { background: transparent; border: 0; min-height: 0; }
.section-head { padding: 14px 16px 10px; border-bottom: 1px solid #dde5e1; }
.section-title { margin: 0; font-size: 18px; line-height: 1.15; color: #0f172a; font-weight: 800; }
.section-desc { margin: 6px 0 0; font-size: 13px; color: #6a7e74; }
.content-area { padding: 12px 14px; display: grid; gap: 10px; min-width: 0; align-content: start; }

.info-box { border: 1px solid #d7e2db; border-radius: 12px; background: #fff; padding: 12px; }
.info-text { margin: 0; font-size: 13px; color: #475569; }
.info-strong { font-weight: 700; }
.info-list { margin: 10px 0 0; padding-left: 18px; color: #64748b; font-size: 12px; display: grid; gap: 4px; }

.field { display: grid; gap: 6px; }
.field label { font-size: 12px; text-transform: uppercase; letter-spacing: .08em; font-weight: 800; color: #6a7e74; display: inline-flex; align-items: center; gap: 7px; }
.help { width: 16px; height: 16px; border: 1px solid #cdd8d2; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 10px; color: #8ca198; position: relative; cursor: help; background: #eef4f1; text-transform: none; }
.help:hover::after { content: attr(data-tip); position: absolute; left: 22px; top: 50%; transform: translateY(-50%); white-space: nowrap; padding: 6px 8px; background: #0f172a; color: #fff; font-size: 11px; border-radius: 8px; z-index: 20; text-transform: none; letter-spacing: 0; }

input { width: 100%; border: 1px solid #cad7d1; border-radius: 12px; background: #fff; font-size: 16px; line-height: 1.25; padding: 9px 12px; color: #1f2937; }
input:focus { outline: none; border-color: #9cb5aa; box-shadow: 0 0 0 2px rgba(52,199,89,.15); }

.color-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.color-picker { width: 40px; height: 40px; border-radius: 10px; border: 1px solid #cad7d1; padding: 2px; }
.mono-input { flex: 1; min-width: 180px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.field-hint { margin: 0; font-size: 11px; color: #7d9087; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; color: #334155; }

.check-box { border: 1px solid #d7e2db; border-radius: 12px; padding: 10px; background: #fff; }
.inline-check { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; color: #475569; text-transform: none; letter-spacing: 0; font-weight: 700; }
.inline-check input { width: 14px; height: 14px; }
.check-hint { margin: 6px 0 0; font-size: 12px; color: #64748b; }

.footer-proto-body,
.editor { background: var(--background); color: var(--foreground); }
.tabs { border-color: var(--border); background: var(--card); }
.tab { border-color: var(--primary); background: var(--primary); color: var(--primary-foreground); }
.section-head { border-color: color-mix(in srgb, var(--border) 62%, transparent); }
.section-title,
.info-strong { color: var(--foreground); }
.section-desc,
.info-text,
.info-list,
.inline-check,
.check-hint,
.field-hint,
.mono { color: var(--muted-foreground); }
.info-box,
.check-box { border-color: var(--border); background: var(--card); }
input { border-color: var(--input); background: var(--card); color: var(--foreground); }
input:focus {
  outline: none;
  border-color: var(--ring);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ring) 15%, transparent);
}
.color-picker { border-color: var(--input); background: var(--card); }
.help:hover::after {
  border: 1px solid var(--border);
  background: var(--popover);
  color: var(--popover-foreground);
  box-shadow: var(--shadow-elegant);
}

@media (max-width: 900px) {
  .footer-proto-body { grid-template-columns: 1fr; min-height: 100%; height: 100%; }
  .tabs { border-right: 0; border-bottom: 0; padding: 8px 8px 8px 16px; margin-bottom: 8px; }
}
</style>

