<template>
  <div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="space-y-3">
      <div ref="wrapperRef" class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-3">
        <canvas ref="canvasRef" class="signature-canvas"></canvas>
      </div>

      <p class="text-xs text-slate-500">
        Use o dedo ou o mouse para desenhar dentro da área destacada.
      </p>

      <div class="flex flex-wrap gap-3">
        <button
          type="button"
          class="btn-secondary flex-1"
          :disabled="disabled || loading || !hasSignature"
          @click="clearCanvas"
        >
          Limpar
        </button>

        <button
          type="button"
          class="btn-primary flex-1"
          :disabled="primaryDisabled"
          @click="emitSignature"
        >
          <span v-if="loading">Processando...</span>
          <span v-else>Assinar contrato</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";

const props = withDefaults(
  defineProps<{
    loading?: boolean;
    disabled?: boolean;
    canSubmit?: boolean;
  }>(),
  {
    loading: false,
    disabled: false,
    canSubmit: true,
  }
);

const emit = defineEmits<{
  (event: "submit", value: string): void;
}>();

const canvasRef = ref<HTMLCanvasElement | null>(null);
const wrapperRef = ref<HTMLDivElement | null>(null);

const hasSignature = ref(false);
const isDrawing = ref(false);

let context: CanvasRenderingContext2D | null = null;
let resizeObserver: ResizeObserver | null = null;

const getCanvasSize = () => {
  const canvas = canvasRef.value;
  const wrapper = wrapperRef.value;

  if (!canvas || !wrapper) {
    return { width: 0, height: 0 };
  }

  const wrapperRect = wrapper.getBoundingClientRect();

  const horizontalPadding = 24; // p-3 + p-3 do wrapper visual
  const width = Math.max(wrapperRect.width - horizontalPadding, 100);
  const height = 220;

  return { width, height };
};

const setupCanvas = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const { width, height } = getCanvasSize();
  if (!width || !height) return;

  const dpr = window.devicePixelRatio || 1;

  canvas.width = Math.floor(width * dpr);
  canvas.height = Math.floor(height * dpr);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width, height);

  ctx.lineWidth = 2.4;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.strokeStyle = "#0f172a";
  ctx.fillStyle = "#0f172a";

  context = ctx;
  hasSignature.value = false;
  isDrawing.value = false;
};

const getCoordinates = (event: PointerEvent) => {
  const canvas = canvasRef.value;
  if (!canvas) return { x: 0, y: 0 };

  const rect = canvas.getBoundingClientRect();

  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
  };
};

const startDrawing = (event: PointerEvent) => {
  if (props.disabled || !context) return;

  const canvas = canvasRef.value;
  if (!canvas) return;

  isDrawing.value = true;

  if (canvas.setPointerCapture) {
    canvas.setPointerCapture(event.pointerId);
  }

  const { x, y } = getCoordinates(event);

  context.beginPath();
  context.moveTo(x, y);

  // desenha um ponto inicial para não parecer que falhou no clique/toque
  context.arc(x, y, 0.8, 0, Math.PI * 2);
  context.fill();
  context.beginPath();
  context.moveTo(x, y);

  hasSignature.value = true;
  event.preventDefault();
};

const draw = (event: PointerEvent) => {
  if (!isDrawing.value || props.disabled || !context) return;

  const { x, y } = getCoordinates(event);

  context.lineTo(x, y);
  context.stroke();

  hasSignature.value = true;
  event.preventDefault();
};

const endDrawing = (event?: PointerEvent) => {
  if (!isDrawing.value || !context) return;

  const canvas = canvasRef.value;
  if (canvas && event && canvas.releasePointerCapture) {
    canvas.releasePointerCapture(event.pointerId);
  }

  context.closePath();
  isDrawing.value = false;
};

const clearCanvas = () => {
  const canvas = canvasRef.value;
  if (!canvas || !context || props.disabled) return;

  const { width, height } = getCanvasSize();
  context.clearRect(0, 0, width, height);
  hasSignature.value = false;
  isDrawing.value = false;
};

const emitSignature = () => {
  if (primaryDisabled.value) return;

  const canvas = canvasRef.value;
  if (!canvas) return;

  emit("submit", canvas.toDataURL("image/png"));
};

const primaryDisabled = computed(() => {
  if (props.disabled || props.loading) return true;
  if (!props.canSubmit) return true;
  return !hasSignature.value;
});

onMounted(async () => {
  await nextTick();

  const canvas = canvasRef.value;
  if (!canvas) return;

  canvas.style.touchAction = "none";

  setupCanvas();

  canvas.addEventListener("pointerdown", startDrawing);
  canvas.addEventListener("pointermove", draw);
  canvas.addEventListener("pointerup", endDrawing);
  canvas.addEventListener("pointercancel", endDrawing);

  resizeObserver = new ResizeObserver(() => {
    setupCanvas();
  });

  if (wrapperRef.value) {
    resizeObserver.observe(wrapperRef.value);
  }

  window.addEventListener("resize", setupCanvas);
});

onBeforeUnmount(() => {
  const canvas = canvasRef.value;

  if (canvas) {
    canvas.removeEventListener("pointerdown", startDrawing);
    canvas.removeEventListener("pointermove", draw);
    canvas.removeEventListener("pointerup", endDrawing);
    canvas.removeEventListener("pointercancel", endDrawing);
  }

  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }

  window.removeEventListener("resize", setupCanvas);
});
</script>

<style scoped>
.signature-canvas {
  display: block;
  width: 100%;
  height: 220px;
  border-radius: 0.75rem;
  background: white;
  cursor: crosshair;
}

.btn-primary {
  @apply rounded-2xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 transition hover:-translate-y-0.5 disabled:translate-y-0 disabled:bg-emerald-300;
}

.btn-secondary {
  @apply rounded-2xl border border-slate-200 px-5 py-2.5 text-sm font-semibold text-slate-600 shadow-sm transition hover:border-emerald-400 hover:text-emerald-600 disabled:bg-slate-100 disabled:text-slate-400;
}
</style>