<template>
  <footer class="v2-mini-ft">
    <V2LegalInfo align="center" :company-name="companyName" :cnpj="cnpjText" :has-contacts="hasContacts" id="rodape-fino" />
  </footer>
</template>

<script setup lang="ts">
/**
 * Rodapé fino das páginas sem o Rodapé da agência ativo: só "© ano Empresa · CNPJ (i)",
 * com o aviso de responsabilidade no balão do (i), como no rodapé completo.
 */
import { computed, inject } from "vue";
import { PUBLIC_BRANDING_KEY } from "../../../utils/brandingKeys";
import V2LegalInfo from "./V2LegalInfo.vue";

const provided = inject(PUBLIC_BRANDING_KEY, null) as any;
const branding = computed<Record<string, any>>(() => (provided && "value" in provided ? provided.value : provided) || {});
const profile = computed<Record<string, any>>(() => branding.value?.agency_profile || {});
const companyName = computed(() => String(profile.value?.name || branding.value?.agency_name || ""));
const cnpjText = computed(() => {
  const digits = String(profile.value?.cnpj || "").replace(/\D/g, "").slice(0, 14);
  return digits
    ? digits.replace(/(\d{2})(\d)/, "$1.$2").replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d)/, "$1/$2").replace(/(\d{4})(\d{1,2})$/, "$1-$2")
    : "";
});
const hasContacts = computed(() => !!(profile.value?.phone || profile.value?.email));
</script>

<style scoped>
.v2-mini-ft {
  padding: 14px 20px calc(14px + env(safe-area-inset-bottom, 0px));
  background: #0e1a15;
  color: rgba(255, 255, 255, 0.72);
  font-family: Figtree, system-ui, sans-serif;
}
</style>
