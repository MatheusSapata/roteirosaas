<template>
  <section class="flex min-h-[70vh] items-center justify-center px-4 py-10">
    <article class="w-full max-w-xl rounded-[24px] border border-border bg-card p-8 text-center text-card-foreground shadow-soft md:p-10">
      <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-border bg-muted text-primary">
        <MessageSquareTextIcon class="h-7 w-7" aria-hidden="true" />
      </div>
      <p class="mt-5 text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">WhatsApp</p>
      <h1 class="mt-2 font-display text-2xl font-semibold text-foreground">Caixa de entrada indisponível</h1>
      <p class="mx-auto mt-3 max-w-md text-sm leading-6 text-muted-foreground">
        A Caixa de entrada do WhatsApp ainda não está liberada para sua conta.
      </p>
    </article>
  </section>
</template>

<script setup lang="ts">
import { MessageSquareTextIcon } from "lucide-vue-next";
</script>
