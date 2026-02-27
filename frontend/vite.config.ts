import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const devProxyTarget = process.env.VITE_DEV_API_PROXY ?? "http://localhost:8000";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: devProxyTarget,
        changeOrigin: true
      },
      "/uploads": {
        target: devProxyTarget,
        changeOrigin: true
      }
    }
  }
});
