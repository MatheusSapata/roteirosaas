<template>
  <div v-if="isBootstrappingAgencySettings" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8 md:px-8">
    <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
  </div>
  <div v-else class="agency-settings page-wrap">
    <div class="page-eyebrow">{{ viewCopy.hero.eyebrow }}</div>
    <div class="page-topbar">
      <div class="page-title">{{ viewCopy.hero.title }}</div>
      <button type="button" class="btn btn-p" :disabled="saving" @click="save">
        {{ saving ? viewCopy.actions.saving : (hasAgency ? viewCopy.actions.save : viewCopy.actions.create) }}
      </button>
    </div>
    <div class="page-sub">Dados da sua agência usados nas páginas públicas e templates.</div>

    <form @submit.prevent="save">
      <div class="card">
        <div class="card-head">
          <div class="card-eye">Identidade</div>
          <div class="card-title">Dados principais</div>
          <div class="card-sub">Nome, slug e cor que aparecerão nos seus roteiros.</div>
        </div>
        <div class="card-body">
          <div class="grid3">
            <div class="fg">
              <label class="fl">{{ viewCopy.general.nameLabel }}</label>
              <input v-model="form.name" class="fi" />
            </div>
            <div class="fg">
              <label class="fl">{{ viewCopy.general.slugLabel }}</label>
              <div class="ig">
                <span class="ig-pre">roteiroonline.com/</span>
                <input v-model="form.slug" />
              </div>
              <span class="fh">{{ viewCopy.general.slugHint }}</span>
            </div>
            <div class="fg">
              <label class="fl">{{ viewCopy.theme.primaryColorLabel }}</label>
              <div class="cp-row">
                <div class="cp-btn"><input type="color" v-model="form.primary_color" /></div>
                <input v-model="form.primary_color" class="fi" style="max-width:110px" />
              </div>
              <span class="fh">{{ viewCopy.theme.primaryColorHint }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-head">
          <div class="card-eye">Contato</div>
          <div class="card-title">Informações de contato</div>
          <div class="card-sub">Aparece no rodapé das suas páginas públicas.</div>
        </div>
        <div class="card-body">
          <div class="grid3">
            <div class="fg">
              <label class="fl">{{ viewCopy.company.cnpjLabel }}</label>
              <div class="ig">
                <select v-model="companyForm.documentType">
                  <option value="cnpj">{{ viewCopy.company.documentTypeCnpj }}</option>
                  <option value="cpf">{{ viewCopy.company.documentTypeCpf }}</option>
                </select>
                <input v-model="companyForm.cnpj" :placeholder="companyDocumentPlaceholder" />
              </div>
            </div>
            <div class="fg">
              <label class="fl">{{ viewCopy.contact.whatsappLabel }}</label>
              <div class="ig">
                <span class="ig-pre">BR +55</span>
                <input v-model="phoneInput" :placeholder="viewCopy.contact.whatsappPlaceholder" inputmode="numeric" />
              </div>
              <span class="fh">{{ viewCopy.contact.whatsappHelper }}</span>
              <span v-if="phoneMessage" class="ok-msg">{{ phoneMessage }}</span>
              <span v-if="phoneError" class="err-msg">{{ phoneError }}</span>
            </div>
            <div class="fg">
              <label class="fl">{{ viewCopy.contact.emailLabel }}</label>
              <input v-model="form.contact_email" type="email" class="fi" :placeholder="viewCopy.contact.emailPlaceholder" />
              <span class="fh">{{ viewCopy.contact.emailHelper }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-head">
          <div class="card-eye">Localização</div>
          <div class="card-title">Endereço</div>
          <div class="card-sub">Informe o CEP e completaremos os demais campos automaticamente.</div>
        </div>
        <div class="card-body">
          <div class="grid2" style="margin-bottom:14px">
            <div class="fg">
              <label class="fl">{{ viewCopy.address.cepLabel }}</label>
              <input v-model="companyForm.address_zipcode" class="fi" :disabled="isFetchingCep" :placeholder="viewCopy.address.cepPlaceholder" @blur="handleCepBlur" />
              <span class="fh">{{ viewCopy.address.cepHelper }}</span>
              <span v-if="isFetchingCep" class="fh">{{ viewCopy.cep.fetching }}</span>
              <span v-else-if="cepError" class="err-msg">{{ cepError }}</span>
              <span v-else-if="cepMessage" class="ok-msg">{{ cepMessage }}</span>
            </div>
            <div class="fg">
              <label class="fl">{{ viewCopy.address.streetLabel }}</label>
              <input v-model="companyForm.address_street" class="fi" :placeholder="viewCopy.address.streetPlaceholder" />
            </div>
            <div class="fg">
              <label class="fl">{{ viewCopy.address.neighborhoodLabel }}</label>
              <input v-model="companyForm.address_neighborhood" class="fi" :placeholder="viewCopy.address.neighborhoodPlaceholder" />
            </div>
            <div class="fg">
              <label class="fl">{{ viewCopy.address.cityLabel }}</label>
              <input v-model="companyForm.address_city" class="fi" :placeholder="viewCopy.address.cityPlaceholder" />
            </div>
          </div>
          <div class="grid3">
            <div class="fg">
              <label class="fl">{{ viewCopy.address.stateLabel }}</label>
              <input v-model="companyForm.address_state" maxlength="2" class="fi" :placeholder="viewCopy.address.statePlaceholder" />
            </div>
            <div class="fg">
              <label class="fl">{{ viewCopy.address.numberLabel }}</label>
              <input v-model="companyForm.address_number" class="fi" :placeholder="viewCopy.address.numberPlaceholder" />
            </div>
            <div class="fg">
              <label class="fl">{{ viewCopy.address.complementLabel }}</label>
              <input v-model="companyForm.address_complement" class="fi" :placeholder="viewCopy.address.complementPlaceholder" />
            </div>
          </div>
        </div>
      </div>

      <div class="card-row">
        <div class="card" style="margin-bottom:0">
          <div class="card-head">
            <div class="card-eye">Marca</div>
            <div class="card-title">Logo da agência</div>
            <div class="card-sub">Esta logo aparecerá automaticamente em todas as suas páginas.</div>
          </div>
          <div class="card-body">
            <ImageUploadField
              class="agency-logo-upload"
              v-model="form.logo_url"
              :label="''"
              :enable-crop="true"
              :editor-title="viewCopy.logoField.editorTitle"
            />
          </div>
        </div>
        <div class="card" style="margin-bottom:0">
          <div class="card-head social-head">
            <div>
              <div class="card-eye">Marca</div>
              <div class="card-title">Redes sociais</div>
              <div class="card-sub">Links que aparecerão nas páginas públicas e templates.</div>
            </div>
            <button type="button" class="btn btn-p btn-sm" @click="addSocialLink">+ Adicionar rede</button>
          </div>
          <div class="card-body">
            <div v-if="!form.social_links.length" class="fh">{{ viewCopy.socialSection.empty }}</div>
            <div v-for="(social, index) in form.social_links" :key="social.id ?? `social-${index}`" class="social-item">
              <select v-model="social.network" class="fs">
                <option v-for="option in socialNetworkOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
              <input v-model="social.url" class="fi" type="url" />
              <button type="button" class="btn-danger-text" @click="removeSocialLink(index)">Remover</button>
            </div>
          </div>
        </div>
      </div>

      <div class="save-row">
        <span v-if="message" class="ok-msg">{{ message }}</span>
        <span v-if="errorMessage" class="err-msg">{{ errorMessage }}</span>
      </div>
    </form>

    <div v-if="showUnsavedModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4">
      <div class="w-full max-w-md rounded-2xl bg-white p-5 shadow-2xl">
        <h3 class="text-lg font-semibold text-slate-900">Você tem alterações não salvas</h3>
        <p class="mt-2 text-sm text-slate-600">Deseja salvar antes de sair desta página?</p>
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
import { computed, onMounted, reactive, ref, watch, onBeforeUnmount } from "vue";
import { onBeforeRouteLeave, useRouter } from "vue-router";
import ImageUploadField from "../../components/admin/inputs/ImageUploadField.vue";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import { useAuthStore } from "../../store/useAuthStore";
import { addTagsToContactByEmail, viajeChatTagIds } from "../../services/viajeChat";
import { createAdminLocalizer } from "../../utils/adminI18n";
import { normalizeWhatsappDigits } from "../../utils/whatsapp";

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
      pt: "Slug é a parte do link depois da barra, sem espaços ou acentos. Ex.: minha-agencia-incrivel.",
      es: "Slug es la parte del enlace después de la barra, sin espacios ni acentos. Ej.: mi-agencia-increible."
    })
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
    })
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

const hasUnsavedChanges = computed(() => {
  if (!initialSnapshot.value) return false;
  return buildFormSnapshot() !== initialSnapshot.value;
});

const markSnapshot = () => {
  initialSnapshot.value = buildFormSnapshot();
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
  const normalizedSlug = form.slug.trim().toLowerCase();

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
  --verde:#3DCC5F;--verde-d:#2EAD4C;--verde-dim:rgba(61,204,95,.10);--verde-border:rgba(61,204,95,.22);
  --bg:#F2F4F2;--surface:#fff;--surface2:#F5F7F5;--border:#E4E9E4;--border2:#CDD8CD;
  --text:#111A14;--text-2:#4A5E4A;--text-3:#8A9E8A;
  --sh-sm:0 1px 3px rgba(0,0,0,.05),0 1px 2px rgba(0,0,0,.03);
  --radius:12px;--radius-sm:8px;
}
.page-wrap{padding:28px 32px 64px;width:100%;max-width:1200px}
.page-topbar{display:flex;align-items:flex-start;justify-content:space-between;gap:14px}
.page-eyebrow{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--text-3);margin-bottom:3px}
.page-title{font-size:24px;font-weight:800;color:var(--text);letter-spacing:-.3px;line-height:1.2}
.page-sub{font-size:13px;color:var(--text-3);margin-top:4px;margin-bottom:24px}
.card{background:var(--surface);border:1.5px solid var(--border);border-radius:var(--radius);box-shadow:var(--sh-sm);width:100%;margin-bottom:14px}
.card-head{padding:18px 22px 14px;border-bottom:1.5px solid var(--border)}
.card-eye{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--text-3);margin-bottom:3px}
.card-title{font-size:15px;font-weight:800;color:var(--text);letter-spacing:-.2px}
.card-sub{font-size:12px;color:var(--text-3);margin-top:2px;line-height:1.45}
.card-body{padding:20px 22px}
.card-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;width:100%}
.fg{display:flex;flex-direction:column;gap:5px;margin-bottom:14px}
.fl{font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--text-3)}
.fh{font-size:11px;color:var(--text-3);line-height:1.4;margin-top:3px}
.fi{padding:9px 11px;border:1.5px solid var(--border);border-radius:var(--radius-sm);font-family:inherit;font-size:13px;color:var(--text);background:var(--surface);outline:none;transition:border-color .15s;width:100%}
.fi:focus{border-color:var(--verde-border)}
.fs{padding:9px 11px;border:1.5px solid var(--border);border-radius:var(--radius-sm);font-family:inherit;font-size:13px;color:var(--text);background:var(--surface);outline:none;cursor:pointer;width:100%}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}
.ig{display:flex;border:1.5px solid var(--border);border-radius:var(--radius-sm);overflow:hidden;transition:border-color .15s}
.ig:focus-within{border-color:var(--verde-border)}
.ig-pre{padding:9px 11px;background:var(--surface2);font-size:12px;color:var(--text-3);border-right:1.5px solid var(--border);white-space:nowrap;display:flex;align-items:center;gap:5px}
.ig input,.ig select{flex:1;padding:9px 11px;border:none;font-family:inherit;font-size:13px;color:var(--text);background:var(--surface);outline:none}
.ig select{flex:0 0 auto;padding:9px 16px 9px 9px;border-right:1.5px solid var(--border);font-size:12px;background:var(--surface2);cursor:pointer}
.cp-row{display:flex;align-items:center;gap:9px}
.cp-btn{width:38px;height:38px;border-radius:8px;border:1.5px solid var(--border);cursor:pointer;padding:2px;overflow:hidden;flex-shrink:0}
.cp-btn input[type=color]{width:100%;height:100%;border:none;background:transparent;cursor:pointer;padding:0;border-radius:5px}
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:999px;font-size:13px;font-weight:600;cursor:pointer;border:none;font-family:inherit;transition:all .15s;white-space:nowrap;line-height:1.3}
.btn-p{background:var(--verde);color:#0F1F14}
.btn-p:hover{background:var(--verde-d)}
.btn-sm{padding:6px 14px;font-size:12px}
.btn-danger-text{background:transparent;border:none;color:#C0392B;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;padding:0}
.social-head{display:flex;align-items:center;justify-content:space-between;gap:12px}
.social-item{display:grid;grid-template-columns:160px 1fr auto;gap:9px;align-items:center;padding:10px 0;border-bottom:1.5px solid var(--border)}
.social-item:last-child{border-bottom:none;padding-bottom:0}
.save-row{display:flex;align-items:center;gap:10px;margin-top:6px}
.ok-msg{font-size:12px;color:#1a7a35;font-weight:600}
.err-msg{font-size:12px;color:#c0392b;font-weight:600}

:deep(.agency-logo-upload .max-h-\[320px\]){max-height:190px !important;min-height:150px !important}
:deep(.agency-logo-upload .min-h-\[220px\]){min-height:150px !important}
:deep(.agency-logo-upload img){max-height:150px !important;object-fit:contain}

@media(max-width:900px){.page-wrap{padding:20px 16px 40px}.page-topbar{flex-direction:column;align-items:flex-start}}
@media(max-width:768px){.card-row{grid-template-columns:1fr}}
@media(max-width:600px){.grid2,.grid3,.social-item{grid-template-columns:1fr}}
</style>
