<template>
  <section class="rounded-lg border border-border bg-card p-5 text-card-foreground shadow-card">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="font-display text-base font-semibold text-foreground">Leads recentes</h3>
      <span class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{{ leads.length }} itens</span>
    </div>

    <div class="overflow-x-auto">
      <table class="min-w-full text-left text-sm">
        <thead>
          <tr class="border-b border-border text-xs uppercase tracking-wide text-muted-foreground">
            <th class="px-2 py-2">Nome</th>
            <th class="px-2 py-2">Origem</th>
            <th class="px-2 py-2">Cidade</th>
            <th class="px-2 py-2 text-right">Ação</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="lead in leads" :key="String(lead.id)" class="border-b border-border transition-colors hover:bg-muted last:border-0">
            <td class="px-2 py-2 font-medium text-foreground">{{ lead.name || 'Sem nome' }}</td>
            <td class="px-2 py-2 text-muted-foreground">{{ lead.page_title || lead.page_slug || lead.form_name || '-' }}</td>
            <td class="px-2 py-2 text-muted-foreground">{{ lead.city || '-' }}</td>
            <td class="px-2 py-2 text-right">
              <button
                type="button"
                class="rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:bg-accent"
                @click="$emit('openLead', lead.id)"
              >
                Abrir
              </button>
            </td>
          </tr>
          <tr v-if="!leads.length">
            <td colspan="4" class="px-2 py-6 text-center text-sm text-muted-foreground">Nenhum lead recente.</td>
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
