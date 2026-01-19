import { defineStore } from "pinia";
import { ref } from "vue";
import api from "../services/api";

interface User {
  id: number;
  email: string;
  name: string;
  cpf?: string;
  whatsapp?: string;
  is_active: boolean;
  is_superuser: boolean;
  plan: string;
  subscription_id?: number;
  trial_plan?: string | null;
  trial_original_plan?: string | null;
  trial_started_at?: string | null;
  trial_ends_at?: string | null;
  trial_ack_start?: boolean;
  trial_ack_end?: boolean;
}

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem("token"));
  const user = ref<User | null>(null);

  const setToken = (value: string | null) => {
    token.value = value;
    if (value) {
      localStorage.setItem("token", value);
      api.defaults.headers.common.Authorization = `Bearer ${value}`;
    } else {
      localStorage.removeItem("token");
      delete api.defaults.headers.common.Authorization;
    }
  };

  const fetchProfile = async () => {
    if (!token.value) return;
    const res = await api.get<User>("/auth/me");
    user.value = res.data;
  };

  const logout = () => {
    setToken(null);
    user.value = null;
  };

  if (token.value) {
    api.defaults.headers.common.Authorization = `Bearer ${token.value}`;
    fetchProfile().catch(() => logout());
  }

  return { token, user, setToken, fetchProfile, logout };
});
