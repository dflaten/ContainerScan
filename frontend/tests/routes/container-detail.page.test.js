import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeEach, describe, expect, test, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  api: {
    getContainer: vi.fn(),
    updateContainer: vi.fn(),
    deleteContainer: vi.fn(),
    uploadContainerImages: vi.fn(),
    updateImage: vi.fn(),
    deleteImage: vi.fn()
  },
  goto: vi.fn()
}));

vi.mock('$app/navigation', () => ({
  goto: mocks.goto
}));

vi.mock('#lib/api', () => ({
  createApi: () => mocks.api
}));

import Page from '../../src/routes/containers/[id]/+page.svelte';

function buildContainer(overrides = {}) {
  return {
    id: 'container-1',
    code: 'AA-11',
    name: 'Garage Box 3',
    description: 'Camping gear',
    colour: '#3B82F6',
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
    rooms: [{ id: 'room-1', name: 'Garage' }],
    colors: [{ id: 'color-1', name: 'Blue', value: '#3B82F6' }],
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

  test('saves metadata updates through the container api and advances quietly', async () => {
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
    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));

    await waitFor(() => {
      expect(mocks.api.updateContainer).toHaveBeenCalledWith('container-1', {
        name: 'Updated Garage Box 3',
        description: 'Camping gear',
        colour: '#3B82F6',
        room_id: 'room-1',
        tag_ids: ['label-1']
      });
    });

    expect(screen.getByLabelText('Room')).toBeInTheDocument();
    expect(screen.getByText('Room/Tags/Color')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  test('shows save failures in the inline error banner', async () => {
    mocks.api.updateContainer.mockRejectedValue({ detail: 'Unable to save container.' });

    render(Page, { data: buildData() });

    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to save container.');
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
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

    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));
    await screen.findByLabelText('Room');

    await fireEvent.change(screen.getByLabelText('Room'), {
      target: { value: 'room-1' }
    });
    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));

    await waitFor(() => {
      expect(mocks.api.updateContainer).toHaveBeenLastCalledWith('container-1', {
        name: 'Garage Box 3',
        description: 'Camping gear',
        colour: '#3B82F6',
        room_id: 'room-1',
        tag_ids: ['label-1']
      });
    });

    expect(screen.getByText('Images')).toBeInTheDocument();
    expect(screen.getByText('1 already saved')).toBeInTheDocument();
  });

  test('saves organization changes before going back to the details step', async () => {
    mocks.api.updateContainer.mockResolvedValue(buildContainer({ room_id: null }));

    render(Page, { data: buildData() });

    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));
    await screen.findByLabelText('Room');

    await fireEvent.change(screen.getByLabelText('Room'), {
      target: { value: '' }
    });
    await fireEvent.click(screen.getByRole('button', { name: /^back$/i }));

    await waitFor(() => {
      expect(mocks.api.updateContainer).toHaveBeenLastCalledWith('container-1', {
        name: 'Garage Box 3',
        description: 'Camping gear',
        colour: '#3B82F6',
        room_id: null,
        tag_ids: ['label-1']
      });
    });

    expect(screen.getByLabelText('Name')).toBeInTheDocument();
  });

  test('uploads selected images on the final step and redirects to the dashboard', async () => {
    mocks.api.updateContainer.mockResolvedValue(buildContainer());
    mocks.api.uploadContainerImages.mockResolvedValue([]);

    render(Page, { data: buildData({ container: buildContainer({ images: [] }) }) });

    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));
    await screen.findByLabelText('Room');
    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));
    await screen.findByText('1 already saved');

    const uploadInput = document.querySelector('.upload-picker input');
    const file = new File(['image-bytes'], 'inside.jpg', { type: 'image/jpeg' });

    expect(uploadInput).not.toBeNull();
    await fireEvent.change(uploadInput, {
      target: { files: [file] }
    });
    await fireEvent.click(screen.getByRole('button', { name: /^finish$/i }));

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

    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));
    await screen.findByLabelText('Room');
    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));

    expect(screen.getByText(/2 already saved/i)).toBeInTheDocument();
    expect(screen.getByAltText('Inside bin')).toBeInTheDocument();
  });

  test('sets an existing image as the main photo', async () => {
    const container = buildContainer({
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
    });

    mocks.api.updateContainer.mockResolvedValue(container);
    mocks.api.updateImage.mockResolvedValue({
      ...container.images[1],
      is_primary: true
    });

    render(Page, { data: buildData({ container }) });

    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));
    await screen.findByLabelText('Room');
    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));

    await fireEvent.click(screen.getByRole('button', { name: /set as main photo for inside bin/i }));

    await waitFor(() => {
      expect(mocks.api.updateImage).toHaveBeenCalledWith('image-2', {
        is_primary: true,
        caption: 'Inside bin',
        sort_order: 1
      });
      expect(
        screen.queryByRole('button', { name: /set as main photo for inside bin/i })
      ).not.toBeInTheDocument();
    });

    expect(screen.getByText('Main photo')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /set as main photo for front shelf/i })
    ).toBeInTheDocument();
  });

  test('deletes an existing image after confirmation', async () => {
    const container = buildContainer({
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
    });

    mocks.api.updateContainer.mockResolvedValue(container);
    mocks.api.deleteImage.mockResolvedValue(null);
    mocks.api.getContainer.mockResolvedValue(
      buildContainer({ images: [container.images[0]] })
    );
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(Page, { data: buildData({ container }) });

    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));
    await screen.findByLabelText('Room');
    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));

    await fireEvent.click(screen.getByRole('button', { name: /delete inside bin/i }));

    await waitFor(() => {
      expect(mocks.api.deleteImage).toHaveBeenCalledWith('image-2');
      expect(screen.queryByAltText('Inside bin')).not.toBeInTheDocument();
    });

    expect(mocks.api.getContainer).toHaveBeenCalledWith('container-1');
    expect(screen.getByAltText('Front shelf')).toBeInTheDocument();
  });

  test('promotes the next image when the main photo is deleted', async () => {
    const container = buildContainer({
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
    });

    mocks.api.updateContainer.mockResolvedValue(container);
    mocks.api.deleteImage.mockResolvedValue(null);
    mocks.api.getContainer.mockResolvedValue(
      buildContainer({ images: [{ ...container.images[1], is_primary: true }] })
    );
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(Page, { data: buildData({ container }) });

    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));
    await screen.findByLabelText('Room');
    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));

    await fireEvent.click(screen.getByRole('button', { name: /delete front shelf/i }));

    await waitFor(() => {
      expect(mocks.api.deleteImage).toHaveBeenCalledWith('image-1');
      expect(screen.queryByAltText('Front shelf')).not.toBeInTheDocument();
      expect(
        screen.queryByRole('button', { name: /set as main photo for inside bin/i })
      ).not.toBeInTheDocument();
    });

    expect(mocks.api.getContainer).toHaveBeenCalledWith('container-1');
    expect(screen.getByText('Main photo')).toBeInTheDocument();
    expect(screen.getByAltText('Inside bin')).toBeInTheDocument();
  });

  test('keeps the image when deletion is cancelled', async () => {
    const container = buildContainer();

    mocks.api.updateContainer.mockResolvedValue(container);
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);

    render(Page, { data: buildData({ container }) });

    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));
    await screen.findByLabelText('Room');
    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));

    await fireEvent.click(screen.getByRole('button', { name: /delete front shelf/i }));

    expect(confirmSpy).toHaveBeenCalled();
    expect(mocks.api.deleteImage).not.toHaveBeenCalled();
    expect(screen.getByAltText('Front shelf')).toBeInTheDocument();
  });

  test('shows image deletion failures in the inline error banner', async () => {
    const container = buildContainer();

    mocks.api.updateContainer.mockResolvedValue(container);
    mocks.api.deleteImage.mockRejectedValue({ detail: 'Unable to delete photo.' });
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(Page, { data: buildData({ container }) });

    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));
    await screen.findByLabelText('Room');
    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));

    await fireEvent.click(screen.getByRole('button', { name: /delete front shelf/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to delete photo.');
    expect(screen.getByAltText('Front shelf')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /delete front shelf/i })).not.toBeDisabled();
  });

  test('requires a replacement photo after deleting the last image', async () => {
    const container = buildContainer();

    mocks.api.updateContainer.mockResolvedValue(container);
    mocks.api.deleteImage.mockResolvedValue(null);
    mocks.api.getContainer.mockResolvedValue(buildContainer({ images: [] }));
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(Page, { data: buildData({ container }) });

    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));
    await screen.findByLabelText('Room');
    await fireEvent.click(screen.getByRole('button', { name: /^next$/i }));

    expect(screen.getByRole('button', { name: /^finish$/i })).toBeEnabled();

    await fireEvent.click(screen.getByRole('button', { name: /delete front shelf/i }));

    expect(confirmSpy).toHaveBeenCalledWith(expect.stringMatching(/add another photo/i));

    await waitFor(() => {
      expect(screen.queryByAltText('Front shelf')).not.toBeInTheDocument();
    });

    expect(screen.getByText(/add at least one photo to finish/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^finish$/i })).toBeDisabled();
  });

  test('allows navigating steps from the bottom stepper', async () => {
    mocks.api.updateContainer.mockResolvedValue(buildContainer({ description: 'Repacked gear' }));

    render(Page, { data: buildData() });

    await fireEvent.input(screen.getByLabelText('Description'), {
      target: { value: 'Repacked gear' }
    });

    await fireEvent.click(screen.getByRole('button', { name: /go to room\/tags\/color/i }));

    await waitFor(() => {
      expect(mocks.api.updateContainer).toHaveBeenCalledWith('container-1', {
        name: 'Garage Box 3',
        description: 'Repacked gear',
        colour: '#3B82F6',
        room_id: 'room-1',
        tag_ids: ['label-1']
      });
    });

    expect(screen.getByLabelText('Room')).toBeInTheDocument();
  });
});
