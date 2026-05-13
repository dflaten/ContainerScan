import { safeRequest } from '$lib/api';
import { createServerApi } from '$lib/server-api';

function normalizeFilter(value) {
  if (value === null) {
    return '';
  }

  const normalized = value.trim();
  return normalized;
}

export async function load({ fetch, parent, url }) {
  const parentData = await parent();
  const api = createServerApi(fetch);

  const filters = {
    search: normalizeFilter(url.searchParams.get('search'))
  };

  const containerResult = await safeRequest(
    api.listContainers({
      search: filters.search || undefined
    })
  );

  return {
    createdContainerId: normalizeFilter(url.searchParams.get('created')),
    deletedContainerCode: normalizeFilter(url.searchParams.get('deleted')),
    filters,
    containers: containerResult.ok ? containerResult.data : [],
    containerError: containerResult.ok ? null : containerResult.error.detail ?? containerResult.error.message,
    rooms: parentData.rooms,
    tags: parentData.tags
  };
}
