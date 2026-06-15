import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
  server: {
    host: true,
    port: 5180,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true
      }
    }
  },
})
