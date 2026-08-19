import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@site': fileURLToPath(new URL('../src', import.meta.url)),
      'marked': fileURLToPath(new URL('./node_modules/marked/lib/marked.esm.js', import.meta.url)),
      'dompurify': fileURLToPath(new URL('./node_modules/dompurify/dist/purify.es.mjs', import.meta.url)),
    },
  },
  publicDir: fileURLToPath(new URL('../public', import.meta.url)),
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: '0.0.0.0',
    watch: {
      ignored: [
        '**/src-tauri/target/**',
        '**/node_modules/**',
      ],
    },
  },
  envPrefix: ['VITE_', 'TAURI_'],
  build: {
    target: 'esnext',
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
    sourcemap: !!process.env.TAURI_DEBUG,
  },
})
