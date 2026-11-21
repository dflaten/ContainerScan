<script>
  import { goto } from '$app/navigation';
  import { createApi } from '#lib/api';

  export let data;

  const api = createApi(fetch);
  const steps = [
    {
      eyebrow: 'Step 1',
      title: 'Name/Description',
      description: ''
    },
    {
      eyebrow: 'Step 2',
      title: 'Room/Tags/Color',
      description: ''
    },
    {
      eyebrow: 'Step 3',
      title: 'Images',
      description: ''
    }
  ];

  let container = data.container;
  let pageError = null;
  let activeStep = 0;
  let isSavingStep = false;
  let isDeletingContainer = false;
  let isUploadingImages = false;
  let activeImageAction = null;
  let imageStatusMessage = '';
  let selectedFiles = [];
  let form = buildForm(container);

  function buildForm(source) {
    return {
      name: source?.name ?? '',
      description: source?.description ?? '',
      colour: source?.colour ?? '#3B82F6',
      room_id: source?.room_id ?? '',
      tag_ids: source?.tag_ids ?? (source?.label_id ? [source.label_id] : [])
    };
  }

  function toggleTag(tagId) {
    form = {
      ...form,
      tag_ids: form.tag_ids.includes(tagId) ? form.tag_ids.filter((id) => id !== tagId) : [...form.tag_ids, tagId]
    };
  }

  async function saveMetadata() {
    pageError = null;
    isSavingStep = true;

    try {
      container = await api.updateContainer(container.id, {
        ...form,
        room_id: form.room_id || null,
        tag_ids: form.tag_ids
      });
      form = buildForm(container);
      return true;
    } catch (error) {
      pageError = error.detail ?? error.message ?? 'Unable to update the container.';
      return false;
    } finally {
      isSavingStep = false;
    }
  }

  async function handleDetailsNext() {
    const saved = await saveMetadata();
    if (saved) {
      activeStep = 1;
    }
  }

  async function handleOrganizationNext() {
    const saved = await saveMetadata();
    if (saved) {
      activeStep = 2;
    }
  }

  async function navigateToStep(targetStep) {
    if (activeImageAction || isUploadingImages) {
      return;
    }

    if (targetStep === activeStep) {
      return;
    }

    if (activeStep === 0 || activeStep === 1) {
      const saved = await saveMetadata();
      if (!saved) {
        return;
      }
    }

    activeStep = targetStep;
  }

  function handleFileSelection(event) {
    selectedFiles = Array.from(event.currentTarget.files ?? []);
    pageError = null;
  }

  function sortImages(images) {
    return [...images].sort(
      (left, right) =>
        left.sort_order - right.sort_order ||
        String(left.uploaded_at).localeCompare(String(right.uploaded_at)) ||
        String(left.id).localeCompare(String(right.id))
    );
  }

  function imageName(image, index) {
    return image.caption?.trim() || `photo ${index + 1}`;
  }

  $: hasImagesToSave = container.images.length > 0 || selectedFiles.length > 0;
  $: imageActionsDisabled = activeImageAction !== null || isUploadingImages;

  async function handleSetPrimaryImage(image, index) {
    if (image.is_primary || activeImageAction || isUploadingImages) {
      return;
    }

    pageError = null;
    imageStatusMessage = '';
    activeImageAction = { id: image.id, type: 'primary' };

    try {
      // ImageUpdate requires sort_order and would clear the caption if it were omitted.
      const updated = await api.updateImage(image.id, {
        is_primary: true,
        caption: image.caption,
        sort_order: image.sort_order
      });

      container = {
        ...container,
        images: container.images.map((item) =>
          item.id === updated.id ? { ...item, ...updated } : { ...item, is_primary: false }
        )
      };
      imageStatusMessage = `${imageName(image, index)} is now the main photo.`;
    } catch (error) {
      pageError = error.detail ?? error.message ?? 'Unable to update the main photo.';
    } finally {
      activeImageAction = null;
    }
  }

  async function handleDeleteImage(image, index) {
    if (activeImageAction || isUploadingImages) {
      return;
    }

    const name = imageName(image, index);
    const willRunOutOfImages = container.images.length === 1 && selectedFiles.length === 0;
    const lastPhotoWarning = willRunOutOfImages
      ? "\n\nYou'll need to add another photo before you can finish."
      : '';

    if (!window.confirm(`Delete "${name}"? This cannot be undone.${lastPhotoWarning}`)) {
      return;
    }

    pageError = null;
    imageStatusMessage = '';
    activeImageAction = { id: image.id, type: 'delete' };

    try {
      await api.deleteImage(image.id);

      try {
        const refreshed = await api.getContainer(container.id);
        container = { ...container, images: refreshed.images };
      } catch {
        // Fall back to local removal if the refresh fails after a successful delete.
        const remaining = sortImages(container.images.filter((item) => item.id !== image.id));

        if (image.is_primary && remaining.length > 0) {
          remaining[0] = { ...remaining[0], is_primary: true };
        }

        container = { ...container, images: remaining };
      }

      imageStatusMessage = `${name} deleted.`;
    } catch (error) {
      pageError = error.detail ?? error.message ?? 'Unable to delete the photo.';
    } finally {
      activeImageAction = null;
    }
  }

  async function handleImageFinish() {
    pageError = null;

    if (isUploadingImages || activeImageAction) {
      return;
    }

    if (selectedFiles.length === 0 && container.images.length === 0) {
      pageError = 'Choose at least one image before finishing this container.';
      return;
    }

    isUploadingImages = true;

    try {
      if (selectedFiles.length > 0) {
        await api.uploadContainerImages(container.id, { files: selectedFiles });
      }
      await goto('/');
    } catch (error) {
      pageError = error.detail ?? error.message ?? 'Unable to upload images.';
    } finally {
      isUploadingImages = false;
    }
  }

  function isDraftContainer() {
    return (
      !container.description &&
      !container.room_id &&
      (!container.tag_ids || container.tag_ids.length === 0) &&
      container.images.length === 0 &&
      container.name === `Container ${container.code}`
    );
  }

  async function handleContainerDelete() {
    pageError = null;

    if (isDeletingContainer || activeImageAction || isUploadingImages) {
      return;
    }

    if (!window.confirm(`Delete container ${container.code}? This also removes its images.`)) {
      return;
    }

    isDeletingContainer = true;

    try {
      const deletedCode = container.code;
      await api.deleteContainer(container.id);
      await goto(`/?deleted=${encodeURIComponent(deletedCode)}`);
    } catch (error) {
      pageError = error.detail ?? error.message ?? 'Unable to delete the container.';
      isDeletingContainer = false;
    }
  }

  function containerColorOptions() {
    const configuredColors = Array.isArray(data.colors) ? data.colors : [];
    const options = configuredColors.map((color) => ({ value: color.value, label: color.name }));

    if (form.colour && !options.some((option) => option.value === form.colour)) {
      options.unshift({ value: form.colour, label: form.colour });
    }

    return options;
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
  <section class="content-grid detail-grid">
    <article class="panel">
      <div class="panel-heading">
        <span class="eyebrow">Edit Container Details</span>
        {#if steps[activeStep].description}
          <p>{steps[activeStep].description}</p>
        {/if}
      </div>

      {#if isDraftContainer()}
        <div class="notice-banner">
          This container is still a blank record. Attach the printed label, then come back and add the
          contents, location, and photos.
        </div>
      {/if}

      {#if pageError}
        <div class="notice-banner notice-banner-error" role="alert">
          {pageError}
        </div>
      {/if}

      <p class="sr-only" aria-live="polite">{imageStatusMessage}</p>

      <div class="wizard-shell">
        {#if activeStep === 0}
          <form class="wizard-panel" on:submit|preventDefault={handleDetailsNext}>
            <label class="field field-disabled">
              <span>Container Code</span>
              <input value={container.code} type="text" disabled />
            </label>

            <label class="field">
              <span>Name</span>
              <input bind:value={form.name} type="text" required />
            </label>

            <label class="field field-stack">
              <span>Description</span>
              <textarea bind:value={form.description} rows="8"></textarea>
            </label>

            <div class="wizard-actions wizard-actions-end">
              <button class="primary-button" type="submit" disabled={isSavingStep}>
                {isSavingStep ? 'Saving…' : 'Next'}
              </button>
            </div>
          </form>
        {:else if activeStep === 1}
          <form class="wizard-panel" on:submit|preventDefault={handleOrganizationNext}>
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
            </div>

            <div class="field field-stack">
              <span>Tags</span>
              {#if data.tags.length === 0}
                <div class="empty-state">
                  <p>No tags available yet.</p>
                </div>
              {:else}
                <div class="tag-picker-grid">
                  {#each data.tags as tag}
                    <label class:tag-option-selected={form.tag_ids.includes(tag.id)} class="tag-option">
                      <input
                        type="checkbox"
                        checked={form.tag_ids.includes(tag.id)}
                        on:change={() => toggleTag(tag.id)}
                      />
                      <span class="container-label-chip">{tag.name}</span>
                    </label>
                  {/each}
                </div>
              {/if}
            </div>

            <label class="field">
              <span>Color</span>
              <select bind:value={form.colour} name="container_colour">
                {#each containerColorOptions() as option}
                  <option value={option.value}>{option.label}</option>
                {/each}
              </select>
            </label>

            <div class="wizard-actions">
              <button type="button" class="secondary-button" on:click={() => navigateToStep(0)}>Back</button>
              <button class="primary-button" type="submit" disabled={isSavingStep}>
                {isSavingStep ? 'Saving…' : 'Next'}
              </button>
            </div>
          </form>
        {:else}
          <section class="wizard-panel">
            <div class="upload-strip">
              <div class="upload-strip-copy">
                <span class="eyebrow">Add Photos</span>
                {#if container.images.length > 0}
                  <span>{container.images.length} already saved</span>
                {/if}
              </div>

              {#if container.images.length > 0}
                <div class="existing-images">
                  <div class="existing-images-grid">
                    {#each container.images as image, index (image.id)}
                      <figure class:existing-image-primary={image.is_primary} class="existing-image-card">
                        <img class="existing-image-thumb" src={image.url} alt={image.caption || container.name} />
                        <figcaption class="existing-image-actions">
                          {#if image.is_primary}
                            <span class="image-primary-badge">Main photo</span>
                          {:else}
                            <button
                              type="button"
                              class="image-action-button"
                              aria-label={`Set as main photo for ${imageName(image, index)}`}
                              disabled={imageActionsDisabled}
                              on:click={() => handleSetPrimaryImage(image, index)}
                            >
                              {activeImageAction?.id === image.id && activeImageAction.type === 'primary'
                                ? 'Saving…'
                                : 'Set as main'}
                            </button>
                          {/if}
                          <button
                            type="button"
                            class="image-delete-button"
                            aria-label={`Delete ${imageName(image, index)}`}
                            disabled={imageActionsDisabled}
                            on:click={() => handleDeleteImage(image, index)}
                          >
                            {activeImageAction?.id === image.id && activeImageAction.type === 'delete'
                              ? 'Deleting…'
                              : 'Delete'}
                          </button>
                        </figcaption>
                      </figure>
                    {/each}
                  </div>
                </div>
              {/if}

              <label class="upload-picker">
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  disabled={imageActionsDisabled}
                  on:change={handleFileSelection}
                />
                <span>{selectedFiles.length > 0 ? 'Change Images' : 'Choose Images'}</span>
              </label>
            </div>

            {#if selectedFiles.length > 0}
              <div class="selection-summary">
                <strong>{selectedFiles.length} image{selectedFiles.length === 1 ? '' : 's'} selected</strong>
                <ul class="selection-list">
                  {#each selectedFiles as file}
                    <li>{file.name}</li>
                  {/each}
                </ul>
              </div>
            {/if}

            {#if !hasImagesToSave}
              <div class="empty-state">
                <p>Add at least one photo to finish this container.</p>
              </div>
            {/if}

            <div class="wizard-actions">
              <button
                type="button"
                class="secondary-button"
                disabled={imageActionsDisabled}
                on:click={() => navigateToStep(1)}
              >
                Back
              </button>
              <button
                class="primary-button"
                type="button"
                disabled={imageActionsDisabled || !hasImagesToSave}
                on:click={handleImageFinish}
              >
                {isUploadingImages ? 'Uploading…' : 'Finish'}
              </button>
            </div>
          </section>
        {/if}
      </div>

      <div class="bottom-stepper" aria-label="Edit container steps">
        {#each steps as step, index}
          <button
            type="button"
            class:bottom-stepper-item-active={index === activeStep}
            class="bottom-stepper-item"
            aria-label={`Go to ${step.title}`}
            aria-current={index === activeStep ? 'step' : undefined}
            disabled={imageActionsDisabled}
            on:click={() => navigateToStep(index)}
          >
            <span class="bottom-stepper-dot" aria-hidden="true">{index + 1}</span>
            <span class="sr-only">{step.title}</span>
          </button>
        {/each}
      </div>
    </article>
  </section>

  <div class="detail-page-actions">
    <button
      class="button-danger"
      type="button"
      disabled={isDeletingContainer || imageActionsDisabled}
      on:click={handleContainerDelete}
    >
      {isDeletingContainer ? 'Deleting…' : 'Delete Container'}
    </button>
  </div>
{/if}
