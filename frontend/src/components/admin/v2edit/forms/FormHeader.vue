<template>
  <V2EditShell>
    <template #content>
      <EdGroup title="Logo">
        <p class="ved-info">Usa o logo da Capa da viagem ou, sem ele, o logo da agência (Minha Agência).</p>
      </EdGroup>
      <EdGroup title="Links" :count="`${links.length} de 7`">
        <EdList
          :items="links"
          :item-title="item => readText(item.label)"
          :new-item="newLink"
          add-label="Adicionar link"
          item-label="Link"
          :max="7"
          @update:items="patch({ links: $event })"
        >
          <template #default="{ item, update }">
            <EdText :model-value="readText(item.label)" label="Texto" placeholder="Roteiro" :maxlength="40" @update:model-value="update({ label: writeText(item.label, $event) })" />
            <EdSeg
              :model-value="item.targetType"
              label="Leva para"
              :options="[
                { value: 'section', label: 'Seção' },
                { value: 'page', label: 'Página' },
                { value: 'external', label: 'Link' }
              ]"
              @update:model-value="update({ targetType: $event, target: '' })"
            />
            <label v-if="item.targetType === 'section'" class="ved-field">
              <span class="ved-label">Seção</span>
              <select class="ved-select" :value="item.target" @change="update({ target: ($event.target as HTMLSelectElement).value })">
                <option value="">Escolher seção…</option>
                <option v-for="option in sectionOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
              </select>
            </label>
            <label v-else-if="item.targetType === 'page'" class="ved-field">
              <span class="ved-label">Página</span>
              <select class="ved-select" :value="item.target" @change="update({ target: ($event.target as HTMLSelectElement).value })">
                <option value="">{{ loadingPages ? "Carregando…" : "Escolher página…" }}</option>
                <option v-for="page in pages" :key="page.id" :value="pageUrl(page)">{{ page.title }}</option>
              </select>
            </label>
            <EdText v-else :model-value="item.target" label="Endereço" type="url" placeholder="https://" @update:model-value="update({ target: $event })" />
            <EdToggle
              v-if="item.targetType !== 'section'"
              :model-value="!!item.openInNewTab"
              label="Abrir em nova aba"
              @update:model-value="update({ openInNewTab: $event })"
            />
          </template>
        </EdList>
      </EdGroup>
      <EdGroup title="Lado direito do menu">
        <EdSeg
          :model-value="modelValue.actionType || 'none'"
          :options="[
            { value: 'none', label: 'Nada' },
            { value: 'contact', label: 'Botão' },
            { value: 'social', label: 'Redes' }
          ]"
          @update:model-value="patch({ actionType: $event })"
        />
        <template v-if="modelValue.actionType === 'contact'">
          <EdText :model-value="readText(modelValue.contactLabel)" label="Texto do botão" placeholder="Falar no WhatsApp" @update:model-value="patch({ contactLabel: writeText(modelValue.contactLabel, $event) })" />
          <EdSeg
            :model-value="modelValue.contactType || 'whatsapp'"
            label="Ao clicar"
            :options="[
              { value: 'whatsapp', label: 'WhatsApp' },
              { value: 'link', label: 'Link' }
            ]"
            @update:model-value="patch({ contactType: $event, contactValue: '' })"
          />
          <template v-if="(modelValue.contactType || 'whatsapp') === 'whatsapp'">
            <EdText :model-value="modelValue.contactValue || ''" label="WhatsApp" type="tel" placeholder="(11) 99999-9999" @update:model-value="patch({ contactValue: $event })" />
            <EdText :model-value="modelValue.whatsappMessage || ''" label="Mensagem" multiline @update:model-value="patch({ whatsappMessage: $event })" />
          </template>
          <EdText v-else :model-value="modelValue.contactValue || ''" label="Link" type="url" placeholder="https://" @update:model-value="patch({ contactValue: $event })" />
        </template>
        <template v-else-if="modelValue.actionType === 'social'">
          <EdText
            v-for="network in socialNetworks"
            :key="network.id"
            :model-value="socialUrl(network.id)"
            :label="network.label"
            type="url"
            :placeholder="network.placeholder"
            @update:model-value="setSocial(network.id, $event)"
          />
          <p class="ved-hint">Só aparecem as redes preenchidas.</p>
        </template>
      </EdGroup>
    </template>
    <template #look>
      <EdGroup title="Estilo">
        <EdSeg
          :model-value="modelValue.mode || 'solid'"
          label="Fundo do menu"
          :options="[
            { value: 'solid', label: 'Sólido' },
            { value: 'transparent', label: 'Transparente' },
            { value: 'blurred', label: 'Desfoque' }
          ]"
          @update:model-value="setMode"
        />
        <p class="ved-hint">
          {{ hasHero ? "Transparente e desfoque ficam sobre a capa e ganham fundo ao rolar a página." : "Transparente e desfoque precisam de uma Capa da viagem ativa." }}
        </p>
        <EdBackground
          v-if="(modelValue.mode || 'solid') === 'solid'"
          :value="modelValue"
          fallback="#FFFFFF"
          @change="setBackground"
        />
      </EdGroup>
      <EdGroup title="Comportamento">
        <EdToggle :model-value="modelValue.stickyEnabled !== false" label="Fixar no topo ao rolar" @update:model-value="patch({ stickyEnabled: $event })" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed, inject, onMounted, ref } from "vue";
import type { HeaderLinkItem, HeaderSection, HeaderSocialLink, PageSection } from "../../../../types/page";
import { getReadableTextColor } from "../../../../utils/colorContrast";
import { sectionNameV2 } from "../../../../utils/sectionCatalogV2";
import { sectionsInjectionKey } from "../../sectionsContext";
import EdBackground from "../EdBackground.vue";
import EdGroup from "../EdGroup.vue";
import EdList from "../EdList.vue";
import EdSeg from "../EdSeg.vue";
import EdText from "../EdText.vue";
import EdToggle from "../EdToggle.vue";
import V2EditShell from "../V2EditShell.vue";
import { useAgencyPages } from "../useAgencyPages";
import { readText, useDraft, writeText } from "../useDraft";

const props = defineProps<{ modelValue: HeaderSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: HeaderSection): void }>();
const { patch } = useDraft(props, emit);

const links = computed(() => props.modelValue.links || []);
const newLink = (): HeaderLinkItem => ({ id: `header-link-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, label: "", targetType: "section", target: "" });

const sections = inject(sectionsInjectionKey, ref<PageSection[]>([]));
const sectionOptions = computed(() =>
  sections.value
    .map((section, index) => ({ section, index }))
    .filter(({ section }) => section?.anchorId && section.type !== "header" && section.enabled !== false)
    .map(({ section, index }) => ({ id: section.anchorId as string, label: `${index + 1}. ${sectionNameV2(section.type) || section.type}` }))
);
const hasHero = computed(() => sections.value.some(section => section?.type === "hero" && section.enabled !== false));

const { pages, loading: loadingPages, load: loadPages, pageUrl } = useAgencyPages();
onMounted(loadPages);

const socialNetworks: { id: HeaderSocialLink["platform"]; label: string; placeholder: string }[] = [
  { id: "instagram", label: "Instagram", placeholder: "https://instagram.com/suaagencia" },
  { id: "facebook", label: "Facebook", placeholder: "https://facebook.com/suaagencia" },
  { id: "youtube", label: "YouTube", placeholder: "https://youtube.com/@suaagencia" },
  { id: "tiktok", label: "TikTok", placeholder: "https://tiktok.com/@suaagencia" },
  { id: "linkedin", label: "LinkedIn", placeholder: "https://linkedin.com/company/suaagencia" }
];
const socialUrl = (platform: HeaderSocialLink["platform"]) => props.modelValue.socialLinks?.find(item => item.platform === platform)?.url || "";
const setSocial = (platform: HeaderSocialLink["platform"], url: string) => {
  const others = (props.modelValue.socialLinks || []).filter(item => item.platform !== platform);
  patch({ socialLinks: [...others, { platform, url }] });
};

// Sem capa ativa, só o fundo sólido funciona; as cores do texto acompanham o fundo.
const setMode = (mode: HeaderSection["mode"]) => {
  if (mode !== "solid" && !hasHero.value) return;
  patch(mode === "solid" ? { mode, linkTextColor: getReadableTextColor(props.modelValue.backgroundColor || "#ffffff") || "#0f172a" } : { mode, linkTextColor: "#ffffff" });
};
const setBackground = (changes: Record<string, any>) => {
  const readable = getReadableTextColor(changes.backgroundColor) || "#0f172a";
  patch({ ...changes, textColor: readable, linkTextColor: readable });
};
</script>
