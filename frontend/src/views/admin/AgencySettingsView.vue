<template>
  <div class="w-full space-y-6 px-4 py-8 md:px-8">
    <div>
      <p class="text-sm uppercase tracking-wide text-slate-500">Agência</p>
      <h1 class="text-3xl font-bold text-slate-900">Configurações</h1>
    </div>

    <div class="rounded-2xl bg-white p-6 shadow-md">
      <form class="space-y-4" @submit.prevent="save">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
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

        <div>
          <label class="text-sm font-semibold text-slate-600">Cor primária</label>
          <div class="mt-2 space-y-3">
            <div class="flex flex-wrap gap-2">
              <button
                v-for="color in colorPalette"
                :key="color"
                type="button"
                class="flex h-10 w-10 items-center justify-center rounded-full border transition"
                :class="form.primary_color === color ? 'ring-2 ring-emerald-400 border-transparent' : 'border-slate-200'"
                :style="{ background: color }"
                @click="form.primary_color = color"
                :aria-label="`Cor ${color}`"
              ></button>
            </div>

            <div class="flex items-center gap-2">
              <input
                type="color"
                v-model="form.primary_color"
                class="h-10 w-12 cursor-pointer rounded border border-slate-200 bg-white"
              />
              <input
                v-model="form.primary_color"
                placeholder="#41ce5f"
                class="w-full rounded-lg border border-slate-200 px-3 py-2"
              />
            </div>

            <p class="text-xs text-slate-500">
              Essa cor será usada como base nos CTAs do editor. Você pode ajustar depois.
            </p>
          </div>
        </div>

        <div class="grid gap-6 lg:grid-cols-2">
          <div>
            <ImageUploadField
              v-model="form.logo_url"
              label="Logo da agência"
              hint="Envie o arquivo da sua marca. Ela aparece no editor e nas páginas."
              :enable-crop="true"
              editor-title="Refine a logo da agência"
            />
          </div>

          <div class="space-y-4 rounded-2xl border border-slate-100 p-4">
            <div class="space-y-2">
              <label class="text-sm font-semibold text-slate-600">WhatsApp da agência</label>
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
                Usamos esse número como padrão para os links de WhatsApp nos CTAs.
              </p>

              <div class="flex flex-col gap-1 text-sm">
                <span v-if="phoneMessage" class="text-emerald-600">{{ phoneMessage }}</span>
                <span v-if="phoneError" class="text-red-500">{{ phoneError }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <label class="space-y-1 text-xs font-semibold text-slate-500 md:col-span-2">
            CNPJ
            <input
              v-model="companyForm.cnpj"
              type="text"
              placeholder="00.000.000/0000-00"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>

          <label class="space-y-1 text-xs font-semibold text-slate-500 md:col-span-2">
            Endereço / Rua
            <input
              v-model="companyForm.address_street"
              type="text"
              placeholder="Rua, avenida, estrada..."
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
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

          <label class="space-y-1 text-xs font-semibold text-slate-500">
            Bairro
            <input
              v-model="companyForm.address_neighborhood"
              type="text"
              placeholder="Bairro"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>

          <label class="space-y-1 text-xs font-semibold text-slate-500">
            Cidade
            <input
              v-model="companyForm.address_city"
              type="text"
              placeholder="Cidade"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>

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
            CEP
            <input
              v-model="companyForm.address_zipcode"
              type="text"
              placeholder="00000-000"
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </label>
        </div>

        <div class="flex items-center gap-3 pt-2">
          <button
            type="submit"
            class="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-slate-300"
            :disabled="saving"
          >
            {{ saving ? "Salvando..." : (hasAgency ? "Salvar" : "Criar agência") }}
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

const agencyStore = useAgencyStore();
const authStore = useAuthStore();

const colorPalette = ["#41ce5f", "#2563eb", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444", "#0f172a", "#111827"];

const form = reactive({
  id: 0,
  name: "",
  slug: "",
  logo_url: "",
  primary_color: colorPalette[0],
  secondary_color: "",
  cta_whatsapp: ""
});

const hasAgency = ref(false);
const saving = ref(false);
const message = ref("");
const errorMessage = ref("");

const phoneMessage = ref("");
const phoneError = ref("");
const phoneInput = ref("");
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
};

const syncFormWithCurrent = () => {
  const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  if (agency) Object.assign(form, agency);

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
      (err as any)?.response?.data?.detail || "Não foi possível atualizar a senha.";
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
    phoneError.value = "Informe um telefone válido para os CTAs.";
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
    cta_whatsapp: phoneDigits
  };

  let createdAgency = false;

  try {
    saving.value = true;

    if (agencyStore.currentAgencyId) {
      const res = await api.put(`/agencies/${agencyStore.currentAgencyId}`, payload);
      Object.assign(form, res.data);
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
    if (value !== masked) companyForm.address_zipcode = masked;
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
