import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeEach, describe, expect, test, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  api: {
    createRoom: vi.fn(),
    deleteRoom: vi.fn()
  }
}));

vi.mock('$lib/api', () => ({
  createApi: () => mocks.api
}));

import Page from '../../src/routes/rooms/+page.svelte';

function buildData(overrides = {}) {
  return {
    rooms: [
      { id: 'room-1', name: 'Garage' },
      { id: 'room-2', name: 'Attic' }
    ],
    ...overrides
  };
}

describe('rooms management route', () => {
  beforeEach(() => {
    mocks.api.createRoom.mockReset();
    mocks.api.deleteRoom.mockReset();
  });

  test('creates a room and shows it in the list', async () => {
    mocks.api.createRoom.mockResolvedValue({ id: 'room-3', name: 'Basement' });

    render(Page, { data: buildData() });

    await fireEvent.input(screen.getByPlaceholderText('enter room name here'), {
      target: { value: 'Basement' }
    });
    await fireEvent.click(screen.getByRole('button', { name: /add room/i }));

    await waitFor(() => {
      expect(mocks.api.createRoom).toHaveBeenCalledWith({ name: 'Basement' });
    });

    expect(screen.getByText(/added room basement\./i)).toBeInTheDocument();
    expect(screen.getByText('Basement')).toBeInTheDocument();
  });

  test('removes a room from the list', async () => {
    mocks.api.deleteRoom.mockResolvedValue(null);

    render(Page, { data: buildData() });

    const garageRow = screen.getByText('Garage').closest('.room-list-item');
    expect(garageRow).not.toBeNull();
    await fireEvent.click(garageRow.querySelector('button'));

    await waitFor(() => {
      expect(mocks.api.deleteRoom).toHaveBeenCalledWith('room-1');
    });

    expect(screen.queryByText('Garage')).not.toBeInTheDocument();
    expect(screen.getByText(/removed room garage\./i)).toBeInTheDocument();
  });
});
