<script>
  export let form;
  export let data;

  const LABELS_PER_ROW = 2;
  const ROWS_PER_PAGE = 3;
  const LABELS_PER_PAGE = LABELS_PER_ROW * ROWS_PER_PAGE;

  function qrSrcFor(container) {
    return data.qrImageUrls?.[container.id] ?? '';
  }

  function printLabels() {
    window.print();
  }

  function chunkContainers(containers) {
    return containers.length === 0 ? [] : [containers.slice(0, LABELS_PER_PAGE)];
  }

  $: selectedPages = chunkContainers(data.selectedContainers);
</script>

<svelte:head>
  <title>HomeIndex | Print Labels</title>
</svelte:head>

<section class="hero-panel print-toolbar">
  <span class="eyebrow">Print</span>
  <p>
    Generate one brand-new sheet of six QR labels, review the preview, then create and print it
    on a letter-sized page with cutting space between each label.
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

  <section class="panel print-sheet-panel">
      <div class="panel-heading print-toolbar">
        <span class="eyebrow">New Sheet</span>
        <h2>
          {#if data.selectedContainers.length === 0}
            Preview one fresh page of labels
          {:else}
            {data.selectedContainers.length} new label{data.selectedContainers.length === 1 ? '' : 's'} ready for one sheet
          {/if}
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
        {:else}
          <p>Generate a new six-label sheet, review the preview, then create and print it.</p>
        {/if}
      </div>

      <div class="notice-banner print-spec-banner">
        {#if data.draftSheet}
          Draft full-sheet preview. Confirm with Create Full Sheet to generate and save {LABELS_PER_PAGE} new labels.
        {:else if data.savedSheet}
          Saved sheet ready to print. This page shows one 2 by 3 sheet of QR labels.
        {:else}
          One sheet at a time. Each page holds {LABELS_PER_PAGE} labels arranged {LABELS_PER_ROW} across and {ROWS_PER_PAGE} down.
        {/if}
      </div>

      <div class="notice-banner print-tip-banner">
        For clean output, disable browser headers and footers in the print dialog before printing.
      </div>

      {#if data.selectedContainers.length === 0}
        <div class="empty-state">
          <h3>No draft sheet yet.</h3>
          <p>Use Preview New Full Sheet above to generate a brand-new page of labels before printing.</p>
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
                  <article class="print-tile" style="--print-tile-colour: #FFFFFF;">
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
  </section>
{/if}
