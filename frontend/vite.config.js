import adapter from '@sveltejs/adapter-node';
import { sveltekit } from '@sveltejs/kit/vite';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vite';

const devApiTarget = process.env.INTERNAL_API_URL ?? 'http://localhost:8000';

export default defineConfig({
  cacheDir: '.vite-cache',
  plugins: [
    sveltekit({
      preprocess: vitePreprocess(),
      adapter: adapter()
    })
  ],
  server: {
    proxy: {
      '/api': {
        target: devApiTarget,
        changeOrigin: true
      },
      '/images': {
        target: devApiTarget,
        changeOrigin: true
      }
    }
  },
  ...(process.env.VITEST ? { resolve: { conditions: ['browser'] } } : {}),
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.js']
  }
});
