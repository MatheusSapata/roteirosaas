<template>
  <div class="rooming-view">
    <RoomingHeader
      :product-name="headerName"
      :trip-date="roomingData?.product.trip_date"
      :total-passengers="roomingData?.stats.total_passengers ?? 0"
      @refresh="loadData"
      @create-room="openCreateModal()"
    />

    <p v-if="errorMessage" class="rooming-error">{{ errorMessage }}</p>

    <RoomingStats v-if="roomingData" :stats="roomingData.stats" />

    <section v-if="roomingData" class="rooming-layout">
      <div class="rooming-layout__rooms">
        <RoomGroupSection
          v-for="group in roomingData.accommodations"
          :key="group.key"
          :group="group"
          @create-room="openCreateModal"
          @add-passenger="openAssignModal"
          @remove-passenger="handleRemovePassenger"
          @request-rename="handleRenameRequest"
        />
        <p v-if="!roomingData.accommodations.length" class="rooming-empty-state">
          Nenhum tipo de acomodação configurado para este produto.
        </p>
      </div>
      <RoomingSidebar
        class="rooming-layout__sidebar"
        :pending-passengers="roomingData.pending_passengers"
        :alerts="roomingData.alerts"
        :auto-match-loading="autoMatchLoading"
        @assign-passenger="openAssignModalForPassenger"
        @auto-match="openAutoMatchModal"
      />
    </section>

    <p v-if="loading" class="rooming-loading">Carregando rooming list...</p>

    <div v-if="createModalOpen" class="modal-overlay">
      <div class="modal-card">
        <header class="modal-header">
          <h3>Criar quarto</h3>
          <button type="button" class="modal-close" @click="closeCreateModal">&times;</button>
        </header>
        <form class="modal-body" @submit.prevent="submitCreateRoom">
          <label>
            Tipo de acomodação
            <select v-model="createForm.optionKey" required>
              <option disabled value="">Selecione um tipo</option>
              <option v-for="option in roomingData?.options" :key="option.key" :value="option.key">
                {{ option.label }} · {{ option.capacity }} pessoas
                {{ option.product_room_id ? " (Modelo)" : option.variation_public_id ? " (Pacote)" : "" }}
              </option>
              <option value="custom">Outro (informar manualmente)</option>
            </select>
          </label>
          <label v-if="createForm.optionKey === 'custom'">
            Descrição
            <input v-model="createForm.customLabel" type="text" required placeholder="Quarto duplo" />
          </label>
          <label v-if="createForm.optionKey === 'custom'">
            Capacidade
            <input v-model.number="createForm.customCapacity" type="number" min="1" required />
          </label>
          <label>
            Nome do quarto
            <input v-model="createForm.roomName" type="text" placeholder="Ex: Quarto 101" />
          </label>
          <footer class="modal-footer">
            <button type="button" class="modal-secondary" @click="closeCreateModal">Cancelar</button>
            <button type="submit" class="modal-primary" :disabled="actionLoading">
              {{ actionLoading ? "Salvando..." : "Criar" }}
            </button>
          </footer>
        </form>
      </div>
    </div>

    <div v-if="assignModalOpen" class="modal-overlay">
      <div class="modal-card">
        <header class="modal-header">
          <h3>Alocar passageiro</h3>
          <button type="button" class="modal-close" @click="closeAssignModal">&times;</button>
        </header>
        <form class="modal-body" @submit.prevent="submitAssignPassenger">
          <label>
            Quarto
            <select v-model.number="assignContext.roomId" required :disabled="!availableRooms.length">
              <option disabled value="">Selecione um quarto</option>
              <option v-for="room in availableRooms" :key="room.id" :value="room.id">
                {{ room.name }} · {{ room.occupancy }}/{{ room.capacity }}
              </option>
            </select>
          </label>
          <p v-if="!availableRooms.length" class="modal-empty">Nenhum quarto disponível para alocação manual.</p>
          <label>
            Passageiro sem quarto
            <select v-model.number="assignContext.passengerId" required>
              <option disabled value="">Selecione um passageiro</option>
              <option v-for="passenger in roomingData?.pending_passengers" :key="passenger.id" :value="passenger.id">
                {{ passenger.name }} · Pedido #{{ passenger.order_code }}
              </option>
            </select>
          </label>
          <footer class="modal-footer">
            <button type="button" class="modal-secondary" @click="closeAssignModal">Cancelar</button>
            <button
              type="submit"
              class="modal-primary"
              :disabled="actionLoading || !assignContext.passengerId || !assignContext.roomId"
            >
              {{ actionLoading ? "Alocando..." : "Confirmar" }}
            </button>
          </footer>
        </form>
      </div>
    </div>

    <div v-if="renameModalOpen" class="modal-overlay">
      <div class="modal-card">
        <header class="modal-header">
          <h3>Renomear quarto</h3>
          <button type="button" class="modal-close" @click="closeRenameModal">&times;</button>
        </header>
        <form class="modal-body" @submit.prevent="submitRenameRoom">
          <label>
            Nome do quarto
            <input v-model="renameContext.name" type="text" maxlength="120" required />
          </label>
          <footer class="modal-footer">
            <button type="button" class="modal-secondary" @click="closeRenameModal">Cancelar</button>
            <button type="submit" class="modal-primary" :disabled="actionLoading">
              {{ actionLoading ? "Salvando..." : "Salvar" }}
            </button>
          </footer>
        </form>
      </div>
    </div>

    <div v-if="autoMatchModalOpen && autoMatchPreview" class="modal-overlay">
      <div class="modal-card modal-card--wide">
        <header class="modal-header">
          <h3>Prévia da organização automática</h3>
          <button type="button" class="modal-close" @click="closeAutoMatchModal">&times;</button>
        </header>
        <section class="modal-body auto-match-preview">
          <p class="modal-subtitle">Revise o que será feito antes de aplicar.</p>
          <div class="auto-match-summary">
            <p>Passageiros pendentes: {{ autoMatchPreview.summary.pending_before }}</p>
            <p>Serão alocados: {{ autoMatchPreview.summary.passengers_to_allocate }}</p>
            <p>Quartos completados: {{ autoMatchPreview.summary.rooms_to_complete }}</p>
            <p>Novos quartos criados: {{ autoMatchPreview.summary.rooms_to_create }}</p>
            <p>Continuarão pendentes: {{ autoMatchPreview.summary.pending_after }}</p>
          </div>
          <section>
            <h4>Quartos que serão completados</h4>
            <p v-if="!autoMatchPreview.fills.length">Nenhum quarto existente será alterado.</p>
            <article v-for="fill in autoMatchPreview.fills" :key="fill.room_id" class="auto-match-card">
              <header>
                <strong>{{ fill.room_name }}</strong>
                <span>{{ fill.before }}/{{ fill.capacity }} → {{ fill.after }}/{{ fill.capacity }}</span>
              </header>
              <div>
                <p>Entrarão:</p>
                <ul>
                  <li v-for="passenger in fill.passengers_added" :key="passenger.id">{{ passenger.name }}</li>
                </ul>
              </div>
            </article>
          </section>
          <section>
            <h4>Novos quartos</h4>
            <p v-if="!autoMatchPreview.new_rooms.length">Nenhum novo quarto será criado.</p>
            <article
              v-for="room in autoMatchPreview.new_rooms"
              :key="room.room_type_key + '-' + room.passengers.map(p => p.id).join('-')"
              class="auto-match-card"
            >
              <header>
                <strong>{{ room.room_label }}</strong>
                <span>{{ room.capacity }} vagas</span>
              </header>
              <div>
                <p>Passageiros:</p>
                <ul>
                  <li v-for="passenger in room.passengers" :key="passenger.id">{{ passenger.name }}</li>
                </ul>
              </div>
            </article>
          </section>
          <section>
            <h4>Sem quarto após a organização</h4>
            <p v-if="!autoMatchPreview.remaining_unassigned.length">Todos os passageiros elegíveis serão acomodados.</p>
            <ul v-else class="auto-match-list">
              <li v-for="passenger in autoMatchPreview.remaining_unassigned" :key="passenger.id">
                {{ passenger.name }}
              </li>
            </ul>
          </section>
        </section>
        <footer class="modal-footer">
          <button type="button" class="modal-secondary" @click="closeAutoMatchModal">Cancelar</button>
          <button type="button" class="modal-primary" :disabled="autoMatchApplying" @click="confirmAutoMatch">
            {{ autoMatchApplying ? "Aplicando..." : "Confirmar e aplicar" }}
          </button>
        </footer>
      </div>
    </div>

    <div v-if="swapModalOpen && swapContext.room && swapContext.incomingPassengerId" class="modal-overlay">
      <div class="modal-card">
        <header class="modal-header">
          <h3>Quarto cheio — realizar troca</h3>
          <button type="button" class="modal-close" @click="closeSwapModal">&times;</button>
        </header>
        <div class="modal-body swap-modal">
          <p>Selecione quem sairá do quarto {{ swapContext.room.name }}:</p>
          <ul class="modal-swap-list">
            <li v-for="passenger in swapContext.room.passengers" :key="passenger.id">
              <label>
                <input
                  type="radio"
                  name="swap-outgoing"
                  :value="passenger.id"
                  v-model.number="swapContext.outgoingPassengerId"
                />
                {{ passenger.name }}
              </label>
            </li>
          </ul>
        </div>
        <footer class="modal-footer">
          <button type="button" class="modal-secondary" @click="closeSwapModal">Cancelar</button>
          <button
            type="button"
            class="modal-primary"
            :disabled="!swapContext.outgoingPassengerId || actionLoading"
            @click="submitSwap"
          >
            {{ actionLoading ? "Confirmando..." : "Confirmar troca" }}
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import RoomingHeader from "../../components/admin/rooming/RoomingHeader.vue";
import RoomingStats from "../../components/admin/rooming/RoomingStats.vue";
import RoomGroupSection from "../../components/admin/rooming/RoomGroupSection.vue";
import RoomingSidebar from "../../components/admin/rooming/RoomingSidebar.vue";
import {
  applyAutoMatch,
  createRoom,
  getRoomingList,
  movePassenger,
  previewAutoMatch,
  removePassengerFromRoom,
  renameRoom,
  swapPassengers,
} from "../../services/rooming";
import type {
  AutoMatchPreviewResponse,
  CreateRoomPayload,
  RoomingListResponse,
  RoomingPassenger,
  RoomingRoom,
} from "../../types/rooming";

const route = useRoute();
const productId = computed(() => route.params.productId as string);

const roomingData = ref<RoomingListResponse | null>(null);
const loading = ref(false);
const actionLoading = ref(false);
const errorMessage = ref("");

const createModalOpen = ref(false);
const assignModalOpen = ref(false);

const createForm = reactive({
  optionKey: "",
  customLabel: "",
  customCapacity: 2,
  roomName: "",
});

const assignContext = reactive<{ roomId: number | null; passengerId: number | null }>({
  roomId: null,
  passengerId: null,
});

const allRooms = computed(() => roomingData.value?.accommodations.flatMap(group => group.rooms) ?? []);
const availableRooms = computed(() => allRooms.value.filter(room => !room.locked));
const renameModalOpen = ref(false);
const renameContext = reactive<{ room: RoomingRoom | null; name: string }>({
  room: null,
  name: "",
});
const autoMatchModalOpen = ref(false);
const autoMatchPreview = ref<AutoMatchPreviewResponse | null>(null);
const autoMatchLoading = ref(false);
const autoMatchApplying = ref(false);
const swapModalOpen = ref(false);
const swapContext = reactive<{ room: RoomingRoom | null; incomingPassengerId: number | null; outgoingPassengerId: number | null }>({
  room: null,
  incomingPassengerId: null,
  outgoingPassengerId: null,
});

const headerName = computed(() => roomingData.value?.product.name ?? `#${productId.value ?? ""}`);

const loadData = async () => {
  if (!productId.value) {
    return;
  }
  loading.value = true;
  errorMessage.value = "";
  try {
    const response = await getRoomingList(productId.value);
    roomingData.value = response.data;
  } catch (error) {
    console.error("Erro ao carregar rooming list", error);
    const detail = (error as any)?.response?.data?.detail;
    errorMessage.value = detail || "Não foi possível carregar os dados do rooming. Tente novamente.";
  } finally {
    loading.value = false;
  }
};

onMounted(loadData);
watch(productId, loadData);

const selectedOption = computed(() =>
  roomingData.value?.options.find(option => option.key === createForm.optionKey) ?? null,
);

const resetCreateForm = (optionKey = "") => {
  createForm.optionKey = optionKey;
  createForm.customLabel = "";
  createForm.customCapacity = 2;
  createForm.roomName = "";
};

const openCreateModal = (optionKey = "") => {
  resetCreateForm(optionKey);
  createModalOpen.value = true;
};

const closeCreateModal = () => {
  createModalOpen.value = false;
};

const submitCreateRoom = async () => {
  if (!productId.value) {
    return;
  }
  const option = selectedOption.value;
  const computedAccommodationLabel = option?.label ?? (createForm.customLabel || undefined);
  const computedCapacity = option?.capacity ?? createForm.customCapacity;
  const payload: CreateRoomPayload = {
    label: createForm.roomName || undefined,
    variation_public_id: option?.variation_public_id,
    accommodation_label: computedAccommodationLabel,
    capacity: computedCapacity,
    product_room_id: option?.product_room_id ?? undefined,
  };
  if (!payload.accommodation_label || !payload.capacity) {
    errorMessage.value = "Defina o tipo e capacidade do quarto.";
    return;
  }
  actionLoading.value = true;
  try {
    await createRoom(productId.value, payload);
    await loadData();
    closeCreateModal();
  } catch (error) {
    console.error("Erro ao criar quarto", error);
    errorMessage.value = "Não foi possível criar o quarto.";
  } finally {
    actionLoading.value = false;
  }
};

const openAssignModal = (room: RoomingRoom) => {
  if (room.locked) {
    errorMessage.value = "Quartos privativos não permitem nova alocação.";
    return;
  }
  errorMessage.value = "";
  assignContext.roomId = room.id;
  assignContext.passengerId = roomingData.value?.pending_passengers[0]?.id ?? null;
  assignModalOpen.value = true;
};

const openAssignModalForPassenger = (passenger: RoomingPassenger) => {
  if (!availableRooms.value.length) {
    errorMessage.value = "Não há quartos disponíveis para alocar este passageiro.";
    return;
  }
  errorMessage.value = "";
  assignContext.roomId = availableRooms.value[0]?.id ?? null;
  assignContext.passengerId = passenger.id;
  assignModalOpen.value = true;
};

const closeAssignModal = () => {
  assignModalOpen.value = false;
  assignContext.roomId = null;
  assignContext.passengerId = null;
};

const submitAssignPassenger = async () => {
  if (!productId.value || !assignContext.roomId || !assignContext.passengerId) {
    return;
  }
  const targetRoom = allRooms.value.find(room => room.id === assignContext.roomId);
  if (!targetRoom) {
    errorMessage.value = "Quarto não encontrado.";
    return;
  }
  if (targetRoom.locked) {
    errorMessage.value = "Quarto bloqueado para alterações.";
    return;
  }
  const passenger = roomingData.value?.pending_passengers.find(
    pending => pending.id === assignContext.passengerId,
  );
  const consumesCapacity = passenger?.consumes_capacity !== false;
  if (consumesCapacity && targetRoom.occupancy >= targetRoom.capacity) {
    closeAssignModal();
    openSwapModal(assignContext.passengerId, targetRoom);
    return;
  }
  actionLoading.value = true;
  try {
    await movePassenger(productId.value, {
      passenger_id: assignContext.passengerId,
      target_room_id: targetRoom.id,
    });
    await loadData();
    closeAssignModal();
  } catch (error) {
    console.error("Erro ao alocar passageiro", error);
    errorMessage.value = "Não foi possível alocar o passageiro.";
  } finally {
    actionLoading.value = false;
  }
};

const handleRemovePassenger = async (room: RoomingRoom, passenger: RoomingPassenger) => {
  if (!productId.value) {
    return;
  }
  if (room.locked) {
    errorMessage.value = "Quartos privativos não permitem remover passageiros manualmente.";
    return;
  }
  actionLoading.value = true;
  try {
    await removePassengerFromRoom(productId.value, room.id, passenger.id);
    await loadData();
  } catch (error) {
    console.error("Erro ao remover passageiro", error);
    errorMessage.value = "Não foi possível remover o passageiro do quarto.";
  } finally {
    actionLoading.value = false;
  }
};

const handleRenameRequest = (room: RoomingRoom) => {
  if (!room.is_private) {
    return;
  }
  renameContext.room = room;
  renameContext.name = room.name;
  renameModalOpen.value = true;
};

const closeRenameModal = () => {
  renameModalOpen.value = false;
  renameContext.room = null;
  renameContext.name = "";
};

const submitRenameRoom = async () => {
  if (!productId.value || !renameContext.room) {
    return;
  }
  const nextName = renameContext.name.trim();
  if (!nextName) {
    errorMessage.value = "Informe um nome válido.";
    return;
  }
  actionLoading.value = true;
  try {
    await renameRoom(productId.value, renameContext.room.id, nextName);
    await loadData();
    closeRenameModal();
  } catch (error) {
    console.error("Erro ao renomear quarto", error);
    errorMessage.value = "Não foi possível renomear o quarto.";
  } finally {
    actionLoading.value = false;
  }
};

const openAutoMatchModal = async () => {
  if (!productId.value) {
    return;
  }
  autoMatchLoading.value = true;
  autoMatchPreview.value = null;
  try {
    const response = await previewAutoMatch(productId.value);
    if (
      !response.data.summary.passengers_to_allocate &&
      !response.data.summary.rooms_to_create
    ) {
      errorMessage.value = "Nenhuma organização automática possível no momento.";
      return;
    }
    autoMatchPreview.value = response.data;
    autoMatchModalOpen.value = true;
  } catch (error) {
    console.error("Erro ao simular auto-match", error);
    errorMessage.value = "Não foi possível gerar a prévia de organização automática.";
  } finally {
    autoMatchLoading.value = false;
  }
};

const closeAutoMatchModal = () => {
  autoMatchModalOpen.value = false;
  autoMatchPreview.value = null;
};

const confirmAutoMatch = async () => {
  if (!productId.value || !autoMatchPreview.value) {
    return;
  }
  autoMatchApplying.value = true;
  try {
    const response = await applyAutoMatch(productId.value, {
      preview_token: autoMatchPreview.value.preview_token,
    });
    closeAutoMatchModal();
    await loadData();
    errorMessage.value = `Organização aplicada: ${response.data.summary.passengers_to_allocate} passageiros alocados, ${response.data.summary.rooms_to_complete} quarto(s) completado(s), ${response.data.summary.rooms_to_create} quarto(s) criado(s).`;
  } catch (error) {
    console.error("Erro ao aplicar auto-match", error);
    errorMessage.value = "Não foi possível aplicar a organização automática.";
  } finally {
    autoMatchApplying.value = false;
  }
};

const openSwapModal = (incomingPassengerId: number, room: RoomingRoom) => {
  swapContext.room = room;
  swapContext.incomingPassengerId = incomingPassengerId;
  swapContext.outgoingPassengerId = null;
  swapModalOpen.value = true;
};

const closeSwapModal = () => {
  swapModalOpen.value = false;
  swapContext.room = null;
  swapContext.incomingPassengerId = null;
  swapContext.outgoingPassengerId = null;
};

const submitSwap = async () => {
  if (!productId.value || !swapContext.room || !swapContext.incomingPassengerId || !swapContext.outgoingPassengerId) {
    return;
  }
  actionLoading.value = true;
  try {
    await swapPassengers(productId.value, {
      incoming_passenger_id: swapContext.incomingPassengerId,
      target_room_id: swapContext.room.id,
      outgoing_passenger_id: swapContext.outgoingPassengerId,
    });
    await loadData();
    closeSwapModal();
  } catch (error) {
    console.error("Erro ao trocar passageiros", error);
    errorMessage.value = "Não foi possível realizar a troca.";
  } finally {
    actionLoading.value = false;
  }
};
</script>

<style scoped>
.rooming-view {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem;
  background: #f5f7fb;
  min-height: 100vh;
}

.rooming-layout {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(280px, 1fr);
  gap: 1.5rem;
}

.rooming-layout__rooms {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.rooming-layout__sidebar {
  position: sticky;
  top: 1.5rem;
}

.rooming-loading,
.rooming-empty-state,
.rooming-error {
  margin: 0;
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #475569;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
}

.rooming-error {
  border-color: #fecaca;
  background: #fee2e2;
  color: #b91c1c;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 1rem;
}

.modal-card {
  width: min(480px, 100%);
  background: #fff;
  border-radius: 1rem;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.25);
  overflow: hidden;
}

.modal-card--wide {
  width: min(700px, 100%);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 700;
  color: #0f172a;
}

.modal-close {
  border: none;
  background: transparent;
  font-size: 1.5rem;
  line-height: 1;
  color: #94a3b8;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.25rem;
}

.modal-body label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-weight: 600;
  color: #0f172a;
  font-size: 0.9rem;
}

.modal-body input,
.modal-body select {
  border: 1px solid #cbd5f5;
  border-radius: 0.6rem;
  padding: 0.55rem;
  font-size: 0.95rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.25rem 1.25rem;
}

.modal-empty {
  margin: 0;
  color: #b91c1c;
  font-size: 0.85rem;
}

.auto-match-preview {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.auto-match-preview section + section {
  border-top: 1px solid #e2e8f0;
  padding-top: 0.75rem;
}

.modal-subtitle {
  margin: 0 0 0.5rem 0;
  color: #475569;
  font-size: 0.95rem;
}

.auto-match-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.5rem;
  background: #f8fafc;
  border-radius: 0.75rem;
  padding: 0.85rem;
  font-size: 0.9rem;
}

.auto-match-card {
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 0.9rem;
  background: #fff;
}

.auto-match-card header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  gap: 1rem;
}

.auto-match-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.swap-modal {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-bottom: 0;
}

.swap-modal__summary {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  background: #f8fafc;
  font-size: 0.9rem;
  color: #0f172a;
}

.swap-modal__text {
  margin: 0;
}

.swap-modal__meta {
  margin: 0;
  color: #475569;
  font-weight: 500;
}

.swap-modal__notice {
  margin: 0;
  font-size: 0.85rem;
  color: #92400e;
}

.modal-swap-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.modal-swap-item {
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 0.6rem 0.75rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.modal-swap-item label {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  cursor: pointer;
}

.modal-swap-item input {
  margin: 0;
}

.modal-swap-item__name {
  margin: 0;
  font-weight: 600;
  color: #0f172a;
}

.modal-swap-item__meta {
  margin: 0;
  font-size: 0.8rem;
  color: #64748b;
}

.modal-swap-item--selected {
  border-color: #34d399;
  box-shadow: 0 0 0 2px rgba(52, 211, 153, 0.2);
}

.modal-primary,
.modal-secondary {
  border-radius: 0.75rem;
  padding: 0.5rem 1.25rem;
  font-weight: 600;
  border: 1px solid transparent;
}

.modal-primary {
  background: #1ebd63;
  border-color: #12a14f;
  color: #fff;
  box-shadow: 0 10px 20px rgba(18, 161, 79, 0.25);
}

.modal-primary:hover {
  background: #10924a;
  border-color: #0c6e37;
}

.modal-secondary {
  background: transparent;
  border-color: #cbd5f5;
  color: #475569;
}

@media (max-width: 1024px) {
  .rooming-layout {
    grid-template-columns: 1fr;
  }

  .rooming-layout__sidebar {
    position: static;
  }
}
</style>


