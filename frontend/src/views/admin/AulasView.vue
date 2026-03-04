<template>
  <div class="space-y-8 px-4 py-6 md:px-8">
    <section class="rounded-3xl bg-white/95 p-6 shadow-xl shadow-slate-200/70">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.4em] text-slate-500">Trilha premium</p>
          <h1 class="mt-2 text-3xl font-bold text-slate-900">Aulas</h1>
          <p class="mt-1 max-w-3xl text-sm text-slate-500">
            Aprofunde o uso do construtor de páginas com aulas curtas e diretas. Escolha uma lição, ative o player e pratique acompanhando o passo a passo.
          </p>
        </div>
        <div class="rounded-2xl border border-slate-200/80 p-4 text-sm text-slate-600 shadow-sm">
          <p class="font-semibold text-slate-900">Progresso</p>
          <div class="mt-2 flex items-center gap-3">
            <div class="h-2 flex-1 overflow-hidden rounded-full bg-slate-200/80">
              <div class="h-full rounded-full bg-emerald-500 transition-all duration-500" :style="{ width: `${progressPercent}%` }"></div>
            </div>
            <span class="font-semibold text-slate-900">{{ progressPercent }}%</span>
          </div>
          <p class="mt-1 text-xs text-slate-500">
            {{ completedLessons.length }} de {{ lessons.length }} aulas concluídas
          </p>
        </div>
      </div>
    </section>

    <section class="grid items-start gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
      <div class="space-y-4 rounded-3xl bg-white shadow-xl shadow-slate-200/70 lg:p-6">
        <div class="relative overflow-hidden rounded-2xl bg-slate-900">
          <div class="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-slate-950/70"></div>
          <template v-if="activeLesson">
            <iframe
              v-if="activeLesson.videoType !== 'file'"
              :key="`embed-${activeLesson.id}`"
              class="aspect-video w-full rounded-2xl border-0"
              :src="activeLesson.videoUrl"
              frameborder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowfullscreen
            ></iframe>
            <video
              v-else
              :key="`file-${activeLesson.id}`"
              controls
              controlslist="nodownload"
              playsinline
              preload="metadata"
              class="aspect-video w-full rounded-2xl bg-black object-cover"
              :poster="activeLesson.thumbnail"
            >
              <source :src="activeLesson.videoUrl" type="video/mp4" />
              Seu navegador não suporta o player de vídeo.
            </video>
          </template>
          <div
            v-else
            class="aspect-video w-full rounded-2xl bg-slate-900 text-sm font-semibold text-slate-200 flex items-center justify-center text-center"
          >
            {{ lessonsLoading ? "Carregando aulas..." : "Nenhuma aula disponível no momento." }}
          </div>
        </div>

        <div v-if="activeLesson" class="space-y-4 rounded-2xl bg-slate-50/70 p-5">
          <div class="flex flex-wrap items-center gap-3 text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">
            <span class="rounded-full bg-slate-200/60 px-3 py-1 text-[0.65rem] text-slate-700">
              {{ activeLesson.level || "Aula" }}
            </span>
            <span class="text-slate-400">&bull;</span>
            <span>{{ activeLesson.duration || "Tempo livre" }}</span>
          </div>
          <h2 class="text-2xl font-bold text-slate-900">{{ activeLesson.title }}</h2>
          <p class="text-sm text-slate-600">{{ activeLesson.description }}</p>
        </div>
      </div>

      <aside class="space-y-4 rounded-3xl bg-white p-4 shadow-xl shadow-slate-200/70">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.4em] text-slate-500">Playlist</p>
            <h3 class="text-lg font-semibold text-slate-900">Selecione a aula</h3>
          </div>
          <span class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
            {{ lessons.length }} aulas
          </span>
        </div>

        <p
          v-if="!lessons.length"
          class="rounded-2xl border border-dashed border-slate-200 px-3 py-6 text-center text-sm text-slate-500"
        >
          {{ lessonsLoading ? "Carregando aulas..." : "Nenhuma aula cadastrada ainda." }}
        </p>

        <ul v-else class="space-y-3">
          <li v-for="lesson in lessons" :key="lesson.id">
            <button
              type="button"
              class="w-full rounded-2xl border p-3 text-left transition hover:-translate-y-0.5 hover:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-brand"
              :class="[
                activeLessonId === lesson.id
                  ? 'border-brand/40 bg-brand/5 shadow-lg shadow-brand/20'
                  : 'border-slate-200 bg-white shadow-sm'
              ]"
              @click="selectLesson(lesson.id)"
            >
              <div class="flex items-start gap-3">
                <img
                  :src="lesson.thumbnail"
                  alt=""
                  class="h-16 w-24 flex-shrink-0 rounded-xl object-cover"
                  loading="lazy"
                />
                <div class="flex-1">
                  <div class="flex items-center justify-between text-xs text-slate-500">
                    <span>{{ lesson.duration || "—" }}</span>
                    <span v-if="completedLessons.includes(lesson.id)" class="text-emerald-500">Concluída</span>
                  </div>
                  <p class="mt-1 text-sm font-semibold text-slate-900">{{ lesson.title }}</p>
                  <p class="mt-1 text-xs text-slate-500 line-clamp-2">
                    {{ lesson.description }}
                  </p>
                </div>
              </div>
            </button>
          </li>
        </ul>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useLessonsStore } from "../../store/useLessonsStore";

const lessonsStore = useLessonsStore();
const lessons = computed(() => lessonsStore.sortedLessons);
const lessonsLoading = computed(() => lessonsStore.loading);

const activeLessonId = ref<number | null>(null);
const completedLessons = ref<number[]>([]);

watch(
  lessons,
  newLessons => {
    if (!newLessons.length) {
      activeLessonId.value = null;
      return;
    }
    if (!newLessons.some(lesson => lesson.id === activeLessonId.value)) {
      activeLessonId.value = newLessons[0].id;
    }
  },
  { immediate: true }
);

const activeLesson = computed(() => lessons.value.find(lesson => lesson.id === activeLessonId.value) || null);

const progressPercent = computed(() => {
  if (!lessons.value.length) return 0;
  const completed = Math.min(completedLessons.value.length, lessons.value.length);
  return Math.round((completed / lessons.value.length) * 100);
});

const selectLesson = (lessonId: number) => {
  activeLessonId.value = lessonId;
  if (!completedLessons.value.includes(lessonId)) {
    completedLessons.value.push(lessonId);
  }
};

onMounted(async () => {
  await lessonsStore.ensureLessons();
  if (!activeLessonId.value && lessons.value.length) {
    activeLessonId.value = lessons.value[0].id;
  }
});
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
