import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, test, vi } from 'vitest';

import Page from '../../src/routes/print/+page.svelte';

function buildContainer(overrides = {}) {
  return {
    id: 'container-1',
    code: 'AA-11',
    name: 'Garage Box 3',
    room_id: 'room-1',
    label_id: 'label-1',
    ...overrides
  };
}

function buildData(overrides = {}) {
  return {
    containers: [buildContainer(), buildContainer({ id: 'container-2', code: 'BB-22' })],
    labels: [{ id: 'label-1', name: 'Tools', colour: '#AABBCC' }],
    printError: null,
    rooms: [{ id: 'room-1', name: 'Garage' }],
    selectedIds: ['container-1'],
    selectedContainers: [buildContainer()],
    ...overrides
  };
}

describe('print route', () => {
  test('renders a printable tile for each selected container', () => {
    render(Page, { data: buildData() });

    expect(
      screen.getByRole('heading', { name: /1 label selected across 1 sheet/i })
    ).toBeInTheDocument();
    expect(screen.getByAltText(/qr label for aa-11/i)).toHaveAttribute(
      'src',
      '/api/containers/container-1/qr'
    );
  });

  test('renders select-all and clear-selection links for choosing which labels to print', () => {
    render(Page, { data: buildData() });

    expect(screen.getByRole('link', { name: /select all/i })).toHaveAttribute(
      'href',
      '/print?id=container-1&id=container-2'
    );
    expect(screen.getByRole('link', { name: /clear selection/i })).toHaveAttribute(
      'href',
      '/print'
    );
  });

  test('calls window.print from the toolbar action', async () => {
    const printSpy = vi.spyOn(window, 'print').mockImplementation(() => {});

    render(Page, { data: buildData() });
    await fireEvent.click(screen.getByRole('button', { name: /print selected labels/i }));

    expect(printSpy).toHaveBeenCalled();
  });
});
