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
                placeholder="#0ea5e9"
                class="w-full rounded-lg border border-slate-200 px-3 py-2"
              />
            </div>
            <p class="text-xs text-slate-500">Essa cor será usada como base nos CTAs do editor. Você pode ajustar depois.</p>
          </div>
        </div>

        <ImageUploadField
          v-model="form.logo_url"
          label="Logo da agência"
          hint="Envie o arquivo da sua marca. Ela aparece no editor e nas páginas."
          :enable-crop="true"
          editor-title="Refine a logo da agência"
        />

        <div class="mt-8 space-y-2 border-t border-slate-100 pt-4">
          <div class="space-y-1">
            <p class="text-sm uppercase tracking-wide text-slate-500">Contato</p>
          </div>

          <div class="mt-4 max-w-md space-y-2">
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
            <p class="text-xs text-slate-500">Usamos esse número como padrão para os links de WhatsApp nos CTAs.</p>
            <div class="flex flex-col gap-1 text-sm">
              <span v-if="phoneMessage" class="text-emerald-600">{{ phoneMessage }}</span>
              <span v-if="phoneError" class="text-red-500">{{ phoneError }}</span>
            </div>
          </div>
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
import { onMounted, reactive, ref } from "vue";
import ImageUploadField from "../../components/admin/inputs/ImageUploadField.vue";
import api from "../../services/api";
import { useAgencyStore } from "../../store/useAgencyStore";
import { useAuthStore } from "../../store/useAuthStore";

const agencyStore = useAgencyStore();
const authStore = useAuthStore();
const colorPalette = ["#0ea5e9", "#2563eb", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444", "#0f172a", "#111827"];

const form = reactive({
  id: 0,
  name: "",
  slug: "",
  logo_url: "",
  primary_color: colorPalette[0],
  secondary_color: ""
});
const hasAgency = ref(false);
const saving = ref(false);
const message = ref("");
const errorMessage = ref("");
const phoneMessage = ref("");
const phoneError = ref("");
const phoneInput = ref("");

const syncFormWithCurrent = () => {
  const agency = agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId);
  if (agency) Object.assign(form, agency);
  if (!form.primary_color) form.primary_color = colorPalette[0];
  phoneInput.value = (authStore.user?.whatsapp || "").replace(/\D/g, "");
};

const load = async () => {
  errorMessage.value = "";
  message.value = "";
  phoneMessage.value = "";
  phoneError.value = "";
  await authStore.fetchProfile();
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
  const digits = (phoneInput.value || "").replace(/\D/g, "");
  form.name = normalizedName;
  form.slug = normalizedSlug;
  const payload = {
    name: normalizedName,
    slug: normalizedSlug,
    logo_url: form.logo_url,
    primary_color: form.primary_color,
    secondary_color: form.secondary_color
  };
  try {
    saving.value = true;
    if (agencyStore.currentAgencyId) {
      const res = await api.put(`/agencies/${agencyStore.currentAgencyId}`, payload);
      Object.assign(form, res.data);
      message.value = "Agência atualizada.";
    } else {
      const res = await api.post("/agencies", payload);
      await agencyStore.loadAgencies();
      agencyStore.currentAgencyId = res.data.id;
      hasAgency.value = true;
      syncFormWithCurrent();
      message.value = "Ag?ncia criada.";
    }
    if (digits) {
      const updated = await updateUserPhone(digits);
      if (updated) {
        phoneMessage.value = "Telefone atualizado.";
      }
    }
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail;
    errorMessage.value = detail || "N?o foi poss?vel salvar/criar. Verifique login e permiss?es.";
  } finally {
    saving.value = false;
  }
};


onMounted(load);

const updateUserPhone = async (digits: string) => {
  try {
    const res = await api.put("/auth/me", { whatsapp: digits });
    authStore.user = res.data;
    phoneError.value = "";
    return true;
  } catch (err) {
    console.error(err);
    phoneError.value = "N?o foi possivel salvar o telefone.";
    return false;
  }
};
</script>
