<template>
  <div class="space-y-6">
    <header class="flex flex-wrap items-start justify-between gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Lista de passageiros</p>
        <h1 class="text-2xl font-semibold text-slate-900">
          {{ product?.name || "Carregando produto..." }}
        </h1>
        <p class="text-sm text-slate-500">{{ tripDateLabel }}</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button class="pill" :disabled="passengersLoading" @click="refreshPassengers">
          {{ passengersLoading ? "Atualizando..." : "Atualizar" }}
        </button>
        <button class="pill" @click="goBack">Voltar</button>
      </div>
    </header>
    <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Passageiros</p>
          <p class="text-sm text-slate-500">
            {{ sortedPassengerRows.length }} passageiros listados
            <span v-if="hasActiveFilters"> de {{ passengerRows.length }}</span>
            <span v-if="relatedSalesCount"> • {{ relatedSalesCount }} venda(s)</span>
          </p>
          <p class="text-xs text-slate-500" v-if="passengerRows.length">
            Dados obtidos a partir das vendas confirmadas deste produto.
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex flex-wrap items-center rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-semibold text-slate-600">
            <span class="mr-2 text-[11px] uppercase tracking-[0.3em] text-slate-400">Ordenar por</span>
            <select
              v-model="sortMode"
              class="rounded-full border border-transparent bg-white px-3 py-1 text-sm font-semibold text-slate-800 focus:outline-none"
            >
              <option value="default">Padrão</option>
              <option value="alpha">Ordem alfabética</option>
              <option value="boarding">Local de embarque</option>
              <option value="boarding_alpha">Local de embarque + ordem alfabética</option>
              <option value="departure">Horário</option>
            </select>
          </div>
          <button class="pill" type="button" @click="resetSort" :disabled="sortMode === 'default'">
            Redefinir ordem
          </button>
          <button class="pill" type="button" @click="resetFilters" :disabled="!hasActiveFilters">
            Limpar filtros
          </button>
          <button class="pill" :disabled="passengersLoading" @click="refreshPassengers">
            {{ passengersLoading ? "Carregando..." : "Recarregar" }}
          </button>
          <button class="pill" :disabled="!sortedPassengerRows.length || passengersLoading" @click="openExportDialog">
            Exportar PDF
          </button>
          <button class="pill" :disabled="!sortedPassengerRows.length || passengersLoading || isExportingExcel" @click="exportPassengersExcel">
            {{ isExportingExcel ? "Gerando Excel..." : "Exportar Excel" }}
          </button>
        </div>
      </div>

      <div v-if="passengerRows.length || hasActiveFilters" class="mt-4 grid gap-3 rounded-2xl border border-slate-100 bg-slate-50/70 p-3 md:grid-cols-2 xl:grid-cols-6">
        <label class="space-y-1">
          <span class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Busca</span>
          <input
            v-model="searchQuery"
            type="search"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-slate-300 focus:outline-none"
            placeholder="Nome, CPF, contato, embarque..."
          />
        </label>
        <label class="space-y-1">
          <span class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Tipo</span>
          <select
            v-model="passengerTypeFilter"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-slate-300 focus:outline-none"
          >
            <option value="all">Todos</option>
            <option v-for="option in typeFilterOptions" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
        </label>
        <label class="space-y-1">
          <span class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Embarque</span>
          <select
            v-model="boardingFilter"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-slate-300 focus:outline-none"
          >
            <option value="all">Todos</option>
            <option v-for="option in boardingFilterOptions" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
        </label>
        <label class="space-y-1">
          <span class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Data</span>
          <select
            v-model="departureDateFilter"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-slate-300 focus:outline-none"
          >
            <option value="all">Todas</option>
            <option v-for="option in departureDateFilterOptions" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
        </label>
        <label class="space-y-1">
          <span class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Horário</span>
          <select
            v-model="departureFilter"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-slate-300 focus:outline-none"
          >
            <option value="all">Todos</option>
            <option v-for="option in departureFilterOptions" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
        </label>
        <label class="space-y-1">
          <span class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Venda</span>
          <select
            v-model="saleFilter"
            class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-slate-300 focus:outline-none"
          >
            <option value="all">Todas</option>
            <option v-for="saleId in saleFilterOptions" :key="saleId" :value="String(saleId)">
              #{{ saleId }}
            </option>
          </select>
        </label>
      </div>

      <div v-if="passengersLoading" class="mt-4 rounded-2xl border border-dashed border-slate-200 p-4 text-sm text-slate-500">
        Carregando lista de passageiros...
      </div>
      <div v-else-if="errorMessage" class="mt-4 rounded-2xl border border-rose-100 bg-rose-50 p-4 text-sm text-rose-700">
        {{ errorMessage }}
      </div>
      <div v-else-if="!passengerRows.length" class="mt-4 rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-500">
        Nenhum passageiro preenchido para as vendas deste produto.
      </div>
      <div v-else-if="!sortedPassengerRows.length" class="mt-4 rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-500">
        Nenhum passageiro encontrado com os filtros aplicados.
      </div>
      <div v-else class="mt-4 overflow-hidden rounded-2xl border border-slate-100">
        <div class="max-h-[480px] overflow-y-auto custom-scroll">
          <table class="min-w-full divide-y divide-slate-100 text-sm">
            <thead class="bg-slate-50 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
              <tr>
                <th class="px-3 py-2 text-left">Passageiro</th>
                <th class="px-3 py-2 text-left">Documento</th>
                <th class="px-3 py-2 text-left">Nascimento</th>
                <th class="px-3 py-2 text-left">Contato</th>
                <th class="px-3 py-2 text-left">Tipo</th>
                <th class="px-3 py-2 text-left">Embarque</th>
                <th class="px-3 py-2 text-left">Data</th>
                <th class="px-3 py-2 text-left">Horário</th>
                <th class="px-3 py-2 text-left">Venda</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="row in sortedPassengerRows" :key="`${row.saleId}-${row.passenger.id || row.passenger.passenger_index}`">
                <td class="px-3 py-3">
                  <p class="font-semibold text-slate-900">{{ row.passenger.name }}</p>
                </td>
                <td class="px-3 py-3 text-sm text-slate-600">
                  {{ row.passenger.cpf || "Não informado" }}
                </td>
                <td class="px-3 py-3 text-sm text-slate-600">
                  {{ passengerBirthdate(row.passenger) }}
                </td>
                <td class="px-3 py-3 text-sm text-slate-600">
                  {{ passengerContact(row.passenger) }}
                </td>
                <td class="px-3 py-3 text-sm text-slate-600">
                  {{ passengerTypeLabel(row.passenger.type) }}
                </td>
                <td class="px-3 py-3 text-sm text-slate-600">
                  {{ row.passenger.boarding_location || "Não informado" }}
                </td>
                <td class="px-3 py-3 text-sm text-slate-600">
                  {{ row.departureDateLabel }}
                </td>
                <td class="px-3 py-3 text-sm text-slate-600">
                  {{ row.departureLabel }}
                </td>
                <td class="px-3 py-3 text-sm text-slate-600">
                  <p class="font-semibold text-slate-900">#{{ row.saleId }}</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <teleport to="body">
      <transition name="fade">
        <div
          v-if="exportDialogOpen"
          class="fixed inset-0 z-[1050] flex items-center justify-center bg-slate-900/60 p-4"
          @click.self="closeExportDialog"
        >
          <div class="w-full max-w-lg space-y-4 rounded-3xl bg-white p-6 shadow-2xl">
            <header>
              <p class="text-xs FONT-semibold uppercase tracking-[0.3em] text-slate-400">Exportar lista</p>
              <h2 class="text-xl font-semibold text-slate-900">Escolha as colunas do PDF</h2>
              <p class="text-sm text-slate-500">
                O arquivo respeita a ordem e a filtragem exibidas na tabela. Marque as colunas desejadas e gere o PDF.
              </p>
            </header>
            <div class="space-y-2">
              <div class="rounded-2xl border border-slate-200 px-4 py-3">
                <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Orientação do PDF</p>
                <div class="mt-3 flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="pill"
                    :class="pdfOrientation === 'portrait' ? 'bg-slate-900 text-white hover:bg-slate-800' : ''"
                    :disabled="isExportingPdf"
                    @click="pdfOrientation = 'portrait'"
                  >
                    Retrato
                  </button>
                  <button
                    type="button"
                    class="pill"
                    :class="pdfOrientation === 'landscape' ? 'bg-slate-900 text-white hover:bg-slate-800' : ''"
                    :disabled="isExportingPdf"
                    @click="pdfOrientation = 'landscape'"
                  >
                    Paisagem
                  </button>
                </div>
              </div>
              <label
                v-for="column in exportColumns"
                :key="column.id"
                class="flex items-center rounded-2xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700"
              >
                <input
                  type="checkbox"
                  class="mr-3 h-4 w-4 rounded border-slate-300 text-slate-700 focus:ring-slate-500"
                  :value="column.id"
                  v-model="selectedExportColumns"
                  :disabled="isExportingPdf"
                />
                {{ column.label }}
              </label>
            </div>
            <p class="text-xs text-slate-500">
              Cabeçalho do PDF: logo da agência, nome do produto e data do produto. Após a tabela adicionamos o selo "Passageiros".
            </p>
            <p v-if="exportError" class="rounded-2xl border border-rose-100 bg-rose-50 px-4 py-2 text-sm text-rose-700">
              {{ exportError }}
            </p>
            <div class="flex justify-end gap-3">
              <button class="pill" type="button" :disabled="isExportingPdf" @click="closeExportDialog">
                Cancelar
              </button>
              <button
                class="pill bg-slate-900 text-white hover:bg-slate-800"
                :class="{ 'opacity-70': isExportingPdf }"
                type="button"
                :disabled="!selectedExportColumns.length || isExportingPdf"
                @click="exportPassengersPdf"
              >
                {{ isExportingPdf ? "Gerando..." : "Exportar PDF" }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getProductDetail, getSaleDetails, listSales } from "../../services/finance";
import type { Passenger, ProductDetail, SalePaymentStatus, SaleSummary } from "../../types/finance";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";
import { useAgencyStore } from "../../store/useAgencyStore";
import { fetchMediaDataUrl } from "../../services/media";

interface ProductPassengerRow {
  saleId: number;
  passenger: Passenger;
  paymentStatus: SalePaymentStatus;
  channel: string;
  groupLabel: string | null;
  departureId: number | null;
  departureDateLabel: string;
  departureLabel: string;
}

type SortMode = "default" | "alpha" | "boarding" | "boarding_alpha" | "departure";
type PdfOrientation = "portrait" | "landscape";

interface ExportColumnDefinition {
  id: string;
  label: string;
  getValue: (row: ProductPassengerRow) => string;
}

const route = useRoute();
const router = useRouter();
const agencyStore = useAgencyStore();
const productId = computed(() => route.params.productId as string);
const product = ref<ProductDetail | null>(null);
const passengersLoading = ref(false);
const passengerRows = ref<ProductPassengerRow[]>([]);
const sortMode = ref<SortMode>("default");
const searchQuery = ref("");
const passengerTypeFilter = ref("all");
const boardingFilter = ref("all");
const departureDateFilter = ref("all");
const departureFilter = ref("all");
const saleFilter = ref("all");
const relatedSalesCount = ref(0);
const errorMessage = ref<string | null>(null);
const exportDialogOpen = ref(false);
const exportError = ref<string | null>(null);
const isExportingPdf = ref(false);
const isExportingExcel = ref(false);
const pdfOrientation = ref<PdfOrientation>("portrait");

const currentAgency = computed(() => agencyStore.agencies.find(a => a.id === agencyStore.currentAgencyId) || null);
const exportAgency = computed(() => {
  if (product.value?.agency_id) {
    return agencyStore.agencies.find(a => a.id === product.value?.agency_id) || currentAgency.value;
  }
  return currentAgency.value;
});

const typeFilterOptions = computed(() => {
  const labels = new Set<string>();
  passengerRows.value.forEach(row => labels.add(passengerTypeLabel(row.passenger.type)));
  return Array.from(labels).sort((a, b) => a.localeCompare(b, "pt-BR"));
});

const boardingFilterOptions = computed(() => {
  const labels = new Set<string>();
  passengerRows.value.forEach(row => {
    const value = (row.passenger.boarding_location || "").trim() || "Não informado";
    labels.add(value);
  });
  return Array.from(labels).sort((a, b) => a.localeCompare(b, "pt-BR"));
});

const departureFilterOptions = computed(() => {
  const labels = new Set<string>();
  passengerRows.value.forEach(row => {
    const value = (row.departureLabel || "").trim();
    if (value) labels.add(value);
  });
  return Array.from(labels).sort((a, b) => a.localeCompare(b, "pt-BR"));
});

const departureDateFilterOptions = computed(() => {
  const labels = new Set<string>();
  passengerRows.value.forEach(row => {
    const value = (row.departureDateLabel || "").trim();
    if (value) labels.add(value);
  });
  return Array.from(labels).sort((a, b) => a.localeCompare(b, "pt-BR"));
});

const saleFilterOptions = computed(() => {
  const ids = new Set<number>();
  passengerRows.value.forEach(row => ids.add(row.saleId));
  return Array.from(ids).sort((a, b) => a - b);
});

const hasActiveFilters = computed(
  () =>
    !!searchQuery.value.trim() ||
    passengerTypeFilter.value !== "all" ||
    boardingFilter.value !== "all" ||
    departureDateFilter.value !== "all" ||
    departureFilter.value !== "all" ||
    saleFilter.value !== "all",
);

const filteredPassengerRows = computed(() => {
  const term = searchQuery.value.trim().toLowerCase();
  return passengerRows.value.filter(row => {
    const passengerType = passengerTypeLabel(row.passenger.type);
    const boarding = row.passenger.boarding_location || "Não informado";
    const departureDate = row.departureDateLabel || "Sem data";
    const departure = row.departureLabel || "Sem horário";
    if (passengerTypeFilter.value !== "all" && passengerType !== passengerTypeFilter.value) return false;
    if (boardingFilter.value !== "all" && boarding !== boardingFilter.value) return false;
    if (departureDateFilter.value !== "all" && departureDate !== departureDateFilter.value) return false;
    if (departureFilter.value !== "all" && departure !== departureFilter.value) return false;
    if (saleFilter.value !== "all" && String(row.saleId) !== saleFilter.value) return false;
    if (!term) return true;
    const searchable = [
      row.passenger.name || "",
      row.passenger.cpf || "",
      passengerContact(row.passenger),
      boarding,
      departureDate,
      departure,
      passengerType,
      `#${row.saleId}`,
    ]
      .join(" ")
      .toLowerCase();
    return searchable.includes(term);
  });
});
const sortedPassengerRows = computed(() => {
  if (sortMode.value === "default") return filteredPassengerRows.value;
  const rows = [...filteredPassengerRows.value];
  if (sortMode.value === "alpha") {
    rows.sort((a, b) => a.passenger.name.localeCompare(b.passenger.name));
  } else if (sortMode.value === "boarding") {
    rows.sort((a, b) => {
      const aKey = (a.passenger.boarding_location || "zzzzz").toLowerCase();
      const bKey = (b.passenger.boarding_location || "zzzzz").toLowerCase();
      if (aKey === bKey) return a.saleId - b.saleId;
      return aKey.localeCompare(bKey);
    });
  } else if (sortMode.value === "boarding_alpha") {
    rows.sort((a, b) => {
      const aKey = (a.passenger.boarding_location || "zzzzz").toLowerCase();
      const bKey = (b.passenger.boarding_location || "zzzzz").toLowerCase();
      if (aKey === bKey) return a.passenger.name.localeCompare(b.passenger.name);
      return aKey.localeCompare(bKey);
    });
  } else if (sortMode.value === "departure") {
    rows.sort((a, b) => {
      const aHasDeparture = Number.isFinite(a.departureId);
      const bHasDeparture = Number.isFinite(b.departureId);
      if (aHasDeparture && bHasDeparture) {
        const diff = Number(a.departureId) - Number(b.departureId);
        if (diff !== 0) return diff;
      } else if (aHasDeparture !== bHasDeparture) {
        return aHasDeparture ? -1 : 1;
      }
      if (a.saleId !== b.saleId) return a.saleId - b.saleId;
      return a.passenger.name.localeCompare(b.passenger.name);
    });
  }
  return rows;
});

const resetSort = () => {
  sortMode.value = "default";
};

const resetFilters = () => {
  searchQuery.value = "";
  passengerTypeFilter.value = "all";
  boardingFilter.value = "all";
  departureDateFilter.value = "all";
  departureFilter.value = "all";
  saleFilter.value = "all";
};

const loadProduct = async () => {
  if (!productId.value) return;
  try {
    const { data } = await getProductDetail(productId.value);
    product.value = data;
  } catch (err) {
    console.error("Erro ao carregar produto", err);
    product.value = null;
  }
};

const fetchSalesForProduct = async (): Promise<SaleSummary[]> => {
  const sales: SaleSummary[] = [];
  let page = 1;
  const pageSize = 100;
  let totalPages = 1;
  do {
    const { data } = await listSales(page, pageSize);
    sales.push(...data.items.filter(item => item.requires_passengers));
    totalPages = Math.max(1, Math.ceil(data.total / data.page_size));
    page += 1;
  } while (page <= totalPages);
  return sales;
};

const refreshPassengers = async () => {
  if (!productId.value) return;
  passengersLoading.value = true;
  errorMessage.value = null;
  try {
    const sales = await fetchSalesForProduct();
    if (!sales.length) {
      relatedSalesCount.value = 0;
      passengerRows.value = [];
      return;
    }

    const details = await Promise.all(
      sales.map(sale =>
        getSaleDetails(sale.id)
          .then(response => response.data)
          .catch(() => null),
      ),
    );

    const rows: ProductPassengerRow[] = [];
    const matchedSaleIds = new Set<number>();
    const currentProductDbId = Number(product.value?.id || 0) || null;
    details.forEach(detail => {
      if (!detail) return;
      const allItems = detail.items || [];
      const targetItems = currentProductDbId
        ? allItems.filter(item => Number(item.product_id || 0) === currentProductDbId)
        : [];
      const fallbackDirectSale = detail.product_public_id === productId.value;
      const hasTargetItems = targetItems.length > 0;
      if (!hasTargetItems && !fallbackDirectSale) return;

      const groupLabels = new Map<number, string>();
      const departureByGroup = new Map<number, number | null>();
      const sourceItems = hasTargetItems ? targetItems : allItems;
      const sourceItemIds = new Set(sourceItems.map(item => item.id));
      const itemById = new Map(sourceItems.map(item => [item.id, item]));
      detail.passenger_groups?.forEach(group => {
        if (group.id) {
          if (!sourceItemIds.has(group.sale_item_id)) return;
          groupLabels.set(group.id, group.label || `${group.product_name} #${group.group_index}`);
          const item = itemById.get(group.sale_item_id);
          departureByGroup.set(group.id, item?.departure_id ?? null);
        }
      });
      detail.passengers.forEach(passenger => {
        if (passenger.passenger_group_id && !groupLabels.has(passenger.passenger_group_id)) return;
        if (!passenger.passenger_group_id && !fallbackDirectSale) return;
        const label = passenger.passenger_group_id ? groupLabels.get(passenger.passenger_group_id) || null : null;
        const departureId = passenger.passenger_group_id ? departureByGroup.get(passenger.passenger_group_id) ?? null : null;
        const item = passenger.passenger_group_id
          ? itemById.get(
              detail.passenger_groups?.find(group => group.id === passenger.passenger_group_id)?.sale_item_id || 0,
            )
          : undefined;
        const departureDate = (item?.departure_date || "").trim();
        const departureDateLabel = formatDepartureDate(departureDate);
        const departureTime = (item?.departure_time || "").trim();
        const departureLabel = departureTime || (departureId ? `#${departureId}` : "Sem horário");
        rows.push({
          saleId: detail.id,
          passenger,
          paymentStatus: detail.payment_status,
          channel: detail.channel,
          groupLabel: label,
          departureId,
          departureDateLabel,
          departureLabel,
        });
        matchedSaleIds.add(detail.id);
      });
    });

    rows.sort((a, b) => {
      if (a.saleId !== b.saleId) return a.saleId - b.saleId;
      return a.passenger.name.localeCompare(b.passenger.name);
    });

    relatedSalesCount.value = matchedSaleIds.size;
    passengerRows.value = rows;
  } catch (err) {
    console.error("Erro ao carregar passageiros do produto", err);
    errorMessage.value = "Não foi possível carregar os passageiros. Tente novamente.";
  } finally {
    passengersLoading.value = false;
  }
};

const goBack = () => {
  router.push({ name: "products" });
};

const passengerTypeLabel = (type: string) => {
  if (type === "child_free") return "Criança (cortesia)";
  if (type === "child_paid") return "Criança paga";
  return "Adulto";
};

const passengerContact = (passenger: Passenger) => passenger.phone || passenger.whatsapp || "Não informado";

const passengerBirthdate = (passenger: Passenger) => {
  if (!passenger.birthdate) return "Não informado";
  try {
    return new Date(passenger.birthdate).toLocaleDateString("pt-BR");
  } catch {
    return passenger.birthdate;
  }
};

const formatDepartureDate = (value?: string | null) => {
  if (!value) return "Sem data";
  const raw = String(value).trim();
  if (!raw) return "Sem data";
  const isoPart = raw.includes("T") ? raw.split("T")[0] : raw;
  const parsed = new Date(`${isoPart}T00:00:00`);
  if (!Number.isNaN(parsed.getTime())) {
    return parsed.toLocaleDateString("pt-BR");
  }
  return raw;
};

const tripDateLabel = computed(() => {
  if (!product.value?.trip_date) return "Sem data definida";
  try {
    const base = new Date(product.value.trip_date).toLocaleDateString("pt-BR");
    return product.value.date_is_flexible ? `${base} (flexível)` : base;
  } catch {
    return product.value.trip_date;
  }
});

const exportColumns: ExportColumnDefinition[] = [
  { id: "passenger", label: "Passageiro", getValue: row => row.passenger.name || "Passageiro sem nome" },
  { id: "document", label: "Documento", getValue: row => row.passenger.cpf || "Não informado" },
  { id: "birthdate", label: "Nascimento", getValue: row => passengerBirthdate(row.passenger) },
  { id: "contact", label: "Contato", getValue: row => passengerContact(row.passenger) },
  { id: "type", label: "Tipo", getValue: row => passengerTypeLabel(row.passenger.type) },
  { id: "boarding", label: "Embarque", getValue: row => row.passenger.boarding_location || "Não informado" },
  { id: "departure_date", label: "Data", getValue: row => row.departureDateLabel },
  { id: "departure", label: "Horário", getValue: row => row.departureLabel },
  { id: "sale", label: "Venda", getValue: row => `#${row.saleId}` },
];

const selectedExportColumns = ref<string[]>(exportColumns.map(column => column.id));
const activeExportColumns = computed(() =>
  exportColumns.filter(column => selectedExportColumns.value.includes(column.id)),
);

const buildPdfFilename = (name?: string | null) => {
  if (!name) return "passageiros.pdf";
  const sanitized = name
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `${sanitized || "passageiros"}.pdf`;
};

const blobToDataUrl = (blob: Blob): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });

const tryDirectLogoFetch = async (url: string): Promise<string | null> => {
  try {
    const response = await fetch(url, { mode: "cors" });
    if (!response.ok) return null;
    const blob = await response.blob();
    return await blobToDataUrl(blob);
  } catch {
    return null;
  }
};

const fetchAgencyLogoDataUrl = async (): Promise<string | null> => {
  const logoUrl = exportAgency.value?.logo_url;
  if (!logoUrl) return null;
  const direct = await tryDirectLogoFetch(logoUrl);
  if (direct) return direct;
  const proxied = await fetchMediaDataUrl(logoUrl);
  if (!proxied) {
    console.warn("Não foi possível carregar o logo da agência (proxy e fetch direto falharam).");
  }
  return proxied;
};

const openExportDialog = () => {
  if (!sortedPassengerRows.value.length) return;
  exportError.value = null;
  pdfOrientation.value = "portrait";
  exportDialogOpen.value = true;
};

const closeExportDialog = () => {
  if (isExportingPdf.value) return;
  exportDialogOpen.value = false;
};

const exportPassengersPdf = async () => {
  if (!activeExportColumns.value.length) {
    exportError.value = "Selecione pelo menos uma coluna para exportar.";
    return;
  }
  if (!sortedPassengerRows.value.length) {
    exportError.value = "Não há passageiros para exportar.";
    return;
  }
  isExportingPdf.value = true;
  exportError.value = null;
  try {
    const doc = new jsPDF(pdfOrientation.value === "landscape" ? "l" : "p", "mm", "a4");
    const leftMargin = 16;
    let cursorY = 20;

    const logoDataUrl = await fetchAgencyLogoDataUrl();
    if (logoDataUrl) {
      doc.addImage(logoDataUrl, "PNG", leftMargin, cursorY - 6, 30, 12);
      cursorY += 18;
    }

    doc.setFontSize(16);
    doc.setTextColor("#0f172a");
    doc.text(product.value?.name || "Produto sem nome", leftMargin, cursorY);
    cursorY += 8;
    doc.setFontSize(11);
    doc.setTextColor("#475569");
    doc.text(`Data: ${tripDateLabel.value}`, leftMargin, cursorY);
    cursorY += 10;

    const tableHead = [activeExportColumns.value.map(column => column.label)];
    const tableBody = sortedPassengerRows.value.map(row =>
      activeExportColumns.value.map(column => column.getValue(row)),
    );

    autoTable(doc, {
      head: tableHead,
      body: tableBody,
      startY: cursorY,
      styles: { fontSize: 10, cellPadding: 2.4, textColor: "#0f172a" },
      headStyles: { fillColor: [241, 245, 249], textColor: "#0f172a", fontStyle: "bold" },
      alternateRowStyles: { fillColor: [248, 250, 252] },
    });

    const docWithAutoTable = doc as jsPDF & { lastAutoTable?: { finalY: number } };
    const finalY = docWithAutoTable.lastAutoTable?.finalY ?? cursorY;
    const totalPassengers = sortedPassengerRows.value.length;

    doc.setFontSize(12);
    doc.setTextColor("#0f172a");
    doc.text(`Total de passageiros: ${totalPassengers}`, leftMargin, finalY + 12);

    doc.save(buildPdfFilename(product.value?.name));
    exportDialogOpen.value = false;
  } catch (err) {
    console.error("Erro ao exportar passageiros do produto", err);
    exportError.value = "Não foi possível gerar o PDF. Tente novamente.";
  } finally {
    isExportingPdf.value = false;
  }
};

const exportPassengersExcel = async () => {
  if (!sortedPassengerRows.value.length) return;
  isExportingExcel.value = true;
  try {
    const headerRows = [
      ["Produto", product.value?.name || "Produto sem nome"],
      ["Data da viagem", tripDateLabel.value],
      ["Total de passageiros", String(sortedPassengerRows.value.length)],
      [],
    ];
    const tableHeaders = exportColumns.map(column => column.label);
    const tableRows = sortedPassengerRows.value.map(row => exportColumns.map(column => column.getValue(row)));
    const worksheet = XLSX.utils.aoa_to_sheet([
      ...headerRows,
      tableHeaders,
      ...tableRows,
    ]);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Passageiros");
    XLSX.writeFile(workbook, buildPdfFilename(product.value?.name).replace(/\.pdf$/i, ".xlsx"));
  } catch (err) {
    console.error("Erro ao exportar passageiros para Excel", err);
  } finally {
    isExportingExcel.value = false;
  }
};

const ensureAgencyLoaded = async () => {
  if (!agencyStore.agencies.length) {
    try {
      await agencyStore.loadAgencies();
    } catch (err) {
      console.warn("Não foi possível carregar agências antes da exportação", err);
    }
  }
};

const initialize = async () => {
  await ensureAgencyLoaded();
  await loadProduct();
  await refreshPassengers();
};

onMounted(() => initialize());

watch(
  () => productId.value,
  () => {
    initialize();
  },
);
</script>

<style scoped>
.pill {
  @apply rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-slate-300;
}
.pill:disabled {
  @apply cursor-not-allowed border-slate-100 text-slate-400 opacity-60 hover:border-slate-100;
}
.custom-scroll {
  scrollbar-width: thin;
  scrollbar-color: #94a3b8 transparent;
}
.custom-scroll::-webkit-scrollbar {
  width: 6px;
}
.custom-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scroll::-webkit-scrollbar-thumb {
  background-color: #94a3b8;
  border-radius: 9999px;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>


