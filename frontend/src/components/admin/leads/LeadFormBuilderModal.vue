<template>
  <Teleport to="body">
    <transition name="fade">
      <div v-if="modelValue" class="fm-ov open" @click="onOverlayClick">
        <div class="fm-modal">
          <div class="fm-hd">
            <div class="fm-hd-top">
              <div>
                <div class="fm-ey">Formulário</div>
                <div class="fm-title">{{ title }}</div>
                <div class="fm-sub-txt">{{ state.name?.trim() || "Personalize a aparência, os campos e as notificações." }}</div>
              </div>
              <button class="fm-close" @click="close">
                <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
            <div class="fm-tabs">
              <button class="fm-tab-btn" :class="{ on: activeTab === 'visual' }" @click="activeTab = 'visual'">
                <svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
                Visual
              </button>
              <button class="fm-tab-btn" :class="{ on: activeTab === 'notification' }" @click="activeTab = 'notification'">
                <svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
                Notificação inteligente
              </button>
            </div>
          </div>

          <div class="fm-body">
            <div v-if="activeTab === 'visual'" class="fm-pane on">
              <div class="fm-left">
                <div class="fm-row">
                  <label class="fm-lbl">Nome interno</label>
                  <input v-model="state.name" class="fm-inp" placeholder="ex: Captação Geral" />
                  <span class="fm-hint">Não é exibido para o visitante — apenas para identificação interna.</span>
                </div>
                <div class="fm-row">
                  <label class="fm-lbl">Título exibido</label>
                  <input v-model="state.title" class="fm-inp" placeholder="ex: Quero receber mais informações" />
                </div>
                <div class="fm-grid3">
                  <div class="fm-row">
                    <label class="fm-lbl">Texto do botão</label>
                    <input v-model="state.buttonLabel" class="fm-inp" placeholder="ex: Quero saber mais" />
                  </div>
                  <div class="fm-row">
                    <label class="fm-lbl">Exibir logo no formulário</label>
                    <label class="fm-check-row fm-check-row-inline">
                      <input v-model="state.showLogo" type="checkbox" />
                      <div>
                        <div class="fm-check-lbl">Mostrar logo</div>
                      </div>
                    </label>
                  </div>
                  <div class="fm-row">
                    <label class="fm-lbl">Status inicial do lead</label>
                    <select v-model="state.defaultStatusId" class="fm-sel">
                      <option value="">Sem status padrão</option>
                      <option v-for="status in statuses" :key="status.id" :value="String(status.id)">{{ status.name }}</option>
                    </select>
                  </div>
                </div>
                <div class="fm-row">
                  <div class="fmf-sec-lbl">Selecione os campos que deseja coletar</div>
                  <div class="fmf-grid">
                    <button
                      v-for="preset in fieldPresets"
                      :key="preset.type"
                      class="fmf-chip"
                      :class="{ on: selectedTypes.includes(preset.type) }"
                      @click="toggleField(preset.type)"
                    >
                      <span class="fmf-chip-ic"><svg viewBox="0 0 24 24" v-html="preset.icon"></svg></span>
                      <span class="fmf-name">{{ preset.label }}</span>
                      <span class="fmf-chk"></span>
                    </button>
                  </div>
                  <div class="fmf-sel-note">{{ state.fields.length }} campos selecionados</div>
                </div>
              </div>
              <div class="fm-right">
                <LeadFormPreview :form="state" />
              </div>
            </div>

            <div v-else class="fm-pane on">
              <div v-if="!hasWhatsAppPlanAccess" class="fmn-plan-gate">
                <h3 class="fmn-plan-gate-title">Recurso indisponível no seu plano</h3>
                <p class="fmn-plan-gate-text">
                  A Notificação inteligente via WhatsApp está disponível apenas para o plano Escala.
                </p>
                <button type="button" class="btn btn-p" @click="goToPlans">Fazer upgrade</button>
              </div>
              <template v-else>
              <div class="fmn-left">
                <div class="fm-row">
                  <label class="fm-lbl">Mensagem para envio via WhatsApp</label>
                  <div class="fmn-vars">
                    <button v-for="token in messageTokens" :key="token.key" type="button" class="fmn-var" @click="insertToken(token.value)">{{ token.label }}</button>
                  </div>
                  <textarea ref="messageEditorRef" v-model="state.autoWhatsAppMessageTemplate" class="fm-inp fm-ta" style="margin-top:6px;min-height:110px"></textarea>
                  <span class="fm-hint">Variáveis serão substituídas pelos dados do lead no envio real.</span>
                </div>

                <div class="fm-row">
                  <label class="fm-lbl">Delay para envio</label>
                  <div class="fmn-delay-row">
                    <input v-model.number="delayValue" class="fmn-delay-inp" type="number" min="0" placeholder="0" />
                    <select v-model="delayUnit" class="fmn-delay-sel">
                      <option value="s">segundos</option>
                      <option value="min">minutos</option>
                      <option value="h">horas</option>
                    </select>
                    <span class="fmn-delay-lbl">após o preenchimento</span>
                  </div>
                  <span class="fm-hint">Defina 0 para enviar imediatamente.</span>
                </div>

                <div class="fm-row">
                  <label class="fm-lbl" style="margin-bottom:8px">Não enviar se o lead...</label>
                  <div class="fmn-sw-block">
                    <div class="fmn-sw-row">
                      <div class="fmn-sw-txt"><div class="fmn-sw-lbl">Já é cliente</div><div class="fmn-sw-hint">Lead consta como cliente ativo na plataforma</div></div>
                      <label class="fmn-toggle"><input v-model="state.autoWhatsAppSkipIfClient" type="checkbox" /><span class="fmn-track"></span></label>
                    </div>
                    <div class="fmn-sw-row">
                      <div class="fmn-sw-txt"><div class="fmn-sw-lbl">Já preencheu este formulário</div><div class="fmn-sw-hint">Mesmo e-mail ou telefone já foi enviado neste formulário</div></div>
                      <label class="fmn-toggle"><input v-model="state.autoWhatsAppSkipIfFormAlreadySubmitted" type="checkbox" /><span class="fmn-track"></span></label>
                    </div>
                    <div class="fmn-sw-row">
                      <div class="fmn-sw-txt"><div class="fmn-sw-lbl">Já se cadastrou nessa página</div><div class="fmn-sw-hint">Lead já converteu em qualquer formulário desta página</div></div>
                      <label class="fmn-toggle"><input v-model="state.autoWhatsAppSkipIfPageAlreadySubmitted" type="checkbox" /><span class="fmn-track"></span></label>
                    </div>
                    <div class="fmn-sw-row">
                      <div class="fmn-sw-txt"><div class="fmn-sw-lbl">Tem oportunidade aberta</div><div class="fmn-sw-hint">Já existe uma oportunidade em andamento para este lead</div></div>
                      <label class="fmn-toggle"><input v-model="state.autoWhatsAppSkipIfOpenOpportunity" type="checkbox" /><span class="fmn-track"></span></label>
                    </div>
                  </div>
                </div>
              </div>

              <div class="fmn-right">
                <div class="fmn-wapp">
                  <div class="fmn-wapp-bar">
                    <div class="fmn-wapp-av">
                      <svg viewBox="0 0 24 24" width="18" height="18"><path d="M17.498 14.382c-.301-.15-1.767-.867-2.04-.966-.273-.101-.473-.15-.673.15-.197.295-.771.964-.944 1.162-.175.195-.349.21-.646.075-.3-.15-1.263-.465-2.403-1.485-.888-.795-1.484-1.77-1.66-2.07-.174-.3-.019-.465.13-.615.136-.135.301-.345.451-.523.146-.181.194-.301.297-.496.1-.21.049-.375-.025-.524-.075-.15-.672-1.62-.922-2.206-.24-.584-.487-.51-.672-.51-.172-.015-.371-.015-.571-.015-.2 0-.523.074-.797.359-.273.3-1.045 1.02-1.045 2.475s1.07 2.865 1.219 3.075c.149.195 2.105 3.195 5.1 4.485.714.3 1.27.48 1.704.629.714.227 1.365.195 1.88.121.574-.091 1.767-.721 2.016-1.426.255-.705.255-1.29.18-1.425-.074-.135-.27-.21-.57-.345"/></svg>
                    </div>
                    <div><div class="fmn-wapp-name">Roteiro Online</div><div class="fmn-wapp-status">online</div></div>
                  </div>
                  <div class="fmn-wapp-body"><div class="fmn-bubble"><div>{{ renderedPreviewMessage }}</div><div class="fmn-bubble-time">agora ✓✓</div></div></div>
                  <div class="fmn-wapp-ibar"><div class="fmn-wapp-fake-inp">Mensagem</div></div>
                </div>
              </div>
              </template>
            </div>
          </div>

          <div class="fm-foot">
            <div class="fm-foot-left">{{ errorMessage || "Formulário não salvo" }}</div>
            <div style="display:flex;gap:10px">
              <button class="btn btn-o btn-sm" @click="close">Cancelar</button>
              <button class="btn btn-p btn-sm" :disabled="saving" @click="handleSubmit">
                <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                {{ saving ? "Salvando..." : "Salvar alterações" }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import type { LeadFieldType, LeadForm, LeadFormField, LeadFormPayload } from "../../../types/leads";
import { useLeadCaptureStore } from "../../../store/useLeadCaptureStore";
import { useAuthStore } from "../../../store/useAuthStore";
import LeadFormPreview from "./LeadFormPreview.vue";

const props = defineProps<{ modelValue: boolean; form?: LeadForm | null; saving?: boolean }>();
const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  save: [{ id: string | null; form: LeadFormPayload }];
  invalid: [message: string];
}>();

type BuilderTab = "visual" | "notification";
const generateId = () => `field-${Math.random().toString(36).slice(2, 9)}`;
const router = useRouter();
const auth = useAuthStore();

interface FieldPreset { type: LeadFieldType; label: string; placeholder: string; icon: string; }
const fieldPresets: FieldPreset[] = [
  { type: "name", label: "Nome completo", placeholder: "Seu nome", icon: '<path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>' },
  { type: "phone", label: "Telefone / WhatsApp", placeholder: "(00) 00000-0000", icon: '<path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.4 10.87a19.79 19.79 0 01-3.07-8.67A2 2 0 012.31 0h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L6.91 7.91a16 16 0 006.5 6.5l.72-.73a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/>' },
  { type: "email", label: "E-mail", placeholder: "email@exemplo.com", icon: '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>' },
  { type: "cpf", label: "CPF", placeholder: "000.000.000-00", icon: '<rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/>' },
  { type: "city", label: "Cidade", placeholder: "Sua cidade", icon: '<path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>' },
  { type: "birthdate", label: "Data de nascimento", placeholder: "1990-01-31", icon: '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>' }
];

const messageTokens = [
  { key: "nome", label: "{{nome}}", value: "{{nome}}" },
  { key: "first_name", label: "{{first_name}}", value: "{{first_name}}" },
  { key: "pagina", label: "{{pagina}}", value: "{{origem}}" },
  { key: "saudacao", label: "{{saudacao}}", value: "{{saudacao}}" }
];

const leadStore = useLeadCaptureStore();
const statuses = computed(() => leadStore.statuses);
const normalizePlanKey = (value: string | null | undefined) => {
  const key = String(value || "").trim().toLowerCase();
  if (!key) return "free";
  if (key === "escala" || key === "infinity" || key === "scale") return "scale";
  if (key === "teste" || key === "test") return "test";
  if (key === "growth" || key === "agency" || key === "agencia") return "agency";
  if (key === "essencial" || key === "professional" || key === "trial") return "professional";
  return key;
};
const hasWhatsAppPlanAccess = computed(() => {
  const trial = normalizePlanKey(auth.user?.trial_plan);
  const base = normalizePlanKey(auth.user?.plan);
  const allowed = new Set(["scale", "test", "infinity"]);
  return allowed.has(trial) || allowed.has(base);
});
const activeTab = ref<BuilderTab>("visual");
const messageEditorRef = ref<HTMLTextAreaElement | null>(null);
const delayValue = ref(0);
const delayUnit = ref<"s" | "min" | "h">("min");

const state = reactive<LeadFormPayload>({
  name: "",
  title: "",
  subtitle: "",
  buttonLabel: "Quero saber mais",
  buttonColor: "#3DCC5F",
  showLogo: false,
  fields: [],
  defaultStatusId: null,
  autoWhatsAppMessageTemplate: "Olá {{first_name}}, recebemos seu cadastro! Em breve entraremos em contato via WhatsApp.",
  autoWhatsAppDelaySeconds: 0,
  autoWhatsAppSkipIfClient: false,
  autoWhatsAppSkipIfFormAlreadySubmitted: false,
  autoWhatsAppSkipIfPageAlreadySubmitted: false,
  autoWhatsAppSkipIfOpenOpportunity: false
});

const editingId = ref<string | null>(null);
const errorMessage = ref("");
const title = computed(() => (editingId.value ? "Editar formulário" : "Novo formulário"));
const selectedTypes = computed(() => state.fields.map(field => field.type));
const greetingByHour = computed(() => {
  const hour = new Date().getHours();
  if (hour < 12) return "Bom dia";
  if (hour < 18) return "Boa tarde";
  return "Boa noite";
});

const renderedPreviewMessage = computed(() => {
  const base = String(state.autoWhatsAppMessageTemplate || "").trim() || "Olá {{first_name}}, recebemos seu cadastro!";
  return base
    .replaceAll("{{saudacao}}", greetingByHour.value)
    .replaceAll("{{nome}}", "João Silva")
    .replaceAll("{{first_name}}", "João")
    .replaceAll("{{primeiro_nome}}", "João")
    .replaceAll("{{telefone}}", "(11) 99999-9999")
    .replaceAll("{{email}}", "joao@email.com")
    .replaceAll("{{pagina}}", "Nome da página")
    .replaceAll("{{origem}}", "Nome da página")
    .replaceAll("{{formulario}}", state.name?.trim() || "Formulário")
    .replaceAll("{{cidade}}", "São Paulo");
});

const syncDelayFromSeconds = (seconds: number) => {
  const s = Math.max(0, Number(seconds || 0));
  if (s % 3600 === 0 && s !== 0) {
    delayUnit.value = "h";
    delayValue.value = s / 3600;
    return;
  }
  if (s % 60 === 0 && s !== 0) {
    delayUnit.value = "min";
    delayValue.value = s / 60;
    return;
  }
  delayUnit.value = "s";
  delayValue.value = s;
};

const syncSecondsFromDelay = () => {
  const val = Math.max(0, Number(delayValue.value || 0));
  if (delayUnit.value === "h") state.autoWhatsAppDelaySeconds = val * 3600;
  else if (delayUnit.value === "min") state.autoWhatsAppDelaySeconds = val * 60;
  else state.autoWhatsAppDelaySeconds = val;
};

const createFieldFromPreset = (type: LeadFieldType, value?: Partial<LeadFormField>): LeadFormField => {
  const preset = fieldPresets.find(item => item.type === type);
  return { id: value?.id || generateId(), type, label: preset?.label || value?.label || type, placeholder: preset?.placeholder || value?.placeholder || "", required: value?.required !== undefined ? value.required : true };
};

const toggleField = (type: LeadFieldType) => {
  const index = state.fields.findIndex(field => field.type === type);
  if (index >= 0) state.fields.splice(index, 1);
  else state.fields.push(createFieldFromPreset(type));
};

const resetState = () => {
  state.name = "";
  state.title = "";
  state.subtitle = "";
  state.buttonLabel = "Quero saber mais";
  state.buttonColor = "#3DCC5F";
  state.showLogo = false;
  state.fields = [];
  state.defaultStatusId = null;
  state.autoWhatsAppMessageTemplate = "Olá {{first_name}}, recebemos seu cadastro! Em breve entraremos em contato via WhatsApp.";
  state.autoWhatsAppDelaySeconds = 0;
  state.autoWhatsAppSkipIfClient = false;
  state.autoWhatsAppSkipIfFormAlreadySubmitted = false;
  state.autoWhatsAppSkipIfPageAlreadySubmitted = false;
  state.autoWhatsAppSkipIfOpenOpportunity = false;
  syncDelayFromSeconds(0);
  activeTab.value = "visual";
  editingId.value = null;
  errorMessage.value = "";
};

const hydrateFromForm = (form?: LeadForm | null) => {
  if (!form) return resetState();
  state.name = form.name || "";
  state.title = form.title || "";
  state.subtitle = form.subtitle || "";
  state.buttonLabel = form.buttonLabel || "Quero saber mais";
  state.buttonColor = form.buttonColor || "#3DCC5F";
  state.showLogo = form.showLogo === true;
  state.fields = (form.fields || []).map(field => createFieldFromPreset(field.type, field));
  state.defaultStatusId = form.defaultStatusId ? String(form.defaultStatusId) : null;
  state.autoWhatsAppMessageTemplate = form.autoWhatsAppMessageTemplate || "Olá {{first_name}}, recebemos seu cadastro! Em breve entraremos em contato via WhatsApp.";
  state.autoWhatsAppDelaySeconds = Number(form.autoWhatsAppDelaySeconds || 0);
  state.autoWhatsAppSkipIfClient = Boolean(form.autoWhatsAppSkipIfClient);
  state.autoWhatsAppSkipIfFormAlreadySubmitted = Boolean(form.autoWhatsAppSkipIfFormAlreadySubmitted);
  state.autoWhatsAppSkipIfPageAlreadySubmitted = Boolean(form.autoWhatsAppSkipIfPageAlreadySubmitted);
  state.autoWhatsAppSkipIfOpenOpportunity = Boolean(form.autoWhatsAppSkipIfOpenOpportunity);
  syncDelayFromSeconds(state.autoWhatsAppDelaySeconds || 0);
  activeTab.value = "visual";
  editingId.value = String(form.id);
  errorMessage.value = "";
};

const close = () => emit("update:modelValue", false);
const onOverlayClick = (event: MouseEvent) => { if (event.target === event.currentTarget) close(); };

const validate = () => {
  syncSecondsFromDelay();
  if (!state.name.trim()) return (errorMessage.value = "Defina um nome para o formulário."), false;
  if (!state.title.trim()) return (errorMessage.value = "Informe o título do formulário."), false;
  if (!state.fields.length) return (errorMessage.value = "Selecione pelo menos um campo."), false;
  const hasName = state.fields.some(field => field.type === "name");
  const hasPhone = state.fields.some(field => field.type === "phone");
  const hasEmail = state.fields.some(field => field.type === "email");
  if (!hasName || (!hasPhone && !hasEmail)) {
    return (
      errorMessage.value = "O formulário precisa ter Nome + E-mail ou Nome + Telefone.",
      false
    );
  }
  errorMessage.value = "";
  return true;
};

const buildPayload = (): LeadFormPayload => ({
  name: state.name.trim(),
  title: state.title.trim(),
  subtitle: state.subtitle?.trim() || "",
  buttonLabel: state.buttonLabel?.trim() || "Quero saber mais",
  buttonColor: state.buttonColor?.trim() || "#3DCC5F",
  showLogo: state.showLogo === true,
  fields: state.fields.map(field => ({ ...field })),
  defaultStatusId: state.defaultStatusId || null,
  autoWhatsAppMessageTemplate: state.autoWhatsAppMessageTemplate?.trim() || null,
  autoWhatsAppDelaySeconds: Number(state.autoWhatsAppDelaySeconds || 0),
  autoWhatsAppSkipIfClient: Boolean(state.autoWhatsAppSkipIfClient),
  autoWhatsAppSkipIfFormAlreadySubmitted: Boolean(state.autoWhatsAppSkipIfFormAlreadySubmitted),
  autoWhatsAppSkipIfPageAlreadySubmitted: Boolean(state.autoWhatsAppSkipIfPageAlreadySubmitted),
  autoWhatsAppSkipIfOpenOpportunity: Boolean(state.autoWhatsAppSkipIfOpenOpportunity)
});

const handleSubmit = () => {
  if (!validate()) {
    emit("invalid", errorMessage.value || "Dados inválidos do formulário.");
    return;
  }
  emit("save", { id: editingId.value, form: buildPayload() });
};

const insertToken = (tokenValue: string) => {
  const editor = messageEditorRef.value;
  if (!editor) return;
  const start = editor.selectionStart ?? editor.value.length;
  const end = editor.selectionEnd ?? editor.value.length;
  const text = String(state.autoWhatsAppMessageTemplate || "");
  state.autoWhatsAppMessageTemplate = `${text.slice(0, start)}${tokenValue}${text.slice(end)}`;
  requestAnimationFrame(() => {
    editor.focus();
    editor.selectionStart = editor.selectionEnd = start + tokenValue.length;
  });
};

const goToPlans = () => {
  router.push("/admin/planos");
};

watch([delayValue, delayUnit], () => syncSecondsFromDelay());

watch(
  () => props.modelValue,
  open => {
    document.body.style.overflow = open ? "hidden" : "";
    if (open) {
      leadStore.fetchStatuses().catch(() => undefined);
      hydrateFromForm(props.form || null);
    } else {
      resetState();
    }
  },
  { immediate: true }
);

watch(() => props.form, form => { if (props.modelValue) hydrateFromForm(form || null); });

onUnmounted(() => { document.body.style.overflow = ""; });
</script>

<style scoped>
.fade-enter-active,.fade-leave-active{transition:opacity .18s ease}.fade-enter-from,.fade-leave-to{opacity:0}
.fm-ov{position:fixed;inset:0;background:rgba(17,26,20,.52);z-index:500;display:flex;align-items:center;justify-content:center;padding:20px}
.fm-modal{background:#fff;border-radius:16px;width:100%;max-width:940px;max-height:90vh;display:flex;flex-direction:column;box-shadow:0 24px 64px rgba(0,0,0,.2);overflow:hidden}
.fm-hd{padding:22px 26px 0;flex-shrink:0}.fm-hd-top{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px}
.fm-ey{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#8a9e8a;margin-bottom:3px}.fm-title{font-size:20px;font-weight:800;color:#111a14;letter-spacing:-.3px}.fm-sub-txt{font-size:13px;color:#8a9e8a;margin-top:2px}
.fm-close{width:32px;height:32px;border-radius:8px;background:#f5f7f5;border:1.5px solid #e4e9e4;display:flex;align-items:center;justify-content:center;cursor:pointer}
.fm-close svg{width:13px;height:13px;stroke:#8a9e8a;fill:none;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}
.fm-tabs{display:flex;border-bottom:1.5px solid #e4e9e4;padding:0 2px}.fm-tab-btn{padding:11px 18px;border:none;background:transparent;border-bottom:2.5px solid transparent;font-size:13px;font-weight:600;color:#8a9e8a;cursor:pointer;display:flex;align-items:center;gap:6px;margin-bottom:-1.5px}
.fm-tab-btn svg{width:13px;height:13px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}.fm-tab-btn.on{color:#2ead4c;border-bottom-color:#2ead4c;font-weight:700}
.fm-body{overflow-y:auto;flex:1;min-height:0}.fm-pane{padding:22px 26px 28px;gap:24px;display:flex}.fm-pane-col{flex-direction:column!important}
.fm-row{display:flex;flex-direction:column;gap:5px}.fm-lbl{font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#8a9e8a;display:block}
.fm-inp{padding:9px 11px;border:1.5px solid #e4e9e4;border-radius:8px;font-size:13px;color:#111a14;outline:none;width:100%;background:#fff}.fm-hint{font-size:11px;color:#8a9e8a;margin-top:2px;line-height:1.5}
.fm-grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}.fm-sel{padding:9px 30px 9px 11px;border:1.5px solid #e4e9e4;border-radius:8px;font-size:13px;color:#4a5e4a;outline:none;background:#fff;width:100%}
.fm-check-row{display:flex;align-items:flex-start;gap:10px;padding:10px 14px;border:1.5px solid #e4e9e4;border-radius:8px;cursor:pointer;background:#fff;max-width:340px}.fm-check-row input{width:15px;height:15px;accent-color:#3DCC5F;margin-top:2px}
.fm-check-lbl{font-size:13px;font-weight:600;color:#111a14}.fm-check-hint{font-size:11px;color:#8a9e8a;margin-top:2px}
.fm-check-row-inline{align-items:center;height:40px;padding:0 12px;max-width:none}.fm-check-row-inline input{margin-top:0}
.fm-left{flex:1;min-width:0;display:flex;flex-direction:column;gap:14px}.fm-right{width:270px;flex-shrink:0}
.fmf-sec-lbl{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#8a9e8a;margin-bottom:10px}.fmf-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.fmf-chip{display:flex;align-items:center;gap:9px;padding:10px 12px;border:1.5px solid #e4e9e4;border-radius:10px;cursor:pointer;background:#fff}.fmf-chip.on{background:rgba(61,204,95,.1);border-color:rgba(61,204,95,.22)}
.fmf-chip-ic{width:28px;height:28px;border-radius:7px;background:#f5f7f5;display:flex;align-items:center;justify-content:center;flex-shrink:0}.fmf-chip-ic svg{width:13px;height:13px;fill:none;stroke:#8a9e8a;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.fmf-chip.on .fmf-chip-ic{background:rgba(61,204,95,.18)}.fmf-chip.on .fmf-chip-ic svg{stroke:#1A7A35}.fmf-name{flex:1;font-size:12px;font-weight:600;color:#4a5e4a}.fmf-chip.on .fmf-name{color:#1A7A35}
.fmf-chk{width:16px;height:16px;border-radius:4px;border:1.5px solid #e4e9e4;flex-shrink:0;display:flex;align-items:center;justify-content:center}.fmf-chip.on .fmf-chk{background:#3DCC5F;border-color:#2ead4c}.fmf-chip.on .fmf-chk::after{content:'';display:block;width:7px;height:4px;border-left:2px solid #0F1F14;border-bottom:2px solid #0F1F14;transform:rotate(-45deg) translate(1px,-1px)}
.fmf-sel-note{font-size:12px;color:#8a9e8a;margin-top:6px}
.fmn-left{flex:1;min-width:0;display:flex;flex-direction:column;gap:16px}.fmn-right{width:250px;flex-shrink:0}
.fmn-plan-gate{min-height:360px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:12px;padding:24px;margin:auto}
.fmn-plan-gate-title{font-size:22px;font-weight:800;color:#111a14;letter-spacing:-.02em}
.fmn-plan-gate-text{max-width:540px;font-size:14px;color:#64748b;line-height:1.5}
.fmn-vars{display:flex;flex-wrap:wrap;gap:5px}.fmn-var{padding:2px 8px;border-radius:5px;font-size:10px;font-weight:700;background:rgba(99,102,241,.08);color:#4338CA;border:1.5px solid rgba(99,102,241,.18);cursor:pointer;font-family:monospace}
.fm-ta{min-height:110px;resize:vertical;line-height:1.5}
.fmn-delay-row{display:flex;align-items:center;gap:8px}.fmn-delay-inp{width:72px;padding:9px 10px;border:1.5px solid #e4e9e4;border-radius:8px;font-size:13px;text-align:center}.fmn-delay-sel{padding:9px 30px 9px 10px;border:1.5px solid #e4e9e4;border-radius:8px;font-size:13px}.fmn-delay-lbl{font-size:13px;color:#8a9e8a}
.fmn-sw-block{background:#fff;border:1.5px solid #e4e9e4;border-radius:12px;overflow:hidden}.fmn-sw-row{display:flex;align-items:center;gap:14px;padding:12px 16px;border-bottom:1px solid #e4e9e4}.fmn-sw-row:last-child{border-bottom:none}
.fmn-sw-txt{flex:1}.fmn-sw-lbl{font-size:13px;font-weight:600;color:#111a14}.fmn-sw-hint{font-size:11px;color:#8a9e8a}
.fmn-toggle{position:relative;width:38px;height:22px;flex-shrink:0}.fmn-toggle input{opacity:0;width:0;height:0;position:absolute}.fmn-track{position:absolute;inset:0;background:#cdd8cd;border-radius:999px;transition:.2s;cursor:pointer}.fmn-toggle input:checked+.fmn-track{background:#3DCC5F}.fmn-track::after{content:'';position:absolute;width:16px;height:16px;background:#fff;border-radius:50%;left:3px;top:3px;transition:.2s;box-shadow:0 1px 3px rgba(0,0,0,.2)}.fmn-toggle input:checked+.fmn-track::after{left:19px}
.fmn-wapp{border-radius:14px;overflow:hidden;border:1.5px solid #e4e9e4;box-shadow:0 4px 16px rgba(0,0,0,.08);display:flex;flex-direction:column;min-height:480px}.fmn-wapp-bar{background:#075E54;padding:10px 14px;display:flex;align-items:center;gap:10px}.fmn-wapp-av{width:32px;height:32px;border-radius:50%;background:#128C7E;display:flex;align-items:center;justify-content:center}.fmn-wapp-av svg{fill:#fff}
.fmn-wapp-name{font-size:13px;font-weight:700;color:#fff}.fmn-wapp-status{font-size:10px;color:rgba(255,255,255,.65)}.fmn-wapp-body{background:#E5DDD5;padding:12px;min-height:100px;flex:1;display:flex;align-items:flex-start}.fmn-bubble{background:#fff;border-radius:0 10px 10px 10px;padding:10px 12px;font-size:12px;color:#111;line-height:1.55;white-space:pre-wrap;width:92%}.fmn-bubble-time{font-size:10px;color:rgba(0,0,0,.38);text-align:right;margin-top:5px}.fmn-wapp-ibar{background:#f0f0f0;padding:8px 10px;border-top:1px solid rgba(0,0,0,.08)}.fmn-wapp-fake-inp{background:#fff;border-radius:20px;padding:6px 12px;font-size:11px;color:#8a9e8a}
.fm-foot{padding:14px 26px;border-top:1.5px solid #e4e9e4;display:flex;align-items:center;justify-content:space-between;background:#fff}.fm-foot-left{font-size:12px;color:#8a9e8a}
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:9px;font-size:13px;font-weight:700;cursor:pointer;border:none}.btn svg{width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:2.5}.btn-p{background:#3DCC5F;color:#0F1F14}.btn-o{background:#fff;color:#4A5E4A;border:1.5px solid #E4E9E4}.btn-sm{padding:6px 12px;font-size:12px}
@media(max-width:980px){.fm-modal{max-width:98vw;max-height:95vh}.fm-pane{flex-direction:column}.fm-right,.fmn-right{width:100%}.fm-grid3{grid-template-columns:1fr}.fmf-grid{grid-template-columns:1fr 1fr}}
</style>
