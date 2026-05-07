import { createApi, safeRequest } from '$lib/api';

export async function load({ fetch, params, parent, url }) {
  const parentData = await parent();
  const api = createApi(fetch);
  const containerResult = await safeRequest(api.getContainer(params.id));

  return {
    container: containerResult.ok ? containerResult.data : null,
    containerError: containerResult.ok
      ? null
      : containerResult.error.detail ?? containerResult.error.message,
    createdNotice: url.searchParams.get('created') === '1',
    imageUploadErrorNotice: url.searchParams.get('image_upload_error') === '1',
    labels: parentData.labels,
    rooms: parentData.rooms
  };
}
