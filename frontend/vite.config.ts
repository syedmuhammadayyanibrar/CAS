import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const spaBypass = {
  target: 'http://localhost:8000',
  bypass(req: any) {
    if (req.headers?.accept?.includes('text/html')) {
      return '/index.html'
    }
  },
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/webhooks': 'http://localhost:8000',
      '/contracts': spaBypass,
      '/systems': spaBypass,
      '/mesh': spaBypass,
      '/events': spaBypass,
      '/audit': spaBypass,
      '/reviews': spaBypass,
      '/memory': spaBypass,
      '/dashboard': spaBypass,
      '/automations': spaBypass,
      '/demo': spaBypass,
      '/evaluation': spaBypass,
    }
  }
})
