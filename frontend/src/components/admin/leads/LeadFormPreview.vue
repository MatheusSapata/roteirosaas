<template>
  <div class="preview-card">
    <div class="preview-body">
      <img v-if="agencyLogo && displayLogo" :src="agencyLogo" alt="Logo da agência" class="preview-logo" />
      <h3>{{ form.title?.trim() || "Quero receber mais informações" }}</h3>
      <p>{{ form.subtitle?.trim() || "Preencha seus dados e entraremos em contato." }}</p>

      <div class="preview-fields">
        <div v-for="field in visibleFields" :key="field.id || field.type" class="preview-field">
          <label>{{ field.label || presetLabels[field.type] }}</label>
          <textarea v-if="field.type === 'textarea'" :placeholder="field.placeholder || 'Digite sua resposta'" disabled></textarea>
          <input v-else :placeholder="field.placeholder || presetPlaceholders[field.type] || 'Digite sua resposta'" disabled />
        </div>
      </div>

      <button :style="buttonStyle" disabled>{{ buttonLabel }}</button>
      <small>Seus dados estão protegidos</small>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { storeToRefs } from "pinia";
import { useAgencyStore } from "../../../store/useAgencyStore";
import type { LeadForm, LeadFormField } from "../../../types/leads";

const props = defineProps<{ form: Partial<LeadForm> }>();

const agencyStore = useAgencyStore();
const { agencies, currentAgencyId } = storeToRefs(agencyStore);

const currentAgency = computed(() => agencies.value.find(agency => agency.id === currentAgencyId.value) || agencies.value[0] || null);
const agencyLogo = computed(() => currentAgency.value?.logo_url || "");
const displayLogo = computed(() => props.form.showLogo !== false);

const presetLabels: Record<string, string> = {
  name: "Nome completo",
  phone: "Telefone",
  email: "E-mail",
  city: "Cidade",
  cpf: "CPF",
  birthdate: "Data de nascimento"
};

const presetPlaceholders: Record<string, string> = {
  name: "Seu nome",
  phone: "(00) 00000-0000",
  email: "voce@email.com",
  city: "São Paulo - SP",
  cpf: "000.000.000-00",
  birthdate: "1990-01-31"
};

const visibleFields = computed<LeadFormField[]>(() => (props.form.fields || []).filter(Boolean));
const buttonLabel = computed(() => props.form.buttonLabel?.trim() || "Quero saber mais");
const buttonStyle = computed(() => ({
  backgroundColor: props.form.buttonColor || "#3CC96C",
  border: `1px solid ${props.form.buttonColor || "#3CC96C"}`
}));
</script>

<style scoped>
.preview-card { width: 100%; max-width: 305px; border: 1px solid #e3ebe5; border-radius: 16px; background: #f4f7f5; overflow: hidden; }

.preview-body { padding: 12px; text-align: center; }
.preview-logo { width: 48px; height: 48px; object-fit: contain; margin: 0 auto 8px; border-radius: 10px; }
.preview-body h3 { margin: 0; font-size: 16px; color: #1d2b25; line-height: 1.15; }
.preview-body p { margin: 6px 0 10px; color: #809289; font-size: 12px; }

.preview-fields { display: grid; gap: 7px; text-align: left; }
.preview-field label { display: block; margin-bottom: 4px; font-size: 10px; font-weight: 700; color: #90a099; text-transform: uppercase; }
.preview-field input { width: 100%; border-radius: 9px; border: 1px solid #dee7e1; padding: 7px 9px; font-size: 12px; background: #ecf1ee; color: #93a09a; }
.preview-field textarea { width: 100%; min-height: 54px; resize: none; border-radius: 9px; border: 1px solid #dee7e1; padding: 7px 9px; font-size: 12px; background: #ecf1ee; color: #93a09a; }

.preview-body button { width: 100%; margin-top: 10px; border-radius: 11px; color: #132e1c; font-size: 14px; font-weight: 800; padding: 9px 10px; }
.preview-body small { display: block; margin-top: 8px; color: #94a29a; font-size: 11px; }
</style>



