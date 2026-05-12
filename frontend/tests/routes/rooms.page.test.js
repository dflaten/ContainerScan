import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeEach, describe, expect, test, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  api: {
    createRoom: vi.fn(),
    deleteRoom: vi.fn(),
    createLabel: vi.fn(),
    deleteLabel: vi.fn()
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
    labels: [
      { id: 'label-1', name: 'Tools', colour: '#AABBCC' },
      { id: 'label-2', name: 'Holiday', colour: '#CC8844' }
    ],
    ...overrides
  };
}

describe('rooms management route', () => {
  beforeEach(() => {
    mocks.api.createRoom.mockReset();
    mocks.api.deleteRoom.mockReset();
    mocks.api.createLabel.mockReset();
    mocks.api.deleteLabel.mockReset();
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

  test('creates a tag and shows it in the list', async () => {
    mocks.api.createLabel.mockResolvedValue({ id: 'label-3', name: 'Archive', colour: '#123456' });

    render(Page, { data: buildData() });

    await fireEvent.input(screen.getByPlaceholderText('enter tag name here'), {
      target: { value: 'Archive' }
    });
    const colourInput = document.querySelector('.label-colour-input');
    expect(colourInput).not.toBeNull();
    await fireEvent.input(colourInput, {
      target: { value: '#123456' }
    });
    await fireEvent.click(screen.getByRole('button', { name: /add tag/i }));

    await waitFor(() => {
      expect(mocks.api.createLabel).toHaveBeenCalledWith({ name: 'Archive', colour: '#123456' });
    });

    expect(screen.getByText(/added tag archive\./i)).toBeInTheDocument();
    expect(screen.getByText('Archive')).toBeInTheDocument();
  });

  test('removes a tag from the list', async () => {
    mocks.api.deleteLabel.mockResolvedValue(null);

    render(Page, { data: buildData() });

    const holidayRow = screen.getByText('Holiday').closest('.room-list-item');
    expect(holidayRow).not.toBeNull();
    await fireEvent.click(holidayRow.querySelector('button'));

    await waitFor(() => {
      expect(mocks.api.deleteLabel).toHaveBeenCalledWith('label-2');
    });

    expect(screen.queryByText('Holiday')).not.toBeInTheDocument();
    expect(screen.getByText(/removed tag holiday\./i)).toBeInTheDocument();
  });
});
