import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    host: true,
    allowedHosts: true,
    proxy: {
      "/health": "http://127.0.0.1:8000",
      "/analyze": "http://127.0.0.1:8000",
      "/heatmaps": "http://127.0.0.1:8000",
      "/api": "http://127.0.0.1:8000",
    },
  },
});
