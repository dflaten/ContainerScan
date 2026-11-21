import { defineEnvVars } from '@sveltejs/kit/env';

export const variables = defineEnvVars({
  INTERNAL_API_URL: {
    description: 'Base URL the server-side code uses to reach the FastAPI backend.',
    schema: (value) => value ?? 'http://backend:8000'
  }
});
