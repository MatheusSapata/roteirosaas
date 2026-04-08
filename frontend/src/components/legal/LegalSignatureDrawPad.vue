<template>
  <div class="pad-card">
    <p class="pad-label">{{ label }}</p>
    <div class="pad-canvas-wrapper">
      <canvas ref="canvasRef" class="pad-canvas"></canvas>
    </div>
    <div class="pad-actions">
      <button type="button" class="btn-secondary" :disabled="disabled" @click="clearCanvas">Limpar</button>
      <button type="button" class="btn-primary" :disabled="disabled || !hasSignature" @click="emitValue">
        Atualizar preview
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    modelValue: string | null;
    disabled?: boolean;
    label?: string;
  }>(),
  {
    modelValue: null,
    disabled: false,
    label: "Desenhe sua assinatura",
  }
);

const emit = defineEmits<{
  (event: "update:modelValue", value: string | null): void;
}>();

const canvasRef = ref<HTMLCanvasElement | null>(null);
let ctx: CanvasRenderingContext2D | null = null;
const isDrawing = ref(false);
const hasSignature = ref(false);

const setupCanvas = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const dpr = typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1;
  const displayWidth = canvas.clientWidth || 480;
  const height = 180;
  canvas.width = displayWidth * dpr;
  canvas.height = height * dpr;
  ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.scale(dpr, dpr);
  ctx.lineWidth = 2.2;
  ctx.lineCap = "round";
  ctx.strokeStyle = "#0f172a";
  ctx.clearRect(0, 0, displayWidth, height);
  hasSignature.value = false;
};

const getCoordinates = (event: PointerEvent) => {
  const canvas = canvasRef.value;
  if (!canvas) return { x: 0, y: 0 };
  const rect = canvas.getBoundingClientRect();
  return { x: event.clientX - rect.left, y: event.clientY - rect.top };
};

const startDrawing = (event: PointerEvent) => {
  if (props.disabled || !ctx) return;
  isDrawing.value = true;
  const { x, y } = getCoordinates(event);
  ctx.beginPath();
  ctx.moveTo(x, y);
  event.preventDefault();
};

const draw = (event: PointerEvent) => {
  if (!isDrawing.value || props.disabled || !ctx) return;
  const { x, y } = getCoordinates(event);
  ctx.lineTo(x, y);
  ctx.stroke();
  hasSignature.value = true;
  event.preventDefault();
};

const endDrawing = () => {
  if (!isDrawing.value || !ctx) return;
  ctx.closePath();
  isDrawing.value = false;
};

const emitValue = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;
  if (!hasSignature.value) {
    emit("update:modelValue", null);
    return;
  }
  emit("update:modelValue", canvas.toDataURL("image/png"));
};

const clearCanvas = () => {
  setupCanvas();
  emit("update:modelValue", null);
};

const handleResize = () => setupCanvas();

onMounted(() => {
  const canvas = canvasRef.value;
  if (!canvas) return;
  setupCanvas();
  canvas.addEventListener("pointerdown", startDrawing);
  canvas.addEventListener("pointermove", draw);
  canvas.addEventListener("pointerup", endDrawing);
  canvas.addEventListener("pointerleave", endDrawing);
  canvas.style.touchAction = "none";
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  const canvas = canvasRef.value;
  if (canvas) {
    canvas.removeEventListener("pointerdown", startDrawing);
    canvas.removeEventListener("pointermove", draw);
    canvas.removeEventListener("pointerup", endDrawing);
    canvas.removeEventListener("pointerleave", endDrawing);
  }
  window.removeEventListener("resize", handleResize);
});

watch(
  () => props.disabled,
  value => {
    if (value) {
      isDrawing.value = false;
    }
  }
);
</script>

<style scoped>
.pad-card {
  @apply rounded-3xl border border-slate-200 bg-white p-4 shadow-sm;
}
.pad-label {
  @apply text-xs font-semibold uppercase tracking-[0.3em] text-slate-400 mb-2;
}
.pad-canvas-wrapper {
  @apply rounded-2xl border border-dashed border-slate-300 bg-slate-50;
  min-height: 220px;
}
.pad-canvas {
  @apply h-[220px] w-full rounded-2xl bg-white;
}
.pad-actions {
  @apply mt-3 flex flex-wrap gap-3;
}
.btn-primary {
  @apply rounded-full bg-emerald-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 transition hover:-translate-y-0.5 disabled:bg-emerald-200;
}
.btn-secondary {
  @apply rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 shadow-sm transition hover:border-slate-400 disabled:text-slate-400;
}
</style>
