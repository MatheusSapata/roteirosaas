<template>
  <section class="seat-step" :class="{ 'seat-step--summary': context && !canSelectSeats, 'seat-step--embedded': showHeader === false }">
    <div class="seat-step__shell">
      <header v-if="showHeader" class="seat-step__header" :class="{ 'seat-step__header--center': !canSelectSeats }">
        <div class="seat-step__headline">
          <p class="seat-step__eyebrow" v-if="canSelectSeats">Selecao de assentos</p>
          <h2 v-if="canSelectSeats">
            Escolha de assentos
          </h2>
          <div v-else class="seat-modal__hero">
            <div class="seat-modal__hero-icon">&#10003;</div>
            <div class="seat-modal__hero-copy">
              <h2 class="seat-modal__hero-title">Reserva confirmada</h2>
              <p class="seat-modal__hero-subtitle">Seus assentos foram garantidos</p>
            </div>
          </div>
          <p v-if="canSelectSeats" class="seat-step__meta">
            <span>{{ context?.product_name || "Produto" }}</span>
            <span>{{ context?.trip_vehicle?.display_name || "Veiculo 1" }}</span>
            <span>{{ context?.trip_vehicle ? `${context.trip_vehicle.occupied_seats}/${context.trip_vehicle.capacity} ocupados` : "Ocupacao a confirmar" }}</span>
            <span>Etapa 2 de 2</span>
          </p>
          <p v-else class="subtitle" :class="{ 'subtitle--centered': !canSelectSeats }">
            {{ context?.product_name }} &middot;
            {{ formattedTripDate || "Data a confirmar" }}
          </p>
          <p v-if="!canSelectSeats && context?.trip_vehicle" class="subtitle subtitle--muted" :class="{ 'subtitle--centered': !canSelectSeats }">
            Ônibus liberado: {{ context.trip_vehicle.display_name || "Operacional" }} &middot;
            {{ context.trip_vehicle.occupied_seats }}/{{ context.trip_vehicle.capacity }} ocupados
          </p>
        </div>
        <div v-if="canSelectSeats" class="seat-step__progress">
          <span>Etapa 2 de 2</span>
          <strong>{{ context?.stats.assigned_passengers || 0 }}/{{ context?.passengers.length || 0 }} com assento</strong>
          <div class="seat-step__progress-track">
            <div class="seat-step__progress-fill" :style="{ width: progressPercentage + '%' }"></div>
          </div>
        </div>
      </header>

      <div v-if="loading" class="seat-modal__state">
        <div class="spinner"></div>
        <p>Carregando mapa de assentos...</p>
      </div>

      <div v-else-if="errorMessage" class="seat-modal__state seat-modal__state--error">
        <p>{{ errorMessage }}</p>
        <button type="button" class="btn-secondary" @click="() => loadContext(activeVehicleId)">Tentar novamente</button>
      </div>

      <div v-else-if="context && canSelectSeats" class="seat-step__content selection-layout">
          <aside class="passenger-panel">
            <div class="panel-card">
              <div class="panel-heading">
                <p class="eyebrow">Passageiros</p>
                <strong>{{ context.passengers.length }}</strong>
              </div>
              <p class="progress-text">
                {{ context.stats.assigned_passengers }} de {{ context.passengers.length }} passageiros com assento
              </p>
              <div class="progress-bar">
                <div
                  class="progress-bar__fill"
                  :style="{ width: progressPercentage + '%' }"
                ></div>
              </div>
              <ul class="passenger-list">
                <li
                  v-for="(passenger, index) in context.passengers"
                  :key="passenger.id"
                  :class="[
                    'passenger-item',
                    passenger.id === activePassengerId ? 'passenger-item--active' : '',
                    passenger.status === 'assigned' ? 'passenger-item--assigned' : '',
                  ]"
                  @click="setActivePassenger(passenger.id)"
                  :aria-selected="passenger.id === activePassengerId"
                >
                  <div class="passenger-item__index">{{ index + 1 }}</div>
                  <div class="passenger-item__info">
                    <p class="passenger-name">{{ passenger.name }}</p>
                    <p
                      class="passenger-seat"
                      :class="passenger.status === 'assigned' ? 'passenger-seat--assigned' : 'passenger-seat--empty'"
                    >
                      {{ passengerSeatSummary(passenger) }}
                    </p>
                  </div>
                  <span
                    :class="[
                      'passenger-status-badge',
                      passenger.status === 'assigned'
                        ? 'passenger-status-badge--assigned'
                        : 'passenger-status-badge--pending',
                    ]"
                  >
                    {{ passengerStatusLabel(passenger) }}
                  </span>
                </li>
              </ul>
            </div>
          </aside>

          <section class="map-panel">
            <div class="panel-card map-card">
              <div class="map-card__header">
                <div>
                  <p class="eyebrow">Mapa de assentos</p>
                  <h3>{{ context.trip_vehicle?.display_name || "Veiculo operacional" }}</h3>
                  <span>Selecione um assento livre para o passageiro ativo.</span>
                </div>
                <div class="map-card__kpi" v-if="context.trip_vehicle">
                  <strong>{{ context.trip_vehicle.occupied_seats }}/{{ context.trip_vehicle.capacity }}</strong>
                  <span>ocupados</span>
                </div>
              </div>
              <div v-if="vehicleOptions.length > 1" class="vehicle-tabs">
                <button
                  v-for="vehicle in vehicleOptions"
                  :key="vehicle.id"
                  type="button"
                  :class="['vehicle-tab', vehicle.id === activeVehicleId ? 'vehicle-tab--active' : '']"
                  @click="selectVehicle(vehicle.id)"
                >
                  <span class="vehicle-tab__name">{{ vehicle.display_name || `Veiculo ${vehicle.order_index}` }}</span>
                  <span class="vehicle-tab__meta">
                    {{ vehicle.occupied_seats }}/{{ vehicle.capacity }} ocupados
                  </span>
                </button>
              </div>
              <ul class="map-legend">
                <li class="legend-item">
                  <span class="legend-dot legend-dot--available"></span>
                  <span>Livre</span>
                </li>
                <li class="legend-item">
                  <span class="legend-dot legend-dot--selected"></span>
                  <span>Selecionado</span>
                </li>
                <li class="legend-item">
                  <span class="legend-dot legend-dot--occupied"></span>
                  <span>Ocupado</span>
                </li>
                <li class="legend-item">
                  <span class="legend-dot legend-dot--blocked"></span>
                  <span>Bloqueado</span>
                </li>
                <li class="legend-item">
                  <span class="legend-dot legend-dot--mine"></span>
                  <span>Seu grupo</span>
                </li>
              </ul>
              <div v-if="seatDecks.length" class="deck-wrapper">
                <div class="deck-tabs" v-if="seatDecks.length > 1">
                  <button
                    v-for="deck in seatDecks"
                    :key="deck.key"
                    type="button"
                    :class="['deck-tab', deck.key === currentDeck?.key ? 'deck-tab--active' : '']"
                    @click="activeDeckKey = deck.key"
                  >
                    {{ deck.label || `Andar ${deck.key}` }}
                  </button>
                </div>
                <div v-if="currentDeck" class="deck-section">
                  <div class="bus-stage">
                    <span class="bus-front-label">Frente do onibus</span>
                    <div class="bus-shell">
                      <div class="bus-front">
                        <div class="bus-front__window"></div>
                        <div class="bus-front__driver"></div>
                      </div>
                      <div class="bus-body">
                       <div
                          ref="busBodyRef"
                          class="bus-grid"
                          :class="{ 'bus-grid--desktop-horizontal': isDesktop }"
                          :style="{
                            '--seat-unit': `${seatGridUnit}px`,
                            '--seat-gap': `${seatGridGap}px`,
                            gridTemplateColumns: `repeat(${displayDeck.columns || 1}, minmax(${seatGridUnit}px, ${seatGridUnit}px))`,
                          }"
                        >
                          <div
                            v-for="cell in displayDeck.cells"
                            :key="`${displayDeck.key}-${cell.key}`"
                            :class="cellClasses(cell)"
                            @click="handleSeatClick(cell)"
                            :title="seatTooltip(cell)"
                            role="button"
                            tabindex="0"
                          >
                            <span v-if="cell.seat" class="seat-label">
                              {{ cell.seat.seat_label || cell.seat.seat_number }}
                            </span>
                          </div>
                        </div>  
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="empty-state">Layout indisponivel para renderizacao.</div>
              <p class="map-note">Os assentos podem sofrer ajustes pela agencia.</p>
            </div>
          </section>

          <aside class="info-panel">
            <div class="panel-card info-card">
              <div class="panel-heading">
                <p class="eyebrow">Resumo</p>
                <strong>{{ progressPercentage }}%</strong>
              </div>
              <div class="info-summary">
                <span class="info-summary__label">Passageiro</span>
                <span class="info-summary__value">{{ activePassenger?.name || "Selecione um passageiro" }}</span>
              </div>
              <div class="info-summary">
                <span class="info-summary__label">Assento selecionado</span>
                <span class="info-summary__value info-summary__value--seat">{{ activeSeatLabel }}</span>
              </div>
              <div class="info-summary">
                <span class="info-summary__label">Status</span>
                <span :class="['status-pill', passengerStatusClass(activePassenger)]">
                  {{ passengerStatusLabel(activePassenger) }}
                </span>
              </div>
              <div class="info-summary">
                <span class="info-summary__label">Progresso</span>
                <span class="info-summary__value">{{ context.stats.assigned_passengers }} de {{ context.passengers.length }} concluidos</span>
                <div class="progress-bar progress-bar--summary">
                  <div class="progress-bar__fill" :style="{ width: progressPercentage + '%' }"></div>
                </div>
              </div>
              <p class="info-note" v-if="context.preference_notice">
                {{ context.preference_notice }}
              </p>
              <div v-if="context.boarding_notes" class="boarding-notes">
                <p class="eyebrow mb-1">Observacoes</p>
                <p class="text-sm text-slate-600">
                  {{ context.boarding_notes }}
                </p>
              </div>
              <div v-if="selectingSeat" class="inline-loading">
                <div class="spinner spinner--sm"></div>
                <span>Registrando assento...</span>
              </div>
              <p v-if="selectionError" class="selection-error">{{ selectionError }}</p>
              <button
                type="button"
                class="btn-primary w-full mt-6"
                :disabled="!hasPendingSelections || selectingSeat"
                @click="confirmSelection"
              >
                Confirmar assentos
              </button>
              <button type="button" class="btn-secondary mt-2 w-full" @click="handleBack">
                Voltar para passageiros
              </button>
            </div>
          </aside>
        </div>

      <div v-else-if="context" class="seat-step__content summary-only">
        <section class="summary-hero">
          <div class="summary-hero__intro summary-hero__intro--plain">
            <h3>Detalhes da sua reserva</h3>
            <p>
              {{ context.message || "Confira abaixo os passageiros e assentos atribuídos." }}
            </p>
          </div>
          <div class="summary-stats">
            <div class="summary-stat">
              <span class="summary-stat__label">Passageiros</span>
              <strong class="summary-stat__value">{{ context.passengers.length }}</strong>
            </div>
            <div class="summary-stat" v-if="context.trip_vehicle">
              <span class="summary-stat__label">Veículo</span>
              <strong class="summary-stat__value">
                {{ context.trip_vehicle.display_name || `Veículo ${context.trip_vehicle.order_index}` }}
              </strong>
            </div>
            <div class="summary-stat">
              <span class="summary-stat__label">Data</span>
              <strong class="summary-stat__value">{{ formattedTripDate || "A confirmar" }}</strong>
            </div>
            <div class="summary-status-desktop">
              <span class="summary-list-header__status">Todos os assentos garantidos</span>
            </div>
          </div>
        </section>

        <div class="summary-list-header">
          <p class="summary-list-header__title">Passageiros e assentos</p>
          <span class="summary-list-header__status summary-list-header__status--mobile">Todos os assentos garantidos</span>
        </div>

        <ul class="passenger-summary-list">
          <li
            v-for="passenger in context.passengers"
            :key="passenger.id"
            class="passenger-summary-card"
          >
            <div class="passenger-summary-card__identity">
              <div class="passenger-summary-card__avatar">
                {{ passenger.name.slice(0, 1) }}
              </div>
              <div>
                <p class="passenger-name">{{ passenger.name }}</p>
                <p class="passenger-seat">Passageiro confirmado</p>
              </div>
            </div>
            <div class="passenger-summary-card__meta">
              <span class="passenger-summary-card__seat-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" focusable="false">
                  <path
                    fill="currentColor"
                    d="M7 18S4 10 4 6s2-4 2-4h1s1 0 1 1s-1 1-1 3s3 4 3 7s-3 5-3 5m5-1c-1 0-4 2.5-4 2.5c-.3.2-.2.5 0 .8c0 0 1 1.8 3 1.8h6c1.1 0 2-.9 2-2v-1c0-1.1-.9-2-2-2h-5Z"
                  />
                </svg>
              </span>
              <strong class="passenger-summary-card__seat-value">
                {{ passenger.seat_label || passenger.seat_number || "Pendente" }}
              </strong>
            </div>
          </li>
        </ul>
        <div class="summary-footer">
          <p class="summary-note">
            Os assentos escolhidos podem sofrer ajustes operacionais pela agência.
          </p>
          <button type="button" class="btn-primary summary-footer__action" @click="handleBack">Voltar para passageiros</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { isAxiosError } from "axios";
import type { SeatSelectionContext, TripSeatOut, VehicleLayoutCellSchema } from "../../types/transport";
import {
  getPublicSaleSeatSelectionContext,
  getPublicSeatSelectionContext,
  selectSeatForSale,
  selectSeatForSignature,
} from "../../services/transport";

interface SeatCellEntry {
  key: string;
  schema?: VehicleLayoutCellSchema;
  seat: TripSeatOut | null;
}

interface SeatDeckView {
  key: string;
  label: string;
  columns: number;
  cells: SeatCellEntry[];
}

type PassengerEntry = SeatSelectionContext["passengers"][number] | null;

const props = defineProps<{
  token: string;
  tokenType?: "signature" | "sale";
  productPublicId?: string | null;
  showHeader?: boolean;
}>();

const emit = defineEmits<{
  (event: "back"): void;
  (event: "updated", ctx: SeatSelectionContext): void;
  (event: "context-loaded", ctx: SeatSelectionContext): void;
}>();

const loading = ref(false);
const context = ref<SeatSelectionContext | null>(null);
const errorMessage = ref("");
const selectionError = ref("");
const activePassengerId = ref<number | null>(null);
const pendingSelections = ref<Record<number, SeatCellEntry | null>>({});
const selectingSeat = ref(false);
const activeDeckKey = ref<string | null>(null);
const isDesktop = ref(false);
const activeVehicleId = ref<number | null>(null);
const resolvedTokenType = computed(() => props.tokenType || "signature");
const busBodyRef = ref<HTMLElement | null>(null);
const mapAvailableWidth = ref(0);
let busResizeObserver: ResizeObserver | null = null;

const updateViewport = () => {
  if (typeof window === "undefined") return;
  isDesktop.value = window.innerWidth >= 1024;
};

const formattedTripDate = computed(() => {
  if (!context.value?.trip_date) return "";
  const date = new Date(context.value.trip_date);
  if (Number.isNaN(date.getTime())) return context.value.trip_date;
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
});

const activePassenger = computed(() =>
  context.value?.passengers.find(passenger => passenger.id === activePassengerId.value) || null
);

const pendingSeatForActive = computed(() => {
  if (!activePassengerId.value) return null;
  return pendingSelections.value[activePassengerId.value] || null;
});

const hasPendingSelections = computed(() =>
  Object.values(pendingSelections.value).some(entry => entry?.seat)
);

const canSelectSeats = computed(() => {
  if (!context.value) return false;
  const total = context.value.passengers.length;
  const assigned = context.value.stats.assigned_passengers;
  return Boolean(context.value.can_assign && assigned < total);
});

const activeSeatLabel = computed(() => {
  const pending = pendingSeatForActive.value;
  if (pending?.seat) {
    return pending.seat.seat_label || pending.seat.seat_number || "Assento selecionado";
  }
  if (!activePassenger.value) return "Clique em um assento livre";
  return (
    activePassenger.value.seat_label ||
    activePassenger.value.seat_number ||
    "Clique em um assento livre"
  );
});

const progressPercentage = computed(() => {
  if (!context.value) return 0;
  const total = context.value.passengers.length || 1;
  return Math.min(100, Math.round((context.value.stats.assigned_passengers / total) * 100));
});

const vehicleOptions = computed(() => context.value?.vehicles || []);

const seatDecks = computed<SeatDeckView[]>(() => {
  const schema = context.value?.layout?.layout_schema;
  if (!schema) return [];

  const decks = schema.decks?.length
    ? schema.decks
    : schema.rows && schema.cols
      ? [
          {
            key: "andar_unico",
            label: "Andar unico",
            rows: schema.rows,
            cols: schema.cols,
            cells: schema.cells,
          },
        ]
      : [];

  const seatMap = new Map<string, TripSeatOut>();

  (context.value?.seats || []).forEach(seat => {
    const deckKey = seat.deck_key || decks[0]?.key || "andar_unico";
    seatMap.set(`${deckKey}:${seat.row_index}-${seat.col_index}`, seat);
  });

  return decks.map(deck => {
    const cells: SeatCellEntry[] = [];

    for (let row = 0; row < deck.rows; row += 1) {
      for (let col = 0; col < deck.cols; col += 1) {
        const key = `${row}-${col}`;
        const seat = seatMap.get(`${deck.key}:${key}`) || null;
        const schemaCell = deck.cells.find(cell => cell.row === row && cell.col === col);

        cells.push({
          key,
          schema: schemaCell,
          seat,
        });
      }
    }

    return {
      key: deck.key,
      label: deck.label,
      columns: deck.cols,
      cells,
    };
  });
});

const currentDeck = computed<SeatDeckView | null>(() => {
  const decks = seatDecks.value;
  if (!decks.length) return null;
  return decks.find(deck => deck.key === activeDeckKey.value) || decks[0];
});

const transposeDeck = (deck: SeatDeckView): SeatDeckView => {
  const originalColumns = deck.columns || 1;
  const originalRows = Math.ceil(deck.cells.length / originalColumns);

  const matrix: SeatCellEntry[][] = Array.from({ length: originalRows }, (_, row) =>
    deck.cells.slice(row * originalColumns, (row + 1) * originalColumns)
  );

  const transposedCells: SeatCellEntry[] = [];

  for (let col = originalColumns - 1; col >= 0; col -= 1) {
    for (let row = 0; row < originalRows; row += 1) {
      const cell = matrix[row]?.[col];
      if (!cell) continue;

      transposedCells.push({
        ...cell,
        key: `desktop-${col}-${row}`,
      });
    }
  }

  return {
    key: `${deck.key}-desktop`,
    label: deck.label,
    columns: originalRows,
    cells: transposedCells,
  };
};

const displayDeck = computed<SeatDeckView>(() => {
  if (!currentDeck.value) {
    return {
      key: "empty",
      label: "",
      columns: 1,
      cells: [],
    };
  }

  return isDesktop.value ? transposeDeck(currentDeck.value) : currentDeck.value;
});

const seatGridGap = computed(() => (isDesktop.value ? 8 : 6));

const seatGridUnit = computed(() => {
  const columns = displayDeck.value?.columns || 1;
  const fallback = isDesktop.value ? 48 : 36;
  const min = isDesktop.value ? 34 : 28;
  const max = isDesktop.value ? 64 : 46;
  const available = mapAvailableWidth.value;

  if (!available || columns <= 0) return fallback;

  const innerPadding = isDesktop.value ? 24 : 16;
  const usable = available - innerPadding;
  const raw = Math.floor((usable - seatGridGap.value * Math.max(columns - 1, 0)) / columns);

  return Math.max(min, Math.min(max, raw || fallback));
});

const syncBusBodyWidth = () => {
  if (!busBodyRef.value) return;
  mapAvailableWidth.value = Math.floor(busBodyRef.value.clientWidth);
};

const bindBusResizeObserver = () => {
  if (typeof window === "undefined" || typeof ResizeObserver === "undefined") return;
  busResizeObserver?.disconnect();
  busResizeObserver = null;
  if (!busBodyRef.value) return;
  busResizeObserver = new ResizeObserver(() => {
    syncBusBodyWidth();
  });
  busResizeObserver.observe(busBodyRef.value);
  syncBusBodyWidth();
};

const loadContext = async (vehicleId?: number | null) => {
  if (!props.token) return;

  loading.value = true;
  errorMessage.value = "";

  try {
    const { data } =
      resolvedTokenType.value === "sale"
        ? await getPublicSaleSeatSelectionContext(
            props.token,
            vehicleId || undefined,
            undefined,
            props.productPublicId,
          )
        : await getPublicSeatSelectionContext(props.token, vehicleId || undefined);
    context.value = data;
    emit("context-loaded", data);
    activeVehicleId.value = data.trip_vehicle?.id || null;
    pendingSelections.value = {};
    selectionError.value = "";

    if (!activePassengerId.value && data.passengers.length) {
      activePassengerId.value = data.passengers[0].id;
    } else if (activePassengerId.value) {
      const stillExists = data.passengers.some(passenger => passenger.id === activePassengerId.value);
      if (!stillExists && data.passengers.length) {
        activePassengerId.value = data.passengers[0].id;
      }
    }
  } catch (error) {
    if (isAxiosError(error)) {
      errorMessage.value =
        (error.response?.data as { detail?: string })?.detail ||
        "Nao foi possivel carregar o mapa de assentos.";
    } else {
      errorMessage.value = "Nao foi possivel carregar o mapa de assentos.";
    }
  } finally {
    loading.value = false;
  }
};

const setActivePassenger = (passengerId: number) => {
  activePassengerId.value = passengerId;
  selectionError.value = "";
};

const selectVehicle = (vehicleId: number) => {
  if (vehicleId === activeVehicleId.value || loading.value) return;
  activeVehicleId.value = vehicleId;
  void loadContext(vehicleId);
};

const passengerSeatSummary = (passenger?: PassengerEntry) => {
  if (!passenger) return "Sem assento definido";

  const pending = passenger.id ? pendingSelections.value[passenger.id] : null;
  if (pending?.seat) {
    return `Selecionado: ${pending.seat.seat_label || pending.seat.seat_number || "Assento"}`;
  }

  const seat = passenger.seat_label || passenger.seat_number;
  return seat ? `Assento ${seat}` : "Sem assento definido";
};

const passengerStatusLabel = (passenger?: PassengerEntry) =>
  passenger?.status === "assigned" ? "Confirmado" : "Pendente";

const passengerStatusClass = (passenger?: PassengerEntry) =>
  passenger?.status === "assigned" ? "status-pill--success" : "status-pill--pending";

const findPendingSeatOwner = (seatId?: number | null) => {
  if (!seatId) return null;

  for (const [passengerKey, entry] of Object.entries(pendingSelections.value)) {
    if (entry?.seat?.id === seatId) {
      return Number(passengerKey);
    }
  }

  return null;
};

const seatTooltip = (entry: SeatCellEntry) => {
  if (!entry.seat) {
    if (entry.schema?.type === "aisle") return "Corredor do onibus";
    if (entry.schema?.selectable === false) return "Espaco nao selecionavel";
    return "Area vazia";
  }

  const label = entry.seat.seat_label || entry.seat.seat_number || "Assento";
  const pendingOwner = findPendingSeatOwner(entry.seat.id);

  if (pendingOwner && pendingOwner !== activePassengerId.value) {
    return `Assento ${label} reservado para outro passageiro`;
  }

  if (entry.seat.is_blocked || !entry.seat.is_selectable) return `Assento ${label} bloqueado`;
  if (entry.seat.is_occupied && !entry.seat.occupied_by_current_sale) return `Assento ${label} ocupado`;
  if (entry.seat.is_occupied) return `Assento ${label} do seu grupo`;

  return `Clique para selecionar o assento ${label}`;
};

const cellClasses = (entry: SeatCellEntry) => {
  const classes = ["seat-cell"];

  if (!entry.schema) {
    classes.push("seat-cell--empty");
    return classes;
  }

  if (entry.schema.type === "aisle" || entry.schema.type === "empty") {
    classes.push("seat-cell--aisle");
    return classes;
  }

  if (!entry.seat) {
    classes.push(entry.schema.selectable === false ? "seat-cell--blocked" : "seat-cell--available");
    return classes;
  }

  const seat = entry.seat;
  const pendingOwner = findPendingSeatOwner(seat.id);

  if (pendingOwner) {
    if (pendingOwner === activePassengerId.value) {
      classes.push("seat-cell--selected");
    } else {
      classes.push("seat-cell--occupied");
    }
    return classes;
  }

  if (seat.is_blocked || !seat.is_selectable) {
    classes.push("seat-cell--blocked");
  } else if (seat.is_occupied && !seat.occupied_by_current_sale) {
    classes.push("seat-cell--occupied");
  } else if (seat.is_occupied && activePassengerId.value === seat.occupied_by_passenger_id) {
    classes.push("seat-cell--selected");
  } else if (seat.is_occupied) {
    classes.push("seat-cell--mine");
  } else {
    classes.push("seat-cell--available");
  }

  return classes;
};

const handleSeatClick = (entry: SeatCellEntry) => {
  if (!context.value || !entry.seat) return;
  if (!activePassengerId.value) return;

  if (!entry.seat.is_selectable || entry.seat.is_blocked) {
    selectionError.value = "Este assento nao pode ser selecionado.";
    return;
  }

  if (entry.seat.is_occupied) {
    if (entry.seat.occupied_by_current_sale) {
      selectionError.value = "Este assento ja pertence ao seu grupo.";
    } else {
      selectionError.value = "Assento ja ocupado.";
    }
    return;
  }

  const pendingOwner = findPendingSeatOwner(entry.seat.id);
  if (pendingOwner && pendingOwner !== activePassengerId.value) {
    selectionError.value = "Assento reservado para outro passageiro.";
    return;
  }

  pendingSelections.value = {
    ...pendingSelections.value,
    [activePassengerId.value]: entry,
  };
  selectionError.value = "";
};

const confirmSelection = async () => {
  if (!context.value) return;

  const entries = Object.entries(pendingSelections.value).filter(([, entry]) => entry?.seat);

  if (!entries.length) {
    selectionError.value = "Selecione ao menos um assento antes de confirmar.";
    return;
  }

  selectingSeat.value = true;
  selectionError.value = "";

  try {
    for (const [passengerKey, entry] of entries) {
      const passengerId = Number(passengerKey);
      if (!entry?.seat) continue;

      const selector = resolvedTokenType.value === "sale" ? selectSeatForSale : selectSeatForSignature;
      if (resolvedTokenType.value === "sale") {
        await selectSeatForSale(
          props.token,
          {
            passenger_id: passengerId,
            seat_id: entry.seat.id,
          },
          undefined,
          props.productPublicId,
        );
      } else {
        await selector(props.token, {
          passenger_id: passengerId,
          seat_id: entry.seat.id,
        });
      }
    }

    await loadContext(activeVehicleId.value);
    pendingSelections.value = {};
    selectionError.value = "";
    emit("updated", context.value!);
  } catch (error) {
    if (isAxiosError(error)) {
      selectionError.value =
        (error.response?.data as { detail?: string })?.detail ||
        "Nao foi possivel registrar os assentos.";
    } else {
      selectionError.value = "Nao foi possivel registrar os assentos.";
    }
  } finally {
    selectingSeat.value = false;
  }
};

const handleBack = () => {
  pendingSelections.value = {};
  selectionError.value = "";
  emit("back");
};

watch(
  () => props.productPublicId,
  () => {
    activeVehicleId.value = null;
    activePassengerId.value = null;
    pendingSelections.value = {};
    selectionError.value = "";
    void loadContext();
  },
);

watch(seatDecks, decks => {
  if (!decks.length) {
    activeDeckKey.value = null;
    return;
  }

  if (!activeDeckKey.value || !decks.some(deck => deck.key === activeDeckKey.value)) {
    activeDeckKey.value = decks[0].key;
  }
  requestAnimationFrame(() => {
    bindBusResizeObserver();
    syncBusBodyWidth();
  });
});

onMounted(() => {
  updateViewport();
  window.addEventListener("resize", updateViewport);
  window.addEventListener("resize", syncBusBodyWidth);

  void loadContext(activeVehicleId.value);
  requestAnimationFrame(() => {
    bindBusResizeObserver();
    syncBusBodyWidth();
  });
});

onBeforeUnmount(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("resize", updateViewport);
    window.removeEventListener("resize", syncBusBodyWidth);
  }
  busResizeObserver?.disconnect();
  busResizeObserver = null;
});
</script>

<style scoped>
.seat-step {
  width: 100%;
  animation: seat-step-enter 0.28s ease both;
}

.seat-step--embedded .seat-step__shell {
  gap: 0;
}

.seat-step__shell {
  width: min(1520px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.seat-step__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.35rem;
  padding: 1.25rem 1.4rem;
  border: 1px solid rgba(203, 213, 225, 0.72);
  border-radius: 28px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.92)),
    radial-gradient(circle at 82% 0%, rgba(14, 165, 233, 0.08), transparent 34%);
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.09), inset 0 1px 0 rgba(255, 255, 255, 0.92);
}

.seat-step__header--center {
  flex-direction: column;
  gap: 1rem;
  text-align: center;
}

.seat-step__headline {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  max-width: 980px;
}

.seat-step__headline h2 {
  font-size: clamp(2.125rem, 2.8vw, 2.5rem);
  line-height: 1.02;
  font-weight: 750;
  color: #08111f;
  letter-spacing: 0;
  margin-top: 0.15rem;
}

.seat-step__eyebrow {
  width: fit-content;
  border-radius: 999px;
  border: 1px solid rgba(14, 165, 233, 0.2);
  background: linear-gradient(180deg, #f0f9ff, #ffffff);
  padding: 0.34rem 0.72rem;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #0369a1;
}

.seat-step__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  align-items: center;
  margin-top: 0.5rem;
  color: #5f6b7a;
  font-size: 0.86rem;
  font-weight: 600;
  line-height: 1.4;
}

.seat-step__meta span {
  display: inline-flex;
  align-items: center;
}

.seat-step__meta span:not(:last-child)::after {
  content: "•";
  margin-left: 0.6rem;
  color: #94a3b8;
}

.seat-step__progress {
  display: grid;
  min-width: 214px;
  gap: 0.4rem;
  border-radius: 18px;
  border: 1px solid rgba(16, 185, 129, 0.24);
  background: linear-gradient(180deg, #ecfdf5, #ffffff);
  padding: 0.9rem 1rem;
  text-align: right;
  box-shadow: 0 18px 36px rgba(5, 150, 105, 0.09);
}

.seat-step__progress span {
  font-size: 0.64rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #047857;
}

.seat-step__progress strong {
  font-size: 0.98rem;
  color: #064e3b;
}

.seat-step__progress-track {
  height: 6px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(6, 78, 59, 0.1);
}

.seat-step__progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #064e3b, #059669, #0ea5e9);
  transition: width 0.3s ease;
}

.seat-modal__focus {
  color: #0ea5e9;
  font-weight: 700;
}

.seat-modal__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.seat-modal__hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.9rem;
}

.seat-modal__hero-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 999px;
  background: #10b981;
  color: #fff;
  font-size: 1.65rem;
  font-weight: 700;
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3);
}

.seat-modal__hero-copy {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  align-items: center;
}

.seat-modal__hero-title {
  font-size: 24px;
  line-height: 1.2;
  font-weight: 600;
  color: #0f172a;
}

.seat-modal__hero-subtitle {
  font-size: 15px;
  color: #475569;
}

.seat-modal__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: #22c55e;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 700;
}

.seat-modal__state {
  min-height: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  text-align: center;
  color: #1e293b;
}

.seat-modal__state--error {
  color: #b91c1c;
}

.seat-modal__state--info {
  color: #0f172a;
}

.subtitle {
  font-size: 0.98rem;
  color: #4b5868;
  line-height: 1.6;
}

.subtitle--centered {
  text-align: center;
}

.subtitle--muted {
  font-size: 0.9rem;
  color: #7a8797;
  margin-top: 0.1rem;
}

.seat-step__content {
  display: grid;
  grid-template-columns: minmax(300px, 340px) minmax(620px, 1fr) minmax(320px, 360px);
  gap: 1.5rem;
  padding: 0;
  overflow: hidden;
  align-items: start;
}

.panel-card {
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: 28px;
  padding: 1.35rem;
  background: linear-gradient(180deg, #ffffff, #fbfdff);
  box-shadow: 0 22px 56px rgba(15, 23, 42, 0.065), inset 0 1px 0 rgba(255, 255, 255, 0.95);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.panel-heading strong {
  display: inline-flex;
  min-width: 42px;
  height: 32px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid rgba(203, 213, 225, 0.8);
  background: #f8fafc;
  color: #0f172a;
  font-size: 0.82rem;
  font-weight: 800;
}

.eyebrow {
  font-size: 0.72rem;
  font-weight: 850;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #64748b;
}

.passenger-panel,
.info-panel {
  position: sticky;
  top: 1.25rem;
}

.passenger-panel .panel-card {
  overflow: hidden;
  gap: 1.05rem;
}

.passenger-list {
  margin-top: 0.45rem;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  overflow-y: auto;
}

.passenger-item {
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 20px;
  padding: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  cursor: pointer;
  transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s, background 0.2s;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035);
}

.passenger-item:hover {
  transform: translateY(-1px);
  border-color: #cbd5e1;
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.07);
}

.passenger-item__index {
  width: 38px;
  height: 38px;
  border-radius: 14px;
  background: linear-gradient(145deg, #f8fafc, #e2e8f0);
  font-weight: 850;
  font-size: 0.85rem;
  color: #475569;
  display: flex;
  align-items: center;
  justify-content: center;
}

.passenger-item--active {
  border-color: rgba(14, 165, 233, 0.55);
  background: linear-gradient(180deg, #f0f9ff, #ffffff);
  box-shadow: 0 18px 34px rgba(14, 165, 233, 0.14);
}

.passenger-item--assigned {
  background: linear-gradient(180deg, #ecfdf5, #ffffff);
}

.passenger-item__info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.passenger-name {
  font-weight: 800;
  color: #0f172a;
  line-height: 1.25;
}

.passenger-seat {
  font-size: 0.75rem;
  color: #475569;
}

.passenger-seat--assigned {
  color: #0f172a;
}

.passenger-seat--empty {
  color: #94a3b8;
}

.passenger-status-badge {
  border-radius: 999px;
  padding: 0.28rem 0.72rem;
  font-size: 0.7rem;
  font-weight: 800;
  border: 1px solid transparent;
  min-width: 110px;
  text-align: center;
}

.passenger-status-badge--assigned {
  color: #065f46;
  background: #d1fae5;
  border-color: #86efac;
}

.passenger-status-badge--pending {
  color: #92400e;
  background: #fffbeb;
  border-color: #fde68a;
}

.map-panel,
.map-card,
.deck-section,
.bus-stage {
  min-width: 0;
}

.map-card {
  overflow: visible;
  gap: 1.35rem;
  min-height: 680px;
  padding: 1.5rem;
}

.map-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.25rem 0 0.95rem;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.map-card__header h3 {
  margin-top: 0.35rem;
  font-size: 1.35rem;
  font-weight: 850;
  line-height: 1.15;
  color: #0f172a;
}

.map-card__header span {
  display: inline-block;
  margin-top: 0.35rem;
  color: #64748b;
  font-size: 0.9rem;
}

.map-card__kpi {
  min-width: 118px;
  border-radius: 20px;
  border: 1px solid rgba(14, 165, 233, 0.16);
  background: linear-gradient(180deg, #f0f9ff, #ffffff);
  padding: 0.85rem;
  text-align: right;
}

.map-card__kpi strong {
  display: block;
  color: #0c4a6e;
  font-size: 1.2rem;
  line-height: 1;
}

.map-card__kpi span {
  margin-top: 0.25rem;
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.deck-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  min-width: 0;
}

.vehicle-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-bottom: 0;
}

.vehicle-tab {
  border-radius: 16px;
  border: 1px solid rgba(203, 213, 225, 0.9);
  padding: 0.65rem 1rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
  background: #fff;
  display: inline-flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 150px;
  transition: all 0.2s ease;
}

.vehicle-tab--active {
  border-color: rgba(14, 165, 233, 0.4);
  background: linear-gradient(180deg, #e0f2fe, #ffffff);
  color: #0c4a6e;
  box-shadow: 0 14px 28px rgba(14, 165, 233, 0.14);
}

.vehicle-tab__name {
  font-weight: 700;
}

.vehicle-tab__meta {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: #94a3b8;
}

.deck-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.deck-tab {
  border-radius: 14px;
  border: 1px solid rgba(203, 213, 225, 0.9);
  padding: 0.5rem 0.9rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
  background: #fff;
  transition: all 0.2s ease;
}

.deck-tab--active {
  color: #0369a1;
  background: #e0f2fe;
  border-color: rgba(14, 165, 233, 0.42);
}

.deck-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.deck-heading {
  font-size: 0.9rem;
  font-weight: 700;
  color: #0f172a;
}

.bus-stage {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bus-front-label {
  align-self: center;
  font-size: 0.65rem;
  font-weight: 850;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: #94a3b8;
}

.bus-shell {
  width: 100%;
  padding: 1.35rem 0.75rem 1.1rem;
  position: relative;
  border-radius: 32px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.72), rgba(255, 255, 255, 0.2));
}

.bus-front {
  position: absolute;
  top: 0.6rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
}

.bus-front__window {
  width: 88px;
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(90deg, #cbd5e1, #e2e8f0);
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.08);
}

.bus-front__driver {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: #0369a1;
  box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.1);
}

.bus-body {
  margin-top: 2rem;
  padding: 0 0.25rem 0.5rem;
  display: flex;
  justify-content: center;
  overflow-x: hidden;
  overflow-y: hidden;
  max-height: none;
  min-width: 0;
  width: 100%;
}

.map-legend {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
  margin-bottom: 0;
  list-style: none;
  padding: 0;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 999px;
  background: #ffffff;
  padding: 0.45rem 0.7rem;
  font-size: 0.74rem;
  font-weight: 800;
  color: #475569;
}

.legend-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid transparent;
  display: inline-block;
}

.legend-dot--available {
  background: #dcfce7;
  border-color: #15803d;
}

.legend-dot--selected {
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  border-color: #0ea5e9;
}

.legend-dot--occupied {
  background: #fed7aa;
  border-color: #c2410c;
}

.legend-dot--blocked {
  background: #fee2e2;
  border-color: #be123c;
}

.legend-dot--mine {
  background: #e0e7ff;
  border-color: #4c1d95;
}

.map-note {
  font-size: 0.75rem;
  color: #94a3b8;
}

.bus-grid {
  display: grid;
  gap: var(--seat-gap, 8px);
  background:
    radial-gradient(circle at 50% 0%, rgba(14, 165, 233, 0.05), transparent 38%),
    linear-gradient(180deg, #ffffff, #f8fafc);
  padding: 1.35rem;
  border-radius: 32px;
  border: 1px solid rgba(203, 213, 225, 0.9);
  justify-content: center;
  justify-items: center;
  width: fit-content;
  max-width: 100%;
  min-width: 0;
  margin: 0 auto;
  box-shadow: inset 0 1px 16px rgba(15, 23, 42, 0.035), 0 18px 42px rgba(15, 23, 42, 0.07);
}

.bus-grid--desktop-horizontal {
  min-width: 0;
}

.seat-cell {
  width: var(--seat-unit, 40px);
  height: calc(var(--seat-unit, 40px) + 4px);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.74rem;
  font-weight: 850;
  color: #0f172a;
  border: 1px solid rgba(148, 163, 184, 0.4);
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease, background 0.16s ease, border-color 0.16s ease;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.075), inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

.seat-cell--available {
  background: linear-gradient(180deg, #ffffff, #f0f9ff);
  border-color: #bae6fd;
}

.seat-cell--available:hover {
  transform: translateY(-4px) scale(1.04);
  border-color: #38bdf8;
  box-shadow: 0 16px 30px rgba(2, 132, 199, 0.18);
}

.seat-cell--selected {
  background: linear-gradient(135deg, #075985, #0ea5e9);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 16px 32px rgba(2, 132, 199, 0.32);
}

.seat-cell--selected {
  transform: scale(1.08);
}

.seat-cell--mine {
  background: linear-gradient(180deg, #dbeafe, #eff6ff);
  border-color: #93c5fd;
  color: #0f172a;
  box-shadow: 0 10px 18px rgba(59, 130, 246, 0.25);
  cursor: not-allowed;
}

.seat-cell--occupied {
  background: linear-gradient(180deg, #f1f5f9, #e2e8f0);
  color: #64748b;
  cursor: not-allowed;
  border-color: #cbd5f5;
  box-shadow: none;
}

.seat-cell--blocked {
  background: #f8fafc;
  color: #94a3b8;
  cursor: not-allowed;
  border-style: dashed;
  border-color: #cbd5f5;
  box-shadow: none;
}

.seat-cell--aisle {
  width: calc(var(--seat-unit, 40px) * 0.56);
  height: calc(var(--seat-unit, 40px) + 1px);
  background: linear-gradient(90deg, rgba(148, 163, 184, 0.35), rgba(209, 213, 219, 0.1));
  border-radius: 20px;
  border: none;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
  cursor: default;
  opacity: 1;
  pointer-events: none;
}

.seat-cell--aisle {
  opacity: 0.5;
}


@media (min-width: 1024px) {
  .bus-stage {
    flex-direction: row;
    align-items: center;
    justify-content: center;
    gap: 1rem;
  }

  .bus-front-label {
    writing-mode: vertical-rl;
    transform: rotate(180deg);
    letter-spacing: 0.2em;
    font-size: 0.7rem;
  }

  .bus-shell {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .bus-front {
    position: relative;
    top: auto;
    left: auto;
    transform: none;

    margin-right: 0.5rem;
  }
}

@media (min-width: 1024px) {
  .bus-front {
    flex-direction: row;
    gap: 0.3rem;
  }

  .bus-front__window {
    width: 12px;
    height: 60px;
    border-radius: 999px;
  }

  .bus-front__driver {
    width: 10px;
    height: 10px;
  }
}
.seat-cell--empty {
  opacity: 0;
  cursor: default;
  pointer-events: none;
}

.seat-cell:hover {
  transform: translateY(-2px);
}

.seat-label {
  pointer-events: none;
  color: inherit;
}

.info-card {
  gap: 0.9rem;
}

.info-summary {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid #e2e8f0;
}

.info-summary:last-of-type {
  border-bottom: none;
}

.info-summary__label {
  font-size: 0.7rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #94a3b8;
}

.info-summary__value {
  font-size: 1.03rem;
  font-weight: 800;
  color: #0f172a;
}

.info-summary__value--seat {
  color: #0369a1;
  font-size: 1.35rem;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  width: fit-content;
  padding: 0.35rem 0.8rem;
  font-size: 0.8rem;
  font-weight: 800;
}

.status-pill--success {
  background: #dcfce7;
  color: #15803d;
}

.status-pill--pending {
  background: #fef9c3;
  color: #b45309;
}

.summary-only {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  width: 100%;
  max-width: 680px;
  margin: 0 auto;
  align-items: center;
  text-align: center;
}

.summary-hero {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  align-items: center;
  justify-items: center;
  width: 100%;
}

.summary-hero__intro {
  padding: 1.5rem;
  border-radius: 24px;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  box-shadow: 0 10px 30px rgba(16, 185, 129, 0.08);
}

.summary-hero__intro--plain {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  padding: 0.5rem 0 0;
  border: none;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  align-items: center;
  text-align: center;
}

.summary-hero__intro h3 {
  font-size: 1.4rem;
  font-weight: 700;
  color: #0f172a;
  max-width: none;
}

.summary-hero__intro p {
  font-size: 0.95rem;
  line-height: 1.6;
  color: #475569;
  max-width: 60ch;
}

.summary-hero__inline-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: #64748b;
}

.summary-stats {
  display: grid;
  gap: 0.75rem;
  align-content: start;
  justify-content: center;
  width: 100%;
  max-width: 640px;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
}

.summary-stat {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 96px;
  padding: 1rem 1.1rem;
  border-radius: 20px;
  border: 1px solid rgba(226, 232, 240, 0.7);
  background: #fff;
  box-shadow: 0 3px 10px rgba(15, 23, 42, 0.04);
  transition: all 0.2s ease;
}

.summary-stat:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.summary-stat__label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #94a3b8;
}

.summary-stat__value {
  margin-top: 0.4rem;
  font-size: 1.15rem;
  font-weight: 600;
  color: #0f172a;
}

.summary-note {
  font-size: 0.85rem;
  color: #475569;
  text-align: center;
  max-width: 52ch;
}

.passenger-summary-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.9rem;
  width: 100%;
  max-width: 640px;
  justify-content: center;
}

.summary-list-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  width: 100%;
  text-align: center;
}

.summary-list-header__title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
}

.summary-list-header__status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 0.4rem 0.85rem;
  background: #d1fae5;
  color: #047857;
  font-size: 0.8rem;
  font-weight: 600;
}

.summary-list-header__status--mobile {
  display: inline-flex;
}

.summary-status-desktop {
  display: none;
}

.passenger-summary-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.85rem;
  padding: 1rem 1.05rem;
  border-radius: 20px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  background: #fff;
  box-shadow: 0 3px 10px rgba(15, 23, 42, 0.04);
  transition: all 0.2s ease;
  text-align: left;
}

.passenger-summary-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.passenger-summary-card__identity {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  min-width: 0;
  grid-column: 1 / 3;
}

.passenger-summary-card__avatar {
  width: 42px;
  height: 42px;
  border-radius: 999px;
  background: #d1fae5;
  color: #047857;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  text-transform: uppercase;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.passenger-summary-card__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-self: end;
  gap: 0.1rem;
  flex-shrink: 0;
  min-width: 56px;
}

.passenger-summary-card__seat-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  color: #94a3b8;
}

.passenger-summary-card__seat-icon svg {
  width: 100%;
  height: 100%;
}

.passenger-summary-card__seat-value {
  font-size: 1.125rem;
  color: #0f172a;
  line-height: 1;
}

.summary-card {
  width: 100%;
}

.summary-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.9rem;
  padding-top: 0.5rem;
}

.summary-footer__action {
  width: min(360px, 100%);
}

.summary-footer .btn-primary {
  padding: 1rem 2rem;
  font-size: 15px;
  font-weight: 600;
  border-radius: 999px;
  background: #059669;
  color: #fff;
  box-shadow: 0 10px 30px rgba(16, 185, 129, 0.25);
  transition: all 0.2s ease;
}

.summary-footer .btn-primary:hover {
  transform: translateY(-1px);
  background: #047857;
}

@media (max-width: 1279px) {
  .summary-stats {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    justify-content: center;
  }
}

@media (min-width: 1280px) {
  .summary-hero__intro--plain {
    gap: 0.45rem;
    padding-top: 0;
  }

  .summary-hero__intro h3 {
    max-width: none;
  }

  .summary-hero__intro p {
    max-width: 60ch;
  }

  .passenger-summary-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    justify-content: center;
  }

  .summary-stats {
    grid-template-columns: repeat(4, minmax(140px, 180px));
    align-items: end;
    gap: 1.25rem;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid #e2e8f0;
    justify-content: center;
  }

  .summary-stat {
    min-height: auto;
    padding: 0;
    border: none;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
  }

  .summary-stat:hover {
    transform: none;
    box-shadow: none;
  }

  .summary-stat__value {
    margin-top: 0.3rem;
  }

  .summary-status-desktop {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .summary-list-header {
    margin-top: 0.1rem;
  }

  .summary-list-header__status--mobile {
    display: none;
  }
}

.selection-error {
  font-size: 0.8rem;
  color: #b91c1c;
  margin-top: 0.5rem;
}

.info-note {
  font-size: 0.85rem;
  color: #475569;
  margin-top: 0.5rem;
}

.boarding-notes {
  background: #f8fafc;
  padding: 0.75rem;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
}

.btn-ghost {
  border: 1px solid transparent;
  border-radius: 999px;
  padding: 0.5rem 1rem;
  font-weight: 600;
  color: #0f172a;
  transition: color 0.2s;
}

.btn-ghost:hover {
  color: #0ea5e9;
}

.btn-secondary {
  min-height: 46px;
  border-radius: 15px;
  border: 1px solid #cbd5e1;
  padding: 0.75rem 1.25rem;
  font-weight: 800;
  color: #334155;
  background: #ffffff;
  transition: all 0.18s ease;
}

.btn-secondary:hover {
  transform: translateY(-1px);
  border-color: #94a3b8;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.07);
}

.btn-primary {
  min-height: 52px;
  border-radius: 16px;
  padding: 0.9rem 1.25rem;
  font-weight: 850;
  background: linear-gradient(135deg, #064e3b, #059669);
  color: #fff;
  box-shadow: 0 16px 32px rgba(5, 150, 105, 0.24);
  transition: all 0.18s ease;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 20px 38px rgba(5, 150, 105, 0.28);
}

.btn-primary:disabled {
  opacity: 0.48;
  cursor: not-allowed;
  box-shadow: none;
}

.progress-text {
  font-size: 0.85rem;
  color: #475569;
}

.progress-bar {
  height: 7px;
  width: 100%;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
  margin-top: 0.25rem;
}

.progress-bar__fill {
  height: 100%;
  background: linear-gradient(90deg, #064e3b, #059669, #0ea5e9);
  transition: width 0.3s ease;
}

.progress-bar--summary {
  margin-top: 0.35rem;
}

.inline-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #0f172a;
}

.spinner {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 3px solid #e2e8f0;
  border-top-color: #0ea5e9;
  animation: spin 1s linear infinite;
}

.spinner--sm {
  width: 18px;
  height: 18px;
  border-width: 2px;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #94a3b8;
  border: 1px dashed #cbd5f5;
  border-radius: 16px;
}

@media (max-width: 1024px) {
  .seat-step__header {
    flex-direction: column;
    align-items: flex-start;
    padding: 1.1rem;
    border-radius: 24px;
  }

  .seat-step__progress {
    width: 100%;
    min-width: 0;
    text-align: left;
  }

  .seat-step__content {
    grid-template-columns: 1fr;
    overflow: visible;
  }

  .passenger-panel,
  .info-panel {
    position: static;
  }

  .panel-card {
    min-height: auto;
  }

  .bus-front {
    top: 0.4rem;
  }

  .bus-body {
    justify-content: center;
    overflow-x: hidden;
  }

  .bus-grid {
    width: fit-content;
    max-width: 100%;
  }

  .summary-list-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .passenger-summary-list {
    grid-template-columns: 1fr;
  }

  .passenger-summary-card {
    grid-template-columns: 1fr;
    justify-items: center;
    text-align: center;
  }

  .passenger-summary-card__identity {
    grid-column: auto;
    justify-content: center;
  }

  .passenger-summary-card__meta {
    align-items: center;
    justify-self: center;
  }
}

@media (max-width: 767px) {
  .seat-step__headline h2 {
    font-size: 1.75rem;
  }

  .seat-step__meta {
    gap: 0.35rem;
    font-size: 0.8rem;
  }

  .seat-step__meta span:not(:last-child)::after {
    margin-left: 0.35rem;
  }

  .seat-step__header--center {
    gap: 0.85rem;
  }

  .seat-modal__hero {
    gap: 0.75rem;
  }

  .seat-modal__hero-icon {
    width: 56px;
    height: 56px;
    font-size: 1.35rem;
  }

  .seat-modal__hero-title {
    font-size: 1.35rem;
  }

  .seat-modal__hero-subtitle {
    font-size: 0.95rem;
  }

  .subtitle,
  .subtitle--muted {
    font-size: 0.84rem;
  }

  .summary-only {
    gap: 1.25rem;
  }

  .summary-hero__intro--plain {
    gap: 0.65rem;
    padding-top: 0.15rem;
  }

  .summary-hero__intro h3 {
    max-width: none;
    font-size: 1.2rem;
  }

  .summary-hero__intro p {
    max-width: none;
    font-size: 0.92rem;
  }

  .summary-hero__inline-meta {
    font-size: 0.82rem;
  }

  .summary-stats {
    grid-template-columns: 1fr;
    gap: 0.7rem;
  }

  .summary-stat {
    min-height: auto;
    padding: 0.95rem 1rem;
  }

  .summary-list-header__status {
    width: 100%;
  }

  .passenger-summary-card {
    padding: 1rem;
  }

  .passenger-summary-card__avatar {
    width: 40px;
    height: 40px;
  }

  .passenger-name {
    font-size: 0.98rem;
  }

  .passenger-seat {
    font-size: 0.8rem;
  }

  .passenger-summary-card__seat-value {
    font-size: 1rem;
  }

  .summary-footer {
    padding-top: 0.25rem;
  }

  .summary-footer__action {
    width: 100%;
  }
}

@media (min-width: 1024px) {
  .seat-step__content {
    grid-template-columns: minmax(280px, 340px) minmax(620px, 1fr) minmax(300px, 360px);
    align-items: stretch;
  }

  .map-panel,
  .map-card,
  .deck-section,
  .bus-stage,
  .bus-shell,
  .bus-body {
    min-width: 0;
    width: 100%;
  }

 .bus-stage {
  justify-content: center;
}

  .bus-shell {
    padding: 1rem 0.25rem 0.75rem;
  }

  .bus-front-label {
    margin-bottom: 0.75rem;
  }

  .bus-body {
    overflow-x: hidden;
    overflow-y: hidden;
    justify-content: center;
    padding: 0 0.25rem 0.5rem;
  }

  .bus-grid {
    width: fit-content;
    max-width: 100%;
    min-width: 0;
    margin: 0 auto;
    padding: 1rem;
    gap: var(--seat-gap, 8px);
  }

  .seat-cell {
    width: var(--seat-unit, 40px);
    height: calc(var(--seat-unit, 40px) + 4px);
  }

  .seat-cell--aisle {
    width: calc(var(--seat-unit, 40px) * 0.56);
    height: calc(var(--seat-unit, 40px) - 2px);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes seat-step-enter {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
