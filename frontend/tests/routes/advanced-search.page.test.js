import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { beforeEach, describe, expect, test, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  goto: vi.fn()
}));

vi.mock('$app/navigation', () => ({
  goto: mocks.goto
}));

vi.mock('$app/state', () => ({
  navigating: {
    to: null
  }
}));

import Page from '../../src/routes/advanced-search/+page.svelte';

function buildData(overrides = {}) {
  return {
    filters: {
      search: '',
      room_id: '',
      tag_id: ''
    },
    containerError: null,
    containers: [
      {
        id: 'container-1',
        code: 'AA-11',
        name: 'Garage Box 3',
        description: 'Camping gear',
        room_id: 'room-1',
        label_id: 'label-1',
        tag_ids: ['label-1'],
        tags: [{ id: 'label-1', name: 'Tools', colour: '#AABBCC' }],
        images: []
      }
    ],
    rooms: [{ id: 'room-1', name: 'Garage' }],
    tags: [{ id: 'label-1', name: 'Tools', colour: '#AABBCC' }],
    ...overrides
  };
}

describe('advanced search route', () => {
  beforeEach(() => {
    mocks.goto.mockReset();
    vi.useRealTimers();
  });

  test('shows room and tag filters', () => {
    render(Page, { data: buildData() });

    expect(screen.getByLabelText('Search')).toBeInTheDocument();
    expect(screen.getByLabelText('Room')).toBeInTheDocument();
    expect(screen.getByLabelText('Tag')).toBeInTheDocument();
  });

  test('applies room and tag filters through advanced-search navigation', async () => {
    render(Page, {
      data: buildData({
        filters: {
          search: '',
          room_id: 'room-1',
          tag_id: 'label-1'
        }
      })
    });

    await fireEvent.change(screen.getByLabelText('Room'), {
      target: { value: 'room-1' }
    });

    await waitFor(() => {
      expect(mocks.goto).toHaveBeenCalledWith('/advanced-search?room_id=room-1&tag_id=label-1', {
        replaceState: true,
        keepFocus: true,
        noScroll: true
      });
    });
  });
});
