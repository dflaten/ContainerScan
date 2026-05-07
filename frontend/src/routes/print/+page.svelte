<script>
  export let data;

  const LABELS_PER_ROW = 3;
  const ROWS_PER_PAGE = 4;
  const LABELS_PER_PAGE = LABELS_PER_ROW * ROWS_PER_PAGE;
  const TILE_SIZE_INCHES = 3;

  function roomNameFor(container) {
    return data.rooms.find((room) => room.id === container.room_id)?.name ?? 'Room not set';
  }

  function labelFor(container) {
    return data.labels.find((label) => label.id === container.label_id) ?? null;
  }

  function qrPathFor(containerId) {
    return `/api/containers/${containerId}/qr`;
  }

  function tileColourFor(container) {
    return labelFor(container)?.colour ?? '#FFFFFF';
  }

  function printLabels() {
    window.print();
  }

  function chunkContainers(containers) {
    const pages = [];

    for (let index = 0; index < containers.length; index += LABELS_PER_PAGE) {
      pages.push(containers.slice(index, index + LABELS_PER_PAGE));
    }

    return pages;
  }

  function buildSelectionHref(containerIds) {
    if (containerIds.length === 0) {
      return '/print';
    }

    const params = new URLSearchParams();

    for (const containerId of containerIds) {
      params.append('id', containerId);
    }

    return `/print?${params.toString()}`;
  }

  $: selectedPages = chunkContainers(data.selectedContainers);
</script>

<svelte:head>
  <title>HomeIndex | Print Labels</title>
</svelte:head>

<section class="hero-panel print-toolbar">
  <span class="eyebrow">Print</span>
  <h1>Batch QR label sheet.</h1>
  <p>
    Select exactly which containers to include, then print 3 by 3 inch labels packed onto a
    9 by 12 inch sheet.
  </p>

  <div class="hero-actions">
    <a class="secondary-link" href="/">Back to dashboard</a>
    <button type="button" on:click={printLabels} disabled={data.selectedContainers.length === 0}>
      Print Selected Labels
    </button>
  </div>
</section>

{#if data.printError}
  <section class="panel">
    <div class="diagnostics">
      <h2>Could not load containers</h2>
      <p>{data.printError}</p>
    </div>
  </section>
{:else}
  <section class="content-grid print-grid-layout">
    <article class="panel">
      <div class="panel-heading">
        <span class="eyebrow">Selection</span>
        <h2>Choose containers for this print run</h2>
      </div>

      <div class="notice-banner print-spec-banner">
        {data.selectedContainers.length} selected. {LABELS_PER_PAGE} labels fit on each 9 by 12
        sheet at {TILE_SIZE_INCHES} by {TILE_SIZE_INCHES} inches each.
      </div>

      {#if data.containers.length === 0}
        <div class="empty-state">
          <h3>No containers available.</h3>
          <p>Create a container first, then return here to print its QR label.</p>
        </div>
      {:else}
        <form class="print-selection-form" method="GET">
          <div class="print-selection-actions">
            <a class="secondary-link" href={buildSelectionHref(data.containers.map((container) => container.id))}>
              Select All
            </a>
            <a class="secondary-link" href="/print">Clear Selection</a>
          </div>

          <div class="print-selection-list">
            {#each data.containers as container}
              {@const label = labelFor(container)}
              <label class="print-select-card">
                <input
                  type="checkbox"
                  name="id"
                  value={container.id}
                  checked={data.selectedIds.includes(container.id)}
                />
                <div>
                  <div class="card-topline">
                    <span class="container-code">{container.code}</span>
                    {#if label}
                      <span class="container-label-chip">
                        <span
                          class="label-swatch"
                          style={`background: ${label.colour};`}
                        ></span>
                        {label.name}
                      </span>
                    {/if}
                  </div>
                  <strong>{container.name}</strong>
                  <p>{roomNameFor(container)}</p>
                </div>
              </label>
            {/each}
          </div>

          <div class="form-actions">
            <button type="submit">Update Print Sheet</button>
          </div>
        </form>
      {/if}
    </article>

    <article class="panel panel-wide print-sheet-panel">
      <div class="panel-heading print-toolbar">
        <span class="eyebrow">Sheet Preview</span>
        <h2>
          {data.selectedContainers.length} label{data.selectedContainers.length === 1 ? '' : 's'} selected
          across {selectedPages.length || 0} sheet{selectedPages.length === 1 ? '' : 's'}
        </h2>
      </div>

      {#if data.selectedContainers.length === 0}
        <div class="empty-state">
          <h3>No labels selected yet.</h3>
          <p>Choose one or more containers from the left, then update the sheet before printing.</p>
        </div>
      {:else}
        <div class="print-sheet-pages" aria-label="Printable label sheet">
          {#each selectedPages as page, pageIndex}
            <section class="print-page">
              <div class="print-page-meta">
                <strong>Sheet {pageIndex + 1}</strong>
                <span>
                  Up to {LABELS_PER_PAGE} labels per sheet, {LABELS_PER_ROW} across and {ROWS_PER_PAGE} down
                </span>
              </div>

              <div class="print-sheet">
                {#each page as container}
                  <article class="print-tile" style={`--print-tile-colour: ${tileColourFor(container)};`}>
                    <header class="print-tile-header">
                      <span class="print-tile-code">{container.code}</span>
                    </header>
                    <div class="print-tile-qr">
                      <img src={qrPathFor(container.id)} alt={`QR label for ${container.code}`} />
                    </div>
                    <footer class="print-tile-footer">
                      <strong>{container.name}</strong>
                      <span>{roomNameFor(container)}</span>
                    </footer>
                  </article>
                {/each}
              </div>
            </section>
          {/each}
        </div>
      {/if}
    </article>
  </section>
{/if}
