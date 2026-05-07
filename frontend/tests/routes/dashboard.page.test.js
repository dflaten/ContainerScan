import { render, screen } from '@testing-library/svelte';
import { describe, expect, test } from 'vitest';

import Page from '../../src/routes/+page.svelte';

function buildDashboardData(overrides = {}) {
  return {
    createdContainerId: 'container-1',
    filters: {
      search: '',
      room_id: '',
      label_id: ''
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
        images: []
      }
    ],
    rooms: [{ id: 'room-1', name: 'Garage' }],
    labels: [{ id: 'label-1', name: 'Tools', colour: '#AABBCC' }],
    ...overrides
  };
}

describe('dashboard route', () => {
  test('shows a created-container notice with a detail link', () => {
    render(Page, { data: buildDashboardData() });

    expect(screen.getByText(/created aa-11 for garage box 3\./i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /open detail view/i })).toHaveAttribute(
      'href',
      '/containers/container-1'
    );
  });

  test('shows the empty-state guidance when no containers match', () => {
    render(Page, {
      data: buildDashboardData({
        createdContainerId: '',
        containers: []
      })
    });

    expect(screen.getByText(/no containers matched\./i)).toBeInTheDocument();
    expect(
      screen.getByText(/add sample data or create your first container to populate the dashboard\./i)
    ).toBeInTheDocument();
  });
});
