<template>
  <section class="packages-section section-shell">
    <header class="packages-header">
      <div class="packages-heading">
        <div>
          <p class="section-kicker">Pacotes e tarifas</p>
          <h2>Pacotes do produto</h2>
        </div>
        <p>Estrutura de venda, estoque e precificacao dos pacotes vinculados a este produto.</p>
      </div>

      <div class="packages-header__actions">
        <span class="package-count">{{ filteredVariations.length }} de {{ variations.length }} pacote<span v-if="variations.length !== 1">s</span></span>
        <button type="button" class="section-button" @click="$emit('add')">Adicionar pacote</button>
      </div>
    </header>

    <div class="packages-toolbar">
      <label class="toolbar-field toolbar-field--search">
        <span>Buscar pacote</span>
        <input v-model.trim="searchQuery" type="search" placeholder="Buscar por nome..." />
      </label>

      <label class="toolbar-field">
        <span>Status</span>
        <select v-model="statusFilter">
          <option value="all">Todos</option>
          <option value="active">Ativos</option>
          <option value="inactive">Inativos</option>
        </select>
      </label>

      <label class="toolbar-field">
        <span>Ordenar</span>
        <select v-model="sortBy">
          <option value="name">Nome</option>
          <option value="price-asc">Menor preco</option>
          <option value="price-desc">Maior preco</option>
          <option value="status">Status</option>
        </select>
      </label>

    </div>

    <div class="packages-list">
      <PackageRow
        v-for="item in filteredVariations"
        :key="item.key"
        :variation="item.variation"
        :expanded="expandedKey === item.key"
        @toggle="toggleExpanded(item.key)"
        @edit="$emit('edit', item.variation, item.index)"
        @duplicate="$emit('duplicate', item.variation)"
        @remove="$emit('remove', item.index)"
      />

      <div v-if="!filteredVariations.length" class="packages-empty">
        <p>Nenhum pacote encontrado com os filtros atuais.</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import PackageRow from "./PackageRow.vue";

type ProductVariation = {
  public_id: string | null;
  name: string;
  description: string | null;
  price: number;
  people_included: number;
  status: string;
  stock_mode: string;
  has_accommodation: boolean;
  accommodation_mode: "private" | "shared";
  room_capacity: number;
  slots_per_unit: number;
  total_slots: number | null;
  available_slots: number | null;
  child_policy_enabled?: boolean;
  child_pricing_rules?: Array<{ enabled: boolean }>;
};

const props = defineProps<{
  variations: ProductVariation[];
}>();

defineEmits<{
  (e: "add"): void;
  (e: "edit", variation: ProductVariation, index: number): void;
  (e: "duplicate", variation: ProductVariation): void;
  (e: "remove", index: number): void;
}>();

const searchQuery = ref("");
const statusFilter = ref<"all" | "active" | "inactive">("all");
const sortBy = ref<"name" | "price-asc" | "price-desc" | "status">("name");
const expandedKey = ref<string | null>(null);

const filteredVariations = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  const items = props.variations.map((variation, index) => ({
    variation,
    index,
    key: variation.public_id || `${variation.name}-${index}`,
  }));

  return items
    .filter(item => {
      const statusOk =
        statusFilter.value === "all" ||
        (statusFilter.value === "active" ? item.variation.status === "active" : item.variation.status !== "active");
      const queryOk = !query || item.variation.name.toLowerCase().includes(query);
      return statusOk && queryOk;
    })
    .sort((left, right) => {
      if (sortBy.value === "price-asc") return left.variation.price - right.variation.price;
      if (sortBy.value === "price-desc") return right.variation.price - left.variation.price;
      if (sortBy.value === "status") {
        if (left.variation.status === right.variation.status) {
          return left.variation.name.localeCompare(right.variation.name, "pt-BR");
        }
        return left.variation.status === "active" ? -1 : 1;
      }
      return left.variation.name.localeCompare(right.variation.name, "pt-BR");
    });
});

watch(
  filteredVariations,
  items => {
    if (!items.length) {
      expandedKey.value = null;
      return;
    }
    if (!expandedKey.value || !items.some(item => item.key === expandedKey.value)) {
      expandedKey.value = items[0].key;
    }
  },
  { immediate: true },
);

const toggleExpanded = (key: string) => {
  expandedKey.value = expandedKey.value === key ? null : key;
};
</script>

<style scoped>
.packages-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.7rem;
  border-radius: 1.75rem;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.7);
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.packages-section:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}

.packages-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.25rem;
}

.packages-heading {
  min-width: 0;
}

.section-kicker {
  margin: 0 0 0.4rem;
  font-size: 0.7rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.packages-heading h2 {
  margin: 0;
  font-size: 1.55rem;
  font-weight: 600;
  letter-spacing: -0.045em;
  color: #0f172a;
}

.packages-heading p {
  margin: 0.55rem 0 0;
  max-width: 46rem;
  color: #64748b;
  line-height: 1.6;
}

.packages-header__actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.7rem;
}

.package-count {
  font-size: 0.8rem;
  font-weight: 700;
  color: #94a3b8;
}

.section-button {
  min-height: 2.95rem;
  padding: 0.78rem 1.15rem;
  border-radius: 1rem;
  border: 1px solid rgba(16, 185, 129, 0.1);
  background: linear-gradient(180deg, #10b981, #059669);
  color: #fff;
  font-weight: 700;
  box-shadow: 0 18px 34px -26px rgba(16, 185, 129, 0.42);
}

.packages-toolbar {
  display: grid;
  grid-template-columns: minmax(220px, 1.5fr) repeat(2, minmax(150px, 0.65fr));
  gap: 0.9rem;
  align-items: end;
  padding: 1rem 1.05rem;
  border-radius: 1.3rem;
  border: 1px solid rgba(226, 232, 240, 0.82);
  background: linear-gradient(180deg, rgba(250, 251, 253, 0.94), rgba(248, 250, 252, 0.78));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}

.toolbar-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.45rem;
}

.toolbar-field span {
  font-size: 0.7rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.toolbar-field input,
.toolbar-field select {
  width: 100%;
  min-height: 2.9rem;
  padding: 0.75rem 0.95rem;
  border-radius: 0.95rem;
  border: 1px solid rgba(203, 213, 225, 0.92);
  background: rgba(255, 255, 255, 0.98);
  color: #0f172a;
}

.packages-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.packages-empty {
  padding: 2rem 1rem;
  text-align: center;
  color: #64748b;
}

@media (max-width: 1080px) {
  .packages-toolbar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .packages-section {
    gap: 1.1rem;
    padding: 1.2rem;
    border-radius: 1.35rem;
  }

  .packages-header {
    flex-direction: column;
    align-items: stretch;
  }

  .packages-header__actions {
    align-items: stretch;
  }

  .packages-toolbar {
    grid-template-columns: 1fr;
    padding: 0.9rem;
  }
}
</style>
