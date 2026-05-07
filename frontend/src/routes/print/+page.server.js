import { safeRequest } from '$lib/api';
import { createServerApi } from '$lib/server-api';

export async function load({ fetch, parent, url }) {
  const parentData = await parent();
  const api = createServerApi(fetch);
  const containerResult = await safeRequest(api.listContainers());
  const selectedIds = url.searchParams.getAll('id');

  const containers = containerResult.ok ? containerResult.data : [];
  const selectedContainers = containers.filter((container) => selectedIds.includes(container.id));

  return {
    containers,
    labels: parentData.labels,
    printError: containerResult.ok
      ? null
      : containerResult.error.detail ?? containerResult.error.message,
    rooms: parentData.rooms,
    selectedIds,
    selectedContainers
  };
}
