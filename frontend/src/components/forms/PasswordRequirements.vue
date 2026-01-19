<template>
  <ul class="mt-2 space-y-1 text-sm">
    <li
      v-for="item in requirementList"
      :key="item.key"
      class="flex items-center gap-2"
      :class="item.met ? 'text-green-600' : 'text-slate-500'"
    >
      <span class="text-xs font-semibold" :class="item.met ? 'text-green-600' : 'text-slate-400'">
        {{ item.met ? "✔" : "•" }}
      </span>
      {{ item.label }}
    </li>
  </ul>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ password: string }>();

const requirementList = computed(() => [
  { key: "length", label: "Mínimo de 8 caracteres", met: props.password.length >= 8 },
  { key: "uppercase", label: "Ao menos uma letra maiúscula", met: /[A-Z]/.test(props.password) },
  { key: "lowercase", label: "Ao menos uma letra minúscula", met: /[a-z]/.test(props.password) },
  { key: "number", label: "Ao menos um número", met: /\d/.test(props.password) }
]);
</script>
