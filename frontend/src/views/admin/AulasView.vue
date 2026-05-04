<template>
  <div v-if="isBootstrappingLessons" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8 md:px-8">
    <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
  </div>
  <div v-else class="space-y-8 px-4 py-6 md:px-8">
    <section class="rounded-3xl bg-white/95 p-6 shadow-xl shadow-slate-200/70 dark:bg-[#202020] dark:text-white dark:shadow-none">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.4em] text-slate-500 dark:text-white/70">Trilha premium</p>
          <h1 class="mt-2 text-3xl font-bold text-slate-900 dark:text-white">Aulas</h1>
          <p class="mt-1 max-w-3xl text-sm text-slate-500 dark:text-slate-200">
            Aprofunde o uso do construtor de páginas com aulas curtas e diretas. Escolha uma lição, ative o player e pratique acompanhando o passo a passo.
          </p>
        </div>
        <div class="rounded-2xl border border-slate-200/80 p-4 text-sm text-slate-600 shadow-sm dark:border-[#363636] dark:bg-[#101010] dark:text-white">
          <p class="font-semibold text-slate-900 dark:text-white">Progresso</p>
          <div class="mt-2 flex items-center gap-3">
            <div class="h-2 flex-1 overflow-hidden rounded-full bg-slate-200/80 dark:bg-[#1f1f1f]">
              <div class="h-full rounded-full bg-emerald-500 transition-all duration-500" :style="{ width: `${progressPercent}%` }"></div>
            </div>
            <span class="font-semibold text-slate-900 dark:text-white">{{ progressPercent }}%</span>
          </div>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-300">
            {{ completedLessons.length }} de {{ lessons.length }} aulas concluídas
          </p>
        </div>
      </div>
    </section>

    <section class="grid items-start gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
      <div class="space-y-4 rounded-3xl bg-white p-4 shadow-xl shadow-slate-200/70 lg:p-6 dark:bg-[#202020] dark:shadow-none">
        <div class="relative overflow-hidden rounded-2xl bg-[#05070F]">
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
            class="flex aspect-video w-full items-center justify-center rounded-2xl bg-[#05070F] px-6 text-center text-sm font-semibold text-slate-200"
          >
            {{ lessonsLoading ? "Carregando aulas..." : "Nenhuma aula disponível no momento." }}
          </div>
        </div>

        <div v-if="activeLesson" class="space-y-4 rounded-2xl bg-slate-50/70 p-5 dark:bg-[#181818]">
          <div class="flex flex-wrap items-center gap-3 text-xs font-semibold uppercase tracking-[0.25em] text-slate-500 dark:text-slate-300">
            <span class="rounded-full bg-slate-200/60 px-3 py-1 text-[0.65rem] text-slate-700 dark:bg-white/10 dark:text-white">
              {{ activeLesson.moduleName || "Geral" }}
            </span>
            <span class="text-slate-400">&bull;</span>
            <span>{{ activeLesson.level || "Aula" }}</span>
            <span class="text-slate-400">&bull;</span>
            <span>{{ activeLesson.duration || "Tempo livre" }}</span>
          </div>
          <h2 class="text-2xl font-bold text-slate-900 dark:text-white">{{ activeLesson.title }}</h2>
          <p class="text-sm text-slate-600 dark:text-slate-300">{{ activeLesson.description }}</p>
        </div>
      </div>

      <aside class="space-y-4 rounded-3xl bg-white p-4 shadow-xl shadow-slate-200/70 dark:bg-[#202020] dark:shadow-none">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-[0.4em] text-slate-500 dark:text-white/70">Módulos</p>
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Selecione a aula</h3>
          </div>
          <span class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
            {{ moduleGroups.length }} módulos
          </span>
        </div>

        <p
          v-if="!lessons.length"
          class="rounded-2xl border border-dashed border-slate-200 px-3 py-6 text-center text-sm text-slate-500 dark:border-[#363636] dark:text-slate-300"
        >
          {{ lessonsLoading ? "Carregando aulas..." : "Nenhuma aula cadastrada ainda." }}
        </p>

        <div v-else class="space-y-3">
          <section
            v-for="group in moduleGroups"
            :key="group.key"
            class="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50/70 dark:border-[#363636] dark:bg-[#181818]"
          >
            <button
              type="button"
              class="flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition hover:bg-slate-100/80 dark:hover:bg-white/5"
              @click="toggleModule(group.key)"
            >
              <div>
                <p class="text-sm font-semibold text-slate-900 dark:text-white">{{ group.label }}</p>
                <p class="mt-0.5 text-xs text-slate-500 dark:text-slate-300">{{ group.lessons.length }} aulas</p>
              </div>
              <svg
                viewBox="0 0 24 24"
                class="h-4 w-4 flex-shrink-0 text-slate-500 transition-transform dark:text-slate-300"
                :class="isModuleExpanded(group.key) ? 'rotate-180' : ''"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="m6 9 6 6 6-6" />
              </svg>
            </button>

            <ul v-if="isModuleExpanded(group.key)" class="space-y-3 border-t border-slate-200 p-3 dark:border-[#303030]">
              <li v-for="lesson in group.lessons" :key="lesson.id">
                <button
                  type="button"
                  class="w-full rounded-2xl border p-3 text-left transition hover:-translate-y-0.5 hover:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-brand dark:text-white"
                  :class="[
                    activeLessonId === lesson.id
                      ? 'border-brand/40 bg-brand/5 shadow-lg shadow-brand/20 dark:bg-brand/10'
                      : 'border-slate-200 bg-white shadow-sm dark:border-[#363636] dark:bg-[#101010]'
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
                    <div class="min-w-0 flex-1">
                      <div class="flex items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-300">
                        <span>{{ lesson.duration || "—" }}</span>
                        <span v-if="completedLessons.includes(lesson.id)" class="text-emerald-500">Concluída</span>
                      </div>
                      <p class="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{{ lesson.title }}</p>
                      <p class="mt-1 text-xs text-slate-500 line-clamp-2 dark:text-slate-300">
                        {{ lesson.description }}
                      </p>
                    </div>
                  </div>
                </button>
              </li>
            </ul>
          </section>
        </div>
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
const isBootstrappingLessons = ref(true);

const activeLessonId = ref<number | null>(null);
const completedLessons = ref<number[]>([]);
const expandedModules = ref<string[]>([]);

const moduleGroups = computed(() => {
  const groups = new Map<string, { key: string; label: string; lessons: typeof lessons.value }>();

  lessons.value.forEach(lesson => {
    const label = (lesson.moduleName || "Geral").trim() || "Geral";
    const key = label.toLowerCase();
    if (!groups.has(key)) {
      groups.set(key, { key, label, lessons: [] as typeof lessons.value });
    }
    groups.get(key)!.lessons.push(lesson);
  });

  return Array.from(groups.values());
});

const ensureExpandedModules = () => {
  const validKeys = moduleGroups.value.map(group => group.key);
  expandedModules.value = expandedModules.value.filter(key => validKeys.includes(key));

  if (!expandedModules.value.length && moduleGroups.value.length) {
    expandedModules.value = [moduleGroups.value[0].key];
  }
};

const isModuleExpanded = (key: string) => expandedModules.value.includes(key);

const toggleModule = (key: string) => {
  if (isModuleExpanded(key)) {
    expandedModules.value = expandedModules.value.filter(item => item !== key);
    if (!expandedModules.value.length) {
      expandedModules.value = [key];
    }
    return;
  }
  expandedModules.value = [...expandedModules.value, key];
};

const expandModuleForLesson = (lessonId: number | null) => {
  if (!lessonId) return;
  const group = moduleGroups.value.find(item => item.lessons.some(lesson => lesson.id === lessonId));
  if (!group) return;
  if (!expandedModules.value.includes(group.key)) {
    expandedModules.value = [...expandedModules.value, group.key];
  }
};

watch(
  lessons,
  newLessons => {
    if (!newLessons.length) {
      activeLessonId.value = null;
      expandedModules.value = [];
      return;
    }
    if (!newLessons.some(lesson => lesson.id === activeLessonId.value)) {
      activeLessonId.value = newLessons[0].id;
    }
    ensureExpandedModules();
    expandModuleForLesson(activeLessonId.value);
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
  expandModuleForLesson(lessonId);
  if (!completedLessons.value.includes(lessonId)) {
    completedLessons.value.push(lessonId);
  }
};

onMounted(async () => {
  try {
    await lessonsStore.ensureLessons();
    if (!activeLessonId.value && lessons.value.length) {
      activeLessonId.value = lessons.value[0].id;
    }
    ensureExpandedModules();
    expandModuleForLesson(activeLessonId.value);
  } finally {
    isBootstrappingLessons.value = false;
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
