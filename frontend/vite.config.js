import adapter from '@sveltejs/adapter-node';
import { sveltekit } from '@sveltejs/kit/vite';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vite';

export default defineConfig({
  cacheDir: '.vite-cache',
  plugins: [
    sveltekit({
      preprocess: vitePreprocess(),
      adapter: adapter()
    })
  ],
  ...(process.env.VITEST ? { resolve: { conditions: ['browser'] } } : {}),
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.js']
  }
});
