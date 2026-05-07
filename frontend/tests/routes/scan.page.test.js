import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, test } from 'vitest';

import Page from '../../src/routes/scan/[id]/+page.svelte';

function buildData(overrides = {}) {
  return {
    container: {
      id: 'container-1',
      code: 'AA-11',
      name: 'Garage Box 3',
      description: 'Camping gear and lanterns',
      room: { id: 'room-1', name: 'Garage' },
      label: { id: 'label-1', name: 'Tools', colour: '#AABBCC' },
      images: [
        {
          id: 'image-1',
          url: '/images/garage-box.jpg',
          caption: 'Front shelf view',
          is_primary: true
        },
        {
          id: 'image-2',
          url: '/images/garage-box-inside.jpg',
          caption: 'Inside the box',
          is_primary: false
        }
      ]
    },
    containerError: null,
    ...overrides
  };
}

describe('scan route', () => {
  test('renders the container code, room, description, and image captions', () => {
    render(Page, { data: buildData() });

    expect(screen.getByText('AA-11')).toBeInTheDocument();
    expect(screen.getByText('Garage')).toBeInTheDocument();
    expect(screen.getByText(/camping gear and lanterns/i)).toBeInTheDocument();
    expect(screen.getByText(/front shelf view/i)).toBeInTheDocument();
    expect(screen.getByText(/image 1 of 2/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /edit container details/i })).toHaveAttribute(
      'href',
      '/containers/container-1'
    );
  });

  test('shows the empty-image guidance when no images exist', () => {
    render(
      Page,
      {
        data: buildData({
          container: {
            ...buildData().container,
            images: []
          }
        })
      }
    );

    expect(screen.getByText(/no images yet\./i)).toBeInTheDocument();
  });

  test('paginates through images and opens a full-size viewer', async () => {
    render(Page, { data: buildData() });

    await fireEvent.click(screen.getByRole('button', { name: /next photo/i }));
    expect(screen.getByText(/inside the box/i)).toBeInTheDocument();
    expect(screen.getByText(/image 2 of 2/i)).toBeInTheDocument();

    await fireEvent.click(screen.getByRole('button', { name: /open full-size image 2/i }));
    expect(screen.getByRole('dialog', { name: /full-size container image/i })).toBeInTheDocument();

    await fireEvent.click(screen.getByRole('button', { name: /close full-size image/i }));
    expect(screen.queryByRole('dialog', { name: /full-size container image/i })).not.toBeInTheDocument();
  });
});
