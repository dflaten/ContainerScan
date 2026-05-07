import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeEach, describe, expect, test, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  goto: vi.fn(),
  api: {
    createContainer: vi.fn(),
    uploadContainerImages: vi.fn()
  }
}));

vi.mock('$app/navigation', () => ({
  goto: mocks.goto
}));

vi.mock('$lib/api', () => ({
  createApi: () => mocks.api
}));

import Page from '../../src/routes/containers/new/+page.svelte';

function buildData(overrides = {}) {
  return {
    rooms: [{ id: 'room-1', name: 'Garage' }],
    labels: [{ id: 'label-1', name: 'Tools', colour: '#AABBCC' }],
    ...overrides
  };
}

describe('create container route', () => {
  beforeEach(() => {
    mocks.goto.mockReset();
    mocks.api.createContainer.mockReset();
    mocks.api.uploadContainerImages.mockReset();
  });

  test('shows a reference-data warning when rooms or labels are unavailable', () => {
    render(Page, {
      data: buildData({
        rooms: [],
        labels: []
      })
    });

    expect(screen.getByText(/reference data required/i)).toBeInTheDocument();
  });

  test('redirects to the detail page when image upload fails after container creation', async () => {
    mocks.api.createContainer.mockResolvedValue({ id: 'container-7' });
    mocks.api.uploadContainerImages.mockRejectedValue(new Error('upload failed'));

    render(Page, { data: buildData() });
    const file = new File(['image-bytes'], 'front.jpg', { type: 'image/jpeg' });

    await fireEvent.input(screen.getByLabelText('Name'), {
      target: { value: 'Garage Box 7' }
    });
    await fireEvent.change(document.querySelector('input[type="file"]'), {
      target: { files: [file] }
    });
    await fireEvent.click(screen.getByRole('button', { name: /create container/i }));

    await waitFor(() => {
      expect(mocks.goto).toHaveBeenCalledWith('/containers/container-7?created=1&image_upload_error=1');
    });
  });
});
