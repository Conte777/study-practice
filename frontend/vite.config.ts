import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Match CORS_ORIGINS / compose front port.
  server: { port: 8080, host: true },
})
