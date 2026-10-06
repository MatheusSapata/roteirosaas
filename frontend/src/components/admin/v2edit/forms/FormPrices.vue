<template>
  <V2EditShell>
    <template #content>
      <EdHeading :value="modelValue" type="prices" title-placeholder="Escolha seu pacote" @patch="patch" />
      <EdGroup title="Ofertas" :count="`${items.length} ${items.length === 1 ? 'oferta' : 'ofertas'}`">
        <EdList
          :items="items"
          :item-title="item => readText(item.title)"
          :new-item="newOffer"
          add-label="Adicionar oferta"
          item-label="Oferta"
          @update:items="patch({ items: $event })"
        >
          <template #default="{ item, update }">
            <EdText :model-value="readText(item.title)" label="Nome" placeholder="Quarto duplo" @update:model-value="update({ title: writeText(item.title, $event) })" />
            <div class="ved-pair">
              <EdText :model-value="item.price ?? ''" label="Preço" type="number" min="0" @update:model-value="update({ price: Number(String($event).replace(',', '.')) || 0 })" />
              <label class="ved-field">
                <span class="ved-label">Moeda</span>
                <select class="ved-select" :value="item.currency || 'BRL'" @change="update({ currency: ($event.target as HTMLSelectElement).value })">
                  <option v-for="code in currencies" :key="code" :value="code">{{ code }}</option>
                </select>
              </label>
            </div>
            <EdText :model-value="readText(item.description)" label="Complemento" placeholder="por pessoa · 10x sem juros" @update:model-value="update({ description: writeText(item.description, $event) })" />
            <EdText :model-value="readText(item.badge)" label="Selo" hint="Opcional. Ex.: Mais escolhido." @update:model-value="update({ badge: writeText(item.badge, $event) })" />
            <EdToggle :model-value="!!item.highlight" label="Destacar esta oferta" @update:model-value="update({ highlight: $event })" />
            <EdButton
              :value="item"
              :keys="{ label: 'ctaLabel', mode: 'ctaMode', link: 'ctaLink', section: 'ctaSectionId' }"
              title="Botão da oferta"
              placeholder="Reservar"
              @patch="update"
            />
          </template>
        </EdList>
      </EdGroup>
      <EdPayments :value="modelValue" @patch="patch" />
    </template>
    <template #look>
      <EdGroup title="Fundo">
        <EdBackground :value="modelValue" auto @change="patch" fallback="#F2F4F1" />
      </EdGroup>
    </template>
  </V2EditShell>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { PriceItem, PricesSection } from "../../../../types/page";
import EdBackground from "../EdBackground.vue";
import EdButton from "../EdButton.vue";
import EdGroup from "../EdGroup.vue";
import EdPayments from "../EdPayments.vue";
import EdHeading from "../EdHeading.vue";
import EdList from "../EdList.vue";
import EdText from "../EdText.vue";
import EdToggle from "../EdToggle.vue";
import V2EditShell from "../V2EditShell.vue";
import { readText, useDraft, writeText } from "../useDraft";

const props = defineProps<{ modelValue: PricesSection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: PricesSection): void }>();
const { patch } = useDraft(props, emit);
const items = computed(() => props.modelValue.items || []);
const newOffer = (): PriceItem => ({ title: "", price: 0, currency: "BRL", description: "", badge: "", highlight: false, ctaLabel: "Reservar", ctaMode: "link", ctaLink: "" });
const currencies = ["BRL", "USD", "EUR", "GBP", "ARS", "CLP", "MXN", "COP", "PEN", "UYU", "CAD", "AUD", "CHF", "JPY"];
</script>
