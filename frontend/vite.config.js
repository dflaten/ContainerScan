import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  cacheDir: '.vite-cache',
  plugins: [sveltekit()],
  resolve: {
    conditions: process.env.VITEST ? ['browser'] : []
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.js']
  }
});
