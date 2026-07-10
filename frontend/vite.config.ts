import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

function getBackendProxyTarget(): string {
  const fromEnv = process.env.BACKEND_PROXY_TARGET || process.env.VITE_BACKEND_PROXY_TARGET
  if (fromEnv) return fromEnv

  const portsFile = path.resolve(__dirname, '../.dev/ports.json')
  try {
    const data = JSON.parse(fs.readFileSync(portsFile, 'utf-8')) as {
      backend?: { url?: string }
    }
    if (data.backend?.url) return data.backend.url
  } catch {
    // fall through to default
  }

  return 'http://127.0.0.1:8005'
}

const backendProxyTarget = getBackendProxyTarget()

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    watch: {
      // Avoid ENOSPC (inotify watcher limit) on shared/remote Linux environments.
      usePolling: true,
      interval: 120,
      ignored: ['**/.git/**', '**/node_modules/**', '**/dist/**'],
    },
    proxy: {
      '/api': {
        target: backendProxyTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
