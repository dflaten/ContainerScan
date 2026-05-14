import { safeRequest } from '$lib/api';
import { createServerApi } from '$lib/server-api';

export async function load({ fetch, params, parent, url }) {
  const parentData = await parent();
  const api = createServerApi(fetch);
  const containerResult = await safeRequest(api.getContainer(params.id));

  return {
    container: containerResult.ok ? containerResult.data : null,
    containerError: containerResult.ok
      ? null
      : containerResult.error.detail ?? containerResult.error.message,
    tags: parentData.tags,
    rooms: parentData.rooms
  };
}
