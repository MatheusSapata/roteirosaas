<template>
  <section class="internal-form-section" :style="sectionStyle">
    <div v-if="section.backgroundType === 'image'" class="overlay" :style="{ opacity: section.overlayOpacity ?? .35 }"></div>
    <div class="content" :class="`align-${section.alignment || 'center'}`">
      <div v-if="headingLabel" class="section-heading"><SectionHeadingChip :text="headingLabel" :style-type="section.headingLabelStyle" :accent="headingAccent" /></div>
      <header v-if="title || subtitleHtml"><h2 v-if="title" :style="{ color: textPalette.primary }">{{ title }}</h2><div v-if="subtitleHtml" class="rich-subtitle" :style="{ color: textPalette.muted }" v-html="subtitleHtml"></div></header>
      <form v-if="form" class="form-card" @submit.prevent="submit">
        <div v-for="field in form.fields" :key="field.id" class="field">
          <label :for="fieldId(field.id)">{{ field.label }} <span v-if="field.required">*</span></label>
          <textarea v-if="field.type === 'textarea'" :id="fieldId(field.id)" v-model="values[field.id]" :placeholder="field.placeholder" rows="3" />
          <input v-else :id="fieldId(field.id)" v-model="values[field.id]" :type="inputType(field.type)" :inputmode="inputMode(field.type)" :placeholder="field.placeholder" />
          <small v-if="errors[field.id]">{{ errors[field.id] }}</small>
        </div>
        <button type="submit" :disabled="submitting" :style="buttonStyle">{{ submitting ? "Enviando..." : (form.buttonLabel || "Enviar") }}</button>
        <p v-if="generalError" class="submit-error">{{ generalError }}</p>
      </form>
      <div v-else class="form-card empty">{{ loading ? "Carregando formulário..." : "Formulário indisponível." }}</div>
    </div>
  </section>
  <Teleport to="body">
    <transition name="fade"><div v-if="successVisible" class="success-layer" role="dialog" aria-modal="true"><div class="success-modal"><button type="button" aria-label="Fechar" @click="closeSuccess">×</button><span>✓</span><p>{{ successMessage }}</p></div></div></transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from "vue";
import type { InternalFormSection } from "../../types/page";
import type { LeadForm } from "../../types/leads";
import { fetchPublicLeadForm, submitLeadForm } from "../../services/leadCapture";
import { resolveMediaUrl } from "../../utils/media";
import { createLocalizer, getCurrentLanguage } from "../../utils/i18n";
import SectionHeadingChip from "./SectionHeadingChip.vue";
import { sanitizeHtml } from "../../utils/sanitizeHtml";
import { deriveTextPalette, getReadableTextColor } from "../../utils/colorContrast";

const props = defineProps<{ section: InternalFormSection; pageId?: number | null; pageSlug?: string | null; pageTitle?: string | null; pageUrl?: string | null }>();
const localize = createLocalizer(getCurrentLanguage());
const form = ref<LeadForm | null>(null); const loading = ref(false); const submitting = ref(false); const generalError = ref(""); const successVisible = ref(false);
const values = reactive<Record<string,string>>({}); const errors = reactive<Record<string,string>>({}); let successTimer: ReturnType<typeof setTimeout> | null = null;
const title = computed(() => localize(props.section.title as any)); const subtitle = computed(() => localize(props.section.subtitle as any));
const subtitleHtml = computed(() => sanitizeHtml(subtitle.value));
const textPalette = computed(() => deriveTextPalette(props.section.textColor));
const headingLabel = computed(() => localize((props.section.headingLabel ?? "Fale conosco") as any)); const headingAccent = computed(() => props.section.textColor || "#22c55e");
const successMessage = computed(() => localize(props.section.successMessage as any) || "Obrigado! Recebemos suas informações com sucesso.");
const sectionStyle = computed(() => {
  const s = props.section; let background = s.backgroundColor || "#f8fafc";
  if (s.backgroundType === "gradient") background = `linear-gradient(${s.gradientDirection || "to bottom right"}, ${s.gradientStart || "#0f172a"}, ${s.gradientEnd || "#2563eb"})`;
  const style: Record<string,string> = { background, color: s.textColor || "#0f172a" };
  if (s.backgroundType === "image" && s.backgroundImage) { style.backgroundImage = `url("${resolveMediaUrl(s.backgroundImage)}")`; style.backgroundSize = "cover"; style.backgroundPosition = "center"; }
  return style;
});
const buttonStyle = computed(() => {
  const backgroundColor = props.section.buttonColor || form.value?.buttonColor || "#22c55e";
  return { backgroundColor, color: getReadableTextColor(backgroundColor) };
});
const fieldId = (id:string) => `internal-form-${props.section.anchorId || "section"}-${id}`;
const inputType = (type:string) => type === "email" ? "email" : type === "phone" ? "tel" : type === "birthdate" ? "date" : "text";
const inputMode = (type:string) => type === "email" ? "email" : (type === "phone" || type === "cpf") ? "tel" : "text";
const load = async () => {
  form.value = null; if (!props.section.formId) return; loading.value = true;
  try { form.value = await fetchPublicLeadForm(props.section.formId, { pageId: props.pageId, pageSlug: props.pageSlug }); (form.value.fields || []).forEach(f => values[f.id] = ""); }
  catch { form.value = null; } finally { loading.value = false; }
};
const validate = () => {
  if (!form.value) return false; let valid = true;
  form.value.fields.forEach(field => { const value = (values[field.id] || "").trim(); errors[field.id] = ""; if (field.required && !value) { errors[field.id] = "Campo obrigatório"; valid = false; } else if (field.type === "email" && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) { errors[field.id] = "Informe um e-mail válido"; valid = false; } }); return valid;
};
const submit = async () => {
  if (!form.value || !validate()) return; submitting.value = true; generalError.value = "";
  try { await submitLeadForm(form.value.id, { formId: form.value.id, values: form.value.fields.map(field => ({ fieldId: field.id, type: field.type, value: values[field.id] || "" })), source: "Formulário interno", pageId: props.pageId, pageSlug: props.pageSlug, pageTitle: props.pageTitle, pageUrl: props.pageUrl || (typeof window !== "undefined" ? window.location.href : undefined) }); successVisible.value = true; const seconds = Math.min(30, Math.max(1, props.section.successDurationSeconds || 5)); successTimer = setTimeout(closeSuccess, seconds * 1000); }
  catch { generalError.value = "Não foi possível enviar. Tente novamente."; } finally { submitting.value = false; }
};
const closeSuccess = () => { successVisible.value = false; if (successTimer) clearTimeout(successTimer); successTimer = null; };
watch(() => props.section.formId, load, { immediate: true }); onUnmounted(closeSuccess);
</script>

<style scoped>
.internal-form-section{position:relative;padding:72px 24px}.overlay{position:absolute;inset:0;background:#000}.content{position:relative;z-index:1;display:flex;max-width:1180px;margin:auto;flex-direction:column}.align-left{align-items:flex-start;text-align:left}.align-center{align-items:center;text-align:center}.align-right{align-items:flex-end;text-align:right}header{width:min(100%,620px);margin-bottom:22px}h2{font-size:clamp(30px,4vw,48px);font-weight:800;line-height:1.1}header p{margin-top:10px;font-size:18px;opacity:.9}.form-card{display:grid;width:min(100%,520px);gap:14px;border-radius:22px;background:rgba(255,255,255,.96);padding:24px;text-align:left;color:#0f172a;box-shadow:0 22px 55px rgba(15,23,42,.22)}.field{display:grid;gap:6px}.field label{font-size:13px;font-weight:700}.field label span,.field small,.submit-error{color:#e11d48}.field input,.field textarea{width:100%;border:1px solid #cbd5e1;border-radius:11px;padding:11px 12px;background:white}.form-card button{border:0;border-radius:12px;padding:12px;font-weight:800}.empty{text-align:center;color:#64748b}.success-layer{position:fixed;inset:0;z-index:180;display:flex;align-items:center;justify-content:center;background:rgba(2,6,23,.62);padding:20px}.success-modal{position:relative;width:min(100%,440px);border-radius:24px;background:white;padding:38px 28px;text-align:center;color:#0f172a;box-shadow:0 28px 80px rgba(0,0,0,.35)}.success-modal button{position:absolute;right:14px;top:10px;border:0;background:none;font-size:28px;color:#64748b}.success-modal span{display:inline-grid;height:54px;width:54px;place-items:center;border-radius:50%;background:#dcfce7;color:#16a34a;font-size:28px}.success-modal p{margin-top:16px;font-size:18px;font-weight:700}.fade-enter-active,.fade-leave-active{transition:opacity .2s}.fade-enter-from,.fade-leave-to{opacity:0}@media(max-width:640px){.internal-form-section{padding:48px 16px}.content{align-items:center;text-align:center}.form-card{padding:18px}}
.content{display:grid;align-items:center;gap:clamp(32px,6vw,80px)}.section-heading{grid-column:1/-1;grid-row:1;width:100%;text-align:center;justify-self:center;margin-bottom:calc(clamp(32px,6vw,80px) * -0.55)}.align-center{grid-template-columns:1fr;justify-items:center;text-align:center;row-gap:20px}.align-center .section-heading{margin-bottom:8px}.align-center header{grid-row:2;margin-bottom:0}.align-center .form-card{grid-row:3}.align-left,.align-right{grid-template-columns:minmax(0,520px) minmax(0,1fr)}.align-left .form-card{grid-column:1;grid-row:2}.align-left header{grid-column:2;grid-row:2;text-align:left;margin-bottom:0}.align-right header{grid-column:1;grid-row:2;text-align:left;margin-bottom:0}.align-right .form-card{grid-column:2;grid-row:2}@media(max-width:760px){.content,.align-left,.align-right{grid-template-columns:1fr;justify-items:center;text-align:center;row-gap:20px}.section-heading{grid-column:1;grid-row:1}.align-left header,.align-right header,.align-center header{grid-column:1;grid-row:2;text-align:center;margin-bottom:0}.align-left .form-card,.align-right .form-card,.align-center .form-card{grid-column:1;grid-row:3}}
.rich-subtitle{margin-top:10px;font-size:18px;opacity:.9}.rich-subtitle :deep(p+ p),.rich-subtitle :deep(ul),.rich-subtitle :deep(ol){margin-top:.55rem}.rich-subtitle :deep(ul){list-style:disc;padding-left:1.25rem}.rich-subtitle :deep(ol){list-style:decimal;padding-left:1.25rem}
</style>
