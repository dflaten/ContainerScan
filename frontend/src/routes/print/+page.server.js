import { fail, redirect } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';

import { safeRequest } from '$lib/api';
import { createServerApi } from '$lib/server-api';

export async function load({ fetch, url }) {
  const api = createServerApi(fetch);
  const internalApiBaseUrl = (env.INTERNAL_API_URL ?? 'http://backend:8000').replace(/\/$/, '');
  const sheetId = url.searchParams.get('sheet');
  const draftCodes = url.searchParams.getAll('draft_code');
  const sheetResult = sheetId ? await safeRequest(api.getPrintSheet(sheetId)) : null;

  const savedSheet = sheetResult?.ok ? sheetResult.data : null;
  const draftSheet = draftCodes.length > 0
    ? {
        containers: draftCodes.map((code, index) => ({
          id: url.searchParams.getAll('draft_id')[index] ?? `draft-${code}`,
          code,
          name: `Container ${code}`,
          room_id: null,
          label_id: null,
          isDraft: true
        }))
      }
    : null;
  const selectedContainers = savedSheet ? savedSheet.containers : draftSheet ? draftSheet.containers : [];
  const printError = sheetResult && !sheetResult.ok
    ? sheetResult.error.detail ?? sheetResult.error.message
    : null;
  const qrImageUrls = await buildQrImageUrls(fetch, internalApiBaseUrl, selectedContainers);

  return {
    createdFullSheet: url.searchParams.get('generated') === '1',
    draftSheet,
    missingEmptyLabelsNotice: url.searchParams.get('missingEmptyLabels') === '1',
    printError,
    qrImageUrls,
    savedSheet,
    selectedContainers
  };
}

export const actions = {
  previewFullSheet: async ({ fetch }) => {
    const api = createServerApi(fetch);
    const result = await safeRequest(api.previewFullSheetDraft());

    if (!result.ok) {
      return fail(result.error.status ?? 500, {
        previewFullSheetError: result.error.detail ?? result.error.message
      });
    }

    const params = new URLSearchParams();
    for (const container of result.data.containers) {
      params.append('draft_id', container.id);
      params.append('draft_code', container.code);
    }

    throw redirect(303, `/print?${params.toString()}`);
  },
  createFullSheet: async ({ fetch, request }) => {
    const api = createServerApi(fetch);
    const formData = await request.formData();
    const draftCodes = formData
      .getAll('draft_code')
      .map((value) => String(value).trim())
      .filter((value) => value.length > 0);
    const draftIds = formData
      .getAll('draft_id')
      .map((value) => String(value).trim())
      .filter((value) => value.length > 0);

    if (draftCodes.length === 0 || draftIds.length === 0 || draftCodes.length !== draftIds.length) {
      return fail(400, {
        createFullSheetError: 'Preview a new full sheet before creating labels.'
      });
    }

    const result = await safeRequest(
      api.createFullSheet({
        drafts: draftCodes.map((code, index) => ({
          id: draftIds[index],
          code,
          name: `Container ${code}`,
          room_id: null,
          label_id: null
        }))
      })
    );

    if (!result.ok) {
      return fail(result.error.status ?? 500, {
        createFullSheetError: result.error.detail ?? result.error.message
      });
    }

    throw redirect(303, `/print?sheet=${result.data.id}&generated=1`);
  }
};

async function buildQrImageUrls(fetchFn, internalApiBaseUrl, containers) {
  const entries = await Promise.all(
    containers.map(async (container) => {
      const url = container.isDraft
        ? `${internalApiBaseUrl}/api/print-sheets/drafts/qr-code/${container.id}?code=${encodeURIComponent(container.code)}`
        : `${internalApiBaseUrl}/api/containers/${container.id}/qr-code/inline`;

      try {
        const response = await fetchFn(url);
        if (!response.ok) {
          return [container.id, null];
        }

        const bytes = new Uint8Array(await response.arrayBuffer());
        const base64 = Buffer.from(bytes).toString('base64');
        return [container.id, `data:image/png;base64,${base64}`];
      } catch {
        return [container.id, null];
      }
    })
  );

  return Object.fromEntries(entries);
}
