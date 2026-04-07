<template>
  <div class="space-y-4">
    <div v-if="passengers.length" class="space-y-4">
      <div class="flex flex-wrap gap-2">
        <button
          v-for="(passenger, index) in passengers"
          :key="passenger.localId"
          type="button"
          class="rounded-full border px-3 py-1 text-xs font-semibold transition"
          :class="
            activePassengerIndex === index
              ? 'border-emerald-500 bg-emerald-500 text-white'
              : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
          "
          @click="activePassengerIndex = index"
        >
          Passageiro {{ index + 1 }}
        </button>
      </div>

      <div v-if="currentPassenger" class="rounded-2xl border border-slate-200 p-4">
        <div class="mb-3 flex items-center justify-between">
          <p class="text-sm font-semibold text-slate-700">Passageiro {{ activePassengerIndex + 1 }}</p>
          <button
            v-if="!readonly && passengers.length > 1"
            type="button"
            class="text-xs font-semibold text-rose-500"
            @click="removePassenger(activePassengerIndex)"
          >
            Remover
          </button>
        </div>
        <div class="grid gap-3 md:grid-cols-2">
          <div class="md:col-span-2">
            <label class="mb-1 block text-xs font-semibold text-slate-500">Nome completo</label>
            <input
              v-model="currentPassenger.name"
              type="text"
              :readonly="readonly"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
              placeholder="Nome completo"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">CPF</label>
            <input
              v-model="currentPassenger.cpf"
              type="text"
              :readonly="readonly"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
              placeholder="000.000.000-00"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Nascimento</label>
            <input
              v-model="currentPassenger.birthdate"
              type="date"
              :readonly="readonly"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">Telefone</label>
            <input
              v-model="currentPassenger.phone"
              type="text"
              :readonly="readonly"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-slate-500">WhatsApp</label>
            <input
              v-model="currentPassenger.whatsapp"
              type="text"
              :readonly="readonly"
              class="w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
        </div>
        <div class="mt-3">
          <label class="mb-1 block text-xs font-semibold text-slate-500">Local de embarque</label>
          <input
            v-model="currentPassenger.boarding_location"
            type="text"
            :readonly="readonly"
            class="w-full rounded-lg border border-slate-200 px-3 py-2"
          />
        </div>
        <div class="mt-3">
          <label class="mb-1 block text-xs font-semibold text-slate-500">Observações</label>
          <textarea
            v-model="currentPassenger.extras"
            rows="2"
            :readonly="readonly"
            class="w-full rounded-lg border border-slate-200 px-3 py-2"
          ></textarea>
        </div>
      </div>
    </div>
    <button
      v-if="!readonly"
      type="button"
      class="w-full rounded-xl border border-dashed border-slate-300 px-3 py-3 text-sm font-semibold text-slate-600 hover:border-slate-400"
      @click="addPassenger"
    >
      + Adicionar passageiro
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { Passenger } from "../../types/finance";

interface EditablePassenger extends Passenger {
  localId: string;
}

const props = defineProps<{
  modelValue: Passenger[];
  passengersRequired?: number;
  readonly?: boolean;
}>();
const emit = defineEmits<{ (e: "update:modelValue", value: Passenger[]): void }>();

const passengers = ref<EditablePassenger[]>([]);
let syncing = false;
const activePassengerIndex = ref(0);
const currentPassenger = computed(() => passengers.value[activePassengerIndex.value] || null);

const createPassenger = (): EditablePassenger => ({
  id: 0,
  localId: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2),
  name: "",
  cpf: "",
  birthdate: "",
  phone: "",
  whatsapp: "",
  boarding_location: "",
  extras: ""
});

const syncFromProps = (value: Passenger[]) => {
  syncing = true;
  passengers.value = value.map(passenger => ({ ...createPassenger(), ...passenger }));
  ensureMinimum();
  if (activePassengerIndex.value >= passengers.value.length) {
    activePassengerIndex.value = Math.max(0, passengers.value.length - 1);
  }
  syncing = false;
};

const ensureMinimum = () => {
  const required = Math.max(0, props.passengersRequired || 0);
  while (passengers.value.length < required) {
    passengers.value.push(createPassenger());
  }
};

const emitChange = () => {
  if (syncing) return;
  const sanitized: Passenger[] = passengers.value.map(({ localId, ...rest }) => rest);
  emit("update:modelValue", sanitized);
};

const addPassenger = () => {
  passengers.value.push(createPassenger());
  activePassengerIndex.value = passengers.value.length - 1;
};

const removePassenger = (index: number) => {
  passengers.value.splice(index, 1);
  ensureMinimum();
  if (activePassengerIndex.value >= passengers.value.length) {
    activePassengerIndex.value = Math.max(0, passengers.value.length - 1);
  }
};

watch(
  () => props.modelValue,
  value => {
    syncFromProps(value || []);
  },
  { immediate: true, deep: true }
);

watch(
  () => props.passengersRequired,
  () => {
    ensureMinimum();
    emitChange();
  }
);

watch(
  passengers,
  () => {
    emitChange();
  },
  { deep: true }
);

defineExpose({
  valid: computed(() => passengers.value.every(passenger => (passenger.name || "").trim().length > 0))
});
</script>
