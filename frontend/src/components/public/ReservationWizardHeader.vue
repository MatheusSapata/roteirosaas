<template>
  <header class="wizard-header">
    <div class="wizard-header__brand">
      <div class="wizard-header__logo">
        <img
          v-if="logoUrl"
          :src="logoUrl"
          :alt="agencyName"
          class="wizard-header__logo-image"
        />
        <span v-else>{{ agencyInitials }}</span>
      </div>

      <div class="wizard-header__copy">
        <p class="wizard-header__eyebrow">{{ eyebrow }}</p>
        <h1>{{ title }}</h1>
        <p>{{ subtitle }}</p>
      </div>
    </div>

    <div class="wizard-header__actions">
      <a
        v-if="supportHref"
        :href="supportHref"
        target="_blank"
        rel="noopener"
        class="wizard-header__action wizard-header__action--support"
      >
        Suporte
      </a>
      <button
        v-if="showBack"
        type="button"
        class="wizard-header__action"
        @click="$emit('back')"
      >
        {{ backLabel }}
      </button>
      <span v-if="paymentLabel" class="wizard-header__status">
        {{ paymentLabel }}
      </span>
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  agencyName: string;
  agencyInitials: string;
  logoUrl?: string | null;
  eyebrow: string;
  title: string;
  subtitle: string;
  supportHref?: string | null;
  paymentLabel?: string | null;
  showBack?: boolean;
  backLabel?: string;
}>();

defineEmits<{
  (event: "back"): void;
}>();
</script>

<style scoped>
.wizard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.25rem;
  padding: 1.4rem 1.5rem;
  border-radius: 28px;
  border: 1px solid rgba(203, 213, 225, 0.78);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(248, 250, 252, 0.92));
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
}

.wizard-header__brand {
  display: flex;
  align-items: center;
  gap: 1rem;
  min-width: 0;
}

.wizard-header__logo {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  overflow: hidden;
  border-radius: 18px;
  background: linear-gradient(145deg, #064e3b, #047857 58%, #0f766e);
  color: #ffffff;
  font-size: 0.9rem;
  font-weight: 800;
  box-shadow: 0 14px 28px rgba(4, 120, 87, 0.2);
}

.wizard-header__logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 0.45rem;
}

.wizard-header__copy {
  min-width: 0;
}

.wizard-header__eyebrow {
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: #0f766e;
}

.wizard-header__copy h1 {
  margin-top: 0.35rem;
  font-size: clamp(1.65rem, 2.2vw, 2rem);
  line-height: 1.05;
  font-weight: 800;
  color: #08111f;
}

.wizard-header__copy p:last-child {
  margin-top: 0.45rem;
  max-width: 62ch;
  font-size: 0.95rem;
  line-height: 1.6;
  color: #64748b;
}

.wizard-header__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.wizard-header__action,
.wizard-header__status {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 15px;
  padding: 0.7rem 1rem;
  font-size: 0.8rem;
  font-weight: 800;
}

.wizard-header__action {
  border: 1px solid #dbe4ee;
  background: #ffffff;
  color: #334155;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.wizard-header__action:hover {
  transform: translateY(-1px);
  border-color: #b7c2d0;
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.06);
}

.wizard-header__action--support {
  border-color: rgba(16, 185, 129, 0.22);
  background: linear-gradient(180deg, #ecfdf5, #ffffff);
  color: #065f46;
}

.wizard-header__status {
  border: 1px solid rgba(16, 185, 129, 0.28);
  background: linear-gradient(135deg, #064e3b, #059669);
  color: #ffffff;
  box-shadow: 0 12px 24px rgba(5, 150, 105, 0.18);
}

@media (max-width: 900px) {
  .wizard-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .wizard-header__actions {
    width: 100%;
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .wizard-header {
    padding: 1.1rem;
    border-radius: 22px;
  }

  .wizard-header__logo {
    width: 46px;
    height: 46px;
    border-radius: 14px;
  }

  .wizard-header__copy h1 {
    font-size: 1.45rem;
  }

  .wizard-header__copy p:last-child {
    font-size: 0.88rem;
  }
}
</style>
