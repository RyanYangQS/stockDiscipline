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
        target: "http://127.0.0.1:8080",
        changeOrigin: true,
        configure: (proxy) => {
          // Fallback to other ports if main port fails
          proxy.on("error", () => {
            console.log("Backend at 8080 not available, trying 8081...");
          });
        }
      }
    }
  }
});

