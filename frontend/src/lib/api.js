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

function buildUrl(path, query = undefined) {
  const url = new URL(`${API_BASE_PATH}${path}`, 'http://containerscan.local');

  if (query !== undefined) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null || value === '') {
        continue;
      }

      url.searchParams.set(key, String(value));
    }
  }

  return `${url.pathname}${url.search}`;
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
  const { method = 'GET', body, headers = {}, query } = options;
  const requestPath = buildUrl(path, query);
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

export function createApi(fetchFn) {
  return {
    getHealth() {
      return requestJson(fetchFn, '/health');
    },
    listRooms() {
      return requestJson(fetchFn, '/rooms');
    },
    listLabels() {
      return requestJson(fetchFn, '/labels');
    },
    listContainers(filters = {}) {
      return requestJson(fetchFn, '/containers', { query: filters });
    },
    createContainer(payload) {
      return requestJson(fetchFn, '/containers', {
        method: 'POST',
        headers: {
          'content-type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
    },
    getContainer(containerId) {
      return requestJson(fetchFn, `/containers/${containerId}`);
    },
    updateContainer(containerId, payload) {
      return requestJson(fetchFn, `/containers/${containerId}`, {
        method: 'PUT',
        headers: {
          'content-type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
    },
    async uploadContainerImages(containerId, { files, captions = [] }) {
      const formData = new FormData();

      for (const file of files) {
        formData.append('images', file);
      }

      for (const caption of captions) {
        formData.append('captions', caption);
      }

      return requestJson(fetchFn, `/containers/${containerId}/images`, {
        method: 'POST',
        body: formData
      });
    },
    updateImage(imageId, payload) {
      return requestJson(fetchFn, `/images/${imageId}`, {
        method: 'PUT',
        headers: {
          'content-type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
    },
    deleteImage(imageId) {
      return requestJson(fetchFn, `/images/${imageId}`, {
        method: 'DELETE'
      });
    },
    getScanContainer(containerId) {
      return requestJson(fetchFn, `/scan/${containerId}`);
    },
    getQrDownloadPath(containerId) {
      return buildUrl(`/containers/${containerId}/qr`);
    }
  };
}
