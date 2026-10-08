<template>
  <div v-if="isBootstrappingLessons" class="flex min-h-[60vh] w-full items-center justify-center px-4 py-8 md:px-8">
    <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand"></div>
  </div>
  <div v-else class="lessons-view">
    <div class="lv-head">
      <div class="min-w-0">
        <p class="lv-eyebrow">Aprender</p>
        <h1 class="lv-title">Aulas</h1>
        <p class="lv-sub">Vídeos curtos para montar páginas que vendem e organizar seus leads.</p>
      </div>
      <div v-if="lessons.length" class="lv-progress">
        <div>
          <p class="lv-progress-k">Seu progresso</p>
          <p class="lv-progress-v">{{ completedCount }} de {{ lessons.length }} aulas</p>
        </div>
        <div class="lv-bar"><i :style="{ width: `${progressPercent}%` }"></i></div>
        <span class="lv-progress-pill">{{ progressPercent }}%</span>
      </div>
    </div>

    <div class="lv-grid">
      <section class="lv-card lv-player-card">
        <div class="lv-player">
          <template v-if="activeLesson">
            <template v-if="playing">
              <iframe
                v-if="activeLesson.videoType !== 'file'"
                :key="`embed-${activeLesson.id}`"
                class="lv-media"
                :src="embedUrl(activeLesson.videoUrl)"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
              ></iframe>
              <video
                v-else
                :key="`file-${activeLesson.id}`"
                controls
                autoplay
                controlslist="nodownload"
                playsinline
                preload="metadata"
                class="lv-media"
                :poster="activeLesson.thumbnail"
              >
                <source :src="activeLesson.videoUrl" type="video/mp4" />
                Seu navegador não suporta o player de vídeo.
              </video>
            </template>
            <button
              v-else
              type="button"
              class="lv-poster"
              :style="activeLesson.thumbnail ? { backgroundImage: `url(${activeLesson.thumbnail})` } : undefined"
              :aria-label="`Assistir ${activeLesson.title}`"
              @click="playing = true"
            >
              <span class="lv-play" aria-hidden="true">
                <PlayIcon fill="currentColor" aria-hidden="true" />
              </span>
              <span class="lv-poster-text">
                <small>{{ activeModuleLabel }} · aula {{ activeLessonNumber }}</small>
                <b>{{ activeLesson.title }}</b>
              </span>
            </button>
          </template>
          <div v-else class="lv-player-empty">
            {{ lessonsLoading ? "Carregando aulas..." : "Nenhuma aula disponível no momento." }}
          </div>
        </div>

        <div v-if="activeLesson" class="lv-info">
          <div class="min-w-0 flex-1">
            <div class="lv-tags">
              <span class="lv-tag is-info">{{ activeModuleLabel }}</span>
              <span v-if="activeLesson.level" class="lv-tag">{{ activeLesson.level }}</span>
              <span v-if="activeLesson.duration" class="lv-tag">{{ activeLesson.duration }}</span>
            </div>
            <h2 class="lv-lesson-title">{{ activeLesson.title }}</h2>
            <p class="lv-lesson-text">{{ activeLesson.description }}</p>
          </div>
          <div class="lv-actions">
            <button
              type="button"
              :class="isCompleted(activeLesson.id) ? 'lv-btn-ghost' : 'lv-btn-primary'"
              :aria-pressed="isCompleted(activeLesson.id)"
              @click="toggleLessonCompleted(activeLesson.id, !isCompleted(activeLesson.id))"
            >
              <CheckIcon aria-hidden="true" />
              {{ isCompleted(activeLesson.id) ? "Concluída" : "Marcar como concluída" }}
            </button>
            <button v-if="nextLesson" type="button" class="lv-btn-ghost" @click="selectLesson(nextLesson.id)">Próxima aula</button>
          </div>
        </div>
      </section>

      <aside class="lv-card lv-modules">
        <header>
          <h2>Módulos</h2>
          <p>{{ moduleGroups.length }} {{ moduleGroups.length === 1 ? "módulo" : "módulos" }} · {{ lessons.length }} {{ lessons.length === 1 ? "aula" : "aulas" }}</p>
        </header>

        <p v-if="!lessons.length" class="lv-empty">
          {{ lessonsLoading ? "Carregando aulas..." : "Nenhuma aula cadastrada ainda." }}
        </p>

        <section v-for="(group, groupIndex) in moduleGroups" :key="group.key" class="lv-module">
          <button type="button" class="lv-module-head" :aria-expanded="isModuleExpanded(group.key)" @click="toggleModule(group.key)">
            <span class="lv-num" :class="moduleTone(groupIndex)">{{ groupIndex + 1 }}</span>
            <span class="min-w-0 flex-1">
              <b>{{ group.label }}</b>
              <small>{{ completedIn(group) }} de {{ group.lessons.length }} {{ group.lessons.length === 1 ? "concluída" : "concluídas" }}</small>
            </span>
            <ChevronDownIcon class="lv-chev" :class="{ open: isModuleExpanded(group.key) }" aria-hidden="true" />
          </button>

          <ul v-if="isModuleExpanded(group.key)" class="lv-lessons">
            <li v-for="lesson in group.lessons" :key="lesson.id">
              <button
                type="button"
                class="lv-lesson"
                :class="{ on: activeLessonId === lesson.id }"
                @click="selectLesson(lesson.id)"
              >
                <span
                  class="lv-mark"
                  :class="activeLessonId === lesson.id ? 'is-playing' : isCompleted(lesson.id) ? 'is-done' : ''"
                  aria-hidden="true"
                >
                  <PlayIcon v-if="activeLessonId === lesson.id" fill="currentColor" aria-hidden="true" />
                  <CheckIcon v-else-if="isCompleted(lesson.id)" aria-hidden="true" />
                  <template v-else>{{ lessonNumber(lesson.id) }}</template>
                </span>
                <span class="lv-lesson-name">{{ lesson.title }}</span>
                <span v-if="lesson.duration" class="lv-lesson-time">{{ lesson.duration }}</span>
              </button>
            </li>
          </ul>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CheckIcon, ChevronDownIcon, PlayIcon } from "lucide-vue-next";
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
    return;
  }
  expandedModules.value = [...expandedModules.value, key];
};

const collapseAllModules = () => {
  expandedModules.value = [];
};

const expandAllModules = () => {
  expandedModules.value = moduleGroups.value.map(group => group.key);
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
      activeLessonId.value = newLessons.find(lesson => !completedLessons.value.includes(lesson.id))?.id ?? newLessons[0].id;
    }
    ensureExpandedModules();
    expandModuleForLesson(activeLessonId.value);
  },
  { immediate: true }
);

const activeLesson = computed(() => lessons.value.find(lesson => lesson.id === activeLessonId.value) || null);

const completedCount = computed(() => lessons.value.filter(lesson => completedLessons.value.includes(lesson.id)).length);
const progressPercent = computed(() => {
  if (!lessons.value.length) return 0;
  return Math.round((completedCount.value / lessons.value.length) * 100);
});

// ===== Visual da proposta =====
const playing = ref(false);
watch(activeLessonId, () => {
  playing.value = false;
});
const isCompleted = (lessonId: number) => completedLessons.value.includes(lessonId);
const completedIn = (group: { lessons: typeof lessons.value }) => group.lessons.filter(lesson => isCompleted(lesson.id)).length;
const orderedLessons = computed(() => moduleGroups.value.flatMap(group => group.lessons));
const lessonNumber = (lessonId: number) => orderedLessons.value.findIndex(lesson => lesson.id === lessonId) + 1;
const activeLessonNumber = computed(() => (activeLessonId.value ? lessonNumber(activeLessonId.value) : 0));
const activeModuleLabel = computed(() => (activeLesson.value?.moduleName || "Geral").trim() || "Geral");
const nextLesson = computed(() => {
  const index = orderedLessons.value.findIndex(lesson => lesson.id === activeLessonId.value);
  return index >= 0 ? orderedLessons.value[index + 1] || null : null;
});
const moduleTones = ["tone-success", "tone-info", "tone-violet", "tone-warning"];
const moduleTone = (index: number) => moduleTones[index % moduleTones.length];
// Ao clicar no play, o vídeo já começa tocando.
const embedUrl = (url?: string | null) => {
  if (!url) return "";
  try {
    const parsed = new URL(url);
    parsed.searchParams.set("autoplay", "1");
    return parsed.toString();
  } catch {
    return url;
  }
};

// O progresso fica guardado neste navegador.
const progressKey = "roteiro-aulas-concluidas";
try {
  const stored = JSON.parse(window.localStorage.getItem(progressKey) || "[]");
  if (Array.isArray(stored)) completedLessons.value = stored.filter((id: unknown) => typeof id === "number");
} catch {
  // Sem acesso ao armazenamento: o progresso vale só nesta visita.
}
watch(completedLessons, value => {
  try {
    window.localStorage.setItem(progressKey, JSON.stringify(value));
  } catch {
    // ignora
  }
});

const selectLesson = (lessonId: number) => {
  activeLessonId.value = lessonId;
  expandModuleForLesson(lessonId);
};

const toggleLessonCompleted = (lessonId: number, completed: boolean) => {
  if (completed) {
    if (!completedLessons.value.includes(lessonId)) {
      completedLessons.value = [...completedLessons.value, lessonId];
    }
    return;
  }
  completedLessons.value = completedLessons.value.filter(id => id !== lessonId);
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
.lessons-view { color: var(--foreground); }
.lessons-view :deep(.bg-white),
.lessons-view :deep(.bg-white\/95) { background: var(--card) !important; }
.lessons-view :deep(.bg-slate-50),
.lessons-view :deep(.bg-slate-100),
.lessons-view :deep(.bg-slate-200\/80) { background: var(--muted) !important; }
.lessons-view :deep(.border-slate-200),
.lessons-view :deep(.border-slate-200\/80) { border-color: var(--border) !important; }
.lessons-view :deep(.text-slate-900),
.lessons-view :deep(.text-slate-700),
.lessons-view :deep(.text-slate-600) { color: var(--foreground) !important; }
.lessons-view :deep(.text-slate-500),
.lessons-view :deep(.text-slate-400) { color: var(--muted-foreground) !important; }
.lessons-view :deep(button:hover) { border-color: color-mix(in srgb, var(--primary) 30%, var(--border)); }
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Redesign: aulas */
.lessons-view { display: flex; flex-direction: column; gap: 16px; padding: 0 0 32px; }
.lv-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
.lv-eyebrow { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: color-mix(in srgb, var(--muted-foreground) 80%, transparent); }
.lv-title { margin-top: 4px; font-family: var(--font-display); font-size: 30px; line-height: 38px; font-weight: 600; color: var(--foreground); }
.lv-sub { margin-top: 4px; font-size: 14px; color: var(--muted-foreground); }
.lv-progress { display: flex; align-items: center; gap: 14px; border-radius: 20px; background: var(--card); padding: 12px 16px; box-shadow: var(--shadow-card); }
.lv-progress-k { font-size: 12.5px; color: var(--muted-foreground); }
.lv-progress-v { font-family: var(--font-display); font-size: 18px; font-weight: 600; color: var(--foreground); white-space: nowrap; }
.lv-bar { width: 160px; height: 6px; overflow: hidden; border-radius: 999px; background: var(--muted); }
.lv-bar i { display: block; height: 100%; border-radius: 999px; background: var(--primary); transition: width 0.4s; }
.lv-progress-pill { border-radius: 999px; background: var(--status-success); padding: 1px 8px; font-size: 11.5px; font-weight: 600; color: var(--status-success-foreground); }
.lv-grid { display: grid; grid-template-columns: minmax(0, 1fr) 412px; align-items: start; gap: 16px; }
.lv-card { border-radius: 20px; background: var(--card); box-shadow: var(--shadow-card); }
.lv-player-card { padding: 16px; }
.lv-player { overflow: hidden; border-radius: 16px; background: #0b1512; }
.lv-media { display: block; width: 100%; aspect-ratio: 16 / 9; border: 0; background: #000; }
.lv-poster { position: relative; display: grid; width: 100%; aspect-ratio: 16 / 9; place-items: center; background: linear-gradient(135deg, #0f1f1a, #0b1512 55%, #102a22); background-position: center; background-size: cover; }
.lv-poster::after { content: ""; position: absolute; inset: 0; background: linear-gradient(to top, rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.15) 55%, rgba(0, 0, 0, 0.25)); }
.lv-play { position: relative; z-index: 1; display: grid; place-items: center; width: 72px; height: 72px; border-radius: 999px; background: #1fe3a0; color: #062016; box-shadow: 0 0 0 10px rgba(31, 227, 160, 0.16); transition: transform 0.15s; }
.lv-poster:hover .lv-play { transform: scale(1.05); }
.lv-play svg { width: 26px; height: 26px; margin-left: 3px; }
.lv-poster-text { position: absolute; right: 20px; bottom: 16px; left: 20px; z-index: 1; text-align: left; color: #fff; }
.lv-poster-text small { display: block; font-size: 13px; opacity: 0.85; }
.lv-poster-text b { display: block; font-family: var(--font-display); font-size: 20px; font-weight: 600; }
.lv-player-empty { display: grid; aspect-ratio: 16 / 9; place-items: center; padding: 24px; font-size: 14px; font-weight: 600; color: rgba(255, 255, 255, 0.8); }
.lv-info { display: flex; align-items: flex-start; gap: 16px; padding: 16px 4px 4px; }
.lv-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.lv-tag { border-radius: 999px; background: var(--muted); padding: 1px 9px; font-size: 11.5px; font-weight: 600; color: var(--foreground); }
.lv-tag.is-info { background: var(--status-info); color: var(--status-info-foreground); }
.lv-lesson-title { margin-top: 8px; font-family: var(--font-display); font-size: 22px; font-weight: 600; color: var(--foreground); }
.lv-lesson-text { margin-top: 2px; font-size: 14px; color: var(--muted-foreground); }
.lv-actions { display: flex; flex-shrink: 0; flex-direction: column; align-items: flex-end; gap: 8px; }
.lv-btn-primary, .lv-btn-ghost { display: inline-flex; align-items: center; gap: 8px; height: 40px; padding: 0 18px; border-radius: 999px; font-size: 13.5px; font-weight: 600; white-space: nowrap; }
.lv-btn-primary { background: var(--primary); color: var(--primary-foreground); }
.lv-btn-primary:hover { background: color-mix(in srgb, var(--primary) 88%, black); }
.lv-btn-ghost { background: var(--muted); color: var(--foreground); }
.lv-btn-ghost:hover { background: var(--accent); color: var(--accent-foreground); }
.lv-btn-primary svg, .lv-btn-ghost svg { width: 15px; height: 15px; }
.lv-modules { padding: 18px 14px 14px; }
.lv-modules header { padding: 0 6px 6px; }
.lv-modules header h2 { font-family: var(--font-display); font-size: 17px; font-weight: 600; color: var(--foreground); }
.lv-modules header p { font-size: 13px; color: var(--muted-foreground); }
.lv-empty { padding: 16px 6px; font-size: 13.5px; color: var(--muted-foreground); }
.lv-module-head { display: flex; width: 100%; align-items: center; gap: 12px; border-radius: 14px; padding: 8px 6px; text-align: left; }
.lv-module-head:hover { background: color-mix(in srgb, var(--muted) 60%, transparent); }
.lv-module-head b { display: block; font-size: 14.5px; font-weight: 600; color: var(--foreground); }
.lv-module-head small { display: block; font-size: 12.5px; color: var(--muted-foreground); }
.lv-num { display: grid; place-items: center; width: 32px; height: 32px; flex-shrink: 0; border-radius: 999px; font-size: 13px; font-weight: 600; }
.tone-success { background: var(--status-success); color: var(--status-success-foreground); }
.tone-info { background: var(--status-info); color: var(--status-info-foreground); }
.tone-violet { background: var(--status-violet); color: var(--status-violet-foreground); }
.tone-warning { background: var(--status-warning); color: var(--status-warning-foreground); }
.lv-chev { width: 16px; height: 16px; flex-shrink: 0; color: var(--muted-foreground); transition: transform 0.18s; }
.lv-chev.open { transform: rotate(180deg); }
.lv-lessons { display: flex; flex-direction: column; gap: 2px; padding: 2px 0 6px; }
.lv-lesson { display: flex; width: 100%; align-items: center; gap: 12px; border-radius: 14px; padding: 9px 10px; text-align: left; }
.lv-lesson:hover { background: color-mix(in srgb, var(--muted) 60%, transparent); }
.lv-lesson.on { background: var(--accent); }
.lv-mark { display: grid; place-items: center; width: 26px; height: 26px; flex-shrink: 0; border-radius: 999px; background: var(--muted); font-size: 12px; font-weight: 600; color: var(--muted-foreground); }
.lv-mark svg { width: 12px; height: 12px; }
.lv-mark.is-done { background: var(--status-success); color: var(--status-success-foreground); }
.lv-mark.is-playing { background: var(--primary); color: var(--primary-foreground); }
.lv-mark.is-playing svg { margin-left: 2px; }
.lv-lesson-name { min-width: 0; flex: 1; font-size: 13.5px; font-weight: 600; color: var(--foreground); }
.lv-lesson-time { flex-shrink: 0; font-size: 12px; color: var(--muted-foreground); }
@media (max-width: 1100px) { .lv-grid { grid-template-columns: 1fr; } }
@media (max-width: 640px) {
  .lv-head, .lv-info { flex-direction: column; align-items: stretch; }
  .lv-bar { flex: 1; width: auto; }
  .lv-actions { align-items: stretch; }
}
</style>
