import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: "dist",
    emptyOutDir: true
  },
  server: {
    port: 5173,
    strictPort: false,  // Auto-find available port if 5173 is in use
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8081",
        changeOrigin: true
      }
    }
  }
});

