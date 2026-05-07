import { env } from '$env/dynamic/private';

import { API_BASE_PATH, createApi } from '$lib/api';

export function createServerApi(fetchFn) {
  const internalApiBaseUrl = env.INTERNAL_API_URL ?? 'http://backend:8000';
  return createApi(fetchFn, { basePath: `${internalApiBaseUrl}${API_BASE_PATH}` });
}
