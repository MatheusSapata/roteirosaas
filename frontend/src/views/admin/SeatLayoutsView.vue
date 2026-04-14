<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Biblioteca de layouts</p>
        <h1>Mapas de assentos</h1>
        <p class="subtitle">
          Crie e edite modelos reutilizaveis de onibus para aplicar nas excursões rodoviarias.
        </p>
      </div>
      <div class="actions">
        <button type="button" class="btn-secondary" @click="loadData">Atualizar</button>
        <button type="button" class="btn-primary" @click="openEditor()">Novo layout</button>
      </div>
    </header>

    <section class="layouts-grid">
      <div v-if="loading" class="placeholder-card">Carregando layouts...</div>
      <template v-else>
        <article
          v-for="layout in layouts"
          :key="layout.id"
          class="layout-card"
        >
          <div class="layout-card__header">
            <div>
              <p class="layout-name">{{ layout.name }}</p>
              <p class="layout-meta">{{ layout.vehicle_type }} • {{ layout.seat_count }} lugares</p>
            </div>
            <span :class="['status-pill', layout.is_active ? 'status-pill--success' : 'status-pill--muted']">
              {{ layout.is_active ? "Ativo" : "Inativo" }}
            </span>
          </div>
          <template v-for="preview in [layoutPreviewGrid(layout)]" :key="`preview-${layout.id}`">
            <div class="layout-preview" v-if="preview.cols">
              <div
                class="layout-grid"
                :style="{ gridTemplateColumns: `repeat(${preview.cols}, minmax(12px, 1fr))` }"
              >
                <span
                  v-for="cell in preview.cells"
                  :key="`${cell.row}-${cell.col}`"
                  :class="['layout-cell', cell.type === 'seat' || cell.type === 'preferential' ? 'layout-cell--seat' : '']"
                ></span>
              </div>
            </div>
          </template>
          <div v-if="layout.deck_summaries?.length" class="deck-summary">
            <p class="deck-summary__title">
              {{ layout.deck_mode === "double" ? "Distribuição por andar" : "Lugares disponíveis" }}
            </p>
            <div class="deck-summary__list">
              <span v-for="deck in layout.deck_summaries" :key="deck.key" class="deck-chip">
                {{ deck.label }}: {{ deck.seat_count }} lugares
              </span>
            </div>
          </div>
          <div class="layout-card__actions">
            <button type="button" class="btn-light" @click="openEditor(layout.id)">Editar</button>
            <button type="button" class="btn-light" @click="duplicateLayout(layout.id)">Duplicar</button>
            <button type="button" class="btn-ghost" @click="deleteLayout(layout.id)">Excluir</button>
          </div>
        </article>
      </template>
    </section>

    <section class="vehicles-section">
      <div class="vehicle-header">
        <div>
          <p class="eyebrow">Frota cadastrada</p>
          <h2>Veiculos da agencia</h2>
        </div>
        <button type="button" class="btn-secondary" @click="loadVehicles">Atualizar</button>
      </div>
      <div class="vehicles-grid">
        <article
          v-for="vehicle in vehicles"
          :key="vehicle.id"
          class="vehicle-card"
        >
          <div>
            <p class="vehicle-name">{{ vehicle.name }}</p>
            <p class="vehicle-meta">
              {{ vehicle.plate || "Sem placa" }} •
              {{ layoutNameById(vehicle.layout_id) || "Layout padrao" }}
            </p>
          </div>
          <div class="vehicle-actions">
            <button type="button" class="btn-light" @click="editVehicle(vehicle)">Editar</button>
            <button type="button" class="btn-ghost" @click="removeVehicle(vehicle.id)">Excluir</button>
          </div>
        </article>
        <form class="vehicle-card vehicle-card--form" @submit.prevent="saveVehicle">
          <p class="vehicle-name">Novo veiculo</p>
          <label class="form-field">
            <span>Nome</span>
            <input v-model="vehicleForm.name" required placeholder="Double deck executivo" />
          </label>
          <label class="form-field">
            <span>Placa</span>
            <input v-model="vehicleForm.plate" placeholder="ABC1D23" />
          </label>
          <label class="form-field">
            <span>Layout base</span>
            <select v-model.number="vehicleForm.layout_id">
              <option :value="undefined">Padrão</option>
              <option v-for="layout in layouts" :key="layout.id" :value="layout.id">
                {{ layout.name }}
              </option>
            </select>
          </label>
          <div class="vehicle-actions">
            <button type="submit" class="btn-primary" :disabled="vehicleSaving">
              {{ vehicleForm.id ? "Atualizar veiculo" : "Cadastrar veiculo" }}
            </button>
            <button type="button" class="btn-ghost" @click="resetVehicleForm">Limpar</button>
          </div>
        </form>
      </div>
    </section>

    <div v-if="editorVisible" class="drawer">
      <div class="drawer__backdrop" @click="closeEditor"></div>
      <div class="drawer__panel">
        <header class="drawer__header">
          <div class="header-left">
            <p class="eyebrow">{{ editorState.id ? "Editar layout" : "Novo layout de ônibus" }}</p>
            <h3>{{ editorState.name || "Mapa sem nome" }}</h3>
            <p class="header-subtitle">Configure visualmente o mapa de assentos</p>
          </div>
          <div class="header-actions">
            <button type="button" class="btn-ghost" @click="closeEditor">Fechar</button>
            <button type="submit" form="layout-editor-form" class="btn-primary" :disabled="editorSaving">
              {{ editorState.id ? "Salvar layout" : "Criar layout" }}
            </button>
          </div>
        </header>

        <form id="layout-editor-form" class="editor-form" @submit.prevent="saveLayout">
          <div class="builder-grid">
            <section class="builder-panel layout-details-panel">
              <div class="panel-heading">
                <h4>Dados do layout</h4>
                <p>Defina as informações gerais do ônibus.</p>
              </div>
              <label class="form-field">
                <span>Nome do layout</span>
                <input v-model="editorState.name" required placeholder="Executivo 46 lugares" />
              </label>
              <label class="form-field">
                <span>Tipo do veículo</span>
                <select v-model="editorState.vehicle_type">
                  <option value="executivo">Executivo</option>
                  <option value="semi_leito">Semi-leito</option>
                  <option value="leito">Leito</option>
                  <option value="micro">Micro</option>
                  <option value="double_deck">Double-deck</option>
                  <option value="custom">Custom</option>
                </select>
              </label>
              <div class="grid grid-cols-2 gap-3">
                <label class="form-field">
                  <span>Número de andares</span>
                  <select v-model="editorState.deckMode">
                    <option value="single">1 andar</option>
                    <option value="double">2 andares</option>
                  </select>
                </label>
                <label v-if="isDoubleDeck" class="form-field">
                  <span>Nome do andar</span>
                  <input v-model="editorState.decks[activeDeckIndex].label" placeholder="Andar" />
                </label>
              </div>
              <div v-if="isDoubleDeck" class="deck-tabs">
                <button
                  v-for="(deck, index) in editorState.decks"
                  :key="deck.key"
                  type="button"
                  :class="['deck-tab', activeDeckIndex === index ? 'deck-tab--active' : '']"
                  @click="activeDeckIndex = index"
                >
                  {{ deck.label || (index === 0 ? "Andar inferior" : "Andar superior") }}
                </button>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <label class="form-field">
                  <span>Fileiras</span>
                  <input type="number" v-model.number="activeRows" min="4" max="20" />
                </label>
                <label class="form-field">
                  <span>Colunas</span>
                  <input type="number" v-model.number="activeCols" min="2" max="5" />
                </label>
              </div>
              <label class="form-field">
                <span>Total de assentos disponíveis</span>
                <input
                  type="number"
                  min="1"
                  placeholder="ex: 46"
                  v-model.number="editorState.capacity_total"
                />
                <small class="helper-text">Define a capacidade máxima de passageiros para este ônibus.</small>
              </label>
              <div class="form-field">
                <span>Slug (opcional)</span>
                <input v-model="editorState.slug" placeholder="executivo-2025" />
              </div>
              <div class="form-field">
                <span>Thumbnail (opcional)</span>
                <input v-model="editorState.thumbnail_url" placeholder="https://..." />
              </div>
              <div class="seat-count-summary">
                <p class="seat-count-summary__title">Resumo de assentos</p>
                <div class="indicator-grid">
                <div class="indicator-item">
                  <span>Total no layout</span>
                  <strong>{{ seatIndicators.total }}</strong>
                </div>
                <div class="indicator-item">
                  <span>Selecionáveis</span>
                  <strong>{{ seatIndicators.selectable }}</strong>
                </div>
                <div class="indicator-item">
                  <span>Bloqueados</span>
                  <strong>{{ seatIndicators.blocked }}</strong>
                </div>
                <div class="indicator-item">
                  <span>Capacidade definida</span>
                  <strong>{{ seatIndicators.capacity || "—" }}</strong>
                </div>
              </div>
                <ul class="deck-summary__list">
                  <li v-for="deck in deckSeatSummaries" :key="deck.key">
                    {{ deck.label }}: <strong>{{ deck.seats }}</strong> lugares
                  </li>
                </ul>
              </div>
            </section>

            <section class="builder-panel map-panel">
              <div class="panel-heading">
                <h4>Mapa visual</h4>
                <p>Personalize assentos, corredor e áreas especiais.</p>
              </div>
              <div class="bus-orientation">Frente do ônibus</div>
              <div class="map-actions-row">
                <button type="button" class="btn-ghost" @click="generateAutomaticLabels">Gerar numeração automática</button>
                <button type="button" class="btn-ghost" :disabled="!activeCellKey" @click="clearSeatSelection">Limpar seleção</button>
                <button type="button" class="btn-ghost" @click="resetCurrentLayout">Resetar layout</button>
              </div>
            <div class="bus-shell">
              <div class="bus-front">
                <div class="bus-front__window"></div>
                <div class="bus-front__driver"></div>
              </div>
              <div class="bus-body">
                <div
                  class="editor-grid__canvas"
                  :style="{ gridTemplateColumns: `repeat(${activeCols}, minmax(42px, 1fr))` }"
                >
                  <button
                    v-for="cell in editorGrid"
                    :key="cell.key"
                    type="button"
                    :class="[
                      'editor-cell',
                      `editor-cell--${cell.schema.type}`,
                      cell.isSelected ? 'editor-cell--active' : ''
                    ]"
                    @click="selectCell(cell)"
                  >
                    <span v-if="cell.schema.type === 'seat' || cell.schema.type === 'preferential'">
                      {{ cell.schema.label || cell.schema.row * activeCols + cell.schema.col + 1 }}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </section>

            <section class="builder-panel cell-config-panel">
              <div class="panel-heading">
                <h4>Configuração da célula</h4>
                <p>{{ cellContextLabel }}</p>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <label class="form-field">
                  <span>Tipo</span>
                  <select v-model="cellEditor.type">
                    <option v-for="option in cellTypeOptions" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                </label>
                <label class="form-field">
                  <span>Label</span>
                  <input v-model="cellEditor.label" placeholder="12A" />
                </label>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <label class="checkbox-field">
                  <input type="checkbox" v-model="cellEditor.selectable" />
                  <span>Selecionável</span>
                </label>
                <label class="checkbox-field">
                  <input type="checkbox" v-model="cellEditor.blocked" />
                  <span>Bloqueado</span>
                </label>
              </div>
              <p class="helper-text">
                Selecione uma célula no grid para personalizar. Tipos especiais ajudam a orientar o passageiro.
              </p>
            </section>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import type {
  VehicleLayoutDetail,
  VehicleLayoutPayload,
  VehicleLayoutSchema,
  VehicleOut,
  VehiclePayload,
} from "../../types/transport";
import {
  createVehicleLayoutRequest,
  createVehicleRequest,
  deleteVehicleLayoutRequest,
  deleteVehicleRequest,
  duplicateVehicleLayout,
  getVehicleLayoutDetail,
  listVehicleLayouts,
  listVehiclesRequest,
  updateVehicleLayoutRequest,
  updateVehicleRequest,
} from "../../services/transport";

interface EditorCell {
  key: string;
  schema: VehicleLayoutCellSchema;
  isSelected: boolean;
}

interface VehicleLayoutCellSchema {
  row: number;
  col: number;
  type: string;
  label?: string | null;
  selectable?: boolean;
  blocked?: boolean;
}

interface EditorDeck {
  key: string;
  label: string;
  rows: number;
  cols: number;
  cells: VehicleLayoutCellSchema[];
}

const buildDeck = (key: string, label: string, rows = 12, cols = 4): EditorDeck => ({
  key,
  label,
  rows,
  cols,
  cells: [],
});

const layouts = ref<VehicleLayoutDetail[]>([]);
const loading = ref(false);
const editorVisible = ref(false);
const editorSaving = ref(false);
const activeDeckIndex = ref(0);
const isDoubleDeck = computed(() => editorState.deckMode === "double");

const activeRows = computed({
  get: () => (isDoubleDeck.value ? editorState.decks[activeDeckIndex.value].rows : editorState.rows),
  set: value => {
    if (isDoubleDeck.value) {
      editorState.decks[activeDeckIndex.value].rows = value;
    } else {
      editorState.rows = value;
    }
  },
});

const activeCols = computed({
  get: () => (isDoubleDeck.value ? editorState.decks[activeDeckIndex.value].cols : editorState.cols),
  set: value => {
    const limited = Math.min(5, Math.max(2, value));
    if (isDoubleDeck.value) {
      editorState.decks[activeDeckIndex.value].cols = limited;
    } else {
      editorState.cols = limited;
    }
  },
});

const resolveActiveCells = () => (isDoubleDeck.value ? editorState.decks[activeDeckIndex.value].cells : editorState.cells);

const countSeatCells = (cells: VehicleLayoutCellSchema[]) =>
  cells.filter(cell => cell.type === "seat" || cell.type === "preferential").length;

const deckSeatSummaries = computed(() => {
  if (isDoubleDeck.value) {
    return editorState.decks.map(deck => ({
      key: deck.key,
      label: deck.label,
      seats: countSeatCells(deck.cells),
    }));
  }
  return [
    {
      key: "andar_unico",
      label: "Mapa unico",
      seats: countSeatCells(editorState.cells),
    },
  ];
});

const totalSeatCount = computed(() => deckSeatSummaries.value.reduce((sum, item) => sum + item.seats, 0));

const layoutPreviewGrid = (layout: VehicleLayoutDetail) => {
  const schema = layout.layout_schema;
  if (schema?.decks && schema.decks.length) {
    return {
      cols: schema.decks[0].cols,
      cells: schema.decks[0].cells,
    };
  }
  return {
    cols: schema?.cols ?? 0,
    cells: schema?.cells ?? [],
  };
};
const collectAllCells = () =>
  (editorState.deckMode === "double" ? editorState.decks.flatMap(deck => deck.cells) : editorState.cells);

const seatIndicators = computed(() => {
  const seatCells = collectAllCells().filter(cell => cell.type === "seat" || cell.type === "preferential");
  const selectable = seatCells.filter(cell => cell.selectable !== false && !cell.blocked).length;
  const blocked = seatCells.filter(cell => cell.blocked).length;
  return {
    total: seatCells.length,
    selectable,
    blocked,
    capacity: editorState.capacity_total,
  };
});

const activeCell = computed(() => {
  if (!activeCellKey.value) return null;
  const [row, col] = activeCellKey.value.split("-").map(Number);
  return resolveActiveCells().find(entry => entry.row === row && entry.col === col) || null;
});

const cellContextLabel = computed(() => {
  if (!activeCell.value) return "Nenhuma célula selecionada";
  const label = activeCell.value.label || `${activeCell.value.row + 1}-${activeCell.value.col + 1}`;
  if (activeCell.value.type === "seat" || activeCell.value.type === "preferential") {
    return `Editando assento ${label}`;
  }
  return `Editando célula ${label}`;
});
const editorState = reactive({
  id: undefined as number | undefined,
  name: "",
  vehicle_type: "executivo",
  rows: 12,
  cols: 4,
  cells: [] as VehicleLayoutCellSchema[],
  deckMode: "single" as "single" | "double",
  decks: [buildDeck("andar_inferior", "Andar inferior"), buildDeck("andar_superior", "Andar superior")] as EditorDeck[],
  slug: "",
  capacity_total: null as number | null,
  thumbnail_url: "",
  is_active: true,
});
const activeCellKey = ref<string | null>(null);
const cellEditor = reactive({
  type: "seat",
  label: "",
  selectable: true,
  blocked: false,
});
const cellTypeOptions = [
  { value: "seat", label: "Assento" },
  { value: "preferential", label: "Assento preferencial" },
  { value: "aisle", label: "Corredor" },
  { value: "door", label: "Porta" },
  { value: "driver", label: "Motorista" },
  { value: "stairs", label: "Escada" },
  { value: "wc", label: "Banheiro" },
  { value: "empty", label: "Vazio" },
  { value: "blocked", label: "Bloqueado" },
];

const vehicles = ref<VehicleOut[]>([]);
const vehicleForm = reactive<VehicleOut>({
  id: 0,
  name: "",
  plate: "",
  partner_name: "",
  layout_id: undefined,
  is_active: true,
  created_at: "",
});
const vehicleSaving = ref(false);

const editorGrid = computed<EditorCell[]>(() => {
  const cells: EditorCell[] = [];
  const deckCells = resolveActiveCells();
  const rows = activeRows.value;
  const cols = activeCols.value;
  const map = new Map<string, VehicleLayoutCellSchema>();
  deckCells.forEach(cell => map.set(`${cell.row}-${cell.col}`, cell));
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const key = `${row}-${col}`;
      const schema =
        map.get(key) ||
        ({
          row,
          col,
          type: col === Math.floor(cols / 2) ? "aisle" : "seat",
          selectable: col !== Math.floor(cols / 2),
          blocked: false,
        } as VehicleLayoutCellSchema);
      cells.push({
        key,
        schema,
        isSelected: activeCellKey.value === key,
      });
    }
  }
  return cells;
});

const loadData = async () => {
  loading.value = true;
  try {
    const { data } = await listVehicleLayouts();
    const detailResponses = await Promise.all(data.items.map(item => getVehicleLayoutDetail(item.id)));
    layouts.value = detailResponses.map(response => response.data);
  } finally {
    loading.value = false;
  }
};

const layoutNameById = (layoutId: number | undefined) => {
  if (!layoutId) return null;
  const match = layouts.value.find(entry => entry.id === layoutId);
  return match?.name || null;
};

const openEditor = async (layoutId?: number) => {
  editorVisible.value = true;
  if (layoutId) {
    const { data } = await getVehicleLayoutDetail(layoutId);
    setEditorFromDetail(data);
  } else {
    resetEditor();
  }
};

const closeEditor = () => {
  editorVisible.value = false;
};

const setEditorFromDetail = (detail: VehicleLayoutDetail) => {
  editorState.id = detail.id;
  editorState.name = detail.name;
  editorState.vehicle_type = detail.vehicle_type;
  editorState.slug = detail.slug || "";
  editorState.thumbnail_url = detail.thumbnail_url || "";
  editorState.is_active = detail.is_active;
  const schema = detail.layout_schema;
  const normalizeCell = (cell: VehicleLayoutCellSchema) => ({
    row: cell.row,
    col: cell.col,
    type: cell.type,
    label: cell.label || "",
    selectable: cell.selectable ?? true,
    blocked: cell.blocked ?? false,
  });
  if (schema?.decks && schema.decks.length) {
    editorState.deckMode = "double";
    editorState.decks = schema.decks.slice(0, 2).map((deck, index) => ({
      key: deck.key || `deck_${index + 1}`,
      label: deck.label || (index === 0 ? "Andar inferior" : "Andar superior"),
      rows: deck.rows,
      cols: deck.cols,
      cells: deck.cells.map(normalizeCell),
    }));
    while (editorState.decks.length < 2) {
      editorState.decks.push(buildDeck(`deck_${editorState.decks.length + 1}`, editorState.decks.length === 0 ? "Andar inferior" : "Andar superior"));
    }
    activeDeckIndex.value = 0;
    editorState.rows = editorState.decks[0].rows;
    editorState.cols = editorState.decks[0].cols;
    editorState.cells = editorState.decks[0].cells;
  } else {
    editorState.deckMode = "single";
    editorState.rows = detail.row_count;
    editorState.cols = detail.column_count;
    editorState.cells = schema?.cells ? schema.cells.map(normalizeCell) : [];
    editorState.decks = [buildDeck("andar_inferior", "Andar inferior"), buildDeck("andar_superior", "Andar superior")];
    activeDeckIndex.value = 0;
  }
  activeCellKey.value = null;
};

const resetEditor = () => {
  editorState.id = undefined;
  editorState.name = "";
  editorState.vehicle_type = "executivo";
  editorState.rows = 12;
  editorState.cols = 4;
  editorState.slug = "";
  editorState.thumbnail_url = "";
  editorState.is_active = true;
  editorState.cells = [];
  editorState.deckMode = "single";
  editorState.decks = [buildDeck("andar_inferior", "Andar inferior"), buildDeck("andar_superior", "Andar superior")];
  activeDeckIndex.value = 0;
  activeCellKey.value = null;
};

const selectCell = (entry: EditorCell) => {
  activeCellKey.value = entry.key;
  const collection = resolveActiveCells();
  const [row, col] = entry.key.split("-").map(Number);
  const cell = collection.find(item => item.row === row && item.col === col);
  if (cell) {
    cellEditor.type = cell.type;
    cellEditor.label = cell.label || "";
    cellEditor.selectable = cell.selectable ?? true;
    cellEditor.blocked = cell.blocked ?? false;
  } else {
    cellEditor.type = entry.schema.type;
    cellEditor.label = entry.schema.label || "";
    cellEditor.selectable = entry.schema.selectable ?? true;
    cellEditor.blocked = entry.schema.blocked ?? false;
  }
};

const updateCellFromEditor = () => {
  if (!activeCellKey.value) return;
  const [row, col] = activeCellKey.value.split("-").map(Number);
  const collection = resolveActiveCells();
  const existingIndex = collection.findIndex(entry => entry.row === row && entry.col === col);
  const nextCell: VehicleLayoutCellSchema = {
    row,
    col,
    type: cellEditor.type,
    label: cellEditor.label || undefined,
    selectable: cellEditor.selectable,
    blocked: cellEditor.blocked,
  };
  if (existingIndex >= 0) {
    collection.splice(existingIndex, 1, nextCell);
  } else {
    collection.push(nextCell);
  }
};

const buildDefaultCell = (rows: number, cols: number, row: number, col: number): VehicleLayoutCellSchema => {
  const corridor = Math.floor(cols / 2);
  const isAisle = col === corridor;
  return {
    row,
    col,
    type: isAisle ? "aisle" : "seat",
    label: undefined,
    selectable: !isAisle,
    blocked: false,
  };
};

const getDeckCollections = () => {
  if (editorState.deckMode === "double") {
    return editorState.decks;
  }
  return [
    {
      key: "andar_unico",
      label: "Andar unico",
      rows: editorState.rows,
      cols: editorState.cols,
      cells: editorState.cells,
    },
  ];
};

const upsertCellEntry = (collection: VehicleLayoutCellSchema[], entry: VehicleLayoutCellSchema) => {
  const index = collection.findIndex(item => item.row === entry.row && item.col === entry.col);
  if (index >= 0) {
    collection.splice(index, 1, entry);
  } else {
    collection.push(entry);
  }
};

const syncActiveCellEditor = () => {
  if (!activeCellKey.value) return;
  const deck = isDoubleDeck.value
    ? editorState.decks[activeDeckIndex.value]
    : { rows: editorState.rows, cols: editorState.cols, cells: editorState.cells };
  const [row, col] = activeCellKey.value.split("-").map(Number);
  const match = deck.cells.find(cell => cell.row === row && cell.col === col) || buildDefaultCell(deck.rows, deck.cols, row, col);
  cellEditor.type = match.type;
  cellEditor.label = match.label || "";
  cellEditor.selectable = match.selectable ?? true;
  cellEditor.blocked = match.blocked ?? false;
};

const clearSelection = () => {
  activeCellKey.value = null;
  cellEditor.type = "seat";
  cellEditor.label = "";
  cellEditor.selectable = true;
  cellEditor.blocked = false;
};

const resetLayoutCells = () => {
  if (isDoubleDeck.value) {
    editorState.decks.forEach(deck => deck.cells.splice(0, deck.cells.length));
  } else {
    editorState.cells.splice(0, editorState.cells.length);
  }
  clearSelection();
};

const generateAutomaticLabels = () => {
  updateCellFromEditor();
  let counter = 1;
  getDeckCollections().forEach(deck => {
    for (let row = 0; row < deck.rows; row += 1) {
      for (let col = 0; col < deck.cols; col += 1) {
        const base = deck.cells.find(cell => cell.row === row && cell.col === col) || buildDefaultCell(deck.rows, deck.cols, row, col);
        if (base.type === "seat" || base.type === "preferential") {
          const next = {
            ...base,
            label: String(counter),
          };
          counter += 1;
          upsertCellEntry(deck.cells, next);
        }
      }
    }
  });
  syncActiveCellEditor();
};

const clearSeatSelection = () => {
  clearSelection();
};

const resetCurrentLayout = () => {
  resetLayoutCells();
};

const saveLayout = async () => {
  updateCellFromEditor();
  editorSaving.value = true;
  try {
    const schemaPayload: VehicleLayoutSchema =
      editorState.deckMode === "double"
        ? {
            rows: editorState.decks[0].rows,
            cols: editorState.decks[0].cols,
            cells: [],
            decks: editorState.decks.map((deck, index) => ({
              key: deck.key || `deck_${index + 1}`,
              label: deck.label || (index === 0 ? "Andar inferior" : "Andar superior"),
              rows: deck.rows,
              cols: deck.cols,
              cells: deck.cells,
            })),
          }
        : {
            rows: editorState.rows,
            cols: editorState.cols,
            cells: editorState.cells,
          };
    const payload: VehicleLayoutPayload = {
      name: editorState.name,
      vehicle_type: editorState.vehicle_type,
      slug: editorState.slug || null,
      seat_count: undefined,
      row_count: editorState.deckMode === "double" ? undefined : editorState.rows,
      column_count: editorState.deckMode === "double" ? undefined : editorState.cols,
      thumbnail_url: editorState.thumbnail_url || null,
      is_active: editorState.is_active,
      layout_schema: schemaPayload,
    };
    if (editorState.id) {
      await updateVehicleLayoutRequest(editorState.id, payload);
    } else {
      await createVehicleLayoutRequest(payload);
    }
    await loadData();
    closeEditor();
  } finally {
    editorSaving.value = false;
  }
};

const deleteLayout = async (layoutId: number) => {
  if (!confirm("Excluir este layout?")) return;
  await deleteVehicleLayoutRequest(layoutId);
  await loadData();
};

const duplicateLayout = async (layoutId: number) => {
  await duplicateVehicleLayout(layoutId);
  await loadData();
};

const loadVehicles = async () => {
  const { data } = await listVehiclesRequest();
  vehicles.value = data.items;
};

const editVehicle = (vehicle: VehicleOut) => {
  vehicleForm.id = vehicle.id;
  vehicleForm.name = vehicle.name;
  vehicleForm.plate = vehicle.plate || "";
  vehicleForm.partner_name = vehicle.partner_name || "";
  vehicleForm.layout_id = vehicle.layout_id ?? undefined;
  vehicleForm.is_active = vehicle.is_active;
};

const resetVehicleForm = () => {
  vehicleForm.id = 0;
  vehicleForm.name = "";
  vehicleForm.plate = "";
  vehicleForm.partner_name = "";
  vehicleForm.layout_id = undefined;
  vehicleForm.is_active = true;
};

const saveVehicle = async () => {
  vehicleSaving.value = true;
  try {
    const payload: VehiclePayload = {
      name: vehicleForm.name,
      plate: vehicleForm.plate || null,
      partner_name: vehicleForm.partner_name || null,
      layout_id: vehicleForm.layout_id ?? null,
      is_active: vehicleForm.is_active,
    };
    if (vehicleForm.id) {
      await updateVehicleRequest(vehicleForm.id, payload);
    } else {
      await createVehicleRequest(payload);
    }
    resetVehicleForm();
    await loadVehicles();
  } finally {
    vehicleSaving.value = false;
  }
};

const removeVehicle = async (vehicleId: number) => {
  if (!confirm("Excluir este veiculo?")) return;
  await deleteVehicleRequest(vehicleId);
  await loadVehicles();
};

watch(
  () => ({ type: cellEditor.type, label: cellEditor.label, selectable: cellEditor.selectable, blocked: cellEditor.blocked }),
  () => {
    updateCellFromEditor();
  }
);

watch(
  () => editorState.deckMode,
  mode => {
    activeCellKey.value = null;
    if (mode === "double") {
      editorState.decks[0].rows = editorState.rows;
      editorState.decks[0].cols = editorState.cols;
      editorState.decks[0].cells = editorState.cells.map(cell => ({ ...cell }));
    } else {
      editorState.rows = editorState.decks[0].rows;
      editorState.cols = editorState.decks[0].cols;
      editorState.cells = editorState.decks[0].cells.map(cell => ({ ...cell }));
      activeDeckIndex.value = 0;
    }
  }
);

watch(activeDeckIndex, () => {
  activeCellKey.value = null;
});

onMounted(() => {
  void loadData();
  void loadVehicles();
});
</script>

<style scoped>
.page {
  @apply space-y-8;
}
.page-header {
  @apply flex flex-col gap-4 rounded-3xl border border-slate-100 bg-white p-6 shadow-sm lg:flex-row lg:items-center lg:justify-between;
}
.subtitle {
  @apply text-sm text-slate-600;
}
.actions {
  @apply flex gap-3;
}
.btn-primary {
  @apply rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-emerald-700;
}
.btn-secondary {
  @apply rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-emerald-400;
}
.btn-light {
  @apply rounded-full border border-slate-200 px-3 py-1 text-sm font-semibold text-slate-600;
}
.btn-ghost {
  @apply rounded-full px-3 py-1 text-sm font-semibold text-slate-500 hover:text-emerald-600;
}
.layouts-grid {
  @apply grid gap-4 md:grid-cols-2;
}
.layout-card {
  @apply flex flex-col gap-3 rounded-3xl border border-slate-100 bg-white p-5 shadow-sm;
}
.layout-card__header {
  @apply flex items-center justify-between gap-3;
}
.layout-name {
  @apply text-lg font-semibold text-slate-900;
}
.layout-meta {
  @apply text-sm text-slate-500;
}
.layout-preview {
  @apply rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4;
}
.layout-grid {
  @apply grid gap-2;
}
.layout-cell {
  @apply h-3 w-3 rounded bg-slate-200;
}
.layout-cell--seat {
  @apply bg-emerald-400/70;
}
.layout-card__actions {
  @apply flex flex-wrap gap-2;
}
.deck-summary {
  @apply rounded-2xl border border-slate-100 bg-slate-50/60 p-3;
}
.deck-summary__title {
  @apply text-xs font-semibold uppercase tracking-[0.3em] text-slate-400;
}
.deck-summary__list {
  @apply mt-2 flex flex-wrap gap-2 text-xs text-slate-600;
}
.deck-chip {
  @apply rounded-full bg-white px-2 py-1;
}
.status-pill {
  @apply rounded-full px-3 py-1 text-xs font-semibold;
}
.status-pill--success {
  @apply bg-emerald-100 text-emerald-600;
}
.status-pill--muted {
  @apply bg-slate-100 text-slate-500;
}
.vehicles-section {
  @apply space-y-4 rounded-3xl border border-slate-100 bg-white p-6 shadow-sm;
}
.vehicle-header {
  @apply flex items-center justify-between;
}
.vehicles-grid {
  @apply grid gap-4 md:grid-cols-2;
}
.vehicle-card {
  @apply flex flex-col gap-3 rounded-2xl border border-slate-100 p-4 shadow-sm;
}
.vehicle-card--form {
  @apply bg-slate-50;
}
.vehicle-name {
  @apply text-base font-semibold text-slate-900;
}
.vehicle-meta {
  @apply text-sm text-slate-500;
}
.vehicle-actions {
  @apply flex flex-wrap gap-2;
}
.form-field {
  @apply flex flex-col gap-1 text-sm font-semibold text-slate-600;
}
.form-field input,
.form-field select {
  @apply rounded-2xl border border-slate-200 px-3 py-2 text-sm font-normal text-slate-900 focus:border-emerald-400 focus:outline-none;
}
.checkbox-field {
  @apply flex items-center gap-2 text-sm text-slate-600;
}
.drawer {
  position: fixed;
  inset: 0;
  z-index: 50;
}
.drawer__backdrop {
  @apply absolute inset-0 bg-slate-900/40 backdrop-blur;
}
.drawer__panel {
  @apply absolute right-1/2 top-4 h-[calc(100%-2rem)] w-[95%] max-w-7xl translate-x-1/2 rounded-3xl bg-white p-10 shadow-2xl;
  overflow-y: auto;
}
.drawer__header {
  @apply flex flex-col gap-3 border-b border-slate-100 pb-4 md:flex-row md:items-center md:justify-between;
}
.header-left {
  @apply max-w-xl;
}
.header-subtitle {
  @apply text-sm text-slate-500;
}
.header-actions {
  @apply flex flex-wrap items-center gap-3;
}
.editor-form {
  @apply mt-4;
}
.builder-grid {
  @apply grid gap-4 lg:grid-cols-[30%_40%_30%];
}
.builder-panel {
  @apply rounded-3xl border border-slate-100 bg-white p-5 shadow-sm space-y-4;
}
.panel-heading h4 {
  @apply text-base font-semibold text-slate-900;
}
.panel-heading p {
  @apply text-sm text-slate-500;
}
.layout-details-panel .form-field {
  @apply space-y-1;
}
.deck-tabs {
  @apply flex gap-2;
}
.deck-tab {
  @apply rounded-full border border-slate-200 px-3 py-1 text-sm font-semibold text-slate-600 transition;
}
.deck-tab--active {
  @apply border-emerald-400 bg-emerald-50 text-emerald-700;
}
.seat-count-summary {
  @apply rounded-2xl bg-slate-50/80 p-3 text-sm text-slate-600 space-y-2;
}
.seat-count-summary__title {
  @apply text-sm font-semibold text-slate-800;
}
.indicator-grid {
  @apply grid grid-cols-2 gap-2 md:grid-cols-4;
}
.indicator-item {
  @apply rounded-2xl bg-white/80 p-2 text-center text-xs text-slate-500;
}
.indicator-item strong {
  @apply block text-base text-slate-900;
}
.helper-text {
  @apply text-xs text-slate-500;
}
.editor-grid__canvas {
  @apply grid gap-x-6 gap-y-4 rounded-[2rem] border border-white/40 bg-white/80 p-6;
}
.editor-cell {
  @apply flex min-h-[48px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-xs font-semibold text-slate-600 shadow-sm transition;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, background-color 0.15s ease;
}
.editor-cell--seat {
  @apply border-emerald-300 bg-emerald-50 text-emerald-700;
}
.editor-cell--preferential {
  @apply border-amber-300 bg-amber-50 text-amber-700;
}
.editor-cell--aisle {
  @apply h-full w-full rounded-full border-none bg-slate-200/70 text-transparent shadow-inner cursor-pointer;
}
.editor-cell--door,
.editor-cell--driver,
.editor-cell--stairs,
.editor-cell--wc {
  @apply border-slate-300 bg-slate-100 text-slate-600;
}
.editor-cell--blocked {
  @apply border-slate-200 bg-slate-200 text-slate-400;
}
.editor-cell--active {
  @apply border-emerald-500 bg-emerald-100 text-emerald-700 shadow-lg ring-2 ring-emerald-400/40;
  transform: translateY(-1px);
}
.editor-cell:hover {
  @apply shadow-md;
  transform: translateY(-1px);
}
.editor-cell:active {
  transform: scale(0.98);
}
.drawer__footer {
  @apply flex items-center justify-end gap-3 border-t border-slate-100 pt-4;
}
.bus-orientation {
  @apply text-xs font-semibold text-slate-500;
}
.bus-shell {
  @apply relative rounded-[2.5rem] bg-slate-100 p-6 shadow-inner;
}
.bus-front {
  @apply absolute left-1/2 top-2 flex -translate-x-1/2 flex-col items-center gap-1;
}
.bus-front__window {
  @apply h-4 w-16 rounded-full bg-slate-200;
}
.bus-front__driver {
  @apply h-3 w-3 rounded-full bg-emerald-500;
}
.bus-body {
  @apply mt-8;
}
.map-actions-row {
  @apply mb-3 flex flex-wrap gap-2;
}
.map-actions-row .btn-ghost {
  @apply rounded-full border border-slate-200 bg-white/60 px-3 py-1 text-xs text-slate-600;
}
.cell-config-panel .form-field {
  @apply space-y-1;
}
.builder-panel .btn-ghost[disabled] {
  @apply opacity-60 cursor-not-allowed;
}
.deck-summary__list {
  @apply flex flex-wrap gap-2 text-xs text-slate-500;
}
.deck-summary__list li {
  @apply rounded-full bg-white px-2 py-1;
}
.bus-shell::after {
  content: "";
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 70%;
  height: 100%;
  border-radius: 2rem;
  pointer-events: none;
}
.placeholder-card {
  @apply rounded-3xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500;
}
</style>
