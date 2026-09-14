import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // In dev (`npm run dev`), proxy API calls to the FastAPI backend
    // running separately on :8000. In production the backend serves
    // this app's built files itself, so no proxy is needed there.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
