import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeEach, describe, expect, test, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  api: {
    createRoom: vi.fn(),
    deleteRoom: vi.fn(),
    createTag: vi.fn(),
    deleteTag: vi.fn(),
    createColor: vi.fn(),
    deleteColor: vi.fn()
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
    tags: [
      { id: 'label-1', name: 'Tools' },
      { id: 'label-2', name: 'Holiday' }
    ],
    colors: [
      { id: 'color-1', name: 'Blue', value: '#3B82F6' },
      { id: 'color-2', name: 'Red', value: '#EF4444' }
    ],
    ...overrides
  };
}

describe('rooms management route', () => {
  beforeEach(() => {
    mocks.api.createRoom.mockReset();
    mocks.api.deleteRoom.mockReset();
    mocks.api.createTag.mockReset();
    mocks.api.deleteTag.mockReset();
    mocks.api.createColor.mockReset();
    mocks.api.deleteColor.mockReset();
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
    mocks.api.createTag.mockResolvedValue({ id: 'label-3', name: 'Archive' });

    render(Page, { data: buildData() });

    await fireEvent.input(screen.getByPlaceholderText('enter tag name here'), {
      target: { value: 'Archive' }
    });
    await fireEvent.click(screen.getByRole('button', { name: /add tag/i }));

    await waitFor(() => {
      expect(mocks.api.createTag).toHaveBeenCalledWith({ name: 'Archive' });
    });

    expect(screen.getByText(/added tag archive\./i)).toBeInTheDocument();
    expect(screen.getByText('Archive')).toBeInTheDocument();
  });

  test('removes a tag from the list', async () => {
    mocks.api.deleteTag.mockResolvedValue(null);

    render(Page, { data: buildData() });

    const holidayRow = screen.getByText('Holiday').closest('.room-list-item');
    expect(holidayRow).not.toBeNull();
    await fireEvent.click(holidayRow.querySelector('button'));

    await waitFor(() => {
      expect(mocks.api.deleteTag).toHaveBeenCalledWith('label-2');
    });

    expect(screen.queryByText('Holiday')).not.toBeInTheDocument();
    expect(screen.getByText(/removed tag holiday\./i)).toBeInTheDocument();
  });

  test('creates a color and shows it in the list', async () => {
    mocks.api.createColor.mockResolvedValue({ id: 'color-3', name: 'Green', value: '#22C55E' });

    render(Page, { data: buildData() });

    await fireEvent.input(screen.getByPlaceholderText('enter color name here'), {
      target: { value: 'Green' }
    });
    await fireEvent.input(screen.getByLabelText('Hex Value'), {
      target: { value: '#22C55E' }
    });
    await fireEvent.click(screen.getByRole('button', { name: /add color/i }));

    await waitFor(() => {
      expect(mocks.api.createColor).toHaveBeenCalledWith({ name: 'Green', value: '#22C55E' });
    });

    expect(screen.getByText(/added color green\./i)).toBeInTheDocument();
    expect(screen.getByText('Green')).toBeInTheDocument();
  });

  test('removes a color from the list', async () => {
    mocks.api.deleteColor.mockResolvedValue(null);

    render(Page, { data: buildData() });

    const blueRow = screen.getByText('Blue').closest('.room-list-item');
    expect(blueRow).not.toBeNull();
    await fireEvent.click(blueRow.querySelector('button'));

    await waitFor(() => {
      expect(mocks.api.deleteColor).toHaveBeenCalledWith('color-1');
    });

    expect(screen.queryByText('Blue')).not.toBeInTheDocument();
    expect(screen.getByText(/removed color blue\./i)).toBeInTheDocument();
  });
});
