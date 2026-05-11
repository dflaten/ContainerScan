export const API_BASE_PATH = '/api';

export class ApiError extends Error {
  constructor(message, { status, detail, path }) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.path = path;
  }
}

function buildUrl(path, query = undefined, basePath = API_BASE_PATH) {
  const isAbsoluteBasePath = /^https?:\/\//.test(basePath);
  const normalizedBasePath = isAbsoluteBasePath ? basePath.replace(/\/$/, '') : basePath;
  const url = isAbsoluteBasePath
    ? new URL(`${normalizedBasePath}${path}`)
    : new URL(`${normalizedBasePath}${path}`, 'http://containerscan.local');

  if (query !== undefined) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null || value === '') {
        continue;
      }

      url.searchParams.set(key, String(value));
    }
  }

  return isAbsoluteBasePath ? url.toString() : `${url.pathname}${url.search}`;
}

async function parseError(response, path) {
  let detail = `Request failed with status ${response.status}.`;

  try {
    const payload = await response.json();
    if (typeof payload?.detail === 'string' && payload.detail.length > 0) {
      detail = payload.detail;
    }
  } catch {
    if (response.statusText) {
      detail = response.statusText;
    }
  }

  return new ApiError(detail, {
    status: response.status,
    detail,
    path
  });
}

async function request(fetchFn, path, options = {}) {
  const { method = 'GET', body, headers = {}, query, basePath = API_BASE_PATH } = options;
  const requestPath = buildUrl(path, query, basePath);
  const response = await fetchFn(requestPath, {
    method,
    headers,
    body
  });

  if (!response.ok) {
    throw await parseError(response, requestPath);
  }

  return response;
}

export async function requestJson(fetchFn, path, options = {}) {
  const { headers = {}, ...rest } = options;
  const response = await request(fetchFn, path, {
    ...rest,
    headers: {
      accept: 'application/json',
      ...headers
    }
  });

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export async function safeRequest(request) {
  try {
    const data = await request;
    return { ok: true, data, error: null };
  } catch (error) {
    return { ok: false, data: null, error };
  }
}

export function createApi(fetchFn, config = {}) {
  const { basePath = API_BASE_PATH } = config;
  const createRequestOptions = (options = {}) => ({
    ...options,
    basePath
  });

  return {
    getHealth() {
      return requestJson(fetchFn, '/health', createRequestOptions());
    },
    listRooms() {
      return requestJson(fetchFn, '/rooms', createRequestOptions());
    },
    createRoom(payload) {
      return requestJson(fetchFn, '/rooms', createRequestOptions({
        method: 'POST',
        headers: {
          'content-type': 'application/json'
        },
        body: JSON.stringify(payload)
      }));
    },
    deleteRoom(roomId) {
      return requestJson(fetchFn, `/rooms/${roomId}`, createRequestOptions({
        method: 'DELETE'
      }));
    },
    listLabels() {
      return requestJson(fetchFn, '/labels', createRequestOptions());
    },
    listContainers(filters = {}) {
      return requestJson(fetchFn, '/containers', createRequestOptions({ query: filters }));
    },
    getPrintSheet(printSheetId) {
      return requestJson(fetchFn, `/print-sheets/${printSheetId}`, createRequestOptions());
    },
    previewFullSheetDraft() {
      return requestJson(fetchFn, '/print-sheets/drafts/full-sheet', createRequestOptions({
        method: 'POST'
      }));
    },
    createFullSheet(payload) {
      return requestJson(fetchFn, '/print-sheets/generated/full-sheet', createRequestOptions({
        method: 'POST',
        headers: {
          'content-type': 'application/json'
        },
        body: JSON.stringify(payload)
      }));
    },
    createContainer(payload) {
      return requestJson(fetchFn, '/containers', createRequestOptions({
        method: 'POST',
        headers: {
          'content-type': 'application/json'
        },
        body: JSON.stringify(payload)
      }));
    },
    getContainer(containerId) {
      return requestJson(fetchFn, `/containers/${containerId}`, createRequestOptions());
    },
    updateContainer(containerId, payload) {
      return requestJson(fetchFn, `/containers/${containerId}`, createRequestOptions({
        method: 'PUT',
        headers: {
          'content-type': 'application/json'
        },
        body: JSON.stringify(payload)
      }));
    },
    deleteContainer(containerId) {
      return requestJson(fetchFn, `/containers/${containerId}`, createRequestOptions({
        method: 'DELETE'
      }));
    },
    async uploadContainerImages(containerId, { files, captions = [] }) {
      const formData = new FormData();

      for (const file of files) {
        formData.append('images', file);
      }

      for (const caption of captions) {
        formData.append('captions', caption);
      }

      return requestJson(fetchFn, `/containers/${containerId}/images`, createRequestOptions({
        method: 'POST',
        body: formData
      }));
    },
    updateImage(imageId, payload) {
      return requestJson(fetchFn, `/images/${imageId}`, createRequestOptions({
        method: 'PUT',
        headers: {
          'content-type': 'application/json'
        },
        body: JSON.stringify(payload)
      }));
    },
    deleteImage(imageId) {
      return requestJson(fetchFn, `/images/${imageId}`, createRequestOptions({
        method: 'DELETE'
      }));
    },
    getScanContainer(containerId) {
      return requestJson(fetchFn, `/scan/${containerId}`, createRequestOptions());
    },
    getQrDownloadPath(containerId) {
      return buildUrl(`/containers/${containerId}/qr`);
    }
  };
}
