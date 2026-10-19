import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': `${import.meta.dirname}/src`,
    },
  },
  server: {
    port: 3000,
    host: true,
    // Bind mounts on Windows often miss fs events; polling keeps HMR in sync in Compose.
    watch: process.env.VITE_API_PROXY_TARGET
      ? { usePolling: true, interval: 1000 }
      : undefined,
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
        timeout: 300_000,
        proxyTimeout: 300_000,
      },
    },
  },
})
