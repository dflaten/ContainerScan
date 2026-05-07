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

export async function requestJson(fetchFn, path, options = {}) {
  const { method = 'GET', body, headers = {}, query } = options;
  const requestPath = buildUrl(path, query);
  const response = await fetchFn(requestPath, {
    method,
    headers: {
      accept: 'application/json',
      ...headers
    },
    body
  });

  if (!response.ok) {
    throw await parseError(response, requestPath);
  }

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
    getScanContainer(containerId) {
      return requestJson(fetchFn, `/scan/${containerId}`);
    }
  };
}
