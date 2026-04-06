import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // Base path — must be '/' so all asset references in index.html are absolute.
  // FastAPI mounts /assets from backend/static/assets, so this aligns perfectly.
  base: '/',
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Output goes directly into backend/static/ so FastAPI can serve it.
    // 'emptyOutDir: true' clears stale assets on each build.
    outDir: '../backend/static',
    emptyOutDir: true,
  },
});
