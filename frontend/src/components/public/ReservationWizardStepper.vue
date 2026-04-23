<template>
  <section class="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm sm:px-5 sm:py-3.5">
    <p class="text-[11px] font-extrabold uppercase tracking-[0.24em] text-slate-500">
      Etapas da reserva
    </p>

    <div class="mt-2.5 flex flex-col gap-2.5 lg:flex-row lg:items-center lg:gap-3">
      <template v-for="(step, index) in steps" :key="step.key">
        <article
          class="min-w-0 flex-1 rounded-[18px] border px-3.5 py-3 transition-all duration-200"
          :class="stepCardClass(step.state)"
        >
          <div class="flex items-center gap-3">
            <div
              class="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border text-[13px] font-extrabold"
              :class="stepIndexClass(step.state)"
            >
              <span>{{ stepBadge(index, step.state) }}</span>
            </div>

            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <p class="text-[10px] font-extrabold uppercase tracking-[0.18em] text-slate-400">
                  Etapa {{ index + 1 }}
                </p>
                <span
                  class="inline-flex min-h-5 shrink-0 items-center rounded-full border px-2 text-[10px] font-extrabold uppercase tracking-[0.14em]"
                  :class="stepStatusClass(step.state)"
                >
                  {{ stateLabel(step.state) }}
                </span>
              </div>

              <h3 class="mt-1 text-sm font-extrabold leading-tight text-slate-950 sm:text-[15px]">
                {{ step.label }}
              </h3>
              <p class="mt-0.5 text-[12px] leading-5 text-slate-500">
                {{ step.hint }}
              </p>
            </div>
          </div>
        </article>

        <div
          v-if="index < steps.length - 1"
          class="hidden w-7 shrink-0 items-center justify-center lg:flex"
        >
          <span
            class="h-[2px] w-full rounded-full"
            :class="steps[index + 1].state !== 'upcoming' ? 'bg-sky-400' : 'bg-slate-200'"
          ></span>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
export type WizardStepState = "done" | "active" | "upcoming";

defineProps<{
  steps: Array<{
    key: string;
    label: string;
    hint: string;
    state: WizardStepState;
  }>;
}>();

const stateLabel = (state: WizardStepState) => {
  if (state === "done") return "Concluida";
  if (state === "active") return "Atual";
  return "Proxima";
};

const stepBadge = (index: number, state: WizardStepState) => {
  if (state === "done") return "OK";
  return String(index + 1);
};

const stepCardClass = (state: WizardStepState) => {
  if (state === "done") {
    return "border-emerald-200 bg-emerald-50/60 shadow-sm";
  }

  if (state === "active") {
    return "border-sky-200 bg-sky-50/70 shadow-sm";
  }

  return "border-slate-200 bg-slate-50/60";
};

const stepIndexClass = (state: WizardStepState) => {
  if (state === "done") {
    return "border-emerald-200 bg-emerald-600 text-white";
  }

  if (state === "active") {
    return "border-sky-200 bg-sky-100 text-sky-700";
  }

  return "border-slate-200 bg-white text-slate-500";
};

const stepStatusClass = (state: WizardStepState) => {
  if (state === "done") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }

  if (state === "active") {
    return "border-sky-200 bg-sky-50 text-sky-700";
  }

  return "border-slate-200 bg-white text-slate-500";
};
</script>

<style scoped>
</style>
