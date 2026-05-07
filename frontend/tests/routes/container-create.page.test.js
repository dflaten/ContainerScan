import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeEach, describe, expect, test, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  goto: vi.fn(),
  api: {
    createContainer: vi.fn()
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
  });

  test('allows generating a label even when rooms or labels are unavailable', () => {
    render(Page, {
      data: buildData({
        rooms: [],
        labels: []
      })
    });

    expect(screen.getByRole('button', { name: /generate container label/i })).toBeInTheDocument();
  });

  test('redirects to the detail page after creating a new shell container', async () => {
    mocks.api.createContainer.mockResolvedValue({ id: 'container-7' });

    render(Page, { data: buildData() });

    await fireEvent.input(screen.getByPlaceholderText(/optional, for example garage bin/i), {
      target: { value: 'Garage Box 7' }
    });
    await fireEvent.click(screen.getByRole('button', { name: /generate container label/i }));

    await waitFor(() => {
      expect(mocks.api.createContainer).toHaveBeenCalledWith({
        name: 'Garage Box 7',
        room_id: null,
        label_id: null
      });
    });
    expect(mocks.goto).toHaveBeenCalledWith('/containers/container-7?created=1');
  });
});
