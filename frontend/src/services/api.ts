import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"
});

api.interceptors.response.use(
  response => response,
  error => {
    console.error("API error", error);
    throw error;
  }
);

export default api;
