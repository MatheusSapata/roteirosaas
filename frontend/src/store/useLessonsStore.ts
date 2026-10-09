import { computed, ref } from "vue";
import { defineStore } from "pinia";
import api from "../services/api";

export type LessonVideoType = "file" | "youtube" | "iframe";

export interface Lesson {
  id: number;
  moduleName: string;
  sortOrder: number;
  title: string;
  description: string;
  duration: string;
  level: string;
  videoType: LessonVideoType;
  videoUrl: string;
  thumbnail?: string;
  /** Artigo da Central de Ajuda que substitui a aula quando é mais novo que o vídeo. */
  helpArticle?: string;
  /** Quando o vídeo mudou pela última vez (AAAA-MM-DD…). */
  videoUpdatedAt?: string;
}

export interface LessonPayload {
  moduleName?: string;
  title: string;
  description?: string;
  duration?: string;
  level?: string;
  videoType: LessonVideoType;
  videoUrl: string;
  thumbnailUrl?: string;
  thumbnailBase64?: string;
  /** "" tira a ligação com o artigo. */
  helpArticle?: string;
}

interface ApiLesson {
  id: number;
  module_name?: string | null;
  sort_order?: number | null;
  title: string;
  description?: string | null;
  duration?: string | null;
  level?: string | null;
  video_type: LessonVideoType;
  video_url: string;
  thumbnail_url?: string | null;
  help_article?: string | null;
  video_updated_at?: string | null;
  updated_at?: string | null;
  created_at?: string | null;
}

const mapLesson = (data: ApiLesson): Lesson => ({
  id: data.id,
  moduleName: (data.module_name || "").trim(),
  sortOrder: data.sort_order ?? 0,
  title: data.title,
  description: data.description || "",
  duration: data.duration || "",
  level: data.level || "",
  videoType: data.video_type,
  videoUrl: data.video_url,
  thumbnail: data.thumbnail_url || undefined,
  helpArticle: data.help_article || undefined,
  videoUpdatedAt: data.video_updated_at || data.updated_at || data.created_at || undefined
});

const toApiPayload = (payload: LessonPayload) => ({
  module_name: payload.moduleName?.trim() || undefined,
  title: payload.title.trim(),
  description: payload.description?.trim() || undefined,
  duration: payload.duration?.trim() || undefined,
  level: payload.level?.trim() || undefined,
  video_type: payload.videoType,
  video_url: payload.videoUrl,
  thumbnail_url: payload.thumbnailUrl?.trim() || undefined,
  thumbnail_base64: payload.thumbnailBase64 || undefined,
  ...(payload.helpArticle !== undefined ? { help_article: payload.helpArticle.trim() || null } : {})
});

export const normalizeVideoInput = (input: string): { videoType: LessonVideoType; videoUrl: string } => {
  const trimmed = input.trim();
  if (!trimmed) {
    return { videoType: "file", videoUrl: "" };
  }

  if (trimmed.includes("<iframe")) {
    const match = trimmed.match(/src=["']([^"']+)["']/i);
    return { videoType: "iframe", videoUrl: match ? match[1] : "" };
  }

  const youtubeMatch = trimmed.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([A-Za-z0-9_\-]+)/i);
  if (youtubeMatch?.[1]) {
    return { videoType: "youtube", videoUrl: `https://www.youtube.com/embed/${youtubeMatch[1]}` };
  }

  return { videoType: trimmed.endsWith(".mp4") || trimmed.includes("http") ? "file" : "iframe", videoUrl: trimmed };
};

export const useLessonsStore = defineStore("lessons", () => {
  const lessons = ref<Lesson[]>([]);
  const loading = ref(false);
  const loaded = ref(false);

  const sortedLessons = computed(() =>
    [...lessons.value].sort((a, b) => {
      const moduleCompare = (a.moduleName || "").localeCompare(b.moduleName || "", "pt-BR", { sensitivity: "base" });
      if (moduleCompare !== 0) return moduleCompare;
      const orderCompare = (a.sortOrder ?? 0) - (b.sortOrder ?? 0);
      if (orderCompare !== 0) return orderCompare;
      return a.id - b.id;
    })
  );

  const fetchLessons = async () => {
    loading.value = true;
    try {
      const res = await api.get<ApiLesson[]>("/lessons");
      lessons.value = res.data.map(mapLesson);
      loaded.value = true;
    } finally {
      loading.value = false;
    }
  };

  const ensureLessons = async () => {
    if (!loaded.value && !loading.value) {
      await fetchLessons();
    }
  };

  const addLesson = async (payload: LessonPayload) => {
    const res = await api.post<ApiLesson>("/lessons", toApiPayload(payload));
    const lesson = mapLesson(res.data);
    lessons.value = [lesson, ...lessons.value];
    return lesson;
  };

  const updateLesson = async (id: number, payload: LessonPayload) => {
    const res = await api.put<ApiLesson>(`/lessons/${id}`, toApiPayload(payload));
    const updated = mapLesson(res.data);
    lessons.value = lessons.value.map(lesson => (lesson.id === id ? updated : lesson));
    return updated;
  };

  const reorderLessonsInModule = async (moduleName: string, lessonIds: number[]) => {
    const payload = {
      module_name: moduleName.trim() || null,
      lesson_ids: lessonIds
    };
    let res;
    try {
      res = await api.post<ApiLesson[]>("/lessons/reorder", payload);
    } catch (error: any) {
      if (error?.response?.status !== 405) {
        throw error;
      }
      res = await api.put<ApiLesson[]>("/lessons/reorder", payload);
    }
    lessons.value = res.data.map(mapLesson);
    loaded.value = true;
  };

  const deleteLesson = async (id: number) => {
    await api.delete(`/lessons/${id}`);
    lessons.value = lessons.value.filter(lesson => lesson.id !== id);
  };

  const resetLessons = async () => {
    const res = await api.post<ApiLesson[]>("/lessons/reset");
    lessons.value = res.data.map(mapLesson);
    loaded.value = true;
  };

  return {
    lessons,
    sortedLessons,
    loading,
    loaded,
    fetchLessons,
    ensureLessons,
    addLesson,
    updateLesson,
    reorderLessonsInModule,
    deleteLesson,
    resetLessons
  };
});
