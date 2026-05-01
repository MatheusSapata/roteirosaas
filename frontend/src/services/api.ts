import axios from "axios";
import router from "../router";
import { API_BASE_URL } from "../utils/apiBase";

export const API_PERMISSION_DENIED_EVENT = "app:permission-denied";

const api = axios.create({
  baseURL: API_BASE_URL
});

api.interceptors.request.use(config => {
  const currentRoute = router.currentRoute.value;
  if (currentRoute?.fullPath) {
    config.headers = config.headers || {};
    config.headers["X-Client-Path"] = currentRoute.fullPath;
  }
  return config;
});

api.interceptors.response.use(
  response => response,
  error => {
    console.error("API error", error);
    const status = error?.response?.status;
    const method = String(error?.config?.method || "get").toLowerCase();
    if (status === 403 && method !== "get" && typeof window !== "undefined") {
      const detail =
        error?.response?.data?.detail ||
        "Seu perfil não tem permissão para executar esta ação.";
      window.dispatchEvent(
        new CustomEvent(API_PERMISSION_DENIED_EVENT, {
          detail: { message: detail, status, method }
        })
      );
    }
    throw error;
  }
);

export default api;
