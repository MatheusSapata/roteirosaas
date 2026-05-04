import { computed, ref } from "vue";
import { defineStore } from "pinia";
import api from "../services/api";

export type LessonVideoType = "file" | "youtube" | "iframe";

export interface Lesson {
  id: number;
  moduleName: string;
  title: string;
  description: string;
  duration: string;
  level: string;
  videoType: LessonVideoType;
  videoUrl: string;
  thumbnail?: string;
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
}

interface ApiLesson {
  id: number;
  module_name?: string | null;
  title: string;
  description?: string | null;
  duration?: string | null;
  level?: string | null;
  video_type: LessonVideoType;
  video_url: string;
  thumbnail_url?: string | null;
}

const mapLesson = (data: ApiLesson): Lesson => ({
  id: data.id,
  moduleName: data.module_name || "",
  title: data.title,
  description: data.description || "",
  duration: data.duration || "",
  level: data.level || "",
  videoType: data.video_type,
  videoUrl: data.video_url,
  thumbnail: data.thumbnail_url || undefined
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
  thumbnail_base64: payload.thumbnailBase64 || undefined
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

  const sortedLessons = computed(() => [...lessons.value].sort((a, b) => b.id - a.id));

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
    deleteLesson,
    resetLessons
  };
});
