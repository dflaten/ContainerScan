import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeEach, describe, expect, test, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  api: {
    getContainer: vi.fn(),
    updateContainer: vi.fn(),
    uploadContainerImages: vi.fn(),
    updateImage: vi.fn(),
    deleteImage: vi.fn(),
    getQrDownloadPath: vi.fn((containerId) => `/api/containers/${containerId}/qr`)
  }
}));

vi.mock('$lib/api', () => ({
  createApi: () => mocks.api
}));

import Page from '../../src/routes/containers/[id]/+page.svelte';

function buildContainer(overrides = {}) {
  return {
    id: 'container-1',
    code: 'AA-11',
    name: 'Garage Box 3',
    description: 'Camping gear',
    room_id: 'room-1',
    label_id: 'label-1',
    images: [
      {
        id: 'image-1',
        url: '/images/one.jpg',
        uploaded_at: '2026-05-06T12:00:00Z',
        caption: 'Front shelf',
        sort_order: 0,
        is_primary: true
      }
    ],
    ...overrides
  };
}

function buildData(overrides = {}) {
  return {
    container: buildContainer(),
    containerError: null,
    createdNotice: false,
    imageUploadErrorNotice: false,
    rooms: [{ id: 'room-1', name: 'Garage' }],
    labels: [{ id: 'label-1', name: 'Tools', colour: '#AABBCC' }],
    ...overrides
  };
}

describe('container detail route', () => {
  beforeEach(() => {
    mocks.api.getContainer.mockReset();
    mocks.api.updateContainer.mockReset();
    mocks.api.uploadContainerImages.mockReset();
    mocks.api.updateImage.mockReset();
    mocks.api.deleteImage.mockReset();
  });

  test('shows the initial image-upload retry notice after partial create success', () => {
    render(Page, {
      data: buildData({
        createdNotice: true,
        imageUploadErrorNotice: true
      })
    });

    expect(screen.getByText(/container created\. you can keep editing it here\./i)).toBeInTheDocument();
    expect(
      screen.getByText(/the container was created, but the initial image upload did not complete\./i)
    ).toBeInTheDocument();
  });

  test('saves metadata updates through the container api and shows a success notice', async () => {
    mocks.api.updateContainer.mockResolvedValue(
      buildContainer({
        name: 'Updated Garage Box 3',
        description: 'Updated camping gear'
      })
    );

    render(Page, { data: buildData() });

    await fireEvent.input(screen.getByLabelText('Name'), {
      target: { value: 'Updated Garage Box 3' }
    });
    await fireEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(mocks.api.updateContainer).toHaveBeenCalledWith('container-1', {
        name: 'Updated Garage Box 3',
        description: 'Camping gear',
        room_id: 'room-1',
        label_id: 'label-1'
      });
    });

    expect(screen.getByText(/container details updated\./i)).toBeInTheDocument();
  });
});
