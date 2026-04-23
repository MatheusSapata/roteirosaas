import { defineStore } from "pinia";
import { ref } from "vue";
import api from "../services/api";
import router from "../router";

type RetryableRequestConfig = {
  _retry?: boolean;
  headers?: Record<string, string>;
  url?: string;
};

interface User {
  id: number;
  email: string;
  name: string;
  cpf?: string;
  cnpj?: string;
  whatsapp?: string;
  address_street?: string | null;
  address_number?: string | null;
  address_complement?: string | null;
  address_neighborhood?: string | null;
  address_city?: string | null;
  address_state?: string | null;
  address_zipcode?: string | null;
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
  trial_warn_3days_ack?: boolean;
  trial_warn_1day_ack?: boolean;
  trial_blocked?: boolean;
}

const REFRESH_KEY = "refresh_token";
let responseInterceptorId: number | null = null;

const parseJwt = (token: string) => {
  try {
    const base64 = token.split(".")[1];
    if (!base64) return null;
    const decoded = atob(base64.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
};

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(typeof window !== "undefined" ? localStorage.getItem("token") : null);
  const refreshToken = ref<string | null>(typeof window !== "undefined" ? localStorage.getItem(REFRESH_KEY) : null);
  const user = ref<User | null>(null);
  const isHydrating = ref(Boolean(token.value));
  let refreshTimeout: number | null = null;
  let refreshing: Promise<void> | null = null;
  let hydrating: Promise<void> | null = null;

  const persistToken = (value: string | null) => {
    if (typeof window === "undefined") return;
    if (value) {
      localStorage.setItem("token", value);
    } else {
      localStorage.removeItem("token");
    }
  };

  const persistRefreshToken = (value: string | null) => {
    if (typeof window === "undefined") return;
    if (value) {
      localStorage.setItem(REFRESH_KEY, value);
    } else {
      localStorage.removeItem(REFRESH_KEY);
    }
  };

  const clearRefreshTimer = () => {
    if (refreshTimeout) {
      clearTimeout(refreshTimeout);
      refreshTimeout = null;
    }
  };

  const scheduleRefresh = () => {
    clearRefreshTimer();
    if (typeof window === "undefined") return;
    if (!token.value || !refreshToken.value) return;
    const payload = parseJwt(token.value);
    const expMs = payload?.exp ? payload.exp * 1000 : null;
    if (!expMs) return;
    const offset = 2 * 60 * 1000; // 2 minutos antes
    const delay = expMs - Date.now() - offset;
    if (delay <= 0) {
      refreshAccessToken().catch(() => {});
      return;
    }
    refreshTimeout = window.setTimeout(() => {
      refreshAccessToken().catch(() => {});
    }, delay);
  };

  const setAccessToken = (value: string | null) => {
    token.value = value;
    if (value) {
      api.defaults.headers.common.Authorization = `Bearer ${value}`;
    } else {
      delete api.defaults.headers.common.Authorization;
    }
    persistToken(value);
    if (value) {
      scheduleRefresh();
    } else {
      clearRefreshTimer();
    }
  };

  const setRefreshToken = (value: string | null) => {
    refreshToken.value = value;
    persistRefreshToken(value);
  };

  const setTokens = (access: string | null, refresh?: string | null) => {
    setAccessToken(access);
    if (typeof refresh !== "undefined") {
      setRefreshToken(refresh);
    }
  };

  const refreshAccessToken = async () => {
    if (!refreshToken.value) {
      logout();
      throw new Error("Refresh token indisponível");
    }
    if (!refreshing) {
      refreshing = (async () => {
        try {
          const res = await api.post("/auth/refresh", { refresh_token: refreshToken.value });
          setTokens(res.data.access_token, res.data.refresh_token);
        } catch (err) {
          setTokens(null, null);
          throw err;
        } finally {
          refreshing = null;
        }
      })();
    }
    return refreshing;
  };

  const fetchProfile = async () => {
    if (!token.value) return;
    const res = await api.get<User>("/auth/me");
    user.value = res.data;
  };

  const ensureHydrated = async () => {
    if (!token.value) {
      isHydrating.value = false;
      return;
    }
    if (!hydrating) {
      isHydrating.value = true;
      hydrating = (async () => {
        try {
          await fetchProfile();
        } finally {
          isHydrating.value = false;
          hydrating = null;
        }
      })();
    }
    return hydrating;
  };

  const logout = () => {
    clearRefreshTimer();
    setTokens(null, null);
    user.value = null;
    isHydrating.value = false;
    hydrating = null;
  };

  if (responseInterceptorId === null) {
    responseInterceptorId = api.interceptors.response.use(
      response => response,
      async error => {
        const status = error?.response?.status;
        const originalRequest = error?.config as RetryableRequestConfig | undefined;
        const isRefreshRequest = (originalRequest?.url || "").includes("/auth/refresh");

        if (status === 401 && !isRefreshRequest && originalRequest && !originalRequest._retry && refreshToken.value) {
          originalRequest._retry = true;
          try {
            await refreshAccessToken();
            originalRequest.headers = originalRequest.headers || {};
            if (token.value) {
              originalRequest.headers.Authorization = `Bearer ${token.value}`;
            }
            return api(originalRequest);
          } catch {
            logout();
          }
        } else if (status === 401) {
          logout();
        }

        if (status === 401) {
          const current = router.currentRoute.value;
          if (current.name !== "login") {
            router.push({ name: "login", query: { redirect: current.fullPath } }).catch(() => {});
          }
        }
        return Promise.reject(error);
      }
    );
  }

  if (token.value) {
    api.defaults.headers.common.Authorization = `Bearer ${token.value}`;
    scheduleRefresh();
    ensureHydrated().catch(() => logout());
  } else {
    isHydrating.value = false;
  }

  return { token, user, refreshToken, isHydrating, setTokens, fetchProfile, ensureHydrated, logout, refreshAccessToken };
});
