<script>
  import { goto } from '$app/navigation';
  import { createApi } from '$lib/api';

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

  function handleFileSelection(event) {
    selectedFiles = Array.from(event.currentTarget.files ?? []);
    pageError = null;
  }

  async function handleImageFinish() {
    pageError = null;

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
              <button type="button" class="secondary-button" on:click={() => (activeStep = 0)}>Back</button>
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
                    {#each container.images as image (image.id)}
                      <img class="existing-image-thumb" src={image.url} alt={image.caption || container.name} />
                    {/each}
                  </div>
                </div>
              {/if}

              <label class="upload-picker">
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  disabled={isUploadingImages}
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

            <div class="wizard-actions">
              <button type="button" class="secondary-button" disabled={isUploadingImages} on:click={() => (activeStep = 1)}>
                Back
              </button>
              <button class="primary-button" type="button" disabled={isUploadingImages} on:click={handleImageFinish}>
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
            on:click={() => (activeStep = index)}
          >
            <span class="bottom-stepper-dot" aria-hidden="true">{index + 1}</span>
            <span class="sr-only">{step.title}</span>
          </button>
        {/each}
      </div>
    </article>
  </section>

  <div class="detail-page-actions">
    <button class="button-danger" type="button" disabled={isDeletingContainer} on:click={handleContainerDelete}>
      {isDeletingContainer ? 'Deleting…' : 'Delete Container'}
    </button>
  </div>
{/if}
