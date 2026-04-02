<template>
  <div class="agency-settings w-full space-y-6 px-4 py-8 md:px-8">
    <div>
      <p class="text-sm uppercase tracking-wide text-slate-500">{{ viewCopy.hero.eyebrow }}</p>
      <h1 class="text-3xl font-bold text-slate-900">{{ viewCopy.hero.title }}</h1>
    </div>

    <div class="rounded-2xl bg-white p-6 shadow-md">
      <form class="space-y-4" @submit.prevent="save">
        <div class="grid gap-4 md:grid-cols-2">
          <div class="md:pl-2">
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.general.nameLabel }}</label>
            <input v-model="form.name" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
          </div>

          <div>
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.general.slugLabel }}</label>
            <div class="mt-1 space-y-1">
              <input v-model="form.slug" class="w-full rounded-lg border border-slate-200 px-3 py-2" />
              <p class="text-xs text-slate-500">
                {{ viewCopy.general.slugHint }}
              </p>
            </div>
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-3">
          <label class="space-y-2 text-xs font-semibold text-slate-500 md:pl-2 md:pt-4">
            {{ viewCopy.company.cnpjLabel }}
            <input
              v-model="companyForm.cnpj"
              type="text"
              :placeholder="viewCopy.company.cnpjPlaceholder"
              class="w-full rounded-lg border border-slate-200 px-4 py-3 text-sm"
            />
          </label>
          <div class="space-y-2 md:pl-2">
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.contact.whatsappLabel }}</label>
            <div class="space-y-2">
              <div class="flex gap-2">
                <div class="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2">
                  <span class="text-sm font-semibold text-slate-700">BR</span>
                  <span class="text-sm font-semibold text-slate-700">+55</span>
                </div>
                <input
                  v-model="phoneInput"
                  :placeholder="viewCopy.contact.whatsappPlaceholder"
                  class="w-full rounded-lg border border-slate-200 px-3 py-2"
                  inputmode="numeric"
                />
              </div>

              <p class="text-xs text-slate-500">
                {{ viewCopy.contact.whatsappHelper }}
              </p>

              <div class="flex flex-col gap-1 text-sm">
                <span v-if="phoneMessage" class="text-emerald-600">{{ phoneMessage }}</span>
                <span v-if="phoneError" class="text-red-500">{{ phoneError }}</span>
              </div>
            </div>
          </div>

          <div class="space-y-2 md:pl-2">
            <label class="text-sm font-semibold text-slate-600">{{ viewCopy.theme.primaryColorLabel }}</label>
            <div class="space-y-2">
              <div class="flex items-center gap-3">
                <input
                  type="color"
                  v-model="form.primary_color"
                  class="h-10 w-12 cursor-pointer rounded border border-slate-200 bg-white"
                />
                <input
                  v-model="form.primary_color"
                  :placeholder="viewCopy.theme.primaryColorPlaceholder"
                  class="flex-1 rounded-lg border border-slate-200 px-3 py-2"
                />
              </div>
              <p class="text-xs text-slate-500">
                {{ viewCopy.theme.primaryColorHint }}
              </p>
            </div>
          </div>
        </div>

        <div class="grid gap-6 lg:grid-cols-2">
          <div class="md:pl-2">
            <ImageUploadField
              class="agency-logo-upload"
              v-model="form.logo_url"
              :label="viewCopy.logoField.label"
              :hint="viewCopy.logoField.hint"
              :enable-crop="true"
              :editor-title="viewCopy.logoField.editorTitle"
            />
          </div>
          <div class="space-y-4 md:pl-2">
            <div class="space-y-1 md:pl-0">
              <label class="text-sm font-semibold text-slate-600">{{ viewCopy.socialSection.label }}</label>
              <p class="text-xs text-slate-500">
                {{ viewCopy.socialSection.helper }}
              </p>
            </div>

            <div class="space-y-4">
              <div class="space-y-3">
                <div
                  v-if="!form.social_links.length"
                  class="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500 dark:border-white/20 dark:bg-transparent dark:text-white/70"
                >
                  {{ viewCopy.socialSection.empty }}
                </div>

                <div
                  v-for="(social, index) in form.social_links"
                  :key="social.id ?? `social-${index}`"
                  class="space-y-3 rounded-2xl border border-slate-200/80 bg-slate-50/60 p-4 dark:border-white/10 dark:bg-transparent"
                >
                  <div class="flex flex-col gap-3 md:flex-row md:items-end">
                    <label class="flex-1 text-xs font-semibold text-slate-500 dark:text-white/70">
                      {{ viewCopy.socialSection.networkLabel }}
                      <select
                        v-model="social.network"
                        class="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/15 dark:bg-[#05070f] dark:text-white"
                      >
                        <option v-for="option in socialNetworkOptions" :key="option.value" :value="option.value">
                          {{ option.label }}
                        </option>
                      </select>
                    </label>

                    <label class="flex-[2] text-xs font-semibold text-slate-500 dark:text-white/70">
                      {{ viewCopy.socialSection.linkLabel }}
                      <input
                        v-model="social.url"
                        type="url"
                        :placeholder="socialNetworkPlaceholders[social.network]"
                        class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm dark:border-white/15 dark:bg-[#05070f] dark:text-white dark:placeholder-white/60"
                      />
                    </label>

                    <button
                      type="button"
                      class="text-sm font-semibold text-slate-500 hover:text-red-500 dark:text-white/80 dark:hover:text-red-400"
                      @click="removeSocialLink(index)"
                    >
                      {{ viewCopy.socialSection.removeButton }}
                    </button>
                  </div>
                </div>
              </div>

              <button
                type="button"
                class="flex items-center gap-2 rounded-full bg-[#2F9E49] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#26843a]"
                @click="addSocialLink"
              >
                <span class="text-lg leading-none">+</span>
                {{ viewCopy.socialSection.addButton }}
              </button>
            </div>
          </div>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <label class="space-y-1 text-xs font-semibold text-slate-500 md:pl-2">
            {{ viewCopy.address.cepLabel }}
            <input
              v-model="companyForm.address_zipcode"
              type="text"
              :placeholder="viewCopy.address.cepPlaceholder"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              :disabled="isFetchingCep"
              @blur="handleCepBlur"
            />
            <p class="text-[11px] text-slate-500">
              {{ viewCopy.address.cepHelper }}
            </p>
            <div class="text-[11px]">
              <span v-if="isFetchingCep" class="text-slate-500">{{ viewCopy.cep.fetching }}</span>
              <span v-else-if="cepError" class="text-red-500">{{ cepError }}</span>
              <span v-else-if="cepMessage" class="text-emerald-600">{{ cepMessage }}</span>
            </div>
          </label>

          <label class="space-y-1 text-xs font-semibold text-slate-500">
            {{ viewCopy.address.streetLabel }}
            <input
              v-model="companyForm.address_street"
              type="text"
              :placeholder="viewCopy.address.streetPlaceholder"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>
          <label class="space-y-1 text-xs font-semibold text-slate-500 md:pl-2">
            {{ viewCopy.address.neighborhoodLabel }}
            <input
              v-model="companyForm.address_neighborhood"
              type="text"
              :placeholder="viewCopy.address.neighborhoodPlaceholder"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>

          <label class="space-y-1 text-xs font-semibold text-slate-500 md:pl-2">
            {{ viewCopy.address.cityLabel }}
            <input
              v-model="companyForm.address_city"
              type="text"
              :placeholder="viewCopy.address.cityPlaceholder"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>

          <div class="grid gap-4 md:grid-cols-3 md:col-span-2 md:pl-2">
            <label class="space-y-1 text-xs font-semibold text-slate-500">
              {{ viewCopy.address.stateLabel }}
              <input
                v-model="companyForm.address_state"
                type="text"
                maxlength="2"
                :placeholder="viewCopy.address.statePlaceholder"
                class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm uppercase"
              />
            </label>
            <label class="space-y-1 text-xs font-semibold text-slate-500">
              {{ viewCopy.address.numberLabel }}
              <input
                v-model="companyForm.address_number"
                type="text"
                :placeholder="viewCopy.address.numberPlaceholder"
                class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </label>
            <label class="space-y-1 text-xs font-semibold text-slate-500">
              {{ viewCopy.address.complementLabel }}
              <input
                v-model="companyForm.address_complement"
                type="text"
                :placeholder="viewCopy.address.complementPlaceholder"
                class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </label>
          </div>
        </div>

        <div class="flex items-center gap-3 pt-2 md:pl-2">
          <button
            type="submit"
            class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-slate-300"
            :disabled="saving"
          >
            {{ saving ? viewCopy.actions.saving : (hasAgency ? viewCopy.actions.save : viewCopy.actions.create) }}
          </button>

          <span v-if="message" class="text-sm text-emerald-600">{{ message }}</span>
          <span v-if="errorMessage" class="text-sm text-red-500">{{ errorMessage }}</span>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import ImageUploadField from "../../components/admin/inputs/ImageUploadField.vue";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import { useAuthStore } from "../../store/useAuthStore";
import { addTagsToContactByEmail, viajeChatTagIds } from "../../services/viajeChat";
import { createAdminLocalizer } from "../../utils/adminI18n";
import { normalizeWhatsappDigits } from "../../utils/whatsapp";

const agencyStore = useAgencyStore();
const authStore = useAuthStore();

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
    cnpjLabel: t({ pt: "CNPJ", es: "CNPJ" }),
    cnpjPlaceholder: t({ pt: "00.000.000/0000-00", es: "00.000.000/0000-00" })
  },
  contact: {
    whatsappLabel: t({ pt: "WhatsApp da agência", es: "WhatsApp de la agencia" }),
    whatsappPlaceholder: t({ pt: "11999999999", es: "11999999999" }),
    whatsappHelper: t({
      pt: "Usamos esse número como padrão para os links de WhatsApp nos CTAs.",
      es: "Usamos este número como predeterminado para los enlaces de WhatsApp en los CTAs."
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

const socialNetworkPlaceholders: Record<SocialNetworkValue, string> = {
  instagram: viewCopy.socialSection.placeholders.instagram,
  facebook: viewCopy.socialSection.placeholders.facebook,
  youtube: viewCopy.socialSection.placeholders.youtube,
  tiktok: viewCopy.socialSection.placeholders.tiktok
};

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

const form = reactive({
  id: 0,
  name: "",
  slug: "",
  logo_url: "",
  primary_color: colorPalette[0],
  secondary_color: "",
  cta_whatsapp: "",
  social_links: [] as SocialLinkFormEntry[]
});

const hasAgency = ref(false);
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

const companyForm = reactive({
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
  if (!links?.length) return [];
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

const formatCnpj = (cnpj?: string | null) => {
  if (!cnpj) return "";
  const digits = cnpj.replace(/\D/g, "").slice(0, 14);
  return digits
    .replace(/(\d{2})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1/$2")
    .replace(/(\d{4})(\d{1,2})$/, "$1-$2");
};

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
  companyForm.cnpj = formatCnpj(profile?.cnpj || "");
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

  const fallbackPhone = form.cta_whatsapp || authStore.user?.whatsapp || "";
  const fallbackDigits = fallbackPhone.replace(/\D/g, "");
  phoneInput.value = fallbackDigits.replace(/^0?55/, "");

  syncCompanyData();
};

const saveCompanyData = async () => {
  const payload = {
    cnpj: sanitizeDigits(companyForm.cnpj),
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
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    errorMessage.value = detail || viewCopy.feedback.saveError;
  } finally {
    saving.value = false;
  }
};

watch(
  () => companyForm.cnpj,
  value => {
    const masked = formatCnpj(value || "");
    if (value !== masked) companyForm.cnpj = masked;
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

onMounted(load);
</script>

<style scoped>
:global(.dark-theme .agency-settings input:not([type='color']):not([type='checkbox']):not([type='radio']),
.dark-theme .agency-settings textarea,
.dark-theme .agency-settings select) {
  background-color: #05070f;
  border-color: rgba(255, 255, 255, 0.2);
  color: #f8fafc;
}
:global(.dark-theme .agency-settings input:not([type='color']):not([type='checkbox']):not([type='radio'])::placeholder,
.dark-theme .agency-settings textarea::placeholder,
.dark-theme .agency-settings select::placeholder) {
  color: rgba(248, 250, 252, 0.65);
}
:global(.dark-theme .agency-settings input[type='file']::file-selector-button),
:global(.dark-theme .agency-settings input[type='file']::-webkit-file-upload-button) {
  background-color: #05070f;
  border-color: rgba(255, 255, 255, 0.2);
  color: #f8fafc;
}
:global(.dark-theme .agency-settings input[type='color']) {
  background-color: #05070f;
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow: none;
}
:global(.dark-theme .agency-settings .agency-logo-upload > .rounded-xl) {
  border-color: rgba(255, 255, 255, 0.1);
  background-color: #05070f;
}
:global(.dark-theme .agency-settings .agency-logo-upload .overflow-hidden.border) {
  border-color: rgba(255, 255, 255, 0.15);
  background-color: #05070f;
}
</style>
