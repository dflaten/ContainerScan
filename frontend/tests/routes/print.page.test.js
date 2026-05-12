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
    missingEmptyLabelsNotice: false,
    printError: null,
    qrImageUrls: { 'container-1': 'data:image/png;base64,abc123' },
    selectedContainers: [buildContainer()],
    ...overrides
  };
}

describe('print route', () => {
  test('renders a printable tile for each selected container', () => {
    render(Page, { data: buildData() });

    expect(
      screen.getByRole('heading', { name: /1 new label ready for one sheet/i })
    ).toBeInTheDocument();
    expect(screen.getByAltText(/qr label for aa-11/i)).toHaveAttribute(
      'src',
      'data:image/png;base64,abc123'
    );
  });

  test('renders the new full-sheet action', () => {
    render(Page, { data: buildData() });

    expect(screen.getByRole('button', { name: /preview new full sheet/i })).toBeInTheDocument();
  });

  test('shows a notice when redirected because no empty labels are available', () => {
    render(Page, {
      data: buildData({
        missingEmptyLabelsNotice: true,
        selectedContainers: []
      })
    });

    expect(
      screen.getByText(/no empty labels are currently available\./i)
    ).toBeInTheDocument();
  });

  test('calls window.print from the toolbar action', async () => {
    const printSpy = vi.spyOn(window, 'print').mockImplementation(() => {});

    render(Page, { data: buildData() });
    await fireEvent.click(screen.getByRole('button', { name: /print this sheet/i }));

    expect(printSpy).toHaveBeenCalled();
  });
});
