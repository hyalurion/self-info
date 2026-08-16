import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('.', import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    // Keep existing dist/ contents (the deployed site) and just add/overwrite
    // the preview entry. Avoids emptying dist/ which can hit locked files.
    emptyOutDir: false,
    rollupOptions: {
      input: {
        index: resolve(root, 'index.html'),
        // Extra entry used by json-md-editor's live preview (renders editor
        // data through the same Vue components as the real site).
        preview: resolve(root, 'preview.html'),
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: false,
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    strictPort: false,
  },
})
