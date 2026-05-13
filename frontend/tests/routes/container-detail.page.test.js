import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeEach, describe, expect, test, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  api: {
    getContainer: vi.fn(),
    updateContainer: vi.fn(),
    deleteContainer: vi.fn(),
    uploadContainerImages: vi.fn(),
    updateImage: vi.fn(),
    deleteImage: vi.fn(),
    getQrDownloadPath: vi.fn((containerId) => `/api/containers/${containerId}/qr`)
  },
  goto: vi.fn()
}));

vi.mock('$app/navigation', () => ({
  goto: mocks.goto
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
    tag_ids: ['label-1'],
    tags: [{ id: 'label-1', name: 'Tools', colour: '#AABBCC' }],
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
    rooms: [{ id: 'room-1', name: 'Garage' }],
    tags: [{ id: 'label-1', name: 'Tools', colour: '#AABBCC' }],
    ...overrides
  };
}

describe('container detail route', () => {
  beforeEach(() => {
    mocks.api.getContainer.mockReset();
    mocks.api.updateContainer.mockReset();
    mocks.api.deleteContainer.mockReset();
    mocks.api.uploadContainerImages.mockReset();
    mocks.api.updateImage.mockReset();
    mocks.api.deleteImage.mockReset();
    mocks.goto.mockReset();
    vi.restoreAllMocks();
  });

  test('shows the label-ready notice after creating a shell container', () => {
    render(Page, {
      data: buildData({
        createdNotice: true
      })
    });

    expect(screen.getByText(/label ready\. download it now/i)).toBeInTheDocument();
  });

  test('shows a floating dashboard shortcut on the container page', () => {
    const { container } = render(Page, { data: buildData() });

    expect(container.querySelector('.floating-dashboard-link')).toHaveAttribute('href', '/');
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
    await fireEvent.click(screen.getByRole('button', { name: /save and next/i }));

    await waitFor(() => {
      expect(mocks.api.updateContainer).toHaveBeenCalledWith('container-1', {
        name: 'Updated Garage Box 3',
        description: 'Camping gear',
        room_id: 'room-1',
        tag_ids: ['label-1']
      });
    });

    expect(screen.getByLabelText('Room')).toBeInTheDocument();
    expect(screen.getByText('Room and tags')).toBeInTheDocument();
  });

  test('deletes the container after confirmation and redirects to the dashboard', async () => {
    mocks.api.deleteContainer.mockResolvedValue(null);
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(Page, { data: buildData() });

    await fireEvent.click(screen.getByRole('button', { name: /delete container/i }));

    await waitFor(() => {
      expect(mocks.api.deleteContainer).toHaveBeenCalledWith('container-1');
    });
    expect(mocks.goto).toHaveBeenCalledWith('/?deleted=AA-11');
  });

  test('saves room and tags before advancing to the images step', async () => {
    mocks.api.updateContainer.mockResolvedValue(buildContainer());

    render(Page, { data: buildData() });

    await fireEvent.click(screen.getByRole('button', { name: /save and next/i }));
    await screen.findByLabelText('Room');

    await fireEvent.change(screen.getByLabelText('Room'), {
      target: { value: 'room-1' }
    });
    await fireEvent.click(screen.getByRole('button', { name: /save and next/i }));

    await waitFor(() => {
      expect(mocks.api.updateContainer).toHaveBeenLastCalledWith('container-1', {
        name: 'Garage Box 3',
        description: 'Camping gear',
        room_id: 'room-1',
        tag_ids: ['label-1']
      });
    });

    expect(screen.getByText('Images')).toBeInTheDocument();
    expect(screen.getByText(/choose images for this container/i)).toBeInTheDocument();
  });

  test('uploads selected images on the final step and redirects to the dashboard', async () => {
    mocks.api.updateContainer.mockResolvedValue(buildContainer());
    mocks.api.uploadContainerImages.mockResolvedValue([]);

    render(Page, { data: buildData({ container: buildContainer({ images: [] }) }) });

    await fireEvent.click(screen.getByRole('button', { name: /save and next/i }));
    await screen.findByLabelText('Room');
    await fireEvent.click(screen.getByRole('button', { name: /save and next/i }));
    await screen.findByText(/choose images for this container/i);

    const uploadInput = document.querySelector('.upload-picker input');
    const file = new File(['image-bytes'], 'inside.jpg', { type: 'image/jpeg' });

    expect(uploadInput).not.toBeNull();
    await fireEvent.change(uploadInput, {
      target: { files: [file] }
    });
    await fireEvent.click(screen.getByRole('button', { name: /save and finish/i }));

    await waitFor(() => {
      expect(mocks.api.uploadContainerImages).toHaveBeenCalledWith('container-1', {
        files: [file]
      });
    });
    expect(mocks.goto).toHaveBeenCalledWith('/');
  });

  test('shows the existing images on the final step', async () => {
    mocks.api.updateContainer.mockResolvedValue(
      buildContainer({
        images: [
          {
            id: 'image-1',
            url: '/images/one.jpg',
            uploaded_at: '2026-05-06T12:00:00Z',
            caption: 'Front shelf',
            sort_order: 0,
            is_primary: true
          },
          {
            id: 'image-2',
            url: '/images/two.jpg',
            uploaded_at: '2026-05-07T12:00:00Z',
            caption: 'Inside bin',
            sort_order: 1,
            is_primary: false
          }
        ]
      })
    );

    render(Page, { data: buildData() });

    await fireEvent.click(screen.getByRole('button', { name: /save and next/i }));
    await screen.findByLabelText('Room');
    await fireEvent.click(screen.getByRole('button', { name: /save and next/i }));

    expect(screen.getByText(/2 already saved/i)).toBeInTheDocument();
    expect(screen.getByAltText('Inside bin')).toBeInTheDocument();
  });
});
