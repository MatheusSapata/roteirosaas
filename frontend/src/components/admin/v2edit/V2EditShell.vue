<template>
  <div class="ved">
    <div class="ved-tabs" role="tablist" aria-label="Editar seção">
      <button
        v-for="item in tabs"
        :id="`ved-tab-${item.id}`"
        :key="item.id"
        type="button"
        role="tab"
        class="ved-tab"
        :class="{ on: tab === item.id }"
        :aria-selected="tab === item.id"
        :aria-controls="`ved-panel-${item.id}`"
        @click="tab = item.id"
      >
        <component :is="item.icon" aria-hidden="true" />
        {{ item.label }}
      </button>
    </div>
    <div v-show="tab === 'content'" id="ved-panel-content" class="ved-panel" role="tabpanel" aria-labelledby="ved-tab-content">
      <slot name="content" />
    </div>
    <div v-show="tab === 'look'" id="ved-panel-look" class="ved-panel" role="tabpanel" aria-labelledby="ved-tab-look">
      <slot name="look">
        <p class="ved-info">Esta seção segue as cores e o fundo definidos em Configurações → Cores.</p>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PaletteIcon, TextIcon } from "lucide-vue-next";
import { ref } from "vue";
import "./v2edit.css";

const tabs = [
  { id: "content", label: "Conteúdo", icon: TextIcon },
  { id: "look", label: "Aparência", icon: PaletteIcon }
] as const;
const tab = ref<"content" | "look">("content");
</script>
