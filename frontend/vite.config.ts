import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 5173,
    proxy: {
      '/contracts': 'http://localhost:8000',
      '/systems': 'http://localhost:8000',
      '/mesh': 'http://localhost:8000',
      '/webhooks': 'http://localhost:8000',
      '/events': 'http://localhost:8000',
      '/audit': 'http://localhost:8000',
      '/reviews': 'http://localhost:8000',
      '/memory': 'http://localhost:8000',
      '/dashboard': 'http://localhost:8000',
      '/automations': 'http://localhost:8000',
      '/demo': 'http://localhost:8000',
    }
  }
})
