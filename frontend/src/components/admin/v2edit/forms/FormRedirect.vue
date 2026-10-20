<template>
  <V2EditShell>
    <template #content>
      <EdGroup title="Destino">
        <EdText
          :model-value="modelValue.url || ''"
          label="Endereço de destino"
          type="url"
          placeholder="https://chat.whatsapp.com/..."
          hint="Link do grupo do WhatsApp, Telegram ou outro site. Precisa começar com https://."
          @update:model-value="patch({ url: ($event || '').trim() })"
        />
        <p v-if="urlProblem" class="ved-info ved-warn">{{ urlProblem }}</p>
        <EdRange
          :model-value="seconds"
          label="Contagem"
          :min="1"
          :max="30"
          unit="s"
          hint="Com o pixel da página, use 3 segundos ou mais para a visita ser registrada antes de sair."
          @update:model-value="patch({ seconds: $event })"
        />
        <p class="ved-info">Na prévia a contagem fica parada. Na página publicada ela conta e abre o destino sozinha.</p>
      </EdGroup>

      <EdGroup title="Texto">
        <EdText :model-value="title" label="Título" placeholder="Você está entrando no grupo VIP" @update:model-value="title = $event" />
        <EdText :model-value="subtitle" label="Subtítulo" placeholder="Ofertas e saídas confirmadas em primeira mão." @update:model-value="subtitle = $event" />
      </EdGroup>

      <EdGroup title="Logo e imagem">
        <EdToggle :model-value="modelValue.showLogo !== false" label="Mostrar o logo" @update:model-value="patch({ showLogo: $event })" />
        <ImageUploadField
          v-if="modelValue.showLogo !== false"
          layout="compact"
          label="Logo"
          contain
          enable-crop
          editor-title="Logo desta página"
          edit-label="Editar"
          remove-label="Usar o da agência"
          :model-value="modelValue.logoUrl || ''"
          :fallback-url="agencyLogo"
          :hint="modelValue.logoUrl ? 'Só nesta página.' : 'Logo da agência (Minha Agência). Trocar vale só para esta página.'"
          @update:model-value="patch({ logoUrl: $event || '' })"
        />
        <ImageUploadField layout="compact" enable-crop edit-label="Cortar" editor-title="Cortar foto" label="Imagem" hint="Opcional. Ideal 1600 × 1000 px." :model-value="modelValue.image || ''" @update:model-value="patch({ image: $event || '' })" />
      </EdGroup>

      <EdGroup title="Botão e aviso">
        <EdText :model-value="buttonText" label="Texto do botão" placeholder="Entrar agora" :maxlength="40" hint="Leva ao destino na hora, sem esperar a contagem." @update:model-value="buttonText = $event" />
        <EdText
          :model-value="fallbackText"
          label="Aviso se não abrir"
          placeholder="Não abriu sozinho? Toque no botão acima."
          hint="Aparece quando a contagem termina e o destino não abriu (ex.: app que bloqueia)."
          @update:model-value="fallbackText = $event"
        />
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed, inject, type Ref } from "vue";
import type { RedirectSection } from "../../../../types/page";
import { PUBLIC_BRANDING_KEY } from "../../../../utils/brandingKeys";
import { safeRedirectUrl } from "../../../../utils/redirectUrl";
import ImageUploadField from "../../inputs/ImageUploadField.vue";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdRange from "../EdRange.vue";
import EdText from "../EdText.vue";
import EdToggle from "../EdToggle.vue";
import V2EditShell from "../V2EditShell.vue";
import { useDraft } from "../useDraft";

const props = defineProps<{ modelValue: RedirectSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: RedirectSection): void }>();
const { patch, text } = useDraft(props, emit);
const title = text("title");
const subtitle = text("subtitle");
const buttonText = text("buttonText");
const fallbackText = text("fallbackText");
const seconds = computed(() => Math.min(30, Math.max(1, Math.round(Number(props.modelValue.seconds) || 5))));

const brandingRef = inject<Ref<Record<string, any>> | null>(PUBLIC_BRANDING_KEY, null);
const agencyLogo = computed(() => String(brandingRef?.value?.logo_url || ""));

const urlProblem = computed(() => {
  const url = String(props.modelValue.url || "").trim();
  if (!url) return "Sem destino a página não redireciona: preencha o endereço.";
  if (!safeRedirectUrl(url)) return "Endereço inválido: use o link completo, começando com https://.";
  return "";
});
</script>
