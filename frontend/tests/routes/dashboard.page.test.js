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

import Page from '../../src/routes/+page.svelte';

function buildDashboardData(overrides = {}) {
  return {
    createdContainerId: 'container-1',
    deletedContainerCode: '',
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

describe('dashboard route', () => {
  beforeEach(() => {
    mocks.goto.mockReset();
    vi.useRealTimers();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  test('shows a created-container notice with a detail link', () => {
    render(Page, { data: buildDashboardData() });

    expect(screen.getByText(/created aa-11\./i)).toBeInTheDocument();
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
      screen.getByText(/create your first container to start building the inventory\./i)
    ).toBeInTheDocument();
  });

  test('shows tracked-container and empty-label counts in the overview', () => {
    render(Page, {
      data: buildDashboardData({
        createdContainerId: '',
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
          },
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
      })
    });

    expect(screen.getByText('Containers tracked')).toBeInTheDocument();
    expect(screen.getAllByText('Empty Labels').length).toBeGreaterThan(0);
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  test('shows empty labels in a separate section and removes the documented subheading', () => {
    render(Page, {
      data: buildDashboardData({
        createdContainerId: '',
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
          },
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
      })
    });

    expect(screen.queryByText('Documented')).not.toBeInTheDocument();
    expect(screen.getAllByText('Empty Labels')).toHaveLength(2);
    expect(screen.getByText(/ready for use/i)).toBeInTheDocument();
  });

  test('shows a deleted-container notice when returning from the detail page', () => {
    render(
      Page,
      { data: buildDashboardData({ createdContainerId: '', deletedContainerCode: 'AA-11' }) }
    );

    expect(screen.getByText(/deleted container aa-11\./i)).toBeInTheDocument();
  });

  test('applies the search filter after typing into the search field', async () => {
    vi.useFakeTimers();
    render(Page, { data: buildDashboardData() });

    await fireEvent.input(screen.getByPlaceholderText(/lights, manuals, el-03/i), {
      target: { value: 'camping gear' }
    });

    vi.advanceTimersByTime(300);

    await waitFor(() => {
      expect(mocks.goto).toHaveBeenCalledWith('/?search=camping+gear', {
        replaceState: true,
        keepFocus: true,
        noScroll: true
      });
    });
  });

  test('shows only the search control on the landing page filters panel', () => {
    render(Page, { data: buildDashboardData() });

    expect(screen.getByLabelText('Search')).toBeInTheDocument();
    expect(screen.queryByLabelText('Room')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Label')).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /advanced search/i })).toHaveAttribute(
      'href',
      '/advanced-search'
    );
  });

  test('opens an existing empty label from the dashboard', async () => {
    render(Page, {
      data: buildDashboardData({
        createdContainerId: '',
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
      })
    });

    await fireEvent.click(screen.getByRole('button', { name: /get empty label/i }));

    await waitFor(() => {
      expect(mocks.goto).toHaveBeenCalledWith('/containers/container-empty');
    });
  });

  test('redirects to print labels when no empty labels are available', async () => {
    render(Page, {
      data: buildDashboardData({
        createdContainerId: '',
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
      })
    });

    await fireEvent.click(screen.getByRole('button', { name: /get empty label/i }));

    await waitFor(() => {
      expect(window.confirm).toHaveBeenCalledWith(
        'No empty labels are currently available. Print a new sheet of labels before continuing?'
      );
      expect(mocks.goto).toHaveBeenCalledWith('/print?missingEmptyLabels=1');
    });
  });

  test('does not redirect to print labels when the confirmation is canceled', async () => {
    window.confirm.mockReturnValue(false);

    render(Page, {
      data: buildDashboardData({
        createdContainerId: '',
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
      })
    });

    await fireEvent.click(screen.getByRole('button', { name: /get empty label/i }));

    await waitFor(() => {
      expect(window.confirm).toHaveBeenCalled();
    });
    expect(mocks.goto).not.toHaveBeenCalled();
  });

  test('shows the inventory section before the empty-label section', () => {
    render(
      Page,
      {
        data: buildDashboardData({
          createdContainerId: '',
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
            },
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
        })
      }
    );

    const sectionLabels = screen
      .getAllByText(/Inventory|Empty Labels/, { selector: '.eyebrow' })
      .map((node) => node.textContent);
    expect(sectionLabels.indexOf('Inventory')).toBeLessThan(sectionLabels.indexOf('Empty Labels'));
  });
});
