import { API_BASE_PATH, safeRequest } from '$lib/api';
import { createServerApi } from '$lib/server-api';

export async function load({ fetch, url }) {
  const api = createServerApi(fetch);

  const [health, rooms, labels] = await Promise.all([
    safeRequest(api.getHealth()),
    safeRequest(api.listRooms()),
    safeRequest(api.listLabels())
  ]);

  const diagnostics = [health, rooms, labels]
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
      labelCount: labels.ok ? labels.data.length : null,
      referenceDataReady: rooms.ok && labels.ok
    },
    diagnostics,
    health: health.ok ? health.data : null,
    rooms: rooms.ok ? rooms.data : [],
    labels: labels.ok ? labels.data : []
  };
}
