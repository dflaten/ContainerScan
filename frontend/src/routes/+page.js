import { createApi, safeRequest } from '$lib/api';

function normalizeFilter(value) {
  if (value === null) {
    return '';
  }

  const normalized = value.trim();
  return normalized;
}

export async function load({ fetch, parent, url }) {
  const parentData = await parent();
  const api = createApi(fetch);

  const filters = {
    search: normalizeFilter(url.searchParams.get('search')),
    room_id: normalizeFilter(url.searchParams.get('room_id')),
    label_id: normalizeFilter(url.searchParams.get('label_id'))
  };

  const containerResult = await safeRequest(
    api.listContainers({
      search: filters.search || undefined,
      room_id: filters.room_id || undefined,
      label_id: filters.label_id || undefined
    })
  );

  return {
    filters,
    containers: containerResult.ok ? containerResult.data : [],
    containerError: containerResult.ok ? null : containerResult.error.detail ?? containerResult.error.message,
    rooms: parentData.rooms,
    labels: parentData.labels
  };
}
