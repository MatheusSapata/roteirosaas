<template>
  <section class="media-shell">
    <header class="section-head">
      <div>
        <p class="eyebrow">Preview do checkout</p>
        <h2>Midia do checkout</h2>
      </div>
      <div class="head-actions">
        <button type="button" class="section-btn" @click="$emit('edit')">Editar midia</button>
      </div>
    </header>

    <div class="media-stage">
      <article class="media-frame media-frame--banner" :class="{ 'media-frame--empty': !bannerUrl }">
        <div class="frame-copy">
          <span>Banner principal</span>
          <strong>Hero de conversao</strong>
        </div>
        <img v-if="bannerUrl" :src="bannerUrl" alt="Banner do checkout" />
        <div v-else class="media-empty">
          <strong>Banner nao configurado</strong>
        </div>
      </article>

      <article class="media-frame media-frame--product" :class="{ 'media-frame--empty': !productImageUrl }">
        <div class="frame-copy">
          <span>Imagem de produto</span>
          <strong>Capa comercial</strong>
        </div>
        <img v-if="productImageUrl" :src="productImageUrl" alt="Imagem do produto" />
        <div v-else class="media-empty">
          <strong>Imagem ausente</strong>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  bannerUrl?: string | null;
  productImageUrl?: string | null;
}>();

defineEmits<{
  (e: "edit"): void;
}>();
</script>

<style scoped>
.media-shell {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding: 0.85rem;
  border-radius: 1rem;
  border: 1px solid rgba(226, 232, 240, 0.7);
  background: #fff;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.media-shell:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.eyebrow {
  margin: 0 0 0.32rem;
  font-size: 0.6rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.section-head h2 {
  margin: 0;
  font-size: 0.84rem;
  font-weight: 600;
  letter-spacing: -0.03em;
  color: #0f172a;
}

.head-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.section-btn {
  min-height: 2.1rem;
  padding: 0.45rem 0.82rem;
  font-size: 0.82rem;
  border-radius: 999px;
  border: 1px solid rgba(16, 185, 129, 0.1);
  background: linear-gradient(180deg, #10b981, #059669);
  color: #fff;
  font-weight: 700;
}

.media-stage {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(150px, 0.5fr);
  gap: 0.6rem;
}

.media-frame {
  position: relative;
  overflow: hidden;
  border-radius: 1rem;
  border: 1px solid rgba(226, 232, 240, 0.74);
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.86), rgba(255, 255, 255, 0.92));
  min-height: 104px;
  box-shadow:
    0 14px 34px -18px rgba(15, 23, 42, 0.14),
    0 10px 22px -18px rgba(15, 23, 42, 0.12);
}

.media-frame::after {
  content: "";
  position: absolute;
  inset: auto 0 0;
  height: 28%;
  background: linear-gradient(180deg, transparent, rgba(15, 23, 42, 0.16));
  pointer-events: none;
}

.media-frame img,
.media-empty {
  width: 100%;
  height: 100%;
  min-height: 104px;
}

.media-frame img {
  display: block;
  object-fit: cover;
}

.media-frame--product img,
.media-frame--product .media-empty {
  min-height: 104px;
}

.frame-copy {
  position: absolute;
  left: 0.5rem;
  bottom: 0.5rem;
  z-index: 1;
  padding: 0.22rem 0.42rem;
  border-radius: 0.55rem;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(226, 232, 240, 0.72);
  backdrop-filter: blur(10px);
  box-shadow: 0 20px 36px -28px rgba(15, 23, 42, 0.24);
}

.frame-copy span {
  display: block;
  margin-bottom: 0.08rem;
  font-size: 0.56rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.frame-copy strong {
  color: #0f172a;
  font-size: 0.72rem;
}

.media-empty {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 0.65rem;
  background:
    radial-gradient(circle at top right, rgba(191, 219, 254, 0.32), transparent 35%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
}

.media-empty strong {
  font-size: 0.72rem;
  color: #0f172a;
}

@media (max-width: 960px) {
  .media-stage {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .media-shell {
    padding: 0.8rem;
    border-radius: 1rem;
  }

  .section-head {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
