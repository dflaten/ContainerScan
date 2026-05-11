<script>
  import { goto } from '$app/navigation';
  import { createApi } from '$lib/api';

  export let data;

  const api = createApi(fetch);

  let container = data.container;
  let metadataError = null;
  let metadataNotice = data.createdNotice
    ? 'Label ready. Download it now, then add the container details whenever you pack it.'
    : null;
  let imageNotice = null;
  let imageError = null;
  let isSavingMetadata = false;
  let isDeletingContainer = false;
  let isUploadingImages = false;
  let uploadInput;
  let form = buildForm(container);
  let imageRows = buildImageRows(container);

  function buildForm(source) {
    return {
      name: source?.name ?? '',
      description: source?.description ?? '',
      room_id: source?.room_id ?? '',
      label_id: source?.label_id ?? ''
    };
  }

  function buildImageRows(source) {
    if (!source) {
      return [];
    }

    return [...source.images]
      .sort((left, right) => left.sort_order - right.sort_order || Number(right.is_primary) - Number(left.is_primary))
      .map((image) => ({
        id: image.id,
        url: image.url,
        uploaded_at: image.uploaded_at,
        caption: image.caption ?? '',
        sort_order: image.sort_order,
        is_primary: image.is_primary
      }));
  }

  async function reloadContainer(notice = null, { preserveForm = false } = {}) {
    const refreshed = await api.getContainer(container.id);
    container = refreshed;
    if (!preserveForm) {
      form = buildForm(refreshed);
    }
    imageRows = buildImageRows(refreshed);

    if (notice) {
      imageNotice = notice;
    }
  }

  async function handleMetadataSave() {
    metadataError = null;
    metadataNotice = null;
    isSavingMetadata = true;

    try {
      container = await api.updateContainer(container.id, {
        ...form,
        room_id: form.room_id || null,
        label_id: form.label_id || null
      });
      form = buildForm(container);
      metadataNotice = 'Container details updated.';
    } catch (error) {
      metadataError = error.detail ?? error.message ?? 'Unable to update the container.';
    } finally {
      isSavingMetadata = false;
    }
  }

  async function handleImageUpload(event) {
    imageError = null;
    imageNotice = null;

    const files = Array.from(event.currentTarget.files ?? []);
    if (files.length === 0) {
      imageError = 'Choose at least one image to upload.';
      return;
    }

    isUploadingImages = true;

    try {
      await api.uploadContainerImages(container.id, { files });
      if (uploadInput) {
        uploadInput.value = '';
      }
      await reloadContainer(`Uploaded ${files.length} image${files.length === 1 ? '' : 's'}.`, {
        preserveForm: true
      });
    } catch (error) {
      imageError = error.detail ?? error.message ?? 'Unable to upload images.';
    } finally {
      isUploadingImages = false;
    }
  }

  async function saveImageRow(row) {
    imageError = null;
    imageNotice = null;

    try {
      await api.updateImage(row.id, {
        caption: row.caption,
        sort_order: Number(row.sort_order),
        is_primary: row.is_primary
      });
      await reloadContainer('Image metadata updated.', { preserveForm: true });
    } catch (error) {
      imageError = error.detail ?? error.message ?? 'Unable to update the image.';
    }
  }

  async function removeImage(row) {
    imageError = null;
    imageNotice = null;

    try {
      await api.deleteImage(row.id);
      await reloadContainer('Image removed.', { preserveForm: true });
    } catch (error) {
      imageError = error.detail ?? error.message ?? 'Unable to delete the image.';
    }
  }

  function roomNameFor(roomId) {
    return data.rooms.find((room) => room.id === roomId)?.name ?? 'Not set';
  }

  function labelFor(labelId) {
    return data.labels.find((label) => label.id === labelId) ?? null;
  }

  function isDraftContainer() {
    return (
      !container.description &&
      !container.room_id &&
      !container.label_id &&
      container.images.length === 0 &&
      container.name === `Container ${container.code}`
    );
  }

  async function handleContainerDelete() {
    metadataError = null;
    metadataNotice = null;

    if (!window.confirm(`Delete container ${container.code}? This also removes its images.`)) {
      return;
    }

    isDeletingContainer = true;

    try {
      const deletedCode = container.code;
      await api.deleteContainer(container.id);
      await goto(`/?deleted=${encodeURIComponent(deletedCode)}`);
    } catch (error) {
      metadataError = error.detail ?? error.message ?? 'Unable to delete the container.';
      isDeletingContainer = false;
    }
  }
</script>

<svelte:head>
  <title>HomeIndex | {container ? container.code : 'Container'}</title>
</svelte:head>

{#if data.containerError || !container}
  <section class="panel">
    <div class="panel-heading">
      <span class="eyebrow">Container</span>
      <h2>Container detail</h2>
    </div>

    <div class="diagnostics">
      <h3>Could not load container</h3>
      <p>{data.containerError ?? 'This container is unavailable.'}</p>
    </div>
  </section>
{:else}
  {@const currentLabel = labelFor(form.label_id)}

  <a class="floating-dashboard-link" href="/" aria-label="Back to dashboard" title="Back to dashboard">
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M3 13.2L12 5l9 8.2v7.3a1.5 1.5 0 0 1-1.5 1.5h-4.7v-6.2h-5.6V22H4.5A1.5 1.5 0 0 1 3 20.5z"
        fill="currentColor"
      />
    </svg>
  </a>

  <section class="content-grid detail-grid">
    <article class="panel">
      <div class="panel-heading">
        <span class="eyebrow">Edit Container Details</span>
      </div>

      {#if isDraftContainer()}
        <div class="notice-banner">
          This container is still a blank record. Attach the printed label, then come back and add the
          contents, location, and photos.
        </div>
      {/if}

      {#if metadataNotice}
        <div class="notice-banner">{metadataNotice}</div>
      {/if}

      {#if metadataError}
        <div class="diagnostics">
          <h3>Update failed</h3>
          <p>{metadataError}</p>
        </div>
      {/if}

      <form class="editor-grid" on:submit|preventDefault={handleMetadataSave}>
        <div class="editor-main">
          <label class="field">
            <span>Container Code</span>
            <input value={container.code} type="text" disabled />
            <small class="field-note">Immutable after creation so printed labels stay accurate.</small>
          </label>

          <label class="field">
            <span>Name</span>
            <input bind:value={form.name} type="text" required />
          </label>

          <label class="field field-stack">
            <span>Description</span>
            <textarea bind:value={form.description} rows="8"></textarea>
          </label>

          <div class="editor-columns">
            <label class="field">
              <span>Room</span>
              <select bind:value={form.room_id}>
                <option value="">Not set</option>
                {#each data.rooms as room}
                  <option value={room.id}>{room.name}</option>
                {/each}
              </select>
            </label>

            <label class="field">
              <span>Label</span>
              <select bind:value={form.label_id}>
                <option value="">Not set</option>
                {#each data.labels as label}
                  <option value={label.id}>{label.name}</option>
                {/each}
              </select>
            </label>
          </div>
        </div>

        <aside class="editor-side">
          <div class="support-card">
            <span class="eyebrow">Primary Photo</span>
            <h3>Keep the outside visible</h3>
            <p>
              Start with an exterior photo once the label is attached. Contents photos can follow after that.
            </p>
          </div>

          <div class="form-actions">
            <button type="submit" disabled={isSavingMetadata}>
              {isSavingMetadata ? 'Saving…' : 'Save Changes'}
            </button>
            <button
              class="button-danger"
              type="button"
              disabled={isDeletingContainer}
              on:click={handleContainerDelete}
            >
              {isDeletingContainer ? 'Deleting…' : 'Delete Container'}
            </button>
          </div>
        </aside>
      </form>
    </article>

    <article class="panel panel-wide">
      <div class="panel-heading">
        <span class="eyebrow">Images</span>
        <h2>Manage container photos</h2>
      </div>

      {#if imageNotice}
        <div class="notice-banner">{imageNotice}</div>
      {/if}

      {#if imageError}
        <div class="diagnostics">
          <h3>Image action failed</h3>
          <p>{imageError}</p>
        </div>
      {/if}

      <div class="upload-strip">
        <div class="upload-strip-copy">
          <span class="eyebrow">Add Photos</span>
          <h3>{isUploadingImages ? 'Uploading images…' : 'Drop in the next photos for this container'}</h3>
          <p>
            Start with the exterior/storage-location photo, then add contents images after it.
          </p>
        </div>

        <label class="upload-picker">
          <input
            bind:this={uploadInput}
            type="file"
            accept="image/*"
            multiple
            disabled={isUploadingImages}
            on:change={handleImageUpload}
          />
          <span>{isUploadingImages ? 'Uploading…' : 'Choose Images'}</span>
        </label>
      </div>

      {#if container.images.length === 0}
        <div class="empty-state">
          <h3>No images uploaded yet.</h3>
          <p>Add the exterior photo first so scans show the right physical container immediately.</p>
        </div>
      {:else}
        <div class="image-editor-grid">
          {#each imageRows as row (row.id)}
            <article class="image-editor-card">
              <img class="image-editor-preview" src={row.url} alt={row.caption || container.name} />

              <div class="image-editor-body">
                <div class="image-editor-topline">
                  <strong>{row.is_primary ? 'Primary exterior photo' : 'Secondary image'}</strong>
                  <span>Uploaded {new Date(row.uploaded_at).toLocaleDateString()}</span>
                </div>

                <label class="field field-stack">
                  <span>Caption</span>
                  <input bind:value={row.caption} type="text" placeholder="Front shelf view" />
                </label>

                <div class="editor-columns image-editor-controls">
                  <label class="field">
                    <span>Sort Order</span>
                    <input bind:value={row.sort_order} type="number" min="0" />
                  </label>

                  <label class="checkbox-field">
                    <input bind:checked={row.is_primary} type="checkbox" />
                    <span>Use as primary image</span>
                  </label>
                </div>

                <div class="form-actions">
                  <button type="button" on:click={() => saveImageRow(row)}>Save Image Details</button>
                  <button class="button-danger" type="button" on:click={() => removeImage(row)}>
                    Delete Image
                  </button>
                </div>
              </div>
            </article>
          {/each}
        </div>
      {/if}
    </article>
  </section>

  <div class="detail-page-actions">
    <a class="primary-link" href={api.getQrDownloadPath(container.id)}>Download QR Label</a>
  </div>
{/if}
