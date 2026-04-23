<template>
  <div class="page">
    <header class="ops-header">
      <div class="ops-header__left">
        <p class="eyebrow">Mapa operacional</p>
        <h1 class="ops-header__title">{{ seatContext?.product_name || "Mapa operacional" }}</h1>
        <p class="ops-header__meta">
          <span>{{ tripDateLabel }}</span>
          <span v-if="currentVehicleLabel"> &middot; {{ currentVehicleLabel }}</span>
        </p>
      </div>
      <div class="ops-header__status" v-if="seatContext?.trip_vehicle">
        <span class="status-pill">{{ vehicleStatusLabel(seatContext.trip_vehicle.status) }}</span>
        <p>
          <strong>{{ seatContext.trip_vehicle.occupied_seats }}</strong> ocupados
          <span>&middot;</span>
          <strong>{{ seatContext.trip_vehicle.available_seats }}</strong> livres
        </p>
      </div>
      <div class="header-actions">
        <label v-if="departureOptions.length" class="departure-select">
          <span>Saida</span>
          <select v-model.number="selectedDepartureId" @change="handleDepartureChange">
            <option v-for="departure in departureOptions" :key="departure.id" :value="departure.id">
              {{ departureOptionLabel(departure) }}
            </option>
          </select>
        </label>
        <router-link class="btn-secondary" :to="{ name: 'seat-layouts' }">Biblioteca de layouts</router-link>
        <button type="button" class="btn-primary" @click="refreshSeatData">Atualizar</button>
      </div>
    </header>

    <section class="config-card config-card--premium">
      <form class="config-form" @submit.prevent="saveConfig">

        <div class="trip-settings-card">
          <div class="trip-settings-card__header">
            <h3>Configuracoes da viagem</h3>
            <button type="submit" class="btn-primary" :disabled="configSaving">Salvar configuracao</button>
          </div>
          <div class="trip-settings-card__body">
            
              <label class="form-field">
                <span>Notas de embarque</span>
                <textarea
                  rows="2"
                  v-model="configForm.boardingNotes"
                  placeholder="Informacoes visiveis aos passageiros"
                ></textarea></label>
           
          </div>
        </div>

        <div v-if="configForm.isRoadTrip" class="vehicle-stack">
          <div class="vehicle-stack__header">
            <div>
              <p class="eyebrow">Veiculos da excursao</p>
              <p class="subtitle">Monte a sequencia operacional com capacidade e layout de cada onibus.</p>
            </div>
            <button type="button" class="btn-secondary" @click="addVehicleEntry">Adicionar veiculo</button>
          </div>

          <div class="vehicle-list">
            <article v-for="(vehicle, index) in configForm.vehicles" :key="vehicle.localKey" class="vehicle-card">
              <div class="vehicle-card__header">
                <div class="vehicle-card__heading">
                  <div class="vehicle-card__title">
                    <div>
                      <h3>{{ vehicle.displayName || `Veiculo ${index + 1}` }}</h3>
                      <p class="vehicle-card__order">Ordem de liberacao #{{ vehicle.orderIndex }}</p>
                    </div>
                    <span class="vehicle-status-pill" :class="vehicleStatusClass(vehicle.status)">
                      {{ vehicleStatusLabel(vehicle.status) }}
                    </span>
                  </div>
                </div>
                <div class="vehicle-card__actions">
                  <button
                    type="button"
                    class="vehicle-card__action-btn"
                    title="Alternar detalhes"
                    @click="toggleVehicleCollapse(vehicle.localKey)"
                  >
                    <span aria-hidden="true">{{ isVehicleCollapsed(vehicle.localKey) ? "▾" : "▴" }}</span>
                    {{ isVehicleCollapsed(vehicle.localKey) ? "Expandir" : "Recolher" }}
                  </button>
                  <button
                    type="button"
                    class="vehicle-card__action-btn"
                    title="Mover para cima"
                    @click="moveVehicleEntry(index, -1)"
                    :disabled="index === 0"
                  >
                    <span aria-hidden="true">↑</span>
                    Subir
                  </button>
                  <button
                    type="button"
                    class="vehicle-card__action-btn"
                    title="Mover para baixo"
                    @click="moveVehicleEntry(index, 1)"
                    :disabled="index === configForm.vehicles.length - 1"
                  >
                    <span aria-hidden="true">↓</span>
                    Descer
                  </button>
                  <button
                    type="button"
                    class="vehicle-card__action-btn vehicle-card__action-btn--danger"
                    title="Remover veiculo"
                    @click="removeVehicleEntry(index)"
                  >
                    <span aria-hidden="true">✕</span>
                    Remover
                  </button>
                </div>
              </div>
              <div v-show="!isVehicleCollapsed(vehicle.localKey)" class="vehicle-card__body">
                <div class="vehicle-card__section">
                  <p class="vehicle-card__section-title">Identificacao</p>
                  <div class="vehicle-card__grid">
                    <label class="form-field">
                      <span>Nome publico</span>
                      <input v-model="vehicle.displayName" placeholder="Onibus executivo" />
                    </label>
                    <label class="form-field">
                      <span>Veiculo operacional</span>
                      <select v-model="vehicle.vehicleId" @change="handleVehicleChange(vehicle)">
                        <option :value="undefined">Nao vinculado</option>
                        <option v-for="item in vehicles" :key="item.id" :value="item.id">
                          {{ item.name }}
                        </option>
                      </select>
                    </label>
                  </div>
                </div>

                <div class="vehicle-card__section">
                  <p class="vehicle-card__section-title">Configuracao</p>
                  <div class="vehicle-card__grid">
                    <div class="form-field field-static">
                      <span>Layout aplicado</span>
                      <template v-if="vehicle.vehicleId && !requiresManualLayout(vehicle)">
                        <p class="field-static__value">
                          {{ layoutDisplayName(vehicle) || "Layout vinculado ao veiculo" }}
                        </p>
                        <p class="field-static__hint">Definido automaticamente pelo veiculo escolhido.</p>
                      </template>
                      <template v-else>
                        <select v-model="vehicle.layoutId" @change="handleLayoutChange(vehicle)">
                          <option :value="undefined">Selecione um layout</option>
                          <option v-for="layout in layouts" :key="layout.id" :value="layout.id">
                            {{ layout.name }}
                          </option>
                        </select>
                        <p v-if="vehicle.vehicleId" class="field-static__warning">
                          Este veiculo nao possui layout vinculado. Escolha manualmente.
                        </p>
                      </template>
                    </div>
                    <label class="form-field">
                      <span>Capacidade operacional</span>
                      <input type="number" min="1" v-model.number="vehicle.capacity" />
                    </label>
                  </div>
                </div>

                <div class="vehicle-card__section">
                  <p class="vehicle-card__section-title">Status</p>
                  <div class="vehicle-card__grid vehicle-card__grid--status">
                    <label class="form-field">
                      <span>Status</span>
                      <select v-model="vehicle.status">
                        <option v-for="option in vehicleStatusOptions" :key="option.value" :value="option.value">
                          {{ option.label }}
                        </option>
                      </select>
                    </label>
                    <div class="vehicle-card__toggles">
                      <label class="checkbox-field">
                        <input type="checkbox" v-model="vehicle.isActive" />
                        <span>Disponivel para esta excursao</span>
                      </label>
                      <label class="checkbox-field">
                        <input type="checkbox" v-model="vehicle.autoActivateNext" />
                        <span>Ativar proximo veiculo automaticamente</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </article>
          </div>
        </div>
      </form>
    </section>
    <section class="operations-grid">
      <div class="operations-column passengers-column">
        <div class="panel passengers-panel">
          <div class="panel-header">
            <div>
              <p class="eyebrow">Passageiros</p>
              <p class="subtitle">Filtre e selecione para atribuir rapidamente.</p>
            </div>
            <input type="search" v-model="passengerSearch" placeholder="Buscar passageiro" class="search-input" />
          </div>
          <div class="passenger-filters">
            <button
              v-for="option in passengerFilterOptions"
              :key="option.value"
              type="button"
              :class="['filter-chip', passengerFilter === option.value ? 'filter-chip--active' : '']"
              @click="passengerFilter = option.value"
            >
              {{ option.label }}
              <span class="filter-chip__badge">{{ passengerFilterCounts[option.value] || 0 }}</span>
            </button>
          </div>
          <ul v-if="filteredPassengers.length" class="passenger-list">
            <li
              v-for="passenger in filteredPassengers"
              :key="passenger.id"
              :class="passengerClasses(passenger)"
              @click="selectPassenger(passenger.id)"
            >
              <div class="passenger-item__info">
                <p class="passenger-name">{{ passenger.name }}</p>
                <p class="passenger-status">
                  {{ passengerStatusText(passenger) }}
                  <span v-if="passengerSeatLabel(passenger)"> &middot; {{ passengerSeatLabel(passenger) }}</span>
                </p>
              </div>
              <button
                type="button"
                class="passenger-item__action"
                :disabled="!passenger.seat_id"
                @click.stop="removeAssignment(passenger.id)"
              >
                Liberar
              </button>
            </li>
          </ul>
          <p v-else class="placeholder-card">Nenhum passageiro encontrado.</p>
        </div>
      </div>

      <div class="operations-column map-column">
        <div class="panel map-panel">
          <div v-if="orderedVehicles.length" class="vehicle-tabs">
            <button
              v-for="vehicle in orderedVehicles"
              :key="vehicle.id"
              type="button"
              :class="['vehicle-tab', vehicle.id === selectedTripVehicleId ? 'vehicle-tab--active' : '']"
              @click="switchVehicle(vehicle.id)"
            >
              <div class="vehicle-tab__row">
                <span class="vehicle-tab__name">
                  {{ vehicle.display_name || vehicle.vehicle?.name || `Veiculo ${vehicle.order_index}` }}
                </span>
                <span class="vehicle-tab__status">{{ vehicleStatusLabel(vehicle.status) }}</span>
              </div>
              <p class="vehicle-tab__meta">
                {{ vehicle.occupied_seats }}/{{ vehicle.capacity }} ocupados
                <span class="pill">{{ vehicle.available_seats }} livres</span>
              </p>
            </button>
          </div>
          <div v-else class="placeholder-card">Adicione veiculos na configuracao para liberar o mapa.</div>

          <div v-if="seatContext?.trip_vehicle && displayDeck" class="map-stage">
            <div class="map-stage__summary">
              <div>
                <p class="map-stage__title">
                  {{ seatContext.trip_vehicle.display_name || `Veiculo ${seatContext.trip_vehicle.order_index}` }}
                </p>
                <p class="map-stage__meta">
                  {{ vehicleStatusLabel(seatContext.trip_vehicle.status) }} &middot;
                  {{ seatContext.trip_vehicle.occupied_seats }}/{{ seatContext.trip_vehicle.capacity }} ocupados
                </p>
              </div>
              <span class="pill pill--success">{{ seatContext.trip_vehicle.available_seats }} livres</span>
            </div>

            <div v-if="seatDecks.length > 1" class="deck-tabs">
              <button
                v-for="deck in seatDecks"
                :key="deck.key"
                type="button"
                :class="['deck-tab', activeDeck?.key === deck.key ? 'deck-tab--active' : '']"
                @click="activeDeckKey = deck.key"
              >
                <span>{{ deck.label }}</span>
                <span class="deck-tab__count">{{ deck.seatCount }}</span>
              </button>
            </div>

            <div class="bus-stage__layout">
              <div class="bus-front-label">
                <span class="bus-front-label__dot"></span>
                <span class="bus-front-label__text">Frente do ônibus</span>
              </div>
              <div class="bus-shell">
                <div
                  class="bus-grid"
                  :class="{ 'bus-grid--desktop-horizontal': isDesktop }"
                  :style="{ gridTemplateColumns: `repeat(${displayDeck?.columns || 1}, minmax(46px, 1fr))` }"
                >
                  <button
                    v-for="cell in displayDeck?.cells || []"
                    :key="cell.key"
                    type="button"
                    :class="cellClasses(cell)"
                    @click="handleSeatClick(cell)"
                  >
                    <span v-if="cell.seat">
                    <span v-if="cell.seat.is_blocked" class="seat-lock" aria-label="Assento bloqueado">
                      <svg viewBox="0 0 24 24" role="img" aria-hidden="true" focusable="false">
                        <rect x="5" y="11" width="14" height="10" rx="2" ry="2" fill="none" stroke="currentColor" stroke-width="2"></rect>
                        <path d="M12 15v4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
                        <path d="M8 11V7a4 4 0 0 1 8 0v4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
                      </svg>
                    </span>
                      <template v-else>
                        {{ cell.seat.seat_label || cell.seat.seat_number }}
                      </template>
                    </span>
                  </button>
                </div>
              </div>
            </div>
            <p v-if="seatContext.boarding_notes" class="board-notes">Notas: {{ seatContext.boarding_notes }}</p>
            <div class="map-legend">
              <span class="legend-item legend-item--available">Livre</span>
              <span class="legend-item legend-item--mine">Selecionado</span>
              <span class="legend-item legend-item--occupied">Ocupado</span>
              <span class="legend-item legend-item--blocked">Bloqueado</span>
            </div>
          </div>
          <div v-else-if="seatContext?.trip_vehicle" class="placeholder-card">Mapa nao disponivel.</div>
          <div v-else class="placeholder-card">Aguardando liberacao do proximo veiculo.</div>
        </div>
      </div>

      <div class="operations-column info-column">
        <div class="panel stats-panel">
          <div class="panel-header">
            <div>
              <p class="eyebrow">Estatisticas</p>
              <p class="subtitle">Visao geral do veiculo selecionado.</p>
            </div>
          </div>
          <dl class="stats-grid">
            <div>
              <dt>Total</dt>
              <dd>{{ seatContext?.stats.total_seats || 0 }}</dd>
            </div>
            <div>
              <dt>Ocupados</dt>
              <dd>{{ seatContext?.stats.occupied_seats || 0 }}</dd>
            </div>
            <div>
              <dt>Bloqueados</dt>
              <dd>{{ seatContext?.stats.blocked_seats || 0 }}</dd>
            </div>
            <div>
              <dt>Pendentes</dt>
              <dd>{{ seatContext?.stats.pending_passengers || 0 }}</dd>
            </div>
          </dl>
        </div>

        <div class="panel context-panel">
          <p class="eyebrow">Painel contextual</p>
          <div v-if="selectedSeat" class="seat-context">
            <div class="seat-context__header">
              <div>
                <p class="seat-context__label">Assento</p>
                <h4 class="seat-context__title">Assento {{ selectedSeat.seat_label || selectedSeat.seat_number }}</h4>
              </div>
              <span class="seat-status-badge" :class="seatStatusBadgeClass(selectedSeat)">
                {{ seatStatusDescription(selectedSeat) }}
              </span>
            </div>
            <div class="seat-context__info">
              <p class="seat-context__label">Passageiro</p>
              <p class="seat-context__value">
                {{ selectedSeat.occupied_by_passenger_name || "Sem passageiro" }}
              </p>
            </div>
            <div class="seat-context__actions">
              <div class="seat-context__primary-actions">
                <button
                  v-if="seatIsAvailable(selectedSeat)"
                  type="button"
                  class="btn-light"
                  @click="blockSelectedSeat(true)"
                >
                  Bloquear
                </button>
                <button
                  v-else-if="seatIsBlocked(selectedSeat)"
                  type="button"
                  class="btn-light"
                  @click="blockSelectedSeat(false)"
                >
                  Desbloquear
                </button>
              </div>
              <button
                v-if="seatIsOccupied(selectedSeat) && selectedSeatPassengerId"
                type="button"
                class="seat-context__secondary-action"
                @click="removeAssignment(selectedSeatPassengerId)"
              >
                Remover passageiro
              </button>
            </div>
          </div>
          <div v-else-if="selectedPassenger">
            <h4>{{ selectedPassenger.name }}</h4>
            <p class="context-detail">
              {{ passengerStatusText(selectedPassenger) }}
              <span v-if="passengerSeatLabel(selectedPassenger)"> &middot; {{ passengerSeatLabel(selectedPassenger) }}</span>
            </p>
            <div class="context-actions">
              <button
                type="button"
                class="btn-light"
                :disabled="!selectedPassenger.seat_id"
                @click="removeAssignment(selectedPassenger.id)"
              >
                Liberar assento
              </button>
            </div>
          </div>
          <p v-else class="placeholder-card">Selecione um passageiro ou assento.</p>
        </div>

        <div class="panel history-panel">
          <div class="panel-header">
            <p class="eyebrow">Historico</p>
            <div class="history-actions">
              <button type="button" class="btn-ghost" @click="loadHistory">Atualizar</button>
              <button type="button" class="btn-ghost" @click="historyExpanded = !historyExpanded">
                {{ historyExpanded ? "Recolher" : "Expandir" }}
              </button>
            </div>
          </div>
          <template v-if="historyExpanded">
            <ul v-if="history.length" class="history-list">
              <li v-for="entry in history" :key="entry.id" class="history-item">
                <p class="history-actor">{{ historyActorLabel(entry) }}</p>
                <p class="history-action">{{ historyActionLabel(entry) }}</p>
                <p class="history-passenger-line">
                  <span class="history-passenger-label">{{ historySubjectLabel(entry) }}</span>
                  <span class="history-passenger-name">{{ historySubjectValue(entry) }}</span>
                </p>
                <p v-if="historyChangeDetail(entry)" class="history-detail">
                  {{ historyChangeDetail(entry) }}
                </p>
                <p class="history-meta">{{ formatDate(entry.created_at) }}</p>
              </li>
            </ul>
            <p v-else class="placeholder-card">Nenhuma alteracao recente.</p>
          </template>
          <p v-else class="placeholder-card">Historico recolhido.</p>
        </div>
      </div>
    </section>

    <div v-if="blockPromptSeat" class="modal-backdrop">
      <div class="modal-card">
        <h4>Bloquear assento?</h4>
        <p>
          Deseja bloquear o assento
          <strong>{{ blockPromptSeat.seat_label || blockPromptSeat.seat_number }}</strong>?
        </p>
        <div class="modal-actions">
          <button type="button" class="btn-light" @click="cancelBlockPrompt">Cancelar</button>
          <button type="button" class="btn-primary" @click="confirmBlockPrompt">Bloquear</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import type { DepartureSummary } from "../../types/finance";
import type {
  PassengerSeatSummary,
  SeatHistoryEntry,
  SeatMapContext,
  TripSeatOut,
  TripTransportConfigPayload,
  TripVehicleStatus,
  TripVehicleSummary,
  VehicleLayoutSummary,
  VehicleOut,
} from "../../types/transport";
import { listScheduleDepartures } from "../../services/finance";
import {
  assignSeatAdmin,
  blockSeatRequest,
  getSeatHistory,
  getSeatMapContext,
  getTripTransportConfig,
  listVehicleLayouts,
  listVehiclesRequest,
  removePassengerSeat,
  saveTripTransportConfig,
} from "../../services/transport";

interface SeatCell {
  key: string;
  seat: TripSeatOut | null;
  type: string;
}

interface SeatDeckView {
  key: string;
  label: string;
  columns: number;
  cells: SeatCell[];
  seatCount: number;
  occupiedCount: number;
  blockedCount: number;
  availableCount: number;
}

interface TripVehicleFormEntry {
  id?: number;
  localKey: string;
  vehicleId?: number;
  layoutId?: number;
  displayName: string;
  capacity: number;
  orderIndex: number;
  status: TripVehicleStatus;
  isActive: boolean;
  autoActivateNext: boolean;
}

type PassengerFilter = "all" | "unassigned" | "assigned" | "selected";

const route = useRoute();
const productId = computed(() => route.params.productId as string);

const seatContext = ref<SeatMapContext | null>(null);
const history = ref<SeatHistoryEntry[]>([]);
const layouts = ref<VehicleLayoutSummary[]>([]);
const vehicles = ref<VehicleOut[]>([]);
const configVehicles = ref<TripVehicleSummary[]>([]);
const selectedTripVehicleId = ref<number | null>(null);
const selectedDepartureId = ref<number | null>(null);
const selectedPassengerId = ref<number | null>(null);
const selectedSeatId = ref<number | null>(null);
const configSaving = ref(false);
const passengerSearch = ref("");
const passengerFilter = ref<PassengerFilter>("all");
const activeDeckKey = ref<string | null>(null);
const blockPromptSeat = ref<TripSeatOut | null>(null);
const historyExpanded = ref(false);
const collapsedVehicles = ref<Record<string, boolean>>({});
const isDesktop = ref(false);
const departureOptions = ref<DepartureSummary[]>([]);

const configForm = ref({
  isRoadTrip: false,
  boardingNotes: "",
  regenerateLayout: false,
  vehicles: [] as TripVehicleFormEntry[],
});

const passengerFilterOptions: { value: PassengerFilter; label: string }[] = [
  { value: "all", label: "Todos" },
  { value: "unassigned", label: "Sem assento" },
  { value: "assigned", label: "Com assento" },
  { value: "selected", label: "Selecionado" },
];

const vehicleStatusOptions: { value: TripVehicleStatus; label: string }[] = [
  { value: "active", label: "Ativo" },
  { value: "inactive", label: "Aguardando" },
  { value: "full", label: "Lotado" },
];

const updateViewport = () => {
  if (typeof window === "undefined") return;
  isDesktop.value = window.innerWidth >= 1024;
};

const orderedVehicles = computed(() =>
  [...configVehicles.value].sort((a, b) => a.order_index - b.order_index)
);

const createVehicleKey = () => `temp-${Date.now()}-${Math.random().toString(16).slice(2)}`;

const ensureVehiclesList = () => {
  if (!configForm.value.isRoadTrip) return;
  if (!configForm.value.vehicles.length) {
    addVehicleEntry();
  }
};

const syncVehicleCollapseStates = () => {
  const nextState: Record<string, boolean> = {};
  configForm.value.vehicles.forEach(entry => {
    nextState[entry.localKey] = collapsedVehicles.value[entry.localKey] ?? true;
  });
  collapsedVehicles.value = nextState;
};

const addVehicleEntry = () => {
  const order = configForm.value.vehicles.length + 1;
  const localKey = createVehicleKey();
  configForm.value.vehicles.push({
    localKey,
    displayName: `Veiculo ${order}`,
    capacity: 40,
    orderIndex: order,
    status: order === 1 ? "active" : "inactive",
    isActive: true,
    autoActivateNext: true,
  });
  collapsedVehicles.value = {
    ...collapsedVehicles.value,
    [localKey]: true,
  };
  syncVehicleCollapseStates();
};

const removeVehicleEntry = (index: number) => {
  const entry = configForm.value.vehicles[index];
  if (!entry) return;
  configForm.value.vehicles.splice(index, 1);
  configForm.value.vehicles.forEach((item, idx) => {
    item.orderIndex = idx + 1;
  });
  syncVehicleCollapseStates();
};

const moveVehicleEntry = (index: number, delta: number) => {
  const target = index + delta;
  if (target < 0 || target >= configForm.value.vehicles.length) return;
  const [entry] = configForm.value.vehicles.splice(index, 1);
  configForm.value.vehicles.splice(target, 0, entry);
  configForm.value.vehicles.forEach((item, idx) => {
    item.orderIndex = idx + 1;
  });
};

const findVehicleById = (id?: number) => vehicles.value.find(vehicle => vehicle.id === id);
const findLayoutById = (id?: number) => layouts.value.find(layout => layout.id === id);

const handleLayoutChange = (entry: TripVehicleFormEntry) => {
  if (!entry.layoutId) return;
  const layout = findLayoutById(entry.layoutId);
  if (layout) {
    entry.capacity = layout.seat_count;
  }
};

const handleVehicleChange = (entry: TripVehicleFormEntry) => {
  if (!entry.vehicleId) {
    entry.layoutId = undefined;
    return;
  }

  const vehicle = findVehicleById(entry.vehicleId);
  if (vehicle?.layout_id) {
    entry.layoutId = vehicle.layout_id;
    const layout = findLayoutById(vehicle.layout_id);
    if (layout) {
      entry.capacity = layout.seat_count;
    }
  } else {
    entry.layoutId = undefined;
  }
};

const requiresManualLayout = (entry: TripVehicleFormEntry) => {
  if (!entry.vehicleId) return false;
  const vehicle = findVehicleById(entry.vehicleId);
  return !(vehicle && vehicle.layout_id);
};

const layoutDisplayName = (entry: TripVehicleFormEntry) => {
  if (entry.layoutId) {
    const layout = findLayoutById(entry.layoutId);
    if (layout) return layout.name;
  }
  const vehicle = findVehicleById(entry.vehicleId);
  if (vehicle?.layout_id) {
    const layout = findLayoutById(vehicle.layout_id);
    if (layout) return layout.name;
  }
  return "";
};

const seatDecks = computed<SeatDeckView[]>(() => {
  const schema = seatContext.value?.layout?.layout_schema;
  if (!schema) return [];

  const decks =
    schema.decks && schema.decks.length
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
  const seatsByDeck = new Map<string, TripSeatOut[]>();

  (seatContext.value?.seats || []).forEach(seat => {
    const deckKey = seat.deck_key || decks[0]?.key || "andar_unico";
    seatMap.set(`${deckKey}:${seat.row_index}-${seat.col_index}`, seat);

    if (!seatsByDeck.has(deckKey)) {
      seatsByDeck.set(deckKey, []);
    }
    seatsByDeck.get(deckKey)?.push(seat);
  });

  return decks.map(deck => {
    const cells: SeatCell[] = [];

    for (let row = 0; row < deck.rows; row += 1) {
      for (let col = 0; col < deck.cols; col += 1) {
        const key = `${deck.key}-${row}-${col}`;
        const seat = seatMap.get(`${deck.key}:${row}-${col}`) || null;
        const schemaCell = deck.cells.find(cell => cell.row === row && cell.col === col);

        cells.push({
          key,
          seat,
          type: schemaCell?.type || "empty",
        });
      }
    }

    const deckSeats = seatsByDeck.get(deck.key) || [];
    const seatCount = deckSeats.length;
    const occupiedCount = deckSeats.filter(seat => seat.is_occupied).length;
    const blockedCount = deckSeats.filter(seat => seat.is_blocked || !seat.is_selectable).length;
    const availableCount = Math.max(seatCount - occupiedCount - blockedCount, 0);

    return {
      key: deck.key,
      label: deck.label,
      columns: deck.cols,
      cells,
      seatCount,
      occupiedCount,
      blockedCount,
      availableCount,
    };
  });
});

const activeDeck = computed<SeatDeckView | null>(() => {
  const decks = seatDecks.value;
  if (!decks.length) return null;
  return decks.find(deck => deck.key === activeDeckKey.value) || decks[0];
});

const transposeAdminDeck = (deck: SeatDeckView): SeatDeckView => {
  const originalColumns = deck.columns || 1;
  const originalRows = Math.ceil(deck.cells.length / originalColumns);

  const matrix: SeatCell[][] = Array.from({ length: originalRows }, (_, row) =>
    deck.cells.slice(row * originalColumns, (row + 1) * originalColumns)
  );

  const transposedCells: SeatCell[] = [];

  for (let col = originalColumns - 1; col >= 0; col -= 1) {
    for (let row = 0; row < originalRows; row += 1) {
      const cell = matrix[row]?.[col];
      if (!cell) continue;

      transposedCells.push({
        ...cell,
        key: `desktop-${col}-${row}-${cell.key}`,
      });
    }
  }

  return {
    ...deck,
    key: `${deck.key}-desktop`,
    columns: originalRows,
    cells: transposedCells,
  };
};

const displayDeck = computed<SeatDeckView | null>(() => {
  if (!activeDeck.value) return null;
  return isDesktop.value ? transposeAdminDeck(activeDeck.value) : activeDeck.value;
});

watch(seatDecks, decks => {
  if (!decks.length) {
    activeDeckKey.value = null;
    return;
  }
  if (!activeDeckKey.value || !decks.some(deck => deck.key === activeDeckKey.value)) {
    activeDeckKey.value = decks[0].key;
  }
});

const selectedSeat = computed(() =>
  seatContext.value?.seats.find(seat => seat.id === selectedSeatId.value) || null
);

const selectedPassenger = computed(() =>
  seatContext.value?.passengers.find(passenger => passenger.id === selectedPassengerId.value) || null
);

const selectedSeatPassengerId = computed(() => selectedSeat.value?.occupied_by_passenger_id ?? null);
const selectedPassengerNeedsSeat = computed(() => selectedPassenger.value?.status === "unassigned");

const tripDateLabel = computed(() => {
  const date = seatContext.value?.departure_date || seatContext.value?.trip_date;
  if (!date) return "Sem data definida";
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return date;
  const label = parsed.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
  const time = seatContext.value?.departure_time;
  return time ? `${label} - ${time}` : label;
});

const currentVehicle = computed(() => {
  if (selectedTripVehicleId.value) {
    const persisted = configVehicles.value.find(vehicle => vehicle.id === selectedTripVehicleId.value);
    if (persisted) return persisted;
  }
  return seatContext.value?.trip_vehicle ?? null;
});

const currentVehicleLabel = computed(() => {
  const vehicle = currentVehicle.value;
  if (!vehicle) return null;
  return vehicle.display_name || vehicle.vehicle?.name || `Veiculo ${vehicle.order_index}`;
});

const departureOptionLabel = (departure: DepartureSummary) => {
  const parsed = new Date(`${departure.date}T00:00:00`);
  const dateLabel = Number.isNaN(parsed.getTime())
    ? departure.date
    : parsed.toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" });
  const reserved = Number(departure.capacity_reserved || 0);
  const sold = Number(departure.capacity_sold || 0);
  const total = Number(departure.capacity_total || 0);
  const demand = sold > 0 ? sold : reserved;
  const suffix = total > 0 ? `(${demand}/${total})` : "";
  return `${dateLabel} - ${departure.time} ${suffix}`.trim();
};

const passengerSeatLabel = (passenger: PassengerSeatSummary) =>
  passenger.seat_label || passenger.seat_number || "";

const passengerStatusText = (passenger: PassengerSeatSummary) =>
  passenger.status === "assigned" ? "Com assento" : "Sem assento";

const passengerClasses = (passenger: PassengerSeatSummary) => {
  const classes = ["passenger-item"];
  classes.push(passenger.status === "assigned" ? "passenger-item--assigned" : "passenger-item--pending");
  if (passenger.id === selectedPassengerId.value) {
    classes.push("passenger-item--active");
  }
  return classes;
};

const passengerFilterCounts = computed<Record<PassengerFilter, number>>(() => {
  const list = seatContext.value?.passengers || [];
  const assigned = list.filter(passenger => passenger.status === "assigned").length;
  return {
    all: list.length,
    assigned,
    unassigned: Math.max(list.length - assigned, 0),
    selected: selectedPassengerId.value ? 1 : 0,
  };
});

const filteredPassengers = computed(() => {
  const list = seatContext.value?.passengers || [];
  const term = passengerSearch.value.trim().toLowerCase();

  return list.filter(passenger => {
    const matchesSearch =
      !term ||
      passenger.name.toLowerCase().includes(term) ||
      passengerSeatLabel(passenger).toLowerCase().includes(term);

    if (!matchesSearch) return false;

    if (passengerFilter.value === "unassigned") {
      return passenger.status === "unassigned";
    }
    if (passengerFilter.value === "assigned") {
      return passenger.status === "assigned";
    }
    if (passengerFilter.value === "selected") {
      return passenger.id === selectedPassengerId.value;
    }
    return true;
  });
});

const seatStatusDescription = (seat: TripSeatOut | null) => {
  if (!seat) return "";
  if (!seat.is_selectable || seat.is_blocked) return "Bloqueado";
  if (seat.is_occupied) {
    return seat.occupied_by_current_sale ? "Selecionado neste produto" : "Ocupado";
  }
  return "Disponivel";
};

const seatStatusBadgeClass = (seat: TripSeatOut | null) => {
  if (!seat) return "seat-status-badge--available";
  if (!seat.is_selectable || seat.is_blocked) return "seat-status-badge--blocked";
  if (seat.is_occupied) return "seat-status-badge--occupied";
  return "seat-status-badge--available";
};

const seatIsBlocked = (seat: TripSeatOut | null) => !!seat && (!seat.is_selectable || seat.is_blocked);
const seatIsOccupied = (seat: TripSeatOut | null) => !!seat && seat.is_occupied;
const seatIsAvailable = (seat: TripSeatOut | null) =>
  !!seat && !seat.is_blocked && seat.is_selectable && !seat.is_occupied;

const roleLabels: Record<string, string> = {
  system: "Sistema",
  agencia: "Agencia",
  agency: "Agencia",
  admin: "Agencia",
  client: "Cliente",
  passenger: "Cliente",
};

const titleCase = (value: string) =>
  value.replace(/_/g, " ").replace(/\b\w/g, letter => letter.toUpperCase());

const sentenceCase = (value: string) => value.charAt(0).toUpperCase() + value.slice(1);

const historyActorLabel = (entry: SeatHistoryEntry) => {
  const role = entry.changed_by_role?.toLowerCase() ?? "system";
  return roleLabels[role] || titleCase(role);
};

const describeHistoryEntry = (entry: SeatHistoryEntry) => {
  const oldSeat = entry.old_seat_label || null;
  const newSeat = entry.new_seat_label || null;
  const hasPassenger = !!(entry.passenger_id || entry.passenger_name);

  if (!hasPassenger) {
    if (oldSeat && !newSeat) {
      return { action: "Bloqueou assento", detail: oldSeat };
    }
    if (!oldSeat && newSeat) {
      return { action: "Desbloqueou assento", detail: newSeat };
    }
    if (entry.reason) {
      return { action: sentenceCase(entry.reason), detail: oldSeat || newSeat || "" };
    }
    return { action: "Atualizacao operacional", detail: oldSeat || newSeat || "" };
  }

  if (oldSeat && newSeat && oldSeat !== newSeat) {
    return { action: "Moveu assento", detail: `${oldSeat} → ${newSeat}` };
  }
  if (!oldSeat && newSeat) {
    return { action: "Atribuiu assento", detail: `Sem assento → ${newSeat}` };
  }
  if (oldSeat && !newSeat) {
    return { action: "Passageiro ficou sem assento", detail: `${oldSeat} → Sem assento` };
  }
  if (oldSeat && newSeat && oldSeat === newSeat) {
    return { action: "Confirmou assento", detail: `Permanece em ${newSeat}` };
  }
  if (entry.reason) {
    return { action: sentenceCase(entry.reason), detail: "" };
  }
  return { action: "Atualizacao registrada", detail: "" };
};

const historyActionLabel = (entry: SeatHistoryEntry) => describeHistoryEntry(entry).action;
const historyPassengerName = (entry: SeatHistoryEntry) => entry.passenger_name || "Sem identificacao";
const historyChangeDetail = (entry: SeatHistoryEntry) => describeHistoryEntry(entry).detail;
const historySubjectLabel = (entry: SeatHistoryEntry) =>
  entry.passenger_id || entry.passenger_name ? "Passageiro" : "Assento";
const historySubjectValue = (entry: SeatHistoryEntry) =>
  entry.passenger_name || entry.old_seat_label || entry.new_seat_label || "Sem identificacao";

const vehicleStatusLabel = (status?: TripVehicleStatus | null) => {
  if (status === "active") return "Ativo";
  if (status === "full") return "Lotado";
  return "Aguardando";
};

const vehicleStatusClass = (status?: TripVehicleStatus | null) => {
  if (status === "active") return "vehicle-status-pill--active";
  if (status === "full") return "vehicle-status-pill--full";
  return "vehicle-status-pill--inactive";
};

const selectPassenger = (passengerId: number) => {
  selectedPassengerId.value = passengerId;
  selectedSeatId.value = null;
};

const switchVehicle = async (vehicleId: number) => {
  selectedTripVehicleId.value = vehicleId;
  activeDeckKey.value = null;
  selectedSeatId.value = null;
  selectedPassengerId.value = null;
  await loadSeatContext(vehicleId, selectedDepartureId.value);
  await loadHistory(selectedDepartureId.value);
};

const formatDate = (value?: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const toggleVehicleCollapse = (localKey: string) => {
  collapsedVehicles.value = {
    ...collapsedVehicles.value,
    [localKey]: !collapsedVehicles.value[localKey],
  };
};

const isVehicleCollapsed = (localKey: string) => !!collapsedVehicles.value[localKey];

const cellClasses = (cell: SeatCell) => {
  const classes = ["seat-cell"];

  if (cell.type === "aisle") {
    classes.push("seat-cell--aisle");
    return classes;
  }

  if (cell.type === "empty") {
    classes.push("seat-cell--empty");
    return classes;
  }

  if (!cell.seat) {
    classes.push("seat-cell--empty");
    return classes;
  }

  const seat = cell.seat;

  if (seat.id === selectedSeatId.value) {
    classes.push("seat-cell--mine");
    return classes;
  }

  if (seat.is_blocked || !seat.is_selectable) {
    classes.push("seat-cell--blocked");
    return classes;
  }

  if (seat.is_occupied) {
    classes.push("seat-cell--occupied");
    return classes;
  }

  classes.push("seat-cell--available");
  return classes;
};

const handleSeatClick = async (cell: SeatCell) => {
  if (!cell.seat) return;

  selectedSeatId.value = cell.seat.id;

  if (selectedPassengerNeedsSeat.value && seatIsAvailable(cell.seat) && selectedPassenger.value) {
    await assignPassengerToSeat(selectedPassenger.value.id, cell.seat.id);
    return;
  }

  if (seatIsAvailable(cell.seat)) return;

  if (seatIsBlocked(cell.seat) || seatIsOccupied(cell.seat)) return;
};

const assignPassengerToSeat = async (passengerId: number, seatId: number) => {
  if (!selectedTripVehicleId.value) return;

  await assignSeatAdmin(productId.value, {
    trip_vehicle_id: selectedTripVehicleId.value,
    passenger_id: passengerId,
    seat_id: seatId,
  }, selectedTripVehicleId.value || undefined, selectedDepartureId.value || undefined);

  await loadSeatContext(selectedTripVehicleId.value, selectedDepartureId.value);
  await loadHistory(selectedDepartureId.value);

  selectedPassengerId.value = null;
  selectedSeatId.value = seatId;
};

const removeAssignment = async (passengerId: number) => {
  await removePassengerSeat(productId.value, passengerId);

  if (selectedTripVehicleId.value) {
    await loadSeatContext(selectedTripVehicleId.value, selectedDepartureId.value);
  }
  await loadHistory(selectedDepartureId.value);

  if (selectedPassengerId.value === passengerId) {
    selectedPassengerId.value = null;
  }
};

const blockSelectedSeat = async (shouldBlock: boolean) => {
  if (!selectedSeat.value) return;

  if (shouldBlock) {
    blockPromptSeat.value = selectedSeat.value;
    return;
  }

  await blockSeatRequest(
    productId.value,
    { seat_id: selectedSeat.value.id, is_blocked: false },
    selectedTripVehicleId.value || undefined,
    selectedDepartureId.value || undefined,
  );

  if (selectedTripVehicleId.value) {
    await loadSeatContext(selectedTripVehicleId.value, selectedDepartureId.value);
  }
  await loadHistory(selectedDepartureId.value);
};

const cancelBlockPrompt = () => {
  blockPromptSeat.value = null;
};

const confirmBlockPrompt = async () => {
  if (!blockPromptSeat.value) return;

  await blockSeatRequest(
    productId.value,
    { seat_id: blockPromptSeat.value.id, is_blocked: true },
    selectedTripVehicleId.value || undefined,
    selectedDepartureId.value || undefined,
  );

  blockPromptSeat.value = null;

  if (selectedTripVehicleId.value) {
    await loadSeatContext(selectedTripVehicleId.value, selectedDepartureId.value);
  }
  await loadHistory(selectedDepartureId.value);
};

const loadSeatContext = async (tripVehicleId?: number | null, departureId?: number | null) => {
  const response = await getSeatMapContext(
    productId.value,
    tripVehicleId || undefined,
    departureId || undefined,
  );
  seatContext.value = response.data;

  if (seatContext.value?.vehicles && seatContext.value.vehicles.length) {
    configVehicles.value = seatContext.value.vehicles;
  }

  if (seatContext.value?.trip_vehicle?.id) {
    selectedTripVehicleId.value = seatContext.value.trip_vehicle.id;
  }
  if (seatContext.value?.departure_id) {
    selectedDepartureId.value = seatContext.value.departure_id;
  }

  selectedSeatId.value = null;
};

const loadHistory = async (departureId?: number | null | unknown) => {
  const resolvedDepartureId =
    typeof departureId === "number" && Number.isFinite(departureId) ? departureId : selectedDepartureId.value;
  const response = await getSeatHistory(productId.value, 20, resolvedDepartureId || undefined);
  history.value = response.data?.items || [];
};

const loadDepartureOptions = async () => {
  const now = new Date();
  const from = new Date(now);
  from.setDate(from.getDate() - 30);
  const to = new Date(now);
  to.setDate(to.getDate() + 180);
  try {
    const { data } = await listScheduleDepartures(
      productId.value,
      from.toISOString().slice(0, 10),
      to.toISOString().slice(0, 10),
    );
    const validItems = (data.items || []).filter(item => item.status !== "canceled");
    const itemsWithDemand = validItems.filter(
      item => (item.capacity_sold || 0) > 0 || (item.capacity_reserved || 0) > 0,
    );
    departureOptions.value = (itemsWithDemand.length ? itemsWithDemand : validItems).sort((a, b) =>
      `${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`),
    );
    if (!selectedDepartureId.value && departureOptions.value.length) {
      selectedDepartureId.value = departureOptions.value[0].id;
    }
  } catch {
    departureOptions.value = [];
  }
};

const handleDepartureChange = async () => {
  const vehicleId = selectedTripVehicleId.value;
  await loadSeatContext(vehicleId || undefined, selectedDepartureId.value);
  await loadHistory(selectedDepartureId.value);
};

const syncConfigForm = (payload: Awaited<ReturnType<typeof getTripTransportConfig>>["data"]) => {
  configForm.value.isRoadTrip = payload.is_road_trip;
  configForm.value.boardingNotes = payload.boarding_notes || "";
  configForm.value.regenerateLayout = false;
  configForm.value.vehicles = (payload.vehicles || []).map((vehicle, index) => ({
    id: vehicle.id,
    localKey: createVehicleKey(),
    vehicleId: vehicle.vehicle_id,
    layoutId: vehicle.layout_id,
    displayName: vehicle.display_name || `Veiculo ${index + 1}`,
    capacity: vehicle.capacity,
    orderIndex: vehicle.order_index,
    status: vehicle.status,
    isActive: vehicle.is_active,
    autoActivateNext: vehicle.auto_activate_next,
  }));

  ensureVehiclesList();
  syncVehicleCollapseStates();
};

const loadConfig = async () => {
  const response = await getTripTransportConfig(productId.value);
  syncConfigForm(response.data);
};

const loadVehicles = async () => {
  const [layoutsResponse, vehiclesResponse] = await Promise.all([
    listVehicleLayouts(),
    listVehiclesRequest(),
  ]);
  layouts.value = layoutsResponse.data?.items || [];
  vehicles.value = vehiclesResponse.data?.items || [];
};

const loadAll = async () => {
  await Promise.all([loadVehicles(), loadConfig()]);
  await loadDepartureOptions();
  configVehicles.value = configForm.value.vehicles.map((vehicle, index) => ({
    id: vehicle.id || -(index + 1),
    vehicle_id: vehicle.vehicleId,
    layout_id: vehicle.layoutId,
    display_name: vehicle.displayName,
    capacity: vehicle.capacity,
    order_index: vehicle.orderIndex,
    status: vehicle.status,
    is_active: vehicle.isActive,
    auto_activate_next: vehicle.autoActivateNext,
    occupied_seats: 0,
    available_seats: vehicle.capacity,
    vehicle: vehicle.vehicleId ? findVehicleById(vehicle.vehicleId) : undefined,
  })) as TripVehicleSummary[];

  const initialVehicleId =
    selectedTripVehicleId.value ||
    orderedVehicles.value.find(vehicle => vehicle.status === "active")?.id ||
    orderedVehicles.value[0]?.id ||
    null;

  if (initialVehicleId) {
    await loadSeatContext(initialVehicleId, selectedDepartureId.value);
  } else {
    await loadSeatContext(undefined, selectedDepartureId.value);
  }

  await loadHistory(selectedDepartureId.value);
};

const refreshSeatData = async () => {
  const vehicleId = selectedTripVehicleId.value;
  if (vehicleId) {
    await loadSeatContext(vehicleId, selectedDepartureId.value);
  } else {
    await loadSeatContext(undefined, selectedDepartureId.value);
  }
  await loadHistory(selectedDepartureId.value);
};

const saveConfig = async () => {
  configSaving.value = true;

  try {
    const payload: TripTransportConfigPayload = {
      is_road_trip: configForm.value.isRoadTrip,
      boarding_notes: configForm.value.boardingNotes || null,
      regenerate_layout: configForm.value.regenerateLayout,
      vehicles: configForm.value.isRoadTrip
        ? configForm.value.vehicles.map(vehicle => ({
            id: vehicle.id,
            vehicle_id: vehicle.vehicleId,
            layout_id: vehicle.layoutId,
            display_name: vehicle.displayName,
            capacity: vehicle.capacity,
            order_index: vehicle.orderIndex,
            status: vehicle.status,
            is_active: vehicle.isActive,
            auto_activate_next: vehicle.autoActivateNext,
          }))
        : [],
    };

    await saveTripTransportConfig(productId.value, payload);
    await loadAll();
  } finally {
    configSaving.value = false;
  }
};

watch(
  () => configForm.value.isRoadTrip,
  value => {
    if (value) {
      ensureVehiclesList();
      syncVehicleCollapseStates();
    }
  }
);

onMounted(async () => {
  updateViewport();
  window.addEventListener("resize", updateViewport);
  await loadAll();
});

onBeforeUnmount(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("resize", updateViewport);
  }
});
</script>

<style scoped>
.page {
  @apply space-y-8;
}
.ops-header {
  @apply flex flex-col gap-4 rounded-3xl border border-slate-100 bg-white p-6 shadow-sm lg:flex-row lg:items-center lg:justify-between;
}
.ops-header__left {
  @apply flex flex-col gap-2;
}
.ops-header__title {
  @apply text-3xl font-semibold text-slate-900;
}
.ops-header__meta {
  @apply text-sm text-slate-500;
}
.ops-header__status {
  @apply flex flex-col gap-1 text-sm text-slate-600 lg:items-center;
}
.header-actions {
  @apply flex flex-wrap gap-3;
}
.departure-select {
  @apply flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500;
}
.departure-select span {
  @apply whitespace-nowrap;
}
.departure-select select {
  @apply rounded-full border border-slate-200 bg-white px-3 py-1 text-sm font-semibold normal-case tracking-normal text-slate-700 focus:border-slate-300 focus:outline-none;
}
.btn-primary {
  @apply rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60;
}
.btn-secondary {
  @apply rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300;
}
.btn-light {
  @apply rounded-full border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-600 transition hover:border-slate-300 disabled:cursor-not-allowed disabled:opacity-50;
}
.btn-ghost {
  @apply rounded-full px-3 py-1 text-sm font-semibold text-slate-500 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50;
}
.config-card--premium {
  @apply space-y-6 rounded-3xl border border-slate-100 bg-white p-6 shadow-sm;
}
.config-card__header {
  @apply flex flex-col gap-3 md:flex-row md:items-center md:justify-between;
}
.config-form__grid {
  @apply grid gap-4 md:grid-cols-2;
}
.form-field {
  @apply flex flex-col gap-1 text-sm font-semibold text-slate-600;
}
.form-field input,
.form-field select,
.form-field textarea {
  @apply rounded-2xl border border-slate-200 px-3 py-2 text-sm font-normal text-slate-700 focus:border-emerald-500 focus:outline-none;
}
.form-field--full {
  @apply md:col-span-2;
}
.checkbox-field {
  @apply flex items-start gap-3 text-sm font-semibold text-slate-600;
}
.checkbox-field input {
  @apply mt-1;
}
.highlight-field {
  @apply rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3;
}
.trip-settings-card {
  @apply rounded-3xl border border-slate-100 bg-slate-50/70 p-5;
}
.trip-settings-card__header {
  @apply mb-4 flex items-center justify-between;
}
.trip-settings-card__header h3 {
  @apply text-lg font-semibold text-slate-800;
}
.trip-settings-card__body {
  @apply space-y-4;
}
.trip-settings-card__grid {
  @apply grid gap-4 md:grid-cols-2;
}
.trip-settings-card__toggles {
  @apply grid gap-3 md:grid-cols-2;
}
.toggle-card {
  @apply flex gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm;
}
.toggle-card input {
  @apply mt-1;
}
.toggle-card__content {
  @apply text-sm text-slate-600;
}
.toggle-card__content span {
  @apply block font-semibold text-slate-700;
}
.vehicle-stack {
  @apply space-y-4 rounded-3xl border border-slate-100 bg-white/90 p-5 shadow-inner;
}
.vehicle-stack__header {
  @apply flex flex-col gap-2 md:flex-row md:items-center md:justify-between;
}
.vehicle-stack__header .subtitle {
  @apply text-sm text-slate-500;
}
.vehicle-list {
  @apply flex flex-col gap-4;
}
.vehicle-card {
  @apply space-y-5 rounded-3xl border border-slate-100 bg-white p-6 shadow-sm;
}
.vehicle-card__header {
  @apply flex flex-col gap-4 border-b border-slate-100 pb-4 md:flex-row md:items-start md:justify-between;
}
.vehicle-card__heading {
  @apply space-y-2;
}
.vehicle-card__kicker {
  @apply text-xs uppercase tracking-[0.35em] text-slate-400;
}
.vehicle-card__title {
  @apply flex flex-wrap items-center justify-between gap-4;
}
.vehicle-card__title h3 {
  @apply text-xl font-semibold text-slate-900;
}
.vehicle-card__order {
  @apply text-xs font-semibold text-slate-500;
}
.vehicle-card__actions {
  @apply flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-600;
}
.vehicle-card__action-btn {
  @apply inline-flex items-center gap-1 rounded-full border border-slate-200 px-3 py-1 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-40;
}
.vehicle-card__action-btn span[aria-hidden="true"] {
  @apply text-sm;
}
.vehicle-card__action-btn--danger {
  @apply border-rose-200 text-rose-600 hover:border-rose-300 hover:bg-rose-50 hover:text-rose-700;
}
.vehicle-card__body {
  @apply space-y-5 pt-2;
}
.vehicle-card__section {
  @apply space-y-3 rounded-2xl border border-slate-100 bg-slate-50/70 p-4;
}
.vehicle-card__section-title {
  @apply text-xs font-semibold uppercase tracking-[0.25em] text-slate-400;
}
.vehicle-card__grid {
  @apply grid gap-4 md:grid-cols-2;
}
.vehicle-card__grid--status {
  @apply items-start;
}
.vehicle-card__toggles {
  @apply flex flex-col gap-3 text-sm text-slate-600;
}
.vehicle-status-pill {
  @apply rounded-full bg-slate-100 px-4 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600;
}
.vehicle-status-pill--active {
  @apply bg-emerald-100 text-emerald-700;
}
.vehicle-status-pill--full {
  @apply bg-amber-100 text-amber-700;
}
.vehicle-status-pill--inactive {
  @apply bg-slate-200 text-slate-600;
}
.field-static {
  @apply flex flex-col gap-2;
}
.field-static__value {
  @apply rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-800;
}
.field-static__hint {
  @apply text-xs text-slate-500;
}
.field-static__warning {
  @apply text-xs text-amber-600;
}
.operations-grid {
  @apply grid gap-6;
  grid-template-columns: minmax(0, 1fr);
  align-items: start;
}
@media (min-width: 1024px) {
  .operations-grid {
    grid-template-columns: minmax(250px, 0.9fr) minmax(0, 1.75fr) minmax(240px, 0.82fr);
  }
}
.operations-column {
  @apply space-y-4;
  min-width: 0;
}
.panel {
  @apply flex flex-col gap-4 rounded-3xl border border-slate-100 bg-white p-4 shadow-sm;
}
.panel-header {
  @apply flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between;
}
.passengers-panel {
  @apply h-full;
}
.search-input {
  @apply rounded-2xl border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-emerald-500 focus:outline-none;
}
.passenger-filters {
  @apply flex flex-wrap gap-2;
}
.filter-chip {
  @apply inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600;
}
.filter-chip--active {
  @apply border-emerald-300 bg-emerald-50 text-emerald-700;
}
.filter-chip__badge {
  @apply rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold;
}
.passenger-list {
  @apply flex max-h-[520px] flex-col gap-2 overflow-y-auto pr-1;
}
.passenger-item {
  @apply flex items-center justify-between rounded-2xl border border-transparent bg-slate-50 px-3 py-2 text-left transition;
}
.passenger-item--assigned {
  @apply border-slate-200 bg-white;
}
.passenger-item--pending {
  @apply border-amber-100 bg-amber-50/60;
}
.passenger-item--active {
  @apply border-emerald-300 bg-emerald-50/80 shadow-inner;
}
.passenger-item__info {
  @apply flex flex-col gap-0.5;
}
.passenger-name {
  @apply text-sm font-semibold text-slate-800;
}
.passenger-status {
  @apply text-xs text-slate-500;
}
.passenger-item__action {
  @apply text-xs font-semibold text-rose-500 disabled:opacity-40;
}
.vehicle-tabs {
  @apply flex flex-wrap gap-2;
}
.vehicle-tab {
  @apply w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left transition hover:border-emerald-200 lg:w-auto lg:flex-1;
}
.vehicle-tab--active {
  @apply border-emerald-300 bg-emerald-50 shadow-inner;
}
.vehicle-tab__row {
  @apply flex items-center justify-between gap-2;
}
.vehicle-tab__name {
  @apply text-sm font-semibold text-slate-800;
}
.vehicle-tab__status {
  @apply text-xs font-semibold uppercase tracking-[0.2em] text-slate-500;
}
.vehicle-tab__meta {
  @apply mt-1 flex items-center gap-2 text-xs text-slate-500;
}
.pill {
  @apply rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[11px] font-semibold;
}
.pill--success {
  @apply border-emerald-200 bg-emerald-50 text-emerald-700;
}
.map-panel {
  @apply gap-4;
}
.map-stage {
  @apply space-y-3;
}
.map-stage__summary {
  @apply flex flex-col gap-2 rounded-2xl border border-slate-100 bg-slate-50/70 p-3 md:flex-row md:items-center md:justify-between;
}
.map-stage__title {
  @apply text-base font-semibold text-slate-900;
}
.map-stage__meta {
  @apply text-xs text-slate-600;
}
.deck-tabs {
  @apply flex flex-wrap gap-2;
}
.deck-tab {
  @apply inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1 text-[11px] font-semibold text-slate-600;
}
.deck-tab--active {
  @apply border-emerald-300 bg-emerald-50 text-emerald-700;
}
.deck-tab__count {
  @apply rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold;
}
.bus-shell {
  @apply relative mx-auto w-full rounded-[2.25rem] border border-slate-100 bg-slate-50/60 p-4 shadow-inner;
}
.bus-shell::after {
  content: "";
  @apply pointer-events-none absolute inset-2.5 rounded-[1.85rem] border border-white/50;
}
.seat-cell {
  @apply flex min-h-[48px] min-w-[48px] items-center justify-center rounded-[1.15rem] border text-[11px] font-semibold text-slate-500 shadow-sm transition;
  width: 100%;
  max-width: 56px;
}
.seat-cell--available {
  @apply border-slate-200 bg-slate-50 text-slate-500;
}
.seat-cell--selected {
  @apply border-sky-400 bg-sky-50 text-sky-700 shadow-lg ring-2 ring-sky-200;
}
.seat-cell--occupied {
  @apply border-emerald-400 bg-emerald-50 text-emerald-700;
}
.seat-cell--mine {
  @apply border-indigo-300 bg-indigo-50 text-indigo-700;
}
.seat-cell--blocked {
  @apply border-rose-600 bg-rose-500 text-white shadow-inner;
}
.seat-cell--empty {
  @apply border-transparent bg-transparent;
}
.seat-cell--aisle {
  @apply pointer-events-none border-none bg-transparent text-transparent shadow-none;
}
.seat-cell--aisle::after {
  content: "";
  @apply mx-auto block h-5 w-5 rounded-full bg-slate-200/80;
}
.seat-cell:hover {
  @apply -translate-y-0.5;
}
.seat-lock {
  @apply inline-flex items-center justify-center;
  font-size: 1.4rem;
  line-height: 1;
}
.seat-lock svg {
  width: 1.1em;
  height: 1.1em;
}
.board-notes {
  @apply text-sm text-slate-500;
}
.map-legend {
  @apply flex flex-wrap gap-2 text-[10px] text-slate-500;
}
.legend-item {
  @apply inline-flex items-center gap-2 rounded-full border border-slate-200 px-2.5 py-1;
}
.legend-item--available {
  @apply border-slate-200 bg-slate-50 text-slate-600;
}
.legend-item--mine {
  @apply border-sky-200 bg-sky-50 text-sky-700;
}
.legend-item--occupied {
  @apply border-emerald-200 bg-emerald-50 text-emerald-700;
}
.legend-item--blocked {
  @apply border-rose-500 bg-rose-500 text-white;
}
.stats-grid {
  @apply grid grid-cols-2 gap-3 text-sm;
}
.stats-grid div {
  @apply rounded-2xl border border-slate-100 bg-slate-50/70 p-3;
  min-width: 0;
}
.stats-grid dt {
  @apply text-xs uppercase tracking-[0.2em] text-slate-400;
}
.stats-grid dd {
  @apply text-lg font-semibold text-slate-900;
}
.history-list {
  @apply flex flex-col gap-3;
}
.history-item {
  @apply rounded-2xl border border-slate-100 bg-slate-50/50 p-3;
}
.history-actor {
  @apply text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400;
}
.history-action {
  @apply text-sm font-semibold text-slate-800;
}
.history-passenger-line {
  @apply text-xs font-medium text-slate-500;
}
.history-passenger-label {
  @apply uppercase tracking-[0.2em];
  margin-right: 0.4rem;
}
.history-passenger-name {
  @apply text-slate-800;
}
.history-detail {
  @apply text-xs font-mono tracking-wide text-emerald-700;
}
.history-meta {
  @apply text-xs text-slate-400;
}
.history-actions {
  @apply flex gap-2;
}
.context-panel {
  @apply gap-4;
}
.context-meta,
.context-detail {
  @apply text-sm text-slate-600;
}
.seat-context {
  @apply space-y-4 rounded-3xl border border-slate-100 bg-white/80 p-5 shadow-inner;
}
.seat-context__header {
  @apply flex items-start justify-between gap-4;
}
.seat-context__label {
  @apply text-xs font-semibold uppercase tracking-[0.2em] text-slate-400;
}
.seat-context__title {
  @apply text-lg font-semibold text-slate-900;
}
.seat-context__info {
  @apply space-y-1;
}
.seat-context__value {
  @apply text-base font-semibold text-slate-800;
}
.seat-context__actions {
  @apply space-y-3;
}
.seat-context__primary-actions {
  @apply flex flex-wrap gap-2;
}
.seat-context__secondary-action {
  @apply inline-flex w-full items-center justify-center rounded-full border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-600 transition hover:bg-rose-100;
}
.seat-status-badge {
  @apply rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide;
}
.seat-status-badge--available {
  @apply bg-slate-100 text-slate-700;
}
.seat-status-badge--occupied {
  @apply bg-amber-100 text-amber-700;
}
.seat-status-badge--blocked {
  @apply bg-rose-100 text-rose-700;
}
.modal-backdrop {
  @apply fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4;
}
.modal-card {
  @apply w-full max-w-sm space-y-3 rounded-2xl bg-white p-6 text-center shadow-xl;
}
.modal-actions {
  @apply flex justify-center gap-2;
}
.placeholder-card {
  @apply rounded-2xl border border-dashed border-slate-200 p-4 text-center text-sm text-slate-500;
}

.map-stage {
  min-width: 0;
  width: 100%;
}

.map-panel,
.map-column,
.passengers-column,
.info-column {
  min-width: 0;
  width: 100%;
}
.bus-stage__layout {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  width: 100%;
}
.bus-front-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: #94a3b8;
}
.bus-front-label__dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #38bdf8;
  box-shadow: 0 0 0 6px rgba(56, 189, 248, 0.2);
}
.bus-front-label__text {
  writing-mode: vertical-rl;
  transform: rotate(180deg);
}

.bus-shell {
  width: 100%;
  padding: 0.85rem 0.35rem 0.85rem;
}

.bus-body {
  width: 100%;
  min-width: 0;
  display: flex;
  justify-content: center;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0.25rem;
}

.bus-grid {
  display: grid;
  gap: 8px;
  justify-content: center;
  justify-items: center;
  width: 100%;
  margin: 0;
  padding: 0.85rem 1rem;
}

@media (min-width: 1024px) {
  .bus-body {
    width: 100%;
    min-width: 0;
    overflow-x: auto;
    overflow-y: hidden;
    display: flex;
    justify-content: center;
    padding: 0 0.25rem 0.5rem 0;
  }

  .bus-grid {
    width: 100%;
    min-width: 0;
    max-width: none;
    margin: 0;
    padding: 1rem 1.25rem;
    gap: 10px;
  }
  .bus-stage__layout {
    flex-direction: row;
    align-items: center;
    justify-content: center;
    gap: 2rem;
  }
  .bus-front-label {
    align-items: center;
  }

  .seat-cell {
    width: 48px;
    height: 42px;
  }

  .seat-cell--aisle {
    width: 28px;
    height: 36px;
  }
}

</style>









