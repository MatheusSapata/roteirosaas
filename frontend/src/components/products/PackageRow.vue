<template>
  <article class="package-row" :class="{ 'package-row--expanded': expanded }">
    <button type="button" class="package-row__summary" @click="$emit('toggle')">
      <div class="package-row__identity">
        <span class="chevron" :class="{ 'chevron--expanded': expanded }">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7 4.5 12.5 10 7 15.5" />
          </svg>
        </span>
        <div class="identity-copy">
          <div class="identity-title">
            <h3>{{ variation.name }}</h3>
            <PackageStatusBadge :status="variation.status" />
          </div>
        </div>
      </div>

      <div class="package-row__price">
        <PackagePrice :value="variation.price" compact />
      </div>

      <div class="package-row__edit" @click.stop>
        <button type="button" class="edit-btn" @click="$emit('edit')">Editar</button>
      </div>

      <div class="package-row__menu" @click.stop>
        <PackageRowActions @edit="$emit('edit')" @duplicate="$emit('duplicate')" @remove="$emit('remove')" />
      </div>
    </button>

    <transition name="package-expand">
      <PackageExpandedPanel
        v-if="expanded"
        :variation="variation"
        @edit="$emit('edit')"
        @duplicate="$emit('duplicate')"
        @remove="$emit('remove')"
      />
    </transition>
  </article>
</template>

<script setup lang="ts">
import PackageExpandedPanel from "./PackageExpandedPanel.vue";
import PackagePrice from "./PackagePrice.vue";
import PackageRowActions from "./PackageRowActions.vue";
import PackageStatusBadge from "./PackageStatusBadge.vue";

const props = defineProps<{
  variation: {
    name: string;
    price: number;
    status: string;
    description: string | null;
  };
  expanded: boolean;
}>();

defineEmits<{
  (e: "toggle"): void;
  (e: "edit"): void;
  (e: "duplicate"): void;
  (e: "remove"): void;
}>();

</script>

<style scoped>
.package-row {
  border-radius: 1.5rem;
  border: 1px solid rgba(226, 232, 240, 0.8);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.985), rgba(250, 251, 253, 0.98)),
    radial-gradient(circle at top right, rgba(191, 219, 254, 0.12), transparent 34%);
  box-shadow:
    0 3px 12px rgba(15, 23, 42, 0.04),
    0 18px 32px -30px rgba(15, 23, 42, 0.08);
  overflow: visible;
  transition:
    border-color 0.22s ease,
    box-shadow 0.22s ease,
    transform 0.18s ease;
}

.package-row:hover {
  transform: translateY(-1px);
  border-color: rgba(203, 213, 225, 0.92);
  box-shadow:
    0 10px 28px rgba(15, 23, 42, 0.08),
    0 16px 30px -24px rgba(15, 23, 42, 0.1);
}

.package-row--expanded {
  border-color: rgba(191, 219, 254, 0.9);
  box-shadow:
    0 12px 32px rgba(15, 23, 42, 0.06),
    0 20px 40px -30px rgba(15, 23, 42, 0.1);
}

.package-row__summary {
  display: grid;
  width: 100%;
  grid-template-columns: minmax(0, 1fr) 170px 112px 56px;
  align-items: center;
  gap: 1rem;
  padding: 0.95rem 1.3rem;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.package-row__identity {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  min-width: 0;
}

.chevron {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 999px;
  background: rgba(248, 250, 252, 0.95);
  color: #64748b;
  border: 1px solid rgba(226, 232, 240, 0.88);
  transition:
    transform 0.2s ease,
    background-color 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease;
}

.package-row:hover .chevron,
.package-row--expanded .chevron {
  background: #f1f5f9;
  border-color: rgba(203, 213, 225, 0.96);
  color: #334155;
}

.chevron--expanded {
  transform: rotate(90deg);
}

.chevron svg {
  width: 0.95rem;
  height: 0.95rem;
}

.identity-copy {
  min-width: 0;
}

.identity-title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.7rem;
}

.identity-title h3 {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #020617;
}

.package-row__price {
  display: flex;
  justify-content: flex-end;
  min-width: 0;
}

.package-row__edit,
.package-row__menu {
  display: flex;
  justify-content: flex-end;
}

.edit-btn {
  min-height: 2.7rem;
  min-width: 6.1rem;
  padding: 0.7rem 0.9rem;
  border-radius: 1rem;
  border: 1px solid rgba(203, 213, 225, 0.88);
  background: rgba(248, 250, 252, 0.82);
  color: #1e293b;
  font-weight: 600;
  transition:
    border-color 0.2s ease,
    background-color 0.2s ease,
    color 0.2s ease,
    transform 0.18s ease,
    box-shadow 0.22s ease;
}

.edit-btn:hover {
  transform: translateY(-1px);
  border-color: rgba(203, 213, 225, 0.98);
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 14px 24px -22px rgba(15, 23, 42, 0.2);
}

.package-expand-enter-active,
.package-expand-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.package-expand-enter-from,
.package-expand-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 1440px) {
  .package-row__summary {
    grid-template-columns: minmax(0, 1fr) 150px 112px 56px;
  }
}

@media (max-width: 1180px) {
  .package-row__summary {
    grid-template-columns: minmax(0, 1fr) 140px 112px 56px;
    grid-template-areas:
      "identity price edit menu";
    row-gap: 0.95rem;
  }

  .package-row__identity {
    grid-area: identity;
  }

  .package-row__price {
    grid-area: price;
  }

  .package-row__edit {
    grid-area: edit;
  }

  .package-row__menu {
    grid-area: menu;
  }
}

@media (max-width: 860px) {
  .package-row {
    border-radius: 1.45rem;
  }

  .package-row__summary {
    grid-template-columns: minmax(0, 1fr) auto auto;
    grid-template-areas:
      "identity edit menu"
      "price price price";
    padding: 1rem 1rem 1.05rem;
  }

  .package-row__identity {
    align-items: flex-start;
  }

  .package-row__price {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .package-row__summary {
    grid-template-columns: 1fr auto;
    grid-template-areas:
      "identity menu"
      "price edit";
    gap: 0.85rem;
  }

  .package-row__edit {
    justify-content: flex-start;
  }
}

@media (max-width: 520px) {
  .package-row__summary {
    grid-template-columns: 1fr;
    grid-template-areas:
      "identity"
      "price"
      "edit"
      "menu";
  }

  .package-row__edit,
  .package-row__menu {
    justify-content: flex-start;
  }

  .package-row__menu :deep(.package-row-actions) {
    width: 100%;
    justify-content: flex-start;
  }

  .package-row__menu :deep(.package-row-actions__trigger) {
    width: 2.7rem;
  }
}

@media (max-width: 720px) {
  .identity-title {
    gap: 0.5rem;
  }

  .identity-title h3 {
    font-size: 0.94rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .package-row,
  .chevron,
  .edit-btn,
  .package-expand-enter-active,
  .package-expand-leave-active {
    transition: none;
  }
}
</style>
