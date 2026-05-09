<script>
  export let form;
  export let data;

  const LABELS_PER_ROW = 2;
  const ROWS_PER_PAGE = 3;
  const LABELS_PER_PAGE = LABELS_PER_ROW * ROWS_PER_PAGE;
  const TILE_SIZE_INCHES = 3;

  function roomNameFor(container) {
    return data.rooms.find((room) => room.id === container.room_id)?.name ?? 'Room not set';
  }

  function labelFor(container) {
    return data.labels.find((label) => label.id === container.label_id) ?? null;
  }

  function qrSrcFor(container) {
    return data.qrImageUrls?.[container.id] ?? '';
  }

  function tileColourFor(container) {
    return labelFor(container)?.colour ?? '#FFFFFF';
  }

  function printLabels() {
    window.print();
  }

  function chunkContainers(containers) {
    return containers.length === 0 ? [] : [containers.slice(0, LABELS_PER_PAGE)];
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
  <p>
    Select exactly which containers to include, preview the sheet, then save it before printing
    3 by 3 inch labels arranged with cutting space on a letter-sized sheet.
  </p>

  <div class="print-action-layout">
    <article class="print-action-card">
      <span class="eyebrow">New Labels</span>
      <h2>Fill one fresh sheet</h2>
      <p>Preview a full page of brand-new labels, then confirm them into saved containers.</p>
      <div class="print-action-buttons">
        <form method="POST" action="?/previewFullSheet">
          <button class="print-action-button print-action-button-primary" type="submit">
            Preview New Full Sheet
          </button>
        </form>
      </div>
    </article>

    <article class="print-action-card print-action-card-muted">
      <span class="eyebrow">Current Preview</span>
      <h2>Print what you are looking at</h2>
      <p>Once the preview looks right, print it directly or save it from the selection panel below.</p>
      <div class="print-action-buttons">
        <button
          class="print-action-button print-action-button-ghost"
          type="button"
          on:click={printLabels}
          disabled={data.selectedContainers.length === 0}
        >
          Print Current Preview
        </button>
      </div>
    </article>
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
  {#if form?.previewFullSheetError}
    <section class="panel">
      <div class="diagnostics">
        <h2>Could not preview full sheet</h2>
        <p>{form.previewFullSheetError}</p>
      </div>
    </section>
  {/if}

  {#if form?.createFullSheetError}
    <section class="panel">
      <div class="diagnostics">
        <h2>Could not create full sheet</h2>
        <p>{form.createFullSheetError}</p>
      </div>
    </section>
  {/if}

  {#if data.createdFullSheet && data.savedSheet}
    <section class="panel">
      <div class="notice-banner print-spec-banner">
        Created {data.savedSheet.containers.length} brand-new labels and saved them to sheet {data.savedSheet.id.slice(0, 8)}.
      </div>
    </section>
  {/if}

  {#if data.createdSheet && data.savedSheet}
    <section class="panel">
      <div class="notice-banner print-spec-banner">
        Saved sheet {data.savedSheet.id.slice(0, 8)} with {data.savedSheet.containers.length} label{data.savedSheet.containers.length === 1 ? '' : 's'}.
      </div>
    </section>
  {/if}

  <section class="content-grid print-grid-layout">
    <article class="panel">
      <div class="panel-heading">
        <span class="eyebrow">Selection</span>
        <h2>Choose containers for this print run</h2>
      </div>

      <div class="notice-banner print-spec-banner">
        {#if data.draftSheet}
          Draft full-sheet preview. Confirm with Create Full Sheet to generate and save {LABELS_PER_PAGE} new labels.
        {:else}
          One sheet at a time. {Math.min(data.selectedContainers.length, LABELS_PER_PAGE)} selected and up to {LABELS_PER_PAGE}
          labels fit on each letter sheet at {TILE_SIZE_INCHES} by {TILE_SIZE_INCHES} inches each.
        {/if}
      </div>

      <div class="notice-banner print-tip-banner">
        For clean output, disable browser headers and footers in the print dialog before printing.
      </div>

      {#if data.draftSheet}
        <div class="empty-state">
          <h3>Full-sheet draft is active.</h3>
          <p>
            This preview is not saved yet. Click Create Full Sheet to generate these {LABELS_PER_PAGE}
            new label-first containers and store the sheet.
          </p>
        </div>
      {:else if data.containers.length === 0}
        <div class="empty-state">
          <h3>No containers available.</h3>
          <p>Create a container first, then return here to print its QR label.</p>
        </div>
      {:else}
        <details
          class="print-selection-details"
          open={data.selectedIds.length > 0 || !!form?.createSheetError}
        >
          <summary class="print-selection-summary">
            <div>
              <span class="eyebrow">Existing Labels</span>
              <strong>Build a saved sheet from containers you already made</strong>
              <p>Open this list when you want to reuse labels that already exist in HomeIndex.</p>
            </div>
          </summary>

          <div class="print-selection-body">
            {#if form?.createSheetError}
              <div class="diagnostics">
                <h3>Could not create sheet</h3>
                <p>{form.createSheetError}</p>
              </div>
            {/if}

            <form id="print-selection-form" class="print-selection-form" method="GET">
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
                <button type="submit">Update Preview</button>
                <button type="submit" formaction="?/createSheet" formmethod="POST">Create Sheet</button>
              </div>
            </form>
          </div>
        </details>
      {/if}
    </article>

    <article class="panel panel-wide print-sheet-panel">
      <div class="panel-heading print-toolbar">
        <span class="eyebrow">Sheet Preview</span>
        <h2>
          {data.selectedContainers.length} label{data.selectedContainers.length === 1 ? '' : 's'} selected
          across {selectedPages.length || 0} sheet{selectedPages.length === 1 ? '' : 's'}
        </h2>
        {#if data.savedSheet}
          <p>
            Saved sheet {data.savedSheet.id.slice(0, 8)} created on
            {new Date(data.savedSheet.created_at).toLocaleString()}.
          </p>
        {:else if data.draftSheet}
          <p>
            Draft preview only. These labels are not saved until you click Create Full Sheet.
          </p>
        {/if}
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
                      <img
                        src={qrSrcFor(container)}
                        alt={`QR label for ${container.code}`}
                      />
                    </div>
                  </article>
                {/each}
              </div>
            </section>
          {/each}
        </div>

        {#if data.draftSheet}
          <div class="print-preview-actions">
            <form method="POST" action="?/createFullSheet">
              {#each data.draftSheet.containers as container}
                <input type="hidden" name="draft_id" value={container.id} />
                <input type="hidden" name="draft_code" value={container.code} />
              {/each}
              <button class="print-action-button print-action-button-accent" type="submit">
                Create Full Sheet
              </button>
            </form>
            <button
              class="print-action-button print-action-button-ghost"
              type="button"
              on:click={printLabels}
              disabled={data.selectedContainers.length === 0}
            >
              Print This Sheet
            </button>
          </div>
        {:else if data.selectedContainers.length > 0}
          <div class="print-preview-actions">
            <button
              class="print-action-button print-action-button-ghost"
              type="button"
              on:click={printLabels}
            >
              Print This Sheet
            </button>
          </div>
        {/if}
      {/if}
    </article>
  </section>
{/if}
