<template>
  <AdminMasterDrawer
    :open="open"
    title="Nova empresa"
    subtitle="Cria a conta do dono já ativa, com a empresa e a assinatura prontas para usar."
    icon="building"
    @close="close"
  >
    <form id="create-company-form" class="space-y-3.5" @submit.prevent="submit">
      <div class="am-field">
        <label for="cc-name">Nome do dono</label>
        <input id="cc-name" v-model="form.name" required minlength="2" type="text" autocomplete="off" class="am-input" />
      </div>
      <div class="grid gap-3.5 sm:grid-cols-2">
        <div class="am-field">
          <label for="cc-email">E-mail</label>
          <input id="cc-email" v-model="form.email" required type="email" autocomplete="off" class="am-input" />
        </div>
        <div class="am-field">
          <label for="cc-whats">WhatsApp</label>
          <input id="cc-whats" v-model="form.whatsapp" type="tel" autocomplete="off" placeholder="(00) 00000-0000" class="am-input" />
        </div>
        <div class="am-field">
          <label for="cc-plan">Plano</label>
          <select id="cc-plan" v-model="form.plan" required class="am-input">
            <option v-for="option in planOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </div>
        <div class="am-field">
          <label for="cc-valid">Validade</label>
          <input id="cc-valid" v-model="form.validUntil" required :min="today" type="date" class="am-input" />
        </div>
      </div>
      <div class="am-field">
        <label for="cc-pass">Senha inicial</label>
        <input id="cc-pass" v-model="form.password" required minlength="8" type="password" autocomplete="new-password" class="am-input" />
        <p class="am-card-sub">Mínimo de 8 caracteres, com letra maiúscula, minúscula e número.</p>
      </div>
      <div v-if="error" class="am-notice am-tone-danger"><AmIcon name="alert" /><span>{{ error }}</span></div>
    </form>
    <template #footer>
      <button type="button" class="am-btn" :disabled="saving" @click="close">Cancelar</button>
      <button type="submit" form="create-company-form" class="am-btn am-btn-primary" :disabled="saving">
        {{ saving ? "Criando..." : "Criar empresa" }}
      </button>
    </template>
  </AdminMasterDrawer>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import api from "../../../services/api";
import AmIcon from "../master/AmIcon.vue";
import AdminMasterDrawer from "../master/AdminMasterDrawer.vue";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ (e: "close"): void; (e: "created", message: string): void }>();

const planOptions = [
  { value: "essencial", label: "Profissional" },
  { value: "growth", label: "Agência" },
  { value: "infinity", label: "Escala" },
  { value: "free", label: "Começo (gratuito)" },
  { value: "teste", label: "Teste (interno)" }
];
const today = new Date().toLocaleDateString("en-CA");
const blank = () => ({ name: "", email: "", whatsapp: "", plan: "essencial", validUntil: "", password: "" });
const form = reactive(blank());
const saving = ref(false);
const error = ref("");

watch(
  () => props.open,
  open => {
    if (!open) return;
    Object.assign(form, blank());
    error.value = "";
  }
);

const close = () => {
  if (!saving.value) emit("close");
};

const submit = async () => {
  saving.value = true;
  error.value = "";
  try {
    await api.post("/admin/users", {
      name: form.name.trim(),
      email: form.email.trim().toLowerCase(),
      whatsapp: form.whatsapp.trim() || null,
      password: form.password,
      plan: form.plan,
      valid_until: form.validUntil
    });
    emit("created", `Empresa de ${form.name.trim()} criada.`);
    emit("close");
  } catch (err: any) {
    error.value = err?.response?.data?.detail || "Não foi possível criar a empresa.";
  } finally {
    saving.value = false;
  }
};
</script>
