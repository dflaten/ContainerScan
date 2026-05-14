import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { tick } from 'svelte';
import { beforeEach, describe, expect, test, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  goto: vi.fn(),
  page: {
    url: new URL('http://localhost/'),
    data: {
      containers: []
    }
  }
}));

vi.mock('$app/navigation', () => ({
  afterNavigate: vi.fn(),
  goto: mocks.goto
}));

vi.mock('$app/state', () => ({
  page: mocks.page
}));

import Layout from '../../src/routes/+layout.svelte';

function buildLayoutData(overrides = {}) {
  return {
    bootstrap: {
      apiOnline: true
    },
    ...overrides
  };
}

function setPageState({ pathname = '/', containers = [] } = {}) {
  mocks.page.url = new URL(`http://localhost${pathname}`);
  mocks.page.data = { containers };
}

describe('layout header', () => {
  beforeEach(() => {
    mocks.goto.mockReset();
    setPageState();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  test('shows the API status in a popup when the status dot is clicked', async () => {
    render(Layout, { data: buildLayoutData() });

    await fireEvent.click(screen.getByRole('button', { name: /api status: online/i }));

    expect(screen.getByText('Online')).toBeInTheDocument();
  });

  test('opens an existing empty label from the header on the dashboard', async () => {
    setPageState({
      pathname: '/',
      containers: [
        {
          id: 'container-empty',
          code: 'ZZ-99',
          name: 'Container ZZ-99',
          description: '',
          room_id: '',
          label_id: '',
          tag_ids: [],
          tags: [],
          images: []
        }
      ]
    });

    render(Layout, { data: buildLayoutData() });

    await fireEvent.click(screen.getByRole('button', { name: /get label/i }));

    await waitFor(() => {
      expect(mocks.goto).toHaveBeenCalledWith('/containers/container-empty');
    });
  });

  test('redirects to print labels when no empty labels are available', async () => {
    setPageState({
      pathname: '/',
      containers: [
        {
          id: 'container-full',
          code: 'AA-11',
          name: 'Garage Box 3',
          description: 'Camping gear',
          room_id: 'room-1',
          label_id: 'label-1',
          tag_ids: ['label-1'],
          tags: [{ id: 'label-1', name: 'Tools', colour: '#AABBCC' }],
          images: []
        }
      ]
    });

    render(Layout, { data: buildLayoutData() });

    await fireEvent.click(screen.getByRole('button', { name: /get label/i }));

    await waitFor(() => {
      expect(window.confirm).toHaveBeenCalledWith(
        'No empty labels are currently available. Print a new sheet of labels before continuing?'
      );
      expect(mocks.goto).toHaveBeenCalledWith('/print?missingEmptyLabels=1');
    });
  });

  test('does not show the empty label action away from the dashboard', () => {
    setPageState({ pathname: '/rooms' });

    render(Layout, { data: buildLayoutData() });

    expect(screen.queryByRole('button', { name: /get label/i })).not.toBeInTheDocument();
  });

  test('closes the hamburger menu after a navigation item is clicked', async () => {
    const { container } = render(Layout, { data: buildLayoutData() });
    const menu = container.querySelector('.site-menu');
    const menuToggle = container.querySelector('.site-menu-toggle');

    expect(menu).not.toBeNull();
    expect(menuToggle).not.toBeNull();

    await fireEvent.click(menuToggle);

    await fireEvent.click(screen.getByRole('link', { name: /advanced search/i }));
    await tick();

    expect(menuToggle).toHaveAttribute('aria-expanded', 'false');
    expect(container.querySelector('.site-menu-panel')).toBeNull();
  });

  test('closes the hamburger menu when the page outside the menu is clicked', async () => {
    const { container } = render(Layout, { data: buildLayoutData() });
    const menuToggle = container.querySelector('.site-menu-toggle');

    expect(menuToggle).not.toBeNull();

    await fireEvent.click(menuToggle);
    await fireEvent.click(screen.getByRole('button', { name: /close navigation menu/i }));
    await tick();

    expect(menuToggle).toHaveAttribute('aria-expanded', 'false');
    expect(container.querySelector('.site-menu-panel')).toBeNull();
  });
});
