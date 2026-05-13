<script>
  export let data;

  let currentImageIndex = 0;
  let currentScanImage = null;
  let lightboxImage = null;

  function labelColour() {
    return data.container?.tags?.[0]?.colour ?? data.container?.label?.colour ?? '#4A7560';
  }

  function goToPreviousImage() {
    if (!data.container?.images.length) {
      return;
    }

    currentImageIndex =
      (currentImageIndex - 1 + data.container.images.length) % data.container.images.length;
  }

  function goToNextImage() {
    if (!data.container?.images.length) {
      return;
    }

    currentImageIndex = (currentImageIndex + 1) % data.container.images.length;
  }

  function openLightbox(image) {
    lightboxImage = image;
  }

  function closeLightbox() {
    lightboxImage = null;
  }

  $: if (data.container?.images?.length && currentImageIndex > data.container.images.length - 1) {
    currentImageIndex = 0;
  }
  $: currentScanImage = data.container?.images?.[currentImageIndex] ?? null;
</script>

<svelte:head>
  <title>HomeIndex | {data.container ? data.container.code : 'Scan'}</title>
</svelte:head>

{#if data.containerError || !data.container}
  <section class="scan-shell">
    <article class="scan-card">
      <div class="diagnostics">
        <h2>Could not load container</h2>
        <p>{data.containerError ?? 'This container is unavailable.'}</p>
      </div>
    </article>
  </section>
{:else}
  <section class="scan-shell" style={`--scan-accent: ${labelColour()};`}>
    <article class="scan-card">
      <header class="scan-header">
        <span class="scan-code">{data.container.code}</span>
        <h1>{data.container.name}</h1>
        <div class="scan-meta">
          <span class="scan-pill">
            {data.container.room?.name ?? 'Room not set'}
          </span>
          {#each data.container.tags ?? [] as tag}
            <span class="scan-pill scan-pill-label">{tag.name}</span>
          {/each}
        </div>
        <div class="scan-header-actions">
          <a class="scan-edit-link" href={`/containers/${data.container.id}`}>
            Edit Container Details
          </a>
        </div>
      </header>

      <div class="scan-content">
        <section class="scan-section">
          <span class="eyebrow">Description</span>
          <p class="scan-description">
            {data.container.description || 'This container has not been documented yet.'}
          </p>
        </section>

        <section class="scan-section">
          <span class="eyebrow">Images</span>

          {#if data.container.images.length === 0}
            <div class="empty-state">
              <h2>No images yet.</h2>
              <p>The container record exists, but no photos have been uploaded for this box.</p>
            </div>
          {:else}
            <div class="scan-gallery-shell">
              <div class="scan-gallery-topline">
                <span class="scan-gallery-count">
                  Image {currentImageIndex + 1} of {data.container.images.length}
                </span>
              </div>

              <figure class="scan-figure scan-figure-active">
                <button
                  class="scan-image-button"
                  type="button"
                  on:click={() => openLightbox(currentScanImage)}
                  aria-label={`Open full-size image ${currentImageIndex + 1}`}
                >
                  <img
                    src={currentScanImage.url}
                    alt={currentScanImage.caption || data.container.name}
                    loading="lazy"
                  />
                </button>
                <figcaption>
                  {currentScanImage.caption ||
                    (currentScanImage.is_primary ? 'Primary exterior photo' : 'Container image')}
                </figcaption>
              </figure>

              {#if data.container.images.length > 1}
                <div class="scan-gallery-controls">
                  <button type="button" class="secondary-link" on:click={goToPreviousImage}>
                    Previous Photo
                  </button>
                  <button type="button" class="secondary-link" on:click={goToNextImage}>
                    Next Photo
                  </button>
                </div>
              {/if}
            </div>
          {/if}
        </section>
      </div>
    </article>
  </section>
{/if}

{#if lightboxImage}
  <div class="scan-lightbox" role="dialog" aria-modal="true" aria-label="Full-size container image">
    <button class="scan-lightbox-close" type="button" on:click={closeLightbox} aria-label="Close full-size image">
      Close
    </button>
    <img class="scan-lightbox-image" src={lightboxImage.url} alt={lightboxImage.caption || data.container.name} />
  </div>
{/if}
