<template>
  <div class="itinerary-shell">
    <aside class="itinerary-nav">
      <button type="button" class="itinerary-nav-item" :class="{ active: activeTab === 'text' }" @click="activeTab = 'text'">
        <span class="itinerary-nav-icon">✎</span>
        <span><strong>Textos</strong><small>Título da seção</small></span>
      </button>
      <button type="button" class="itinerary-nav-item" :class="{ active: activeTab === 'days' }" @click="activeTab = 'days'">
        <span class="itinerary-nav-icon">📅</span>
        <span><strong>Dias</strong><small>Roteiro da viagem</small></span>
      </button>
    </aside>

    <section class="itinerary-content">
      <div v-if="activeTab === 'text'" class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Textos da seção</h2>
            <p class="section-desc">Configure os textos exibidos acima dos dias do roteiro.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="field">
            <label>
              Etiqueta acima do título
              <span class="optional">opcional</span>
              <span class="help" data-tip="Texto pequeno exibido acima do título, como Roteiro completo.">?</span>
            </label>
            <input v-model="local.headingLabel" placeholder="Roteiro Completo" />
          </div>

          <div class="field">
            <label>Título da seção <span class="help" data-tip="Título principal exibido acima dos dias do itinerário.">?</span></label>
            <input v-model="local.title" :placeholder="viewCopy.fields.titlePlaceholder" />
          </div>

          <div class="field">
            <label>Subtítulo <span class="help" data-tip="Texto complementar para orientar o visitante.">?</span></label>
            <input v-model="local.subtitle" :placeholder="viewCopy.fields.subtitlePlaceholder" />
          </div>
        </div>
      </div>

      <div v-else class="section-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">Dias do roteiro</h2>
            <p class="section-desc">Adicione, selecione e reordene os dias da viagem.</p>
          </div>
        </div>

        <div class="content-area">
          <div class="segment-bar">
            <div v-if="local.days.length" ref="dayChipsRef" class="segment-tabs">
              <button
                v-for="(day, index) in local.days"
                :key="day.id || index"
                type="button"
                data-day-chip
                class="segment-tab"
                :class="{ active: selectedDayIndex === index }"
                @click="selectedDayIndex = index"
              >
                <span class="segment-handle">⋮⋮</span>
                <span class="segment-name">{{ day.day || formatDayChipLabel(index + 1) }}</span>
                <span class="segment-remove" @click.stop="removeDay(index)">×</span>
              </button>
            </div>
            <div v-else class="empty-days">{{ viewCopy.days.emptyMessage }}</div>
            <div class="segment-actions">
              <button class="add-segment" type="button" @click="addDay">{{ viewCopy.days.addButton }}</button>
            </div>
          </div>

          <div v-if="currentDay" class="segment-panel">
            <div class="compact-grid">
              <div class="field">
                <label>{{ viewCopy.days.dayLabel }} <span class="help" data-tip="Data ou identificação do dia exibida no botão do itinerário.">?</span></label>
                <input v-model="currentDay.day" :placeholder="viewCopy.days.dayPlaceholder" />
              </div>
              <div class="field">
                <label>{{ viewCopy.days.dayTitleLabel }} <span class="help" data-tip="Nome curto do momento do roteiro.">?</span></label>
                <input v-model="currentDay.title" :placeholder="viewCopy.days.dayTitlePlaceholder" />
              </div>
            </div>

            <div class="field">
              <label>{{ viewCopy.days.descriptionLabel }} <span class="help" data-tip="Detalhe o que acontece neste dia.">?</span></label>
              <div class="rich-box">
                <RichTextEditor :key="currentDay?.id || selectedDayIndex" v-model="currentDay.description" :placeholder="viewCopy.days.descriptionPlaceholder" />
              </div>
            </div>

            <div class="media-item">
              <div class="media-preview">
                <img v-if="currentDay.image" :src="currentDay.image" alt="Imagem do dia" />
                <div v-else class="media-empty">Sem imagem</div>
              </div>
              <div class="media-info">
                <strong>{{ viewCopy.days.imageLabel }} <span class="optional">opcional</span> <span class="help" data-tip="Imagem exibida quando o visitante expandir este dia do roteiro.">?</span></strong>
                <p>{{ viewCopy.days.imageHint }}</p>
              </div>
              <div class="btn-row">
                <input ref="dayImageInputRef" type="file" accept="image/*" class="hidden" @change="onDayImageFileChange($event)" />
                <button type="button" @click="dayImageInputRef?.click()">{{ uploadingDayImage ? "Enviando..." : "Substituir" }}</button>
                <button v-if="currentDay.image" type="button" class="danger" @click="removeDayImage(currentDay)">{{ viewCopy.days.removeImage }}</button>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">
            {{ viewCopy.days.emptyStateHint }}
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import Sortable, { type SortableEvent } from "sortablejs";
import RichTextEditor from "./inputs/RichTextEditor.vue";
import { getSectionHeadingDefaults } from "../../utils/sectionHeadings";
import type { ItinerarySection } from "../../types/page";
import { createAdminLocalizer } from "../../utils/adminI18n";
import { useAgencyStore } from "../../store/useAgencyStore";
import { uploadImageFile } from "../../utils/media";

const props = defineProps<{ modelValue: ItinerarySection }>();
const emit = defineEmits<{ (e: "update:modelValue", value: ItinerarySection): void }>();
const headingDefaults = getSectionHeadingDefaults("itinerary");
const t = createAdminLocalizer();
const activeTab = ref<"text" | "days">("text");
const agencyStore = useAgencyStore();
const dayImageInputRef = ref<HTMLInputElement | null>(null);
const uploadingDayImage = ref(false);

const viewCopy = {
  fields: {
    titlePlaceholder: t({ pt: "Assim será nossa viagem!", es: "Asi sera nuestro viaje!" }),
    subtitlePlaceholder: t({ pt: "Clique em cada dia para conferir todos os detalhes.", es: "Haz clic en cada dia para ver todos los detalles." })
  },
  days: {
    emptyMessage: t({ pt: "Nenhum dia cadastrado.", es: "Ningun dia registrado." }),
    addButton: t({ pt: "+ Adicionar dia", es: "+ Agregar dia" }),
    chipPrefix: t({ pt: "Dia", es: "Dia" }),
    dayLabel: t({ pt: "Dia", es: "Dia" }),
    dayPlaceholder: t({ pt: "02/03", es: "02/03" }),
    dayTitleLabel: t({ pt: "Título do dia", es: "Titulo del dia" }),
    dayTitlePlaceholder: t({ pt: "Embarque", es: "Embarque" }),
    descriptionLabel: t({ pt: "Descrição do dia", es: "Descripcion del dia" }),
    descriptionPlaceholder: t({ pt: "Realizaremos o embarque...", es: "Realizaremos el embarque..." }),
    imageLabel: t({ pt: "Imagem do dia", es: "Imagen del dia" }),
    removeImage: t({ pt: "Remover", es: "Eliminar" }),
    imageHint: t({
      pt: "Esta imagem aparece junto aos detalhes do dia.",
      es: "Esta imagen aparece junto a los detalles del dia."
    }),
    emptyStateHint: t({
      pt: "Clique em \"+ Adicionar dia\" para começar a montar o cronograma.",
      es: "Haz clic en \"+ Agregar dia\" para empezar a armar el cronograma."
    })
  }
};

const formatDayChipLabel = (index: number) => `${viewCopy.days.chipPrefix} ${index}`;

const selectedDayIndex = ref(0);
const dayChipsRef = ref<HTMLElement | null>(null);
let chipsSortable: Sortable | null = null;

const createDayId = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
const normalizeDays = (days?: ItinerarySection["days"]): ItinerarySection["days"] => {
  if (!Array.isArray(days)) return [];
  return days.map(day => ({
    ...day,
    id: day.id || createDayId()
  }));
};
const createEmptyDay = () => ({
  id: createDayId(),
  day: "",
  title: "",
  description: "",
  image: ""
});

const local = reactive<ItinerarySection>({
  ...props.modelValue,
  layout: "timeline",
  enabled: true,
  fullWidth: false,
  headingLabel: props.modelValue.headingLabel ?? headingDefaults.label,
  headingLabelStyle: props.modelValue.headingLabelStyle ?? headingDefaults.style,
  days: normalizeDays(props.modelValue.days),
  title: props.modelValue.title ?? viewCopy.fields.titlePlaceholder,
  subtitle: props.modelValue.subtitle ?? viewCopy.fields.subtitlePlaceholder
});
const currentDay = computed(() => local.days[selectedDayIndex.value] || null);

function ensureSelectedDay() {
  if (!local.days.length) {
    selectedDayIndex.value = 0;
    return;
  }
  if (selectedDayIndex.value >= local.days.length) selectedDayIndex.value = local.days.length - 1;
  if (selectedDayIndex.value < 0) selectedDayIndex.value = 0;
}

let syncing = false;
const syncFromProps = (value: ItinerarySection) => {
  syncing = true;
  Object.assign(local, value);
  local.enabled = true;
  local.layout = "timeline";
  local.fullWidth = false;
  local.headingLabel = value.headingLabel ?? headingDefaults.label;
  local.headingLabelStyle = value.headingLabelStyle || headingDefaults.style;
  local.days = normalizeDays(value.days);
  local.title = value.title ?? viewCopy.fields.titlePlaceholder;
  local.subtitle = value.subtitle ?? viewCopy.fields.subtitlePlaceholder;
  ensureSelectedDay();
  scheduleSortableRefresh();
  nextTick(() => {
    syncing = false;
  });
};

watch(
  () => props.modelValue,
  value => {
    if (!value) return;
    syncFromProps(value);
  },
  { deep: true }
);

const addDay = () => {
  local.days.push(createEmptyDay());
  selectedDayIndex.value = local.days.length - 1;
  ensureSelectedDay();
};

const removeDay = (index: number) => {
  if (index < 0 || index >= local.days.length) return;
  local.days.splice(index, 1);
  ensureSelectedDay();
};

const removeDayImage = (day: ItinerarySection["days"][number] | undefined) => {
  if (!day) return;
  day.image = "";
};

const ensureAgencyId = async () => {
  if (!agencyStore.currentAgencyId) {
    await agencyStore.loadAgencies().catch(() => undefined);
  }
  return agencyStore.currentAgencyId;
};

const onDayImageFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file || !currentDay.value) return;
  uploadingDayImage.value = true;
  try {
    const agencyId = await ensureAgencyId();
    if (!agencyId) return;
    const asset = await uploadImageFile(file, agencyId);
    currentDay.value.image = asset.url;
  } catch {
    /* noop */
  } finally {
    target.value = "";
    uploadingDayImage.value = false;
  }
};

const updateSelectionAfterMove = (oldIndex: number, newIndex: number) => {
  if (selectedDayIndex.value === oldIndex) selectedDayIndex.value = newIndex;
  else if (selectedDayIndex.value > oldIndex && selectedDayIndex.value <= newIndex) selectedDayIndex.value -= 1;
  else if (selectedDayIndex.value < oldIndex && selectedDayIndex.value >= newIndex) selectedDayIndex.value += 1;
  ensureSelectedDay();
};

const reorderDays = (oldIndex: number, newIndex: number) => {
  if (oldIndex === newIndex) return;
  if (oldIndex < 0 || oldIndex >= local.days.length) return;
  const [movedDay] = local.days.splice(oldIndex, 1);
  if (!movedDay) return;
  const targetIndex = Math.min(Math.max(newIndex, 0), local.days.length);
  local.days.splice(targetIndex, 0, movedDay);
  updateSelectionAfterMove(oldIndex, targetIndex);
};

const handleDragEnd = (event: SortableEvent) => {
  if (typeof event.oldIndex !== "number" || typeof event.newIndex !== "number") return;
  reorderDays(event.oldIndex, event.newIndex);
};

const destroySortable = () => {
  if (chipsSortable) {
    chipsSortable.destroy();
    chipsSortable = null;
  }
};

function initSortable() {
  if (!dayChipsRef.value || local.days.length <= 1) {
    destroySortable();
    return;
  }
  destroySortable();
  chipsSortable = Sortable.create(dayChipsRef.value, {
    animation: 180,
    draggable: "button[data-day-chip]",
    ghostClass: "itinerary-chip-ghost",
    dragClass: "itinerary-chip-dragging",
    forceFallback: true,
    fallbackTolerance: 5,
    delayOnTouchOnly: true,
    delay: 120,
    swapThreshold: 0.45,
    onEnd: handleDragEnd
  });
}

function scheduleSortableRefresh() {
  nextTick(() => {
    initSortable();
  });
}

onMounted(() => {
  scheduleSortableRefresh();
});

onBeforeUnmount(() => {
  destroySortable();
});

watch(
  () => local.days.length,
  () => {
    scheduleSortableRefresh();
  }
);

watch(
  () => ({ ...local, days: local.days.map(day => ({ ...day })) }),
  value => {
    if (syncing) return;
    emit("update:modelValue", value as ItinerarySection);
  },
  { deep: true }
);
</script>

<style scoped>
.itinerary-shell {
  display: grid;
  grid-template-columns: 178px 1fr;
  height: 100%;
  min-height: 56vh;
}

.itinerary-nav {
  border-right: 1px solid #e6eee8;
  padding: 16px 12px 16px 12px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.itinerary-nav-item {
  width: 100%;
  border: 1px solid #d8dfda;
  border-radius: 14px;
  padding: 7px 9px;
  background: #eef2ef;
  color: #0f172a;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 10px;
}

.itinerary-nav-item.active {
  border-color: #34c759;
  background: #34c759;
}

.itinerary-nav-icon {
  width: 22px;
  height: 22px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.82);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.itinerary-nav-item strong {
  display: block;
  font-size: 16px;
  line-height: 0.95;
  font-weight: 700;
}

.itinerary-nav-item small {
  display: block;
  font-size: 10px;
  color: rgba(15, 23, 42, 0.55);
  font-weight: 600;
}

.itinerary-nav-item.active small {
  color: rgba(7, 82, 36, 0.78);
}

.itinerary-content {
  background: #f4f7f5;
  padding: 10px 14px;
  overflow-y: auto;
}

.section-card {
  height: 100%;
  background: transparent;
  border: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
  gap: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #edf3ef;
}

.section-title {
  margin: 0 0 5px;
  font-size: 17px;
  font-weight: 950;
  letter-spacing: -0.02em;
}

.section-desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.4;
  color: #75867b;
}

.content-area {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.field {
  margin-bottom: 10px;
}

label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #748379;
  font-weight: 950;
  margin-bottom: 6px;
}

.optional {
  text-transform: none;
  letter-spacing: 0;
  font-weight: 700;
  color: #9aaaa0;
  margin-left: auto;
}

.help {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: transparent;
  border: 1px solid #d8e3dc;
  color: #9aaaa0;
  font-size: 9px;
  font-weight: 900;
}

input, textarea {
  width: 100%;
  border: 1px solid #dfe8e2;
  border-radius: 10px;
  background: #fff;
  color: #172132;
  padding: 10px 11px;
  font-size: 14px;
}

.compact-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.segment-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.segment-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.segment-tab {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border: 1px solid #dfe8e2;
  background: #fff;
  border-radius: 999px;
  padding: 8px 9px 8px 11px;
  color: #516358;
  font-size: 12px;
  font-weight: 850;
}

.segment-tab.active {
  background: #f0fff5;
  color: #173b25;
  border-color: #35d467;
}

.segment-remove {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: rgba(225, 60, 60, 0.12);
  color: #d93a3a;
  font-size: 12px;
  font-weight: 900;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.segment-handle {
  color: #9aaaa0;
  font-weight: 950;
}

.add-segment {
  border: 1px solid #dfe8e2;
  border-radius: 8px;
  padding: 7px 10px;
  background: #fff;
  color: #223228;
  font-size: 12px;
  font-weight: 850;
}

.segment-panel {
  margin-top: 8px;
}

.rich-box {
  border: 1px solid #dfe8e2;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.rich-box :deep(.ql-toolbar.ql-snow) {
  border: 0 !important;
  border-bottom: 1px solid #e6eee8 !important;
  background: #fbfdfc;
}

.rich-box :deep(.ql-container.ql-snow) {
  border: 0 !important;
}

.rich-box :deep(.ql-editor) {
  min-height: 120px;
}

.media-item {
  display: grid;
  grid-template-columns: 86px 1fr auto;
  gap: 12px;
  align-items: center;
  border: 1px solid #dfe8e2;
  background: #fff;
  border-radius: 12px;
  padding: 8px;
  margin-top: 10px;
}

.media-preview img,
.media-empty {
  width: 86px;
  height: 58px;
  border-radius: 8px;
  object-fit: cover;
  display: grid;
  place-items: center;
  background: #f1f5f9;
  color: #94a3b8;
  font-size: 12px;
}

.media-info strong {
  font-size: 13px;
}

.media-info p {
  margin: 0;
  color: #7d8d83;
  font-size: 12px;
}

.btn-row {
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: center;
}

.btn-row button {
  border: 1px solid #dfe8e2;
  border-radius: 8px;
  padding: 7px 10px;
  background: #fff;
  color: #223228;
  font-size: 12px;
  font-weight: 850;
}

.danger {
  border: 1px solid #ffd4d4;
  border-radius: 8px;
  background: #fff1f1;
  color: #e13c3c;
  padding: 7px 10px;
  font-size: 12px;
  font-weight: 850;
}

.empty-state,
.empty-days {
  color: #7d8d83;
  font-size: 13px;
}

.itinerary-chip-ghost {
  opacity: 0.5;
}

.itinerary-chip-dragging {
  cursor: grabbing !important;
}

@media (max-width: 900px) {
  .itinerary-shell {
    grid-template-columns: 1fr;
    min-height: 100%;
    height: 100%;
    align-content: start;
    grid-auto-rows: min-content;
  }

  .itinerary-nav {
    border-right: 0;
    border-bottom: 0;
    padding: 8px 8px 8px 16px;
    margin-bottom: 8px;
    flex-direction: row;
    gap: 8px;
  }

  .itinerary-content {
    padding-top: 6px;
  }

  .itinerary-nav-item {
    flex: 1;
    min-width: 0;
    height: 40px;
    min-height: 40px;
    padding: 0 10px;
    border-radius: 13px;
    gap: 8px;
    align-items: center;
  }

  .itinerary-nav-icon {
    width: 20px;
    height: 20px;
    font-size: 11px;
    border-radius: 7px;
  }

  .itinerary-nav-item span {
    display: inline-flex;
    align-items: center;
    gap: 0;
    min-width: 0;
  }

  .itinerary-nav-item strong {
    font-size: 14px;
    line-height: 1;
  }

  .itinerary-nav-item small {
    display: none;
  }

  .compact-grid {
    grid-template-columns: 1fr;
  }

  .media-item {
    grid-template-columns: 70px 1fr;
  }

  .btn-row {
    grid-column: 1 / -1;
    flex-direction: row;
  }
}
</style>
