import { safeRequest } from '$lib/api';
import { createServerApi } from '$lib/server-api';

export async function load({ fetch, params }) {
  const api = createServerApi(fetch);
  const containerResult = await safeRequest(api.getScanContainer(params.id));

  return {
    container: containerResult.ok ? containerResult.data : null,
    containerError: containerResult.ok
      ? null
      : containerResult.error.detail ?? containerResult.error.message
  };
}
