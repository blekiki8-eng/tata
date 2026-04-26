import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/',                    // важливо для Railway
  build: {
    outDir: 'dist',             // більшість шаблонів використовують dist
  },
  server: {
    port: 3000
  }
})
