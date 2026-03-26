import axios from "axios";
import router from "../router";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"
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
    throw error;
  }
);

export default api;
