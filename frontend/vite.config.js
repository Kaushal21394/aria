import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy /api/* → FastAPI on :8000 so we avoid CORS in development.
// Think of this like nginx reverse proxy but only for local dev.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
