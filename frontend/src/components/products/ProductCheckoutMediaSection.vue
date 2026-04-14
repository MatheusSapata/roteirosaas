<template>
<section class="media-card">
  <header class="card-header">
    <div>
      <p class="eyebrow">Checkout e midia</p>
      <h2>Experiencia visual</h2>
      <p class="muted">Visao previa do que seus clientes veem antes de comprar.</p>
    </div>
    <button type="button" class="pill" @click="$emit('edit')">Editar midia</button>
  </header>

  <div class="media-stage">
    <div class="banner-preview" :class="{ 'banner-preview--empty': !bannerUrl }">
      <img v-if="bannerUrl" :src="bannerUrl" alt="Banner" />
      <span v-else>Banner ausente</span>
      <p class="hint">1600x600px recomendado</p>
    </div>
    <div class="product-preview" :class="{ 'product-preview--empty': !productImageUrl }">
      <img v-if="productImageUrl" :src="productImageUrl" alt="Produto" />
      <span v-else>Imagem principal ausente</span>
      <p class="hint">Sugestao: 900x900px</p>
    </div>
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
.media-card {
  background: white;
  border-radius: 1.5rem;
  border: 1px solid #e2e8f0;
  padding: 1.5rem;
  box-shadow: 0 20px 45px -35px rgba(15, 23, 42, 0.4);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}
.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.3em;
  font-size: 0.7rem;
  color: #94a3b8;
}
.muted {
  font-size: 0.9rem;
  color: #475569;
}
.media-stage {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1rem;
}
@media (max-width: 768px) {
  .media-stage {
    grid-template-columns: 1fr;
  }
}
.banner-preview,
.product-preview {
  border-radius: 1.25rem;
  background: #f8fafc;
  border: 1px dashed #cbd5f5;
  padding: 1rem;
  min-height: 200px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  text-align: center;
}
.banner-preview img,
.product-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 1rem;
  border: 1px solid #e2e8f0;
}
.banner-preview--empty,
.product-preview--empty {
  color: #94a3b8;
  font-weight: 600;
}
.hint {
  position: absolute;
  bottom: 0.8rem;
  left: 1rem;
  font-size: 0.75rem;
  color: #94a3b8;
}
.product-preview {
  min-height: 240px;
}
</style>
