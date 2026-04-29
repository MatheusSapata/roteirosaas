<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_4px_18px_rgba(15,23,42,0.05)]">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="text-base font-bold text-slate-900">Leads recentes</h3>
      <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ leads.length }} itens</span>
    </div>

    <div class="overflow-x-auto">
      <table class="min-w-full text-left text-sm">
        <thead>
          <tr class="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
            <th class="px-2 py-2">Nome</th>
            <th class="px-2 py-2">Origem</th>
            <th class="px-2 py-2">Cidade</th>
            <th class="px-2 py-2 text-right">Ação</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="lead in leads" :key="String(lead.id)" class="border-b border-slate-100 last:border-0">
            <td class="px-2 py-2 font-medium text-slate-900">{{ lead.name || 'Sem nome' }}</td>
            <td class="px-2 py-2 text-slate-600">{{ lead.page_title || lead.page_slug || lead.form_name || '-' }}</td>
            <td class="px-2 py-2 text-slate-600">{{ lead.city || '-' }}</td>
            <td class="px-2 py-2 text-right">
              <button
                type="button"
                class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                @click="$emit('openLead', lead.id)"
              >
                Abrir
              </button>
            </td>
          </tr>
          <tr v-if="!leads.length">
            <td colspan="4" class="px-2 py-6 text-center text-sm text-slate-500">Nenhum lead recente.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { LeadContact } from "../../../types/leads";

defineProps<{
  leads: LeadContact[];
}>();

defineEmits<{
  openLead: [id: string | number];
}>();
</script>
