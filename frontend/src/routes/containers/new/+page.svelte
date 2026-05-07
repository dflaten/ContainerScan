<script>
  import { goto } from '$app/navigation';
  import { createApi } from '$lib/api';

  export let data;

  const roomOptions = data.rooms;
  const labelOptions = data.labels;

  let form = {
    name: '',
    description: '',
    room_id: roomOptions[0]?.id ?? '',
    label_id: labelOptions[0]?.id ?? ''
  };
  let selectedFiles;
  let isSubmitting = false;
  let submitError = null;

  async function handleCreate() {
    submitError = null;

    if (!form.room_id || !form.label_id) {
      submitError = 'At least one room and one label are required before creating a container.';
      return;
    }

    isSubmitting = true;
    const api = createApi(fetch);
    let createdContainer = null;

    try {
      createdContainer = await api.createContainer(form);
      const files = selectedFiles ? Array.from(selectedFiles) : [];

      if (files.length > 0) {
        await api.uploadContainerImages(createdContainer.id, { files });
      }

      await goto(`/?created=${createdContainer.id}`);
    } catch (error) {
      if (createdContainer !== null) {
        await goto(`/containers/${createdContainer.id}?created=1&image_upload_error=1`);
        return;
      }

      submitError = error.detail ?? error.message ?? 'Unable to create the container.';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<svelte:head>
  <title>ContainerScan | Create Container</title>
</svelte:head>

<section class="hero-panel">
  <span class="eyebrow">Task 15</span>
  <h1>Create a container with its first images in one pass.</h1>
  <p>
    Assign the room and label up front, then optionally add the first photos now. The first uploaded
    image should show the outside of the container and where it is physically stored.
  </p>

  <div class="hero-actions">
    <a class="secondary-link" href="/">Back to dashboard</a>
  </div>
</section>

<section class="content-grid">
  <article class="panel panel-wide">
    <div class="panel-heading">
      <span class="eyebrow">New Container</span>
      <h2>Container setup</h2>
    </div>

    {#if roomOptions.length === 0 || labelOptions.length === 0}
      <div class="diagnostics">
        <h3>Reference data required</h3>
        <p>
          The create flow needs at least one room and one label. Seed or create those records first,
          then return here.
        </p>
      </div>
    {:else}
      <form class="editor-grid" on:submit|preventDefault={handleCreate}>
        <div class="editor-main">
          <label class="field">
            <span>Name</span>
            <input bind:value={form.name} type="text" name="name" placeholder="Garage Box 3" required />
          </label>

          <label class="field field-stack">
            <span>Description</span>
            <textarea
              bind:value={form.description}
              name="description"
              rows="7"
              placeholder="Camping stove, lantern mantles, spare fuel bottles, tent stakes."
            ></textarea>
          </label>

          <div class="editor-columns">
            <label class="field">
              <span>Room</span>
              <select bind:value={form.room_id} name="room_id" required>
                {#each roomOptions as room}
                  <option value={room.id}>{room.name}</option>
                {/each}
              </select>
            </label>

            <label class="field">
              <span>Label</span>
              <select bind:value={form.label_id} name="label_id" required>
                {#each labelOptions as label}
                  <option value={label.id}>{label.name}</option>
                {/each}
              </select>
            </label>
          </div>
        </div>

        <aside class="editor-side">
          <div class="support-card">
            <span class="eyebrow">First Image Rule</span>
            <h3>Start with the exterior</h3>
            <p>
              The first uploaded image becomes the primary photo. Use it to show the outside of the
              container and its storage location before you add contents photos.
            </p>
          </div>

          <label class="field field-stack">
            <span>Initial Images</span>
            <input bind:files={selectedFiles} type="file" name="images" accept="image/*" multiple />
            <small class="field-note">
              Optional. If you upload multiple images now, the first one will become the primary
              exterior/storage-location photo.
            </small>
          </label>

          {#if submitError}
            <div class="diagnostics">
              <h3>Could not create container</h3>
              <p>{submitError}</p>
            </div>
          {/if}

          <div class="form-actions">
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating…' : 'Create Container'}
            </button>
            <a class="text-link" href="/">Cancel</a>
          </div>
        </aside>
      </form>
    {/if}
  </article>
</section>
