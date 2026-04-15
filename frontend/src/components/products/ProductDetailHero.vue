<template>
  <section class="hero-shell">
    <div class="hero-copy">
      <div class="hero-status-row">
        <span class="status-pill" :class="`status-pill--${statusTone}`">{{ statusLabel }}</span>
        <button v-if="!isCreate" type="button" class="status-edit-btn" @click="$emit('edit')">Editar</button>
        <span class="hero-context">{{ heroMeta }}</span>
      </div>

      <div class="hero-heading">
        <h1>{{ title }}</h1>
        <p>{{ subtitle }}</p>
      </div>

      <div class="hero-meta-strip">
        <span class="meta-chip">{{ tripDateLabel }}</span>
        <span class="meta-chip">{{ operationLabel }}</span>
        <span class="meta-chip">{{ inventoryLabel }}</span>
      </div>

      <div class="hero-actions">
        <template v-if="isCreate">
          <button type="button" class="hero-btn hero-btn--primary" :disabled="saving" @click="$emit('create')">
            {{ saving ? "Criando..." : "Criar produto" }}
          </button>
        </template>
        <template v-else>
          <button type="button" class="hero-btn hero-btn--primary" :disabled="disabled" @click="$emit('sale')">
            Nova venda
          </button>
          <button type="button" class="hero-btn hero-btn--secondary" :disabled="disabled || saving" @click="$emit('duplicate')">
            Duplicar
          </button>
          <button type="button" class="hero-btn hero-btn--ghost" :disabled="disabled || saving" @click="$emit('toggle-status')">
            {{ statusActionLabel }}
          </button>
        </template>
      </div>

      <div v-if="quickActions.length" class="hero-quick-actions">
        <span class="hero-quick-actions__label">Acoes rapidas</span>
        <div class="hero-quick-actions__list">
          <button
            v-for="action in quickActions"
            :key="action.key"
            type="button"
            class="quick-action-chip"
            :disabled="action.disabled"
            @click="$emit('quick-action', action.key)"
          >
            {{ action.label }}
          </button>
        </div>
      </div>

      <div class="hero-stats">
        <article v-for="stat in stats" :key="stat.label" class="hero-stat">
          <span>{{ stat.label }}</span>
          <strong>{{ stat.value }}</strong>
        </article>
      </div>
    </div>

    <div class="hero-media" :class="{ 'hero-media--empty': !imageUrl }">
      <img v-if="imageUrl" :src="imageUrl" :alt="title" />
      <div v-else class="media-empty">
        <span>Preview visual</span>
        <strong>Adicione banner ou imagem principal</strong>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  subtitle: string;
  statusLabel: string;
  statusTone: "success" | "muted" | "warning";
  heroMeta: string;
  tripDateLabel: string;
  operationLabel: string;
  inventoryLabel: string;
  imageUrl?: string | null;
  isCreate?: boolean;
  saving?: boolean;
  disabled?: boolean;
  statusActionLabel: string;
  stats: Array<{ label: string; value: string | number }>;
  quickActions: Array<{ key: string; label: string; disabled: boolean }>;
}>();

defineEmits<{
  (e: "create"): void;
  (e: "sale"): void;
  (e: "duplicate"): void;
  (e: "toggle-status"): void;
  (e: "edit"): void;
  (e: "quick-action", action: string): void;
}>();
</script>

<style scoped>
.hero-shell {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.95fr);
  gap: 2rem;
  padding: 2.3rem;
  border-radius: 2rem;
  background:
    radial-gradient(circle at top left, rgba(191, 219, 254, 0.28), transparent 30%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(247, 250, 252, 0.97));
  border: 1px solid rgba(226, 232, 240, 0.78);
  box-shadow:
    0 18px 42px -30px rgba(15, 23, 42, 0.12),
    0 36px 80px -72px rgba(15, 23, 42, 0.16);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.hero-shell::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.36), transparent 52%, rgba(226, 232, 240, 0.08));
  pointer-events: none;
}

.hero-copy,
.hero-media {
  position: relative;
  z-index: 1;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 1.55rem;
  min-width: 0;
}

.hero-status-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2rem;
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.status-pill--success {
  color: #0f766e;
  background: rgba(20, 184, 166, 0.12);
  border: 1px solid rgba(20, 184, 166, 0.2);
}

.status-pill--muted {
  color: #475569;
  background: rgba(148, 163, 184, 0.14);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.status-pill--warning {
  color: #9a3412;
  background: rgba(249, 115, 22, 0.12);
  border: 1px solid rgba(249, 115, 22, 0.18);
}

.hero-context {
  font-size: 0.9rem;
  color: #64748b;
}

.status-edit-btn {
  border: 1px solid rgba(203, 213, 225, 0.9);
  background: rgba(255, 255, 255, 0.92);
  border-radius: 999px;
  padding: 0.4rem 0.9rem;
  font-size: 0.82rem;
  font-weight: 700;
  color: #0f172a;
}

.hero-heading {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.hero-heading h1 {
  margin: 0;
  font-size: clamp(2.9rem, 4.4vw, 4rem);
  line-height: 0.96;
  letter-spacing: -0.035em;
  font-weight: 650;
  color: #020617;
}

.hero-heading p {
  margin: 0;
  max-width: 58ch;
  font-size: 0.98rem;
  line-height: 1.72;
  color: #64748b;
}

.hero-meta-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  min-height: 2.1rem;
  padding: 0.42rem 0.88rem;
  border-radius: 999px;
  font-size: 0.82rem;
  color: #475569;
  background: rgba(248, 250, 252, 0.86);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.hero-quick-actions {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.hero-quick-actions__label {
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.hero-quick-actions__list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.quick-action-chip {
  min-height: 2.45rem;
  padding: 0.58rem 0.95rem;
  border-radius: 999px;
  border: 1px solid rgba(203, 213, 225, 0.88);
  background: rgba(255, 255, 255, 0.92);
  color: #0f172a;
  font-size: 0.84rem;
  font-weight: 700;
}

.quick-action-chip:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

.hero-btn {
  min-height: 2.85rem;
  padding: 0.75rem 1.2rem;
  border-radius: 1rem;
  border: 1px solid transparent;
  font-weight: 700;
  font-size: 0.92rem;
  letter-spacing: -0.01em;
  transition:
    transform 0.18s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease,
    background-color 0.2s ease,
    color 0.2s ease;
}

.hero-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.hero-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.hero-btn--primary {
  color: #fff;
  background: linear-gradient(180deg, #10b981, #059669);
  box-shadow: 0 18px 32px -24px rgba(16, 185, 129, 0.45);
}

.hero-btn--secondary {
  color: #0f172a;
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(203, 213, 225, 0.9);
}

.hero-btn--ghost {
  color: #7c2d12;
  background: rgba(255, 247, 237, 0.9);
  border-color: rgba(251, 146, 60, 0.22);
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
}

.hero-stat {
  padding: 0.95rem 1rem;
  border-radius: 1.15rem;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(226, 232, 240, 0.82);
  box-shadow: 0 10px 24px -24px rgba(15, 23, 42, 0.24);
}

.hero-stat span {
  display: block;
  margin-bottom: 0.4rem;
  font-size: 0.74rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #94a3b8;
}

.hero-stat strong {
  font-size: clamp(1.48rem, 2.35vw, 2rem);
  letter-spacing: -0.04em;
  color: #020617;
}

.hero-media {
  min-height: 100%;
  position: relative;
  border-radius: 1.9rem;
  overflow: hidden;
  transform: scale(1.01);
  border: 1px solid rgba(226, 232, 240, 0.4);
  box-shadow:
    0 20px 48px -22px rgba(15, 23, 42, 0.18),
    0 18px 36px -30px rgba(15, 23, 42, 0.12);
}

.hero-media img,
.media-empty {
  width: 100%;
  height: 100%;
  min-height: 390px;
  border-radius: 1.9rem;
}

.hero-media img {
  display: block;
  object-fit: cover;
  background: #e2e8f0;
}

.hero-media::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.25), rgba(0, 0, 0, 0));
  pointer-events: none;
}

.hero-media--empty {
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.88), rgba(241, 245, 249, 0.96));
}

.media-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  text-align: center;
  background:
    linear-gradient(160deg, rgba(255, 255, 255, 0.72), rgba(248, 250, 252, 0.96)),
    radial-gradient(circle at center, rgba(191, 219, 254, 0.24), transparent 48%);
  color: #64748b;
}

.media-empty span {
  font-size: 0.78rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #94a3b8;
}

.media-empty strong {
  max-width: 16rem;
  font-size: 1.05rem;
  color: #334155;
}

@media (max-width: 1100px) {
  .hero-shell {
    grid-template-columns: 1fr;
  }

  .hero-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .hero-shell {
    padding: 1.25rem;
    border-radius: 1.5rem;
  }

  .hero-heading h1 {
    font-size: 2.4rem;
  }

  .hero-stats {
    grid-template-columns: 1fr;
  }

  .hero-media img,
  .media-empty {
    min-height: 240px;
  }
}
</style>
