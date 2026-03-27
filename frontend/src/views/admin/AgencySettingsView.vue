<template>
  <div class="agency-settings w-full space-y-6 px-4 py-8 md:px-8">
    <div>
      <p class="text-sm uppercase tracking-wide text-slate-500">Agência</p>
      <h1 class="text-3xl font-bold text-slate-900">Configurações</h1>
    </div>

    <div class="rounded-2xl bg-white p-6 shadow-md">
      <form class="space-y-4" @submit.prevent="save">
        <div class="grid gap-4 md:grid-cols-2">
          <div class="md:pl-2">
            <label class="text-sm font-semibold text-slate-600">Nome</label>
            <input v-model="form.name" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" />
          </div>

          <div>
            <label class="text-sm font-semibold text-slate-600">Slug</label>
            <div class="mt-1 space-y-1">
              <input v-model="form.slug" class="w-full rounded-lg border border-slate-200 px-3 py-2" />
              <p class="text-xs text-slate-500">
                Slug é a parte do link depois da barra, sem espaços ou acentos. Ex.: minha-agencia-incrivel.
              </p>
            </div>
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-3">
          <label class="space-y-2 text-xs font-semibold text-slate-500 md:pl-2 md:pt-4">
            CNPJ
            <input
              v-model="companyForm.cnpj"
              type="text"
              placeholder="00.000.000/0000-00"
              class="w-full rounded-lg border border-slate-200 px-4 py-3 text-sm"
            />
          </label>
          <div class="space-y-2 md:pl-2">
            <label class="text-sm font-semibold text-slate-600">WhatsApp da agência</label>
            <div class="space-y-2">
              <div class="flex gap-2">
                <div class="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2">
                  <span class="text-sm font-semibold text-slate-700">BR</span>
                  <span class="text-sm font-semibold text-slate-700">+55</span>
                </div>
                <input
                  v-model="phoneInput"
                  placeholder="11999999999"
                  class="w-full rounded-lg border border-slate-200 px-3 py-2"
                  inputmode="numeric"
                />
              </div>

              <p class="text-xs text-slate-500">
                Usamos esse numero como padrao para os links de WhatsApp nos CTAs.
              </p>

              <div class="flex flex-col gap-1 text-sm">
                <span v-if="phoneMessage" class="text-emerald-600">{{ phoneMessage }}</span>
                <span v-if="phoneError" class="text-red-500">{{ phoneError }}</span>
              </div>
            </div>
          </div>

          <div class="space-y-2 md:pl-2">
            <label class="text-sm font-semibold text-slate-600">Cor primária</label>
            <div class="space-y-2">
              <div class="flex items-center gap-3">
                <input
                  type="color"
                  v-model="form.primary_color"
                  class="h-10 w-12 cursor-pointer rounded border border-slate-200 bg-white"
                />
                <input
                  v-model="form.primary_color"
                  placeholder="#41ce5f"
                  class="flex-1 rounded-lg border border-slate-200 px-3 py-2"
                />
              </div>
              <p class="text-xs text-slate-500">
                Essa cor sera usada como base nos CTAs do editor. Voce pode ajustar depois.
              </p>
            </div>
          </div>
        </div>

        <div class="grid gap-6 lg:grid-cols-2">
          <div class="md:pl-2">
            <ImageUploadField
              class="agency-logo-upload"
              v-model="form.logo_url"
              label="Logo da agencia"
              hint="Envie o arquivo da sua marca. Ela aparece no editor e nas paginas."
              :enable-crop="true"
              editor-title="Refine a logo da agencia"
            />
          </div>
          <div class="space-y-4 md:pl-2">
            <div class="space-y-1 md:pl-0">
              <label class="text-sm font-semibold text-slate-600">Redes sociais</label>
              <p class="text-xs text-slate-500">
                Informe os links das redes que irão aparecer nas paginas públicas e templates.
              </p>
            </div>

            <div class="space-y-4">
              <div class="space-y-3">
                <div
                  v-if="!form.social_links.length"
                  class="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500 dark:border-white/20 dark:bg-transparent dark:text-white/70"
                >
                  Nenhuma rede social adicionada ainda.
                </div>

                <div
                  v-for="(social, index) in form.social_links"
                  :key="social.id ?? `social-${index}`"
                  class="space-y-3 rounded-2xl border border-slate-200/80 bg-slate-50/60 p-4 dark:border-white/10 dark:bg-transparent"
                >
                  <div class="flex flex-col gap-3 md:flex-row md:items-end">
                    <label class="flex-1 text-xs font-semibold text-slate-500 dark:text-white/70">
                      Rede
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
                      Link
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
                      Remover
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
                Adicionar rede
              </button>
            </div>
          </div>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <label class="space-y-1 text-xs font-semibold text-slate-500 md:pl-2">
            CEP
            <input
              v-model="companyForm.address_zipcode"
              type="text"
              placeholder="00000-000"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              :disabled="isFetchingCep"
              @blur="handleCepBlur"
            />
            <p class="text-[11px] text-slate-500">
              Informe o CEP e completaremos rua, bairro, cidade e UF automaticamente. Você precisa preencher apenas número e complemento.
            </p>
            <div class="text-[11px]">
              <span v-if="isFetchingCep" class="text-slate-500">Buscando endereço pelo CEP...</span>
              <span v-else-if="cepError" class="text-red-500">{{ cepError }}</span>
              <span v-else-if="cepMessage" class="text-emerald-600">{{ cepMessage }}</span>
            </div>
          </label>

          <label class="space-y-1 text-xs font-semibold text-slate-500">
            Endereço / Rua
            <input
              v-model="companyForm.address_street"
              type="text"
              placeholder="Rua, avenida, estrada..."
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>
          <label class="space-y-1 text-xs font-semibold text-slate-500 md:pl-2">
            Bairro
            <input
              v-model="companyForm.address_neighborhood"
              type="text"
              placeholder="Bairro"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>

          <label class="space-y-1 text-xs font-semibold text-slate-500 md:pl-2">
            Cidade
            <input
              v-model="companyForm.address_city"
              type="text"
              placeholder="Cidade"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>

          <div class="grid gap-4 md:grid-cols-3 md:col-span-2 md:pl-2">
            <label class="space-y-1 text-xs font-semibold text-slate-500">
              UF
              <input
                v-model="companyForm.address_state"
                type="text"
                maxlength="2"
                placeholder="SP"
                class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm uppercase"
              />
            </label>
            <label class="space-y-1 text-xs font-semibold text-slate-500">
              Número
              <input
                v-model="companyForm.address_number"
                type="text"
                placeholder="123"
                class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </label>
            <label class="space-y-1 text-xs font-semibold text-slate-500">
              Complemento
              <input
                v-model="companyForm.address_complement"
                type="text"
                placeholder="Sala, bloco..."
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
            {{ saving ? "Salvando..." : (hasAgency ? "Salvar" : "Criar ag�ncia") }}
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

const agencyStore = useAgencyStore();
const authStore = useAuthStore();

const colorPalette = ["#41ce5f", "#2563eb", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444", "#0f172a"];
const socialNetworkOptions = [
  { label: "Instagram", value: "instagram" },
  { label: "Facebook", value: "facebook" },
  { label: "YouTube", value: "youtube" },
  { label: "TikTok", value: "tiktok" }
] as const;

type SocialNetworkValue = (typeof socialNetworkOptions)[number]["value"];

const socialNetworkPlaceholders: Record<SocialNetworkValue, string> = {
  instagram: "https://instagram.com/sua-agencia",
  facebook: "https://facebook.com/sua-agencia",
  youtube: "https://youtube.com/@sua-agencia",
  tiktok: "https://tiktok.com/@sua-agencia"
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
      throw new Error("CEP nao encontrado.");
    }

    fillAddressFromCep(data);
    cepMessage.value = "Endereco preenchido automaticamente pelo CEP.";
  } catch (err) {
    console.error(err);
    cepError.value = "Nao conseguimos localizar esse CEP.";
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
    cepError.value = "CEP precisa ter 8 digitos.";
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
  if (!value) return null;
  const trimmed = value.trim();
  return trimmed || null;
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
  phoneInput.value = fallbackPhone.replace(/\D/g, "");

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
    passwordError.value = "Informe todas as senhas.";
    return;
  }
  if (passwordForm.new !== passwordForm.confirm) {
    passwordError.value = "As senhas novas precisam coincidir.";
    return;
  }
  passwordSaving.value = true;
  try {
    await api.post("/auth/me/password", {
      current_password: passwordForm.current,
      new_password: passwordForm.new
    });
    passwordMessage.value = "Senha atualizada com sucesso.";
    passwordForm.current = "";
    passwordForm.new = "";
    passwordForm.confirm = "";
  } catch (err) {
    console.error(err);
    passwordError.value =
      (err as any)?.response?.data?.detail || "N�o foi poss�vel atualizar a senha.";
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
    errorMessage.value = "Informe nome e slug.";
    return;
  }

  const normalizedName = form.name.trim();
  const normalizedSlug = form.slug.trim().toLowerCase();

  const phoneDigits = sanitizeDigits(phoneInput.value);
  if (phoneDigits && phoneDigits.length < 10) {
    phoneError.value = "Informe um telefone v�lido para os CTAs.";
    return;
  }

  form.name = normalizedName;
  form.slug = normalizedSlug;
  form.cta_whatsapp = phoneDigits || "";

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

    phoneMessage.value = phoneDigits ? "Telefone salvo para os CTAs." : "Telefone removido dos CTAs.";
    message.value = createdAgency ? "Agência criada." : "Configurações atualizadas.";
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    errorMessage.value = detail || "Não foi possível salvar/criar. Verifique login e permissões.";
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
