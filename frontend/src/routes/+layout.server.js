import { API_BASE_PATH, safeRequest } from '$lib/api';
import { createServerApi } from '$lib/server-api';

export async function load({ fetch, url }) {
  const api = createServerApi(fetch);

  const [health, rooms, tags] = await Promise.all([
    safeRequest(api.getHealth()),
    safeRequest(api.listRooms()),
    safeRequest(api.listTags())
  ]);

  const diagnostics = [health, rooms, tags]
    .filter((result) => !result.ok && result.error)
    .map((result) => result.error.detail ?? result.error.message);

  return {
    app: {
      origin: url.origin,
      apiBasePath: API_BASE_PATH
    },
    bootstrap: {
      apiOnline: health.ok && health.data?.status === 'ok',
      roomCount: rooms.ok ? rooms.data.length : null,
      tagCount: tags.ok ? tags.data.length : null,
      referenceDataReady: rooms.ok && tags.ok
    },
    diagnostics,
    health: health.ok ? health.data : null,
    rooms: rooms.ok ? rooms.data : [],
    tags: tags.ok ? tags.data : []
  };
}
