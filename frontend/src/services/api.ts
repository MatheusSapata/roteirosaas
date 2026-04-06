import axios from "axios";
import router from "../router";
import { API_BASE_URL } from "../utils/apiBase";

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
    throw error;
  }
);

export default api;
