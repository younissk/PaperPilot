import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 4321,
    host: true,
  },
  preview: {
    port: 4321,
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
