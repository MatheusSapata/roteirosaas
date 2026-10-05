<template>
  <div v-if="isBootstrappingAgencySettings" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8 md:px-8">
    <div class="h-10 w-10 animate-spin rounded-full border-4 border-border border-t-primary"></div>
  </div>
  <div v-else class="agency-settings page-wrap">
    <AgencyHeader />

    <form ref="formRef" class="as-form" @submit.prevent="save">
      <section class="as-card">
        <header class="as-card-head">
          <p class="as-eyebrow">Identidade</p>
          <h2>Dados principais</h2>
          <p>Nome, link e cor que aparecem nas suas páginas.</p>
        </header>
        <div class="as-row">
          <div class="as-row-label">
            <p>Nome da agência</p>
            <span>Aparece no topo e no rodapé das páginas.</span>
          </div>
          <div class="as-row-field">
            <input v-model="form.name" class="as-input" />
          </div>
        </div>
        <div class="as-row">
          <div class="as-row-label">
            <p>Link da agência</p>
            <span>Sem espaços nem acentos, até 30 caracteres.</span>
          </div>
          <div class="as-row-field as-col">
            <div class="as-input as-group">
              <span class="as-prefix">roteiroonline.com/</span>
              <input :value="form.slug" maxlength="30" @input="handleSlugInput" />
            </div>
            <span class="as-hint">Suas páginas ficam em roteiroonline.com/{{ form.slug || "sua-agencia" }}/nome-da-pagina</span>
          </div>
        </div>
        <div class="as-row">
          <div class="as-row-label">
            <p>Cor principal</p>
            <span>Base dos botões das páginas. Dá para ajustar em cada página.</span>
          </div>
          <div class="as-row-field">
            <label class="as-input as-color">
              <span class="as-swatch" :style="{ background: form.primary_color }">
                <input v-model="form.primary_color" type="color" aria-label="Escolher cor" />
              </span>
              <input v-model="form.primary_color" class="as-color-text" />
            </label>
            <span class="as-preview-btn" :style="{ background: form.primary_color }">Quero reservar</span>
            <span class="as-hint">Prévia do botão</span>
          </div>
        </div>
      </section>

      <section class="as-card">
        <header class="as-card-head">
          <p class="as-eyebrow">Contato</p>
          <h2>Informações de contato</h2>
          <p>Aparecem no rodapé das páginas e nos botões de WhatsApp.</p>
        </header>
        <div class="as-row">
          <div class="as-row-label">
            <p>CNPJ ou CPF</p>
            <span>Do responsável pela agência.</span>
          </div>
          <div class="as-row-field">
            <select v-model="companyForm.documentType" class="as-input as-select">
              <option value="cnpj">{{ viewCopy.company.documentTypeCnpj }}</option>
              <option value="cpf">{{ viewCopy.company.documentTypeCpf }}</option>
            </select>
            <input v-model="companyForm.cnpj" class="as-input" :placeholder="companyDocumentPlaceholder" />
          </div>
        </div>
        <div class="as-row">
          <div class="as-row-label">
            <p>WhatsApp</p>
            <span>Número padrão dos botões de WhatsApp.</span>
          </div>
          <div class="as-row-field as-col">
            <div class="as-input as-group">
              <span class="as-prefix">BR +55</span>
              <input v-model="phoneInput" :placeholder="viewCopy.contact.whatsappPlaceholder" inputmode="numeric" />
            </div>
            <span v-if="phoneMessage" class="as-ok">{{ phoneMessage }}</span>
            <span v-if="phoneError" class="as-err">{{ phoneError }}</span>
          </div>
        </div>
        <div class="as-row">
          <div class="as-row-label">
            <p>E-mail</p>
            <span>Aparece no rodapé das páginas.</span>
          </div>
          <div class="as-row-field">
            <input v-model="form.contact_email" type="email" class="as-input" :placeholder="viewCopy.contact.emailPlaceholder" />
          </div>
        </div>
      </section>

      <section class="as-card">
        <header class="as-card-head">
          <p class="as-eyebrow">Localização</p>
          <h2>Endereço</h2>
          <p>Informe o CEP e completamos o resto.</p>
        </header>
        <div class="as-row">
          <div class="as-row-label">
            <p>CEP</p>
            <span>Preenche rua, bairro, cidade e UF.</span>
          </div>
          <div class="as-row-field as-col">
            <input v-model="companyForm.address_zipcode" class="as-input as-short" :disabled="isFetchingCep" :placeholder="viewCopy.address.cepPlaceholder" @blur="handleCepBlur" />
            <span v-if="isFetchingCep" class="as-hint">{{ viewCopy.cep.fetching }}</span>
            <span v-else-if="cepError" class="as-err">{{ cepError }}</span>
            <span v-else-if="cepMessage" class="as-ok">{{ cepMessage }}</span>
          </div>
        </div>
        <div class="as-row">
          <div class="as-row-label">
            <p>Rua</p>
            <span>Com número e complemento.</span>
          </div>
          <div class="as-row-field">
            <input v-model="companyForm.address_street" class="as-input" :placeholder="viewCopy.address.streetPlaceholder" />
            <input v-model="companyForm.address_number" class="as-input as-xs" :placeholder="viewCopy.address.numberPlaceholder" />
            <input v-model="companyForm.address_complement" class="as-input as-short" :placeholder="viewCopy.address.complementPlaceholder" />
          </div>
        </div>
        <div class="as-row">
          <div class="as-row-label">
            <p>Bairro e cidade</p>
            <span>Com a UF.</span>
          </div>
          <div class="as-row-field">
            <input v-model="companyForm.address_neighborhood" class="as-input" :placeholder="viewCopy.address.neighborhoodPlaceholder" />
            <input v-model="companyForm.address_city" class="as-input" :placeholder="viewCopy.address.cityPlaceholder" />
            <input v-model="companyForm.address_state" maxlength="2" class="as-input as-xs" :placeholder="viewCopy.address.statePlaceholder" />
          </div>
        </div>
      </section>

      <section class="as-card">
        <header class="as-card-head">
          <p class="as-eyebrow">Marca</p>
          <h2>Logo e redes sociais</h2>
          <p>Aparecem automaticamente em todas as suas páginas.</p>
        </header>
        <div class="as-row as-row-top">
          <div class="as-row-label">
            <p>Logo da agência</p>
            <span>Use fundo transparente para ficar bem em qualquer cor.</span>
          </div>
          <div class="as-row-field">
            <ImageUploadField
              class="agency-logo-upload"
              v-model="form.logo_url"
              :label="''"
              :enable-crop="true"
              :editor-title="viewCopy.logoField.editorTitle"
            />
          </div>
        </div>
        <div class="as-row as-row-top">
          <div class="as-row-label">
            <p>Redes sociais</p>
            <span>Links que aparecem nas páginas.</span>
          </div>
          <div class="as-row-field as-col">
            <p v-if="!form.social_links.length" class="as-hint">{{ viewCopy.socialSection.empty }}</p>
            <div v-for="(social, index) in form.social_links" :key="social.id ?? `social-${index}`" class="as-social">
              <select v-model="social.network" class="as-input as-select">
                <option v-for="option in socialNetworkOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
              <input v-model="social.url" class="as-input" type="url" placeholder="https://" />
              <button type="button" class="as-remove" aria-label="Remover rede" title="Remover" @click="removeSocialLink(index)">
                <XIcon aria-hidden="true" />
              </button>
            </div>
            <button type="button" class="as-add" @click="addSocialLink">+ Adicionar rede</button>
          </div>
        </div>
      </section>

      <p v-if="message && !hasUnsavedChanges" class="as-ok as-feedback">{{ message }}</p>
      <p v-if="errorMessage" class="as-err as-feedback">{{ errorMessage }}</p>

      <div v-if="hasUnsavedChanges || !hasAgency" class="as-savebar" :style="saveBarStyle">
        <span class="as-savebar-icon" aria-hidden="true">
          <PencilIcon aria-hidden="true" />
        </span>
        <p class="as-savebar-text">{{ hasAgency ? changedSummary : "Preencha os dados para criar a sua agência." }}</p>
        <button v-if="hasAgency" type="button" class="as-btn-ghost" :disabled="saving" @click="discardChanges">Descartar</button>
        <button type="submit" class="as-btn-primary" :disabled="saving">
          {{ saving ? viewCopy.actions.saving : (hasAgency ? "Salvar alterações" : viewCopy.actions.create) }}
        </button>
      </div>
    </form>

    <div v-if="showUnsavedModal" class="app-modal-overlay fixed inset-0 z-50 flex items-center justify-center px-4">
      <div class="unsaved-modal w-full max-w-md p-5">
        <p class="modal-eyebrow">Alterações pendentes</p>
        <h3 class="mt-2 text-lg font-semibold">Você tem alterações não salvas</h3>
        <p class="mt-2 text-sm">Deseja salvar antes de sair desta página?</p>
        <div class="mt-5 flex items-center justify-end gap-2">
          <button type="button" class="btn btn-o btn-sm" @click="cancelUnsavedNavigation">Continuar editando</button>
          <button type="button" class="btn btn-o btn-sm" @click="discardUnsavedAndNavigate">Sair sem salvar</button>
          <button type="button" class="btn btn-p btn-sm" :disabled="saving" @click="saveAndNavigate">
            {{ saving ? viewCopy.actions.saving : "Salvar e sair" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PencilIcon, XIcon } from "lucide-vue-next";
import { computed, onMounted, reactive, ref, watch, onBeforeUnmount } from "vue";
import { onBeforeRouteLeave, useRouter } from "vue-router";
import ImageUploadField from "../../components/admin/inputs/ImageUploadField.vue";
import AgencyHeader from "../../components/admin/agency/AgencyHeader.vue";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import { useAuthStore } from "../../store/useAuthStore";
import { addTagsToContactByEmail, viajeChatTagIds } from "../../services/viajeChat";
import { createAdminLocalizer } from "../../utils/adminI18n";
import { normalizeWhatsappDigits } from "../../utils/whatsapp";
import { normalizeAgencySlugInput } from "../../utils/slugify";

const agencyStore = useAgencyStore();
const authStore = useAuthStore();
const router = useRouter();

const t = createAdminLocalizer();

const viewCopy = {
  hero: {
    eyebrow: t({ pt: "Agência", es: "Agencia" }),
    title: t({ pt: "Configurações", es: "Configuraciones" })
  },
  general: {
    nameLabel: t({ pt: "Nome", es: "Nombre" }),
    slugLabel: t({ pt: "Slug", es: "Slug" }),
    slugHint: t({
      pt: "Slug é a parte do link depois da barra, sem espaços ou acentos. Você também pode usar ponto. Ex.: minha.agencia-incrivel.",
      es: "Slug es la parte del enlace después de la barra, sin espacios ni acentos. También puedes usar punto. Ej.: mi.agencia-increible."
    }),
    slugLimit: t({ pt: "Limite: 30 caracteres.", es: "Límite: 30 caracteres." })
  },
  company: {
    cnpjLabel: t({ pt: "CNPJ ou CPF do responsável", es: "CNPJ o CPF del responsable" }),
    documentTypeCnpj: t({ pt: "CNPJ", es: "CNPJ" }),
    documentTypeCpf: t({ pt: "CPF", es: "CPF" }),
    cnpjPlaceholder: t({ pt: "00.000.000/0000-00", es: "00.000.000/0000-00" }),
    cpfPlaceholder: t({ pt: "000.000.000-00", es: "000.000.000-00" })
  },
  contact: {
    whatsappLabel: t({ pt: "WhatsApp da agência", es: "WhatsApp de la agencia" }),
    whatsappPlaceholder: t({ pt: "11999999999", es: "11999999999" }),
    whatsappHelper: t({
      pt: "Usamos esse número como padrão para os links de WhatsApp nos CTAs.",
      es: "Usamos este número como predeterminado para los enlaces de WhatsApp en los CTAs."
    }),
    emailLabel: t({ pt: "Email da agência", es: "Email de la agencia" }),
    emailPlaceholder: t({ pt: "contato@suaagencia.com", es: "contacto@tuagencia.com" }),
    emailHelper: t({
      pt: "Esse email aparecerá no contato da seção de rodapé das páginas.",
      es: "Este correo aparecerá en el contacto de la sección de pie de página de las páginas."
    }),
    phoneSaved: t({ pt: "Telefone salvo para os CTAs.", es: "Teléfono guardado para los CTAs." }),
    phoneRemoved: t({ pt: "Telefone removido dos CTAs.", es: "Teléfono quitado de los CTAs." }),
    invalidPhone: t({ pt: "Informe um telefone válido para os CTAs.", es: "Ingresa un teléfono válido para los CTAs." })
  },
  theme: {
    primaryColorLabel: t({ pt: "Cor primária", es: "Color principal" }),
    primaryColorPlaceholder: t({ pt: "#41ce5f", es: "#41ce5f" }),
    primaryColorHint: t({
      pt: "Essa cor será usada como base nos CTAs do editor. Você pode ajustar depois.",
      es: "Este color se usa como base en los CTAs del editor. Puedes ajustarlo después."
    }),
    faviconLabel: t({ pt: "Favicon (domínio próprio)", es: "Favicon (dominio propio)" }),
    faviconDisabledHint: t({
      pt: "Disponível apenas para agências com domínio customizado ativo.",
      es: "Disponible solo para agencias con dominio personalizado activo."
    }),
    faviconEditorTitle: t({ pt: "Ajuste o favicon", es: "Ajusta el favicon" })
  },
  logoField: {
    label: t({ pt: "Logo da agência", es: "Logotipo de la agencia" }),
    labelDescription: t({
      pt: "Esta logo aparecerá automaticamente em todas as suas páginas",
      es: "Este logotipo aparecerá automáticamente en todas tus páginas"
    }),
    hint: t({
      pt: "Envie o arquivo da sua marca. Ela aparece no editor e nas páginas.",
      es: "Sube el archivo de tu marca. Aparece en el editor y en las páginas."
    }),
    editorTitle: t({ pt: "Refine a logo da agência", es: "Refina el logo de la agencia" })
  },
  socialSection: {
    label: t({ pt: "Redes sociais", es: "Redes sociales" }),
    helper: t({
      pt: "Informe os links das redes que irão aparecer nas páginas públicas e templates.",
      es: "Ingresa los enlaces que aparecerán en las páginas públicas y plantillas."
    }),
    empty: t({ pt: "Nenhuma rede social adicionada ainda.", es: "Ninguna red social agregada todavía." }),
    networkLabel: t({ pt: "Rede", es: "Red" }),
    linkLabel: t({ pt: "Link", es: "Enlace" }),
    removeButton: t({ pt: "Remover", es: "Eliminar" }),
    addButton: t({ pt: "Adicionar rede", es: "Agregar red" }),
    placeholders: {
      instagram: t({ pt: "https://instagram.com/sua-agencia", es: "https://instagram.com/tu-agencia" }),
      facebook: t({ pt: "https://facebook.com/sua-agencia", es: "https://facebook.com/tu-agencia" }),
      youtube: t({ pt: "https://youtube.com/@sua-agencia", es: "https://youtube.com/@tu-agencia" }),
      tiktok: t({ pt: "https://tiktok.com/@sua-agencia", es: "https://tiktok.com/@tu-agencia" })
    }
  },
  address: {
    cepLabel: t({ pt: "CEP", es: "CEP" }),
    cepPlaceholder: t({ pt: "00000-000", es: "00000-000" }),
    cepHelper: t({
      pt: "Informe o CEP e completaremos rua, bairro, cidade e UF automaticamente. Você precisa preencher apenas número e complemento.",
      es: "Ingresa el CEP y completaremos calle, barrio, ciudad y estado automáticamente. Solo necesitas llenar número y complemento."
    }),
    streetLabel: t({ pt: "Endereço / Rua", es: "Dirección / Calle" }),
    streetPlaceholder: t({ pt: "Rua, avenida, estrada...", es: "Calle, avenida, carretera..." }),
    neighborhoodLabel: t({ pt: "Bairro", es: "Barrio" }),
    neighborhoodPlaceholder: t({ pt: "Bairro", es: "Barrio" }),
    cityLabel: t({ pt: "Cidade", es: "Ciudad" }),
    cityPlaceholder: t({ pt: "Cidade", es: "Ciudad" }),
    stateLabel: t({ pt: "UF", es: "Estado (UF)" }),
    statePlaceholder: t({ pt: "SP", es: "SP" }),
    numberLabel: t({ pt: "Número", es: "Número" }),
    numberPlaceholder: t({ pt: "123", es: "123" }),
    complementLabel: t({ pt: "Complemento", es: "Complemento" }),
    complementPlaceholder: t({ pt: "Sala, bloco...", es: "Sala, bloque..." })
  },
  cep: {
    fetching: t({ pt: "Buscando endereço pelo CEP...", es: "Buscando dirección por el CEP..." }),
    lookupError: t({ pt: "Não conseguimos localizar esse CEP.", es: "No pudimos localizar ese CEP." }),
    autofill: t({ pt: "Endereço preenchido automaticamente pelo CEP.", es: "Dirección completada automáticamente por el CEP." }),
    notFound: t({ pt: "CEP não encontrado.", es: "CEP no encontrado." }),
    lengthError: t({ pt: "CEP precisa ter 8 dígitos.", es: "El CEP debe tener 8 dígitos." })
  },
  actions: {
    saving: t({ pt: "Salvando...", es: "Guardando..." }),
    save: t({ pt: "Salvar", es: "Guardar" }),
    create: t({ pt: "Criar agência", es: "Crear agencia" })
  },
  validations: {
    missingNameSlug: t({ pt: "Informe nome e slug.", es: "Ingresa el nombre y el slug." })
  },
  feedback: {
    agencyCreated: t({ pt: "Agência criada.", es: "Agencia creada." }),
    agencyUpdated: t({ pt: "Configurações atualizadas.", es: "Configuraciones actualizadas." }),
    saveError: t({
      pt: "Não foi possível salvar/criar. Verifique login e permissões.",
      es: "No fue posible guardar/crear. Verifica el login y los permisos."
    })
  },
  password: {
    missingFields: t({ pt: "Informe todas as senhas.", es: "Ingresa todas las contraseñas." }),
    mismatch: t({ pt: "As senhas novas precisam coincidir.", es: "Las contraseñas nuevas deben coincidir." }),
    success: t({ pt: "Senha atualizada com sucesso.", es: "Contraseña actualizada con éxito." }),
    failure: t({ pt: "Não foi possível atualizar a senha.", es: "No fue posible actualizar la contraseña." })
  }
};

const colorPalette = ["#41ce5f", "#2563eb", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444", "#0f172a"];
const AGENCY_SLUG_MAX_LENGTH = 30;
const socialNetworkOptions = [
  { label: "Instagram", value: "instagram" },
  { label: "Facebook", value: "facebook" },
  { label: "YouTube", value: "youtube" },
  { label: "TikTok", value: "tiktok" }
] as const;

type SocialNetworkValue = (typeof socialNetworkOptions)[number]["value"];

type SocialLinkFormEntry = {
  id?: number;
  network: SocialNetworkValue;
  url: string;
};

type RawSocialLink = {
  id?: number;
  network?: string;
  url?: string;
};

const isValidSocialNetwork = (value?: string): value is SocialNetworkValue => {
  return socialNetworkOptions.some(option => option.value === value);
};

const normalizeSocialNetwork = (value?: string): SocialNetworkValue => {
  return isValidSocialNetwork(value) ? value : socialNetworkOptions[0].value;
};

const createDefaultSocialLinks = (): SocialLinkFormEntry[] =>
  socialNetworkOptions.map(option => ({
    network: option.value,
    url: ""
  }));

const form = reactive({
  id: 0,
  name: "",
  slug: "",
  logo_url: "",
  favicon_url: "",
  primary_color: colorPalette[0],
  secondary_color: "",
  contact_email: "",
  cta_whatsapp: "",
  social_links: createDefaultSocialLinks()
});

const hasAgency = ref(false);
const isBootstrappingAgencySettings = ref(true);
const saving = ref(false);
const message = ref("");
const errorMessage = ref("");

const phoneMessage = ref("");
const phoneError = ref("");
const phoneInput = ref("");
const isFetchingCep = ref(false);
const cepMessage = ref("");
const cepError = ref("");
const passwordForm = reactive({
  current: "",
  new: "",
  confirm: ""
});
const passwordSaving = ref(false);
const passwordMessage = ref("");
const passwordError = ref("");
const showUnsavedModal = ref(false);
const pendingNavigation = ref<string | null>(null);
const bypassUnsavedGuard = ref(false);
const initialSnapshot = ref("");

const companyForm = reactive({
  documentType: "cnpj" as "cnpj" | "cpf",
  cnpj: "",
  address_street: "",
  address_number: "",
  address_complement: "",
  address_neighborhood: "",
  address_city: "",
  address_state: "",
  address_zipcode: ""
});

const fillAddressFromCep = (payload: Record<string, any>) => {
  companyForm.address_street = payload?.logradouro || "";
  companyForm.address_neighborhood = payload?.bairro || "";
  companyForm.address_city = payload?.localidade || "";
  companyForm.address_state = (payload?.uf || "").toUpperCase().slice(0, 2);
};

const fetchAddressByCep = async (digits: string) => {
  try {
    isFetchingCep.value = true;
    cepError.value = "";
    cepMessage.value = "";

    const response = await fetch(`https://viacep.com.br/ws/${digits}/json/`);
    const data = await response.json();
    if (!response.ok || data?.erro) {
      throw new Error(viewCopy.cep.notFound);
    }

    fillAddressFromCep(data);
    cepMessage.value = viewCopy.cep.autofill;
  } catch (err) {
    console.error(err);
    cepError.value = viewCopy.cep.lookupError;
  } finally {
    isFetchingCep.value = false;
  }
};

const handleCepBlur = () => {
  const digits = sanitizeDigits(companyForm.address_zipcode);
  if (!digits) {
    cepMessage.value = "";
    cepError.value = "";
    return;
  }
  if (digits.length !== 8) {
    cepError.value = viewCopy.cep.lengthError;
    cepMessage.value = "";
    return;
  }
  if (isFetchingCep.value) return;
  fetchAddressByCep(digits);
};

const createEmptySocialLink = (): SocialLinkFormEntry => ({
  network: socialNetworkOptions[0].value,
  url: ""
});

const toFormSocialLinks = (links?: RawSocialLink[]) => {
  if (!links?.length) return createDefaultSocialLinks();
  return links.map(link => ({
    id: link.id,
    network: normalizeSocialNetwork(link.network),
    url: link.url || ""
  }));
};

const setFormSocialLinks = (links?: RawSocialLink[]) => {
  form.social_links = toFormSocialLinks(links);
};

const addSocialLink = () => {
  form.social_links.push(createEmptySocialLink());
};

const removeSocialLink = (index: number) => {
  form.social_links.splice(index, 1);
};

const buildSocialLinksPayload = () => {
  return form.social_links
    .map(link => ({
      network: link.network,
      url: (link.url || "").trim()
    }))
    .filter(link => !!link.url);
};

const formatCpf = (cpf?: string | null) => {
  if (!cpf) return "";
  const digits = cpf.replace(/\D/g, "").slice(0, 11);
  return digits
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
};

const formatCnpj = (cnpj?: string | null) => {
  if (!cnpj) return "";
  const digits = cnpj.replace(/\D/g, "").slice(0, 14);
  return digits
    .replace(/(\d{2})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1/$2")
    .replace(/(\d{4})(\d{1,2})$/, "$1-$2");
};

const formatCompanyDocument = (value?: string | null, type: "cnpj" | "cpf" = "cnpj") => {
  if (!value) return "";
  const digits = value.replace(/\D/g, "");
  return type === "cpf" ? formatCpf(digits.slice(0, 11)) : formatCnpj(digits.slice(0, 14));
};

const companyDocumentPlaceholder = computed(() =>
  companyForm.documentType === "cpf" ? viewCopy.company.cpfPlaceholder : viewCopy.company.cnpjPlaceholder
);

const formatCep = (cep?: string | null) => {
  if (!cep) return "";
  const digits = cep.replace(/\D/g, "").slice(0, 8);
  return digits.replace(/(\d{5})(\d{1,3})$/, "$1-$2");
};

const sanitizeDigits = (value?: string | null) => {
  if (!value) return null;
  const digits = value.replace(/\D/g, "");
  return digits || null;
};

const sanitizeText = (value?: string | null) => {
  if (value == null) return null;
  return value.trim();
};

const syncCompanyData = () => {
  const profile = authStore.user;
  const cnpjDigits = (profile?.cnpj || "").replace(/\D/g, "");
  const cpfDigits = (profile?.cpf || "").replace(/\D/g, "");
  if (cnpjDigits) {
    companyForm.documentType = "cnpj";
    companyForm.cnpj = formatCompanyDocument(cnpjDigits, "cnpj");
  } else if (cpfDigits) {
    companyForm.documentType = "cpf";
    companyForm.cnpj = formatCompanyDocument(cpfDigits, "cpf");
  } else {
    companyForm.documentType = "cnpj";
    companyForm.cnpj = "";
  }
  companyForm.address_street = profile?.address_street || "";
  companyForm.address_number = profile?.address_number || "";
  companyForm.address_complement = profile?.address_complement || "";
  companyForm.address_neighborhood = profile?.address_neighborhood || "";
  companyForm.address_city = profile?.address_city || "";
  companyForm.address_state = profile?.address_state || "";
  companyForm.address_zipcode = formatCep(profile?.address_zipcode || "");
  cepMessage.value = "";
  cepError.value = "";
};

const syncFormWithCurrent = () => {
  const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  if (agency) Object.assign(form, agency);
  setFormSocialLinks(agency?.social_links);

  if (!form.primary_color) form.primary_color = colorPalette[0];
  if (!form.contact_email) form.contact_email = "";

  const fallbackPhone = form.cta_whatsapp || authStore.user?.whatsapp || "";
  const fallbackDigits = fallbackPhone.replace(/\D/g, "");
  phoneInput.value = fallbackDigits.replace(/^0?55/, "");

  syncCompanyData();
};

const buildFormSnapshot = () =>
  JSON.stringify({
    name: form.name || "",
    slug: form.slug || "",
    logo_url: form.logo_url || "",
    favicon_url: form.favicon_url || "",
    primary_color: form.primary_color || "",
    secondary_color: form.secondary_color || "",
    contact_email: form.contact_email || "",
    cta_whatsapp: phoneInput.value || "",
    social_links: (form.social_links || []).map(item => ({
      network: item.network || "",
      url: item.url || ""
    })),
    company: {
      documentType: companyForm.documentType,
      cnpj: companyForm.cnpj || "",
      address_street: companyForm.address_street || "",
      address_number: companyForm.address_number || "",
      address_complement: companyForm.address_complement || "",
      address_neighborhood: companyForm.address_neighborhood || "",
      address_city: companyForm.address_city || "",
      address_state: companyForm.address_state || "",
      address_zipcode: companyForm.address_zipcode || ""
    }
  });

const handleSlugInput = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const normalized = normalizeAgencySlugInput(target.value, AGENCY_SLUG_MAX_LENGTH);
  form.slug = normalized;
  target.value = normalized;
};

const hasUnsavedChanges = computed(() => {
  if (!initialSnapshot.value) return false;
  return buildFormSnapshot() !== initialSnapshot.value;
});

const markSnapshot = () => {
  initialSnapshot.value = buildFormSnapshot();
};

// Barra de salvar fixa no rodapé, com a mesma largura do formulário.
const formRef = ref<HTMLElement | null>(null);
const formBox = ref({ left: 0, width: 0 });
let formObserver: ResizeObserver | null = null;
const measureForm = () => {
  const el = formRef.value;
  if (!el) return;
  const rect = el.getBoundingClientRect();
  // O painel pode ter "zoom" aplicado; as medidas da tela precisam ser convertidas.
  const zoom = el.offsetWidth ? rect.width / el.offsetWidth : 1;
  formBox.value = { left: rect.left / zoom, width: rect.width / zoom };
};
const saveBarStyle = computed(() =>
  formBox.value.width ? { left: `${formBox.value.left}px`, width: `${formBox.value.width}px` } : {}
);
watch(formRef, el => {
  formObserver?.disconnect();
  if (!el || typeof ResizeObserver === "undefined") return;
  formObserver = new ResizeObserver(measureForm);
  formObserver.observe(el);
  measureForm();
});
onMounted(() => window.addEventListener("resize", measureForm));
watch(() => hasUnsavedChanges.value, visible => { if (visible) measureForm(); });
onBeforeUnmount(() => {
  window.removeEventListener("resize", measureForm);
  formObserver?.disconnect();
});

// Barra de salvar: diz o que mudou e permite descartar.
const changedSummary = computed(() => {
  if (!initialSnapshot.value) return "";
  const before = JSON.parse(initialSnapshot.value);
  const now = JSON.parse(buildFormSnapshot());
  const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);
  const changes: string[] = [];
  if (!same(before.name, now.name)) changes.push("o nome");
  if (!same(before.slug, now.slug)) changes.push("o link");
  if (!same(before.primary_color, now.primary_color)) changes.push("a cor principal");
  if (!same(before.company.cnpj, now.company.cnpj) || !same(before.company.documentType, now.company.documentType)) changes.push("o CNPJ ou CPF");
  if (!same(before.cta_whatsapp, now.cta_whatsapp)) changes.push("o WhatsApp");
  if (!same(before.contact_email, now.contact_email)) changes.push("o e-mail");
  const addressKeys = ["address_zipcode", "address_street", "address_number", "address_complement", "address_neighborhood", "address_city", "address_state"];
  if (addressKeys.some(key => !same(before.company[key], now.company[key]))) changes.push("o endereço");
  if (!same(before.logo_url, now.logo_url) || !same(before.favicon_url, now.favicon_url)) changes.push("a logo");
  if (!same(before.social_links, now.social_links)) changes.push("as redes sociais");
  if (!changes.length) return "Você tem alterações não salvas.";
  if (changes.length === 1) return `Você alterou ${changes[0]}.`;
  if (changes.length === 2) return `Você alterou ${changes[0]} e ${changes[1]}.`;
  return `Você alterou ${changes.length} informações.`;
});

const discardChanges = () => {
  if (!initialSnapshot.value) return;
  const before = JSON.parse(initialSnapshot.value);
  form.name = before.name;
  form.slug = before.slug;
  form.logo_url = before.logo_url;
  form.favicon_url = before.favicon_url;
  form.primary_color = before.primary_color;
  form.secondary_color = before.secondary_color;
  form.contact_email = before.contact_email;
  phoneInput.value = before.cta_whatsapp;
  setFormSocialLinks(before.social_links);
  Object.assign(companyForm, before.company);
  errorMessage.value = "";
  phoneError.value = "";
  markSnapshot();
};

const saveCompanyData = async () => {
  const documentDigits = sanitizeDigits(companyForm.cnpj);
  const payload = {
    cnpj: companyForm.documentType === "cnpj" ? documentDigits : null,
    cpf: companyForm.documentType === "cpf" ? documentDigits : null,
    address_street: sanitizeText(companyForm.address_street),
    address_number: sanitizeText(companyForm.address_number),
    address_complement: sanitizeText(companyForm.address_complement),
    address_neighborhood: sanitizeText(companyForm.address_neighborhood),
    address_city: sanitizeText(companyForm.address_city),
    address_state: sanitizeText(companyForm.address_state),
    address_zipcode: sanitizeDigits(companyForm.address_zipcode)
  };

  const res = await api.put("/auth/me", payload);
  authStore.user = res.data;
};

const changePassword = async () => {
  passwordError.value = "";
  passwordMessage.value = "";
  if (!passwordForm.current || !passwordForm.new || !passwordForm.confirm) {
    passwordError.value = viewCopy.password.missingFields;
    return;
  }
  if (passwordForm.new !== passwordForm.confirm) {
    passwordError.value = viewCopy.password.mismatch;
    return;
  }
  passwordSaving.value = true;
  try {
    await api.post("/auth/me/password", {
      current_password: passwordForm.current,
      new_password: passwordForm.new
    });
    passwordMessage.value = viewCopy.password.success;
    passwordForm.current = "";
    passwordForm.new = "";
    passwordForm.confirm = "";
  } catch (err) {
    console.error(err);
    passwordError.value =
      (err as any)?.response?.data?.detail || viewCopy.password.failure;
  } finally {
    passwordSaving.value = false;
  }
};

const load = async () => {
  errorMessage.value = "";
  message.value = "";
  phoneMessage.value = "";
  phoneError.value = "";

  await authStore.fetchProfile();
  syncCompanyData();

  await agencyStore.loadAgencies();
  hasAgency.value = !!agencyStore.currentAgencyId;

  if (hasAgency.value) syncFormWithCurrent();
  markSnapshot();
};

const bootstrapAgencySettings = async () => {
  try {
    await load();
  } finally {
    isBootstrappingAgencySettings.value = false;
  }
};

const save = async () => {
  errorMessage.value = "";
  message.value = "";
  phoneMessage.value = "";
  phoneError.value = "";

  if (!form.name || !form.slug) {
    errorMessage.value = viewCopy.validations.missingNameSlug;
    return;
  }

  const normalizedName = form.name.trim();
  const currentAgency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId) || null;
  const slugWasEdited = !agencyStore.currentAgencyId || (form.slug || "").trim() !== (currentAgency?.slug || "");
  const normalizedSlug = slugWasEdited
    ? normalizeAgencySlugInput(form.slug, AGENCY_SLUG_MAX_LENGTH)
    : (currentAgency?.slug || form.slug || "").trim();

  if (!normalizedSlug) {
    errorMessage.value = viewCopy.validations.missingNameSlug;
    form.slug = "";
    return;
  }

  const rawPhoneDigits = (phoneInput.value || "").replace(/\D/g, "");
  if (rawPhoneDigits && rawPhoneDigits.length < 10) {
    phoneError.value = viewCopy.contact.invalidPhone;
    return;
  }

  const phoneDigits = rawPhoneDigits ? normalizeWhatsappDigits(rawPhoneDigits) : "";

  form.name = normalizedName;
  form.slug = normalizedSlug;
  form.cta_whatsapp = phoneDigits;

  const payload = {
    name: normalizedName,
    slug: normalizedSlug,
    logo_url: form.logo_url,
    favicon_url: form.favicon_url || null,
    primary_color: form.primary_color,
    secondary_color: form.secondary_color,
    contact_email: sanitizeText(form.contact_email),
    cta_whatsapp: phoneDigits,
    social_links: buildSocialLinksPayload()
  };

  let createdAgency = false;

  try {
    saving.value = true;

    if (agencyStore.currentAgencyId) {
      const res = await api.put(`/agencies/${agencyStore.currentAgencyId}`, payload);
      Object.assign(form, res.data);
      setFormSocialLinks(res.data?.social_links);
    } else {
      const res = await api.post("/agencies", payload);
      await agencyStore.loadAgencies();
      agencyStore.currentAgencyId = res.data.id;
      hasAgency.value = true;
      syncFormWithCurrent();
      createdAgency = true;
    }

    await saveCompanyData();
    syncCompanyData();
    if (createdAgency && authStore.user?.email) {
      await addTagsToContactByEmail(authStore.user.email, [viajeChatTagIds.AGENCIA_CRIADA]);
    }

    phoneMessage.value = phoneDigits ? viewCopy.contact.phoneSaved : viewCopy.contact.phoneRemoved;
    message.value = createdAgency ? viewCopy.feedback.agencyCreated : viewCopy.feedback.agencyUpdated;
    markSnapshot();
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    errorMessage.value = detail || viewCopy.feedback.saveError;
  } finally {
    saving.value = false;
  }
};

const cancelUnsavedNavigation = () => {
  showUnsavedModal.value = false;
  pendingNavigation.value = null;
};

const discardUnsavedAndNavigate = () => {
  if (!pendingNavigation.value) {
    showUnsavedModal.value = false;
    return;
  }
  const target = pendingNavigation.value;
  showUnsavedModal.value = false;
  pendingNavigation.value = null;
  bypassUnsavedGuard.value = true;
  router.push(target).finally(() => {
    bypassUnsavedGuard.value = false;
  });
};

const saveAndNavigate = async () => {
  const target = pendingNavigation.value;
  await save();
  if (!target || hasUnsavedChanges.value) return;
  showUnsavedModal.value = false;
  pendingNavigation.value = null;
  bypassUnsavedGuard.value = true;
  router.push(target).finally(() => {
    bypassUnsavedGuard.value = false;
  });
};

watch(
  () => companyForm.cnpj,
  value => {
    const masked = formatCompanyDocument(value || "", companyForm.documentType);
    if (value !== masked) companyForm.cnpj = masked;
  }
);

watch(
  () => companyForm.documentType,
  value => {
    companyForm.cnpj = formatCompanyDocument(companyForm.cnpj || "", value);
  }
);

watch(
  () => companyForm.address_zipcode,
  value => {
    const masked = formatCep(value || "");
    if (value !== masked) {
      companyForm.address_zipcode = masked;
      return;
    }
    cepMessage.value = "";
    cepError.value = "";
  }
);

watch(
  () => companyForm.address_state,
  value => {
    if (value == null) return;
    const normalized = value.toUpperCase().slice(0, 2);
    if (normalized !== value) companyForm.address_state = normalized;
  }
);

onBeforeRouteLeave(to => {
  if (bypassUnsavedGuard.value) return true;
  if (!hasUnsavedChanges.value) return true;
  pendingNavigation.value = to.fullPath;
  showUnsavedModal.value = true;
  return false;
});

const handleBeforeUnload = (event: BeforeUnloadEvent) => {
  if (!hasUnsavedChanges.value) return;
  event.preventDefault();
  event.returnValue = "";
};

onMounted(bootstrapAgencySettings);
onMounted(() => {
  window.addEventListener("beforeunload", handleBeforeUnload);
});
onBeforeUnmount(() => {
  window.removeEventListener("beforeunload", handleBeforeUnload);
});
</script>

<style scoped>
.agency-settings {
  --verde:var(--primary);--verde-d:var(--brand-dark);--verde-dim:color-mix(in srgb, var(--primary) 10%, transparent);--verde-border:color-mix(in srgb, var(--primary) 35%, var(--input));
  --bg:var(--background);--surface:var(--card);--surface2:var(--muted);--border2:var(--input);
  --text:var(--foreground);--text-2:var(--card-foreground);--text-3:var(--muted-foreground);
  --sh-sm:var(--shadow-soft);
  --radius:var(--radius-xl);--radius-sm:var(--radius-md);
  color:var(--foreground);
}
.page-wrap{padding:28px 32px 64px;width:100%;max-width:1440px}
.page-topbar{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;flex-wrap:wrap;margin-bottom:24px}
.page-eyebrow{font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--text-3);margin-bottom:5px}
.page-title{font-family:var(--font-display);font-size:26px;font-weight:650;color:var(--text);letter-spacing:-.3px;line-height:1.2}
.page-sub{font-size:13px;color:var(--text-3);margin-top:5px}
.card{overflow:hidden;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--sh-sm);width:100%;margin-bottom:14px}
.card-head{padding:18px 22px 14px;border-bottom:1px solid color-mix(in srgb, var(--border) 42%, transparent);background:color-mix(in srgb, var(--muted) 22%, var(--card))}
.card-eye{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--text-3);margin-bottom:3px}
.card-title{font-family:var(--font-display);font-size:15px;font-weight:650;color:var(--text);letter-spacing:-.2px}
.card-sub{font-size:12px;color:var(--text-3);margin-top:2px;line-height:1.45}
.card-body{padding:20px 22px}
.card-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;width:100%}
.fg{display:flex;flex-direction:column;gap:5px;margin-bottom:14px;min-width:0}
.fl{font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--text-3)}
.fh{font-size:11px;color:var(--text-3);line-height:1.4;margin-top:3px}
.fi{padding:10px 11px;border:1px solid var(--border2);border-radius:var(--radius-sm);font-family:inherit;font-size:13px;color:var(--text);background:var(--bg);outline:none;transition:border-color .15s,box-shadow .15s;width:100%;min-width:0;max-width:100%}
.fi:focus{border-color:var(--verde-border);box-shadow:0 0 0 3px var(--verde-dim)}
.fs{padding:10px 11px;border:1px solid var(--border2);border-radius:var(--radius-sm);font-family:inherit;font-size:13px;color:var(--text);background:var(--bg);outline:none;cursor:pointer;width:100%}
.fs option{background:var(--surface);color:var(--text)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}
.ig{display:flex;border:1px solid var(--border2);border-radius:var(--radius-sm);overflow:hidden;transition:border-color .15s,box-shadow .15s;min-width:0;max-width:100%;background:var(--bg)}
.ig:focus-within{border-color:var(--verde-border);box-shadow:0 0 0 3px var(--verde-dim)}
.ig-pre{padding:9px 11px;background:var(--surface2);font-size:12px;color:var(--text-3);border-right:1px solid var(--border);white-space:nowrap;display:flex;align-items:center;gap:5px}
.ig input,.ig select{flex:1;padding:9px 11px;border:none;font-family:inherit;font-size:13px;color:var(--text);background:var(--bg);outline:none;min-width:0}
.ig select{flex:0 0 auto;padding:9px 16px 9px 9px;border-right:1px solid var(--border);font-size:12px;background:var(--surface2);cursor:pointer}
.cp-row{display:flex;align-items:center;gap:9px}
.cp-btn{width:40px;height:40px;border-radius:8px;border:1px solid var(--border2);background:var(--bg);cursor:pointer;padding:3px;overflow:hidden;flex-shrink:0}
.cp-btn input[type=color]{width:100%;height:100%;border:none;background:transparent;cursor:pointer;padding:0;border-radius:5px}
.favicon-wrap{margin-top:10px}
.favicon-head{display:flex;flex-direction:column;gap:2px;margin-bottom:6px}
.favicon-upload{border:1.5px solid var(--border);border-radius:10px;padding:10px;background:var(--surface2)}
.favicon-upload.is-disabled{opacity:.55;pointer-events:none}
:deep(.favicon-upload .space-y-2){gap:6px}
:deep(.favicon-upload .max-h-\[320px\]){max-height:120px !important;min-height:96px !important}
:deep(.favicon-upload .min-h-\[220px\]){min-height:96px !important}
:deep(.favicon-upload .image-upload-preview){max-height:96px !important;object-fit:contain}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:9px 18px;border-radius:10px;font-size:13px;font-weight:650;cursor:pointer;border:none;font-family:inherit;transition:all .15s;white-space:nowrap;line-height:1.3}
.btn-p{background:var(--verde);color:var(--primary-foreground);box-shadow:var(--shadow-soft)}
.btn-p:hover{background:var(--verde-d)}
.btn:disabled{cursor:not-allowed;opacity:.6}
.btn-sm{padding:6px 14px;font-size:12px}
.btn-o{border:1px solid var(--border);background:var(--bg);color:var(--text)}
.btn-o:hover{background:var(--surface2)}
.btn-danger-text{background:transparent;border:none;color:var(--destructive);font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;padding:0}
.social-head{display:flex;align-items:center;justify-content:space-between;gap:12px}
.social-item{display:grid;grid-template-columns:160px 1fr auto;gap:9px;align-items:center;padding:10px 0;border-bottom:1px solid color-mix(in srgb, var(--border) 36%, transparent)}
.social-item:last-child{border-bottom:none;padding-bottom:0}
.save-row{display:flex;align-items:center;gap:10px;margin-top:6px}
.ok-msg{font-size:12px;color:var(--status-success-foreground);font-weight:600}
.err-msg{font-size:12px;color:var(--destructive);font-weight:600}

.unsaved-modal{border:1px solid var(--border);border-radius:var(--radius-xl);background:var(--card);color:var(--card-foreground);box-shadow:var(--shadow-soft)}
.unsaved-modal h3{font-family:var(--font-display);color:var(--foreground)}
.unsaved-modal > p:not(.modal-eyebrow){color:var(--muted-foreground)}
.modal-eyebrow{font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--muted-foreground)}

:deep(.agency-logo-upload .max-h-\[320px\]){height:190px !important;max-height:190px !important;min-height:190px !important}
:deep(.agency-logo-upload .image-upload-preview){
  width:100% !important;
  height:100% !important;
  min-height:0 !important;
  max-height:none !important;
  object-fit:contain !important;
  object-position:center !important;
}

@media(max-width:900px){.page-wrap{padding:20px 16px 40px;max-width:none}.page-topbar{flex-direction:column;align-items:flex-start}}
@media(max-width:768px){.card-row{grid-template-columns:1fr}}
@media(max-width:600px){
  .grid2,.grid3,.social-item{grid-template-columns:1fr}
  .card-head,.card-body{padding-left:14px;padding-right:14px}
  .slug-field .ig{flex-direction:row}
  .slug-field .ig-pre{
    flex:0 0 58%;
    max-width:58%;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
    border-right:1.5px solid var(--border);
    border-bottom:none;
  }
  .slug-field .ig input{
    flex:0 0 42%;
    max-width:42%;
    min-width:0;
  }
}

/* Redesign: dados da agência */
.agency-settings { display: flex; flex-direction: column; gap: 16px; }
.as-form { display: flex; flex-direction: column; gap: 16px; padding-bottom: 88px; }
.as-card { border-radius: 20px; background: var(--card); padding: 20px 22px 8px; box-shadow: var(--shadow-card); }
.as-card-head { border-bottom: 1px solid var(--border); padding-bottom: 12px; }
.as-eyebrow { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted-foreground); }
.as-card-head h2 { margin-top: 2px; font-family: var(--font-display); font-size: 17px; font-weight: 600; color: var(--foreground); }
.as-card-head p:last-child { margin-top: 1px; font-size: 13px; color: var(--muted-foreground); }
.as-row { display: grid; grid-template-columns: minmax(0, 220px) minmax(0, 1fr); align-items: center; gap: 20px; border-bottom: 1px solid var(--border); padding: 14px 0; }
.as-row:last-child { border-bottom: 0; }
.as-row-top { align-items: start; }
.as-row-label p { font-size: 14px; font-weight: 600; color: var(--foreground); }
.as-row-label span { display: block; margin-top: 2px; font-size: 12.5px; line-height: 1.45; color: var(--muted-foreground); }
.as-row-field { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; min-width: 0; }
.as-col { flex-direction: column; align-items: stretch; gap: 6px; }
.as-col > .as-input { flex: none; }
.as-col > .as-short { align-self: flex-start; width: 180px; }
.as-input { flex: 1; min-width: 0; height: 40px; border: 0 !important; border-radius: 12px; background: var(--muted) !important; padding: 0 12px; font-size: 13.5px; color: var(--foreground); outline: none; }
.as-input:focus, .as-input:focus-within { box-shadow: 0 0 0 2px var(--ring); }
.as-group { display: flex; align-items: center; padding: 0; overflow: hidden; }
.as-group input { flex: 1; min-width: 0; height: 100%; border: 0; background: transparent; padding: 0 12px; font-size: 13.5px; color: var(--foreground); outline: none; }
.as-prefix { flex-shrink: 0; border-right: 1px solid var(--border); padding: 0 10px 0 12px; font-size: 13px; color: var(--muted-foreground); }
.as-select { flex: 0 0 120px; padding-right: 28px; }
.as-short { flex: 0 1 180px; }
.as-xs { flex: 0 0 90px; }
.as-color { display: flex; flex: 0 0 170px; align-items: center; gap: 10px; padding: 0 12px 0 8px; }
.as-swatch { position: relative; width: 24px; height: 24px; flex-shrink: 0; overflow: hidden; border-radius: 8px; }
.as-swatch input { position: absolute; inset: -6px; width: 40px; height: 40px; cursor: pointer; opacity: 0; }
.as-color-text { flex: 1; min-width: 0; border: 0; background: transparent; font-size: 13.5px; color: var(--foreground); outline: none; }
.as-preview-btn { display: inline-flex; align-items: center; height: 34px; padding: 0 16px; border-radius: 999px; font-size: 13px; font-weight: 600; color: #fff; }
.as-hint { font-size: 12px; color: var(--muted-foreground); }
.as-ok { font-size: 12.5px; color: var(--status-success-foreground); }
.as-err { font-size: 12.5px; color: var(--status-danger-foreground); }
.as-feedback { border-radius: 14px; background: var(--card); padding: 10px 14px; box-shadow: var(--shadow-card); }
.as-social { display: flex; align-items: center; gap: 8px; }
.as-remove { display: grid; place-items: center; width: 34px; height: 34px; flex-shrink: 0; border-radius: 999px; background: var(--muted); color: var(--muted-foreground); }
.as-remove:hover { background: var(--status-danger); color: var(--status-danger-foreground); }
.as-remove svg { width: 14px; height: 14px; }
.as-add { align-self: flex-start; height: 34px; padding: 0 14px; border-radius: 999px; background: var(--accent); font-size: 13px; font-weight: 600; color: var(--accent-foreground); }
.as-savebar { position: fixed; bottom: 16px; left: 16px; right: 16px; z-index: 60; display: flex; align-items: center; gap: 12px; border-radius: 20px; background: var(--card); padding: 10px 12px 10px 16px; box-shadow: var(--shadow-elegant); }
.as-savebar-icon { display: grid; place-items: center; width: 32px; height: 32px; flex-shrink: 0; border-radius: 999px; background: var(--status-warning); color: var(--status-warning-foreground); }
.as-savebar-icon svg { width: 15px; height: 15px; }
.as-savebar-text { flex: 1; min-width: 0; font-size: 13.5px; color: var(--foreground); }
.as-btn-ghost, .as-btn-primary { height: 40px; padding: 0 18px; border-radius: 999px; font-size: 13.5px; font-weight: 600; }
.as-btn-ghost { background: var(--muted); color: var(--foreground); }
.as-btn-primary { background: var(--primary); color: var(--primary-foreground); }
.as-btn-primary:hover:not(:disabled) { background: color-mix(in srgb, var(--primary) 88%, black); }
.as-btn-ghost:disabled, .as-btn-primary:disabled { opacity: 0.6; }
@media (max-width: 760px) {
  .as-row { grid-template-columns: 1fr; gap: 8px; }
  .as-select, .as-short, .as-xs, .as-color { flex-basis: 100%; }
  .as-savebar { flex-wrap: wrap; }
}
</style>



