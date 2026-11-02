<template>
  <main class="admin-master-surface am-page w-full platform-brand">
    <AdminMasterHeader
      :title="tab === 'brand' ? 'Marca e SEO' : 'E-mails do sistema'"
      :subtitle="
        tab === 'brand'
          ? 'Logo, favicon e como o Roteiro Online aparece no Google e nos links compartilhados.'
          : 'Textos dos e-mails automáticos: boas-vindas, convite de equipe e redefinição de senha.'
      "
    >
      <button v-if="tab === 'brand'" type="button" class="am-btn am-btn-primary" :disabled="saving || !brandDirty" @click="saveBrand">
        {{ saving ? "Salvando…" : "Salvar alterações" }}
      </button>
      <button v-else type="button" class="am-btn am-btn-primary" :disabled="saving || !emailsDirty" @click="saveEmails">
        {{ saving ? "Salvando…" : "Salvar alterações" }}
      </button>
    </AdminMasterHeader>

    <div v-if="error" class="am-notice am-tone-danger" role="alert"><AmIcon name="alert" /><span>{{ error }}</span></div>
    <div v-if="message" class="am-notice am-tone-success" role="status"><AmIcon name="check" /><span>{{ message }}</span></div>

    <section class="am-card am-card-flush">
      <nav class="am-tabs px-2.5" aria-label="Seções da plataforma">
        <RouterLink to="/admin/administracao/marca" class="am-tab" :class="{ on: tab === 'brand' }">Marca e SEO</RouterLink>
        <RouterLink to="/admin/administracao/emails-sistema" class="am-tab" :class="{ on: tab === 'emails' }">E-mails do sistema</RouterLink>
      </nav>

      <!-- Marca e SEO -->
      <div v-if="tab === 'brand'" class="tab-body">
        <div v-if="!brand" class="am-empty"><span class="am-spinner"></span>Carregando…</div>
        <template v-else>
          <h2 class="am-card-title">Imagens</h2>
          <p class="hint mb-3">PNG, JPG, WebP ou ICO, até 5 MB. Sem imagem enviada, vale a do Roteiro Online de hoje.</p>
          <div class="image-grid">
            <div v-for="slot in imageSlots" :key="slot.field" class="image-slot">
              <div class="image-preview" :class="slot.dark ? 'dark' : slot.green ? 'green' : ''">
                <img :src="brandForm[slot.field] || slot.fallback" :alt="slot.label" />
              </div>
              <p class="slot-title">{{ slot.label }}</p>
              <p class="hint">{{ slot.hint }}</p>
              <div class="flex flex-wrap items-center gap-2 mt-2">
                <label class="am-btn am-btn-sm cursor-pointer">
                  <AmIcon name="upload" />{{ uploading === slot.field ? "Enviando…" : "Enviar imagem" }}
                  <input type="file" accept="image/png,image/jpeg,image/webp,image/x-icon" class="sr-only" :disabled="uploading !== null" @change="upload(slot.field, $event)" />
                </label>
                <button v-if="brandForm[slot.field]" type="button" class="link" @click="brandForm[slot.field] = null">Voltar ao padrão</button>
                <span v-if="brandForm[slot.field] && brandForm[slot.field] !== brand[slot.field]" class="am-badge am-tone-warning">Não salvo</span>
              </div>
            </div>
          </div>

          <h2 class="am-card-title mt-7">Google e links compartilhados</h2>
          <p class="hint mb-3">Vale para as telas do Roteiro Online (login, painel, checkout). As páginas das agências seguem com o título e a imagem de cada página.</p>
          <div class="am-grid-2">
            <div class="space-y-3">
              <div class="am-field">
                <label for="pb-title">Título do site</label>
                <input id="pb-title" v-model="brandForm.site_title" class="am-input" maxlength="120" :placeholder="brand.defaults.site_title" />
              </div>
              <div class="am-field">
                <label for="pb-desc">Descrição</label>
                <textarea id="pb-desc" v-model="brandForm.site_description" class="am-input" rows="3" maxlength="300" :placeholder="brand.defaults.site_description"></textarea>
                <p class="hint mt-1">{{ (brandForm.site_description || "").length }}/300 · o Google mostra cerca de 155 caracteres.</p>
              </div>
              <div class="am-field">
                <label for="pb-color">Cor da barra do navegador no celular</label>
                <div class="flex items-center gap-2">
                  <input id="pb-color-picker" v-model="colorPicker" type="color" class="color-input" aria-label="Escolher cor" />
                  <input id="pb-color" v-model="brandForm.theme_color" class="am-input" style="max-width: 140px" :placeholder="brand.defaults.theme_color" />
                </div>
              </div>
            </div>
            <div>
              <p class="am-label">Prévia no Google</p>
              <div class="serp">
                <p class="serp-url">roteiroonline.com</p>
                <p class="serp-title">{{ brandForm.site_title || brand.defaults.site_title }}</p>
                <p class="serp-desc">{{ brandForm.site_description || brand.defaults.site_description }}</p>
              </div>
              <p class="am-label mt-4">Prévia do link no WhatsApp</p>
              <div class="share-card">
                <img v-if="brandForm.share_image_url" :src="brandForm.share_image_url" alt="" />
                <div v-else class="share-empty">Sem imagem de compartilhamento</div>
                <div class="share-text">
                  <b>{{ brandForm.site_title || brand.defaults.site_title }}</b>
                  <span>{{ brandForm.site_description || brand.defaults.site_description }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- E-mails do sistema -->
      <div v-else class="emails-layout">
        <div v-if="!emails" class="am-empty"><span class="am-spinner"></span>Carregando…</div>
        <template v-else>
          <aside class="email-list" aria-label="E-mails">
            <button v-for="item in emails.items" :key="item.key" type="button" class="email-item" :class="{ on: selected === item.key }" @click="selected = item.key">
              <span class="email-name">{{ item.label }}</span>
              <span class="hint">{{ item.description }}</span>
              <span v-if="isCustom(item.key)" class="am-badge am-tone-violet mt-1 self-start">Texto próprio</span>
            </button>
            <p class="hint p-3">Os e-mails de cobrança ficam em Receita › Avisos de cobrança.</p>
          </aside>

          <div v-if="current" class="email-editor space-y-4">
            <div v-if="!emails.email_configured" class="am-notice am-tone-warning"><AmIcon name="alert" /><span>O envio de e-mail (SMTP) não está configurado no servidor: os e-mails não saem.</span></div>
            <div class="variables">
              <span class="hint">Variáveis (entram no campo em que você clicou por último):</span>
              <button v-for="variable in current.variables" :key="variable.key" type="button" class="am-chip" :title="variable.label" @click="insertVariable(variable.key)">
                {{ varToken(variable.key) }}
              </button>
            </div>
            <div class="am-grid-2">
              <div class="space-y-3">
                <div v-for="field in emailFields" :key="field.id" class="am-field">
                  <label :for="`pe-${field.id}`">{{ field.label }}</label>
                  <textarea
                    v-if="field.multiline"
                    :id="`pe-${field.id}`"
                    v-model="forms[current.key][field.id]"
                    class="am-input"
                    :rows="field.rows"
                    @focus="focusField($event, field.id)"
                  ></textarea>
                  <input v-else :id="`pe-${field.id}`" v-model="forms[current.key][field.id]" class="am-input" @focus="focusField($event, field.id)" />
                </div>
                <p class="hint">*texto* fica em negrito; uma linha em branco no texto abre um parágrafo novo. O link do botão entra sozinho.</p>
                <button type="button" class="am-btn am-btn-sm" :disabled="!isCustom(current.key)" @click="restoreDefault(current.key)">
                  <AmIcon name="undo" />Restaurar texto padrão
                </button>
              </div>
              <div class="space-y-3">
                <p class="am-label">Prévia com dados de exemplo</p>
                <p class="preview-subject"><span class="hint">Assunto:</span> {{ preview?.subject || "…" }}</p>
                <iframe class="preview-frame" title="Prévia do e-mail" sandbox="" :srcdoc="preview?.html || ''"></iframe>
                <div class="test-box">
                  <p class="am-label">Enviar teste</p>
                  <p class="hint">Usa os textos salvos. Salve antes de testar uma mudança.</p>
                  <div class="flex flex-wrap gap-2 mt-2">
                    <input v-model="testTo" class="am-input flex-1 min-w-[180px]" type="email" placeholder="E-mail" aria-label="E-mail para o teste" />
                    <button type="button" class="am-btn" :disabled="testing || !testTo.includes('@') || emailsDirty" @click="sendTest">
                      {{ testing ? "Enviando…" : "Enviar teste" }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import api from "../../services/api";
import AmIcon from "../../components/admin/master/AmIcon.vue";
import AdminMasterHeader from "../../components/admin/master/AdminMasterHeader.vue";
import { defaultBrandAssets, setPlatformBranding } from "../../composables/usePlatformBranding";

type ImageField = "logo_url" | "logo_dark_url" | "favicon_url" | "email_logo_url" | "share_image_url";
type Brand = Record<ImageField, string | null> & {
  site_title: string | null;
  site_description: string | null;
  theme_color: string | null;
  defaults: { site_title: string; site_description: string; theme_color: string };
};
type EmailFieldId = "subject" | "eyebrow" | "title" | "body" | "button_label" | "note";
type EmailItem = {
  key: string;
  label: string;
  description: string;
  variables: { key: string; label: string }[];
  texts: Record<EmailFieldId, string>;
  defaults: Record<EmailFieldId, string>;
  custom_fields: string[];
};

const route = useRoute();
const tab = computed(() => (route.path.endsWith("/emails-sistema") ? "emails" : "brand"));
const error = ref("");
const message = ref("");
const saving = ref(false);
const detail = (e: any, fallback: string) => (typeof e?.response?.data?.detail === "string" ? e.response.data.detail : fallback);
function flash(text: string) {
  message.value = text;
  error.value = "";
  window.setTimeout(() => {
    if (message.value === text) message.value = "";
  }, 5000);
}

// ---------------------------------------------------------------- marca

const imageSlots: { field: ImageField; label: string; hint: string; fallback: string; dark?: boolean; green?: boolean }[] = [
  { field: "logo_url", label: "Logo colorido", hint: "Para fundo claro: menu no tema claro e checkout claro.", fallback: defaultBrandAssets.logoColor },
  { field: "logo_dark_url", label: "Logo branco", hint: "Para fundo escuro: login, menu no tema escuro e checkout escuro.", fallback: defaultBrandAssets.logoWhite, dark: true },
  { field: "favicon_url", label: "Favicon e ícone", hint: "Aba do navegador e menu recolhido. Quadrado, de 64 a 512 px.", fallback: defaultBrandAssets.favicon },
  { field: "email_logo_url", label: "Logo dos e-mails", hint: "Fica na faixa verde do topo dos e-mails. PNG, de preferência.", fallback: "/email/logo-roteiro-online.png", green: true },
  { field: "share_image_url", label: "Imagem de compartilhamento", hint: "Aparece quando alguém manda o link no WhatsApp ou nas redes. 1200 × 630 px.", fallback: "" }
];
const brand = ref<Brand | null>(null);
const brandForm = reactive<Record<string, string | null>>({});
const brandKeys = ["logo_url", "logo_dark_url", "favicon_url", "email_logo_url", "share_image_url", "site_title", "site_description", "theme_color"];
const brandSaved = ref("");
const brandDirty = computed(() => Boolean(brand.value) && JSON.stringify(brandKeys.map(k => brandForm[k] || null)) !== brandSaved.value);
const uploading = ref<ImageField | null>(null);
const colorPicker = computed({
  get: () => (/^#[0-9a-fA-F]{6}$/.test(brandForm.theme_color || "") ? (brandForm.theme_color as string) : brand.value?.defaults.theme_color || "#12B981"),
  set: value => {
    brandForm.theme_color = value;
  }
});

function applyBrand(data: Brand) {
  brand.value = data;
  for (const key of brandKeys) brandForm[key] = (data as any)[key] || null;
  brandSaved.value = JSON.stringify(brandKeys.map(k => brandForm[k] || null));
  setPlatformBranding({
    logo_url: data.logo_url,
    logo_dark_url: data.logo_dark_url,
    favicon_url: data.favicon_url,
    share_image_url: data.share_image_url,
    site_title: data.site_title || data.defaults.site_title,
    site_description: data.site_description || data.defaults.site_description,
    theme_color: data.theme_color || data.defaults.theme_color
  });
}

async function loadBrand() {
  try {
    const { data } = await api.get<Brand>("/admin/platform/branding");
    applyBrand(data);
  } catch (e) {
    error.value = detail(e, "Não foi possível carregar a marca.");
  }
}

async function saveBrand() {
  saving.value = true;
  try {
    const payload: Record<string, string | null> = {};
    for (const key of brandKeys) payload[key] = (brandForm[key] || "").trim() || null;
    const { data } = await api.put<Brand>("/admin/platform/branding", payload);
    applyBrand(data);
    flash("Marca salva. Pode levar até 1 minuto para aparecer em todas as telas.");
  } catch (e) {
    error.value = detail(e, "Não foi possível salvar.");
  } finally {
    saving.value = false;
  }
}

async function upload(field: ImageField, event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  if (brandDirty.value && !window.confirm("O envio salva só a imagem. As outras alterações não salvas continuam na tela. Enviar?")) return;
  uploading.value = field;
  try {
    const body = new FormData();
    body.append("file", file);
    const { data } = await api.post<Brand>("/admin/platform/branding/upload", body, { params: { field } });
    const pending: Record<string, string | null> = {};
    for (const key of brandKeys) pending[key] = brandForm[key];
    applyBrand(data);
    for (const key of brandKeys) if (key !== field) brandForm[key] = pending[key];
    flash("Imagem enviada e salva.");
  } catch (e) {
    error.value = detail(e, "Não foi possível enviar a imagem.");
  } finally {
    uploading.value = null;
  }
}

// ---------------------------------------------------------------- e-mails

const emailFields: { id: EmailFieldId; label: string; multiline?: boolean; rows?: number }[] = [
  { id: "subject", label: "Assunto" },
  { id: "eyebrow", label: "Linha acima do título" },
  { id: "title", label: "Título" },
  { id: "body", label: "Texto", multiline: true, rows: 6 },
  { id: "button_label", label: "Texto do botão" },
  { id: "note", label: "Rodapé do cartão", multiline: true, rows: 3 }
];
const emails = ref<{ items: EmailItem[]; email_configured: boolean } | null>(null);
const forms = reactive<Record<string, Record<EmailFieldId, string>>>({});
const emailsSaved = ref("");
const emailsDirty = computed(() => Boolean(emails.value) && JSON.stringify(forms) !== emailsSaved.value);
const selected = ref("");
const current = computed(() => emails.value?.items.find(item => item.key === selected.value) || null);
const lastField = ref<{ id: EmailFieldId; el: HTMLInputElement | HTMLTextAreaElement } | null>(null);
const varToken = (key: string) => ["{", "{", key, "}", "}"].join("");

function applyEmails(data: { items: EmailItem[]; email_configured: boolean }) {
  emails.value = data;
  for (const item of data.items) forms[item.key] = { ...item.texts };
  emailsSaved.value = JSON.stringify(forms);
  if (!selected.value && data.items.length) selected.value = data.items[0].key;
}

async function loadEmails() {
  try {
    const { data } = await api.get("/admin/platform/emails");
    applyEmails(data);
  } catch (e) {
    error.value = detail(e, "Não foi possível carregar os e-mails.");
  }
}

async function saveEmails() {
  saving.value = true;
  try {
    const { data } = await api.put("/admin/platform/emails", { templates: forms });
    applyEmails(data);
    flash("E-mails salvos. Os próximos envios já usam os textos novos.");
  } catch (e) {
    error.value = detail(e, "Não foi possível salvar.");
  } finally {
    saving.value = false;
  }
}

function isCustom(key: string) {
  const item = emails.value?.items.find(i => i.key === key);
  const form = forms[key];
  if (!item || !form) return false;
  return emailFields.some(field => (form[field.id] || "").trim() !== item.defaults[field.id]);
}

function restoreDefault(key: string) {
  const item = emails.value?.items.find(i => i.key === key);
  if (item) forms[key] = { ...item.defaults };
}

function focusField(event: FocusEvent, id: EmailFieldId) {
  lastField.value = { id, el: event.target as HTMLInputElement | HTMLTextAreaElement };
}

function insertVariable(variable: string) {
  const key = selected.value;
  const target = lastField.value || { id: "body" as EmailFieldId, el: null as any };
  const token = varToken(variable);
  const value = forms[key][target.id] || "";
  const start = target.el?.selectionStart ?? value.length;
  const end = target.el?.selectionEnd ?? value.length;
  forms[key][target.id] = value.slice(0, start) + token + value.slice(end);
  requestAnimationFrame(() => {
    target.el?.focus();
    target.el?.setSelectionRange(start + token.length, start + token.length);
  });
}

const preview = ref<{ subject: string; html: string } | null>(null);
let previewTimer: number | undefined;
async function loadPreview() {
  if (!current.value) return;
  try {
    const { data } = await api.post("/admin/platform/emails/preview", { key: current.value.key, texts: forms[current.value.key] });
    preview.value = data;
  } catch {
    preview.value = null;
  }
}
watch(
  () => [selected.value, JSON.stringify(forms[selected.value] || {})],
  () => {
    window.clearTimeout(previewTimer);
    previewTimer = window.setTimeout(loadPreview, 350);
  }
);

const testTo = ref("");
const testing = ref(false);
async function sendTest() {
  testing.value = true;
  try {
    await api.post("/admin/platform/emails/test", { key: selected.value, to: testTo.value.trim() });
    flash("Teste enviado.");
  } catch (e) {
    error.value = detail(e, "O teste não saiu.");
  } finally {
    testing.value = false;
  }
}

onMounted(() => {
  loadBrand();
  loadEmails();
});
</script>

<style scoped>
.tab-body {
  padding: 18px;
}
.hint {
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--muted-foreground);
}
.link {
  color: var(--primary);
  font-size: 12.5px;
  font-weight: 600;
}
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 14px;
}
.image-slot {
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 14px;
}
.image-preview {
  display: grid;
  place-items: center;
  height: 110px;
  margin-bottom: 10px;
  border-radius: 10px;
  background: repeating-conic-gradient(var(--muted) 0% 25%, var(--card) 0% 50%) 50% / 16px 16px;
  overflow: hidden;
}
.image-preview.dark {
  background: #0a110e;
}
.image-preview.green {
  background: #41ce5f;
}
.image-preview img {
  max-width: 85%;
  max-height: 80px;
  object-fit: contain;
}
.image-preview img[src=""] {
  display: none;
}
.slot-title {
  font-size: 13.5px;
  font-weight: 600;
}
.color-input {
  width: 42px;
  height: 38px;
  padding: 2px;
  border: 1px solid var(--input);
  border-radius: 10px;
  background: var(--background);
}
.serp {
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--card);
}
.serp-url {
  font-size: 12px;
  color: var(--muted-foreground);
}
.serp-title {
  margin-top: 2px;
  font-size: 17px;
  color: #1a0dab;
  overflow-wrap: anywhere;
}
:global(.dark) .serp-title {
  color: #8ab4f8;
}
.serp-desc {
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--muted-foreground);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.share-card {
  max-width: 360px;
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--card);
}
.share-card img {
  width: 100%;
  aspect-ratio: 1200 / 630;
  object-fit: cover;
}
.share-empty {
  display: grid;
  place-items: center;
  aspect-ratio: 1200 / 630;
  background: var(--muted);
  font-size: 12.5px;
  color: var(--muted-foreground);
}
.share-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  font-size: 12.5px;
}
.share-text span {
  color: var(--muted-foreground);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.emails-layout {
  display: grid;
  grid-template-columns: minmax(0, 260px) minmax(0, 1fr);
}
.email-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  border-right: 1px solid var(--border);
}
.email-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 12px;
  border-radius: 12px;
  text-align: left;
}
.email-item:hover {
  background: var(--muted);
}
.email-item.on {
  background: var(--accent);
  color: var(--accent-foreground);
}
.email-name {
  font-size: 13.5px;
  font-weight: 600;
}
.email-editor {
  min-width: 0;
  padding: 18px;
}
.variables {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.preview-subject {
  font-size: 13px;
  font-weight: 600;
  overflow-wrap: anywhere;
}
.preview-frame {
  width: 100%;
  height: 560px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: #eef2ee;
}
.test-box {
  padding: 14px 16px;
  border: 1px dashed var(--border);
  border-radius: 14px;
}
@media (max-width: 900px) {
  .emails-layout {
    grid-template-columns: minmax(0, 1fr);
  }
  .email-list {
    border-right: 0;
    border-bottom: 1px solid var(--border);
  }
}
</style>
