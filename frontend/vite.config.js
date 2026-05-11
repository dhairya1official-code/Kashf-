import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: "127.0.0.1",
    proxy: {
      "/search": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/results": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/takedown": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
})
