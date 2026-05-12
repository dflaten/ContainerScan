<script>
  import { goto } from '$app/navigation';
  import { createApi } from '$lib/api';

  export let data;

  const roomOptions = data.rooms;
  const labelOptions = data.labels;

  let form = {
    name: '',
    room_id: '',
    label_id: ''
  };
  let isSubmitting = false;
  let submitError = null;

  async function handleCreate() {
    submitError = null;

    isSubmitting = true;
    const api = createApi(fetch);

    try {
      const createdContainer = await api.createContainer({
        name: form.name || null,
        room_id: form.room_id || null,
        label_id: form.label_id || null
      });
      await goto(`/containers/${createdContainer.id}?created=1`);
    } catch (error) {
      submitError = error.detail ?? error.message ?? 'Unable to generate the container label.';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<svelte:head>
  <title>HomeIndex | Generate Label</title>
</svelte:head>

<section class="hero-panel">
  <span class="eyebrow">Generate Label</span>
  <h1>Create the record first, fill in the box later.</h1>
  <p>
    Generate a new code and print the QR label now. You can come back after packing the container to
    add the contents, location, label, and photos.
  </p>

  <div class="hero-actions">
    <a class="secondary-link" href="/">Back to dashboard</a>
  </div>
</section>

<section class="content-grid">
  <article class="panel panel-wide">
    <div class="panel-heading">
      <span class="eyebrow">Label Setup</span>
      <h2>Generate a new container code</h2>
    </div>

    <form class="editor-grid" on:submit|preventDefault={handleCreate}>
      <div class="editor-main">
        <label class="field">
          <span>Quick Name</span>
          <input
            bind:value={form.name}
            type="text"
            name="name"
            placeholder="Optional, for example Garage Bin"
          />
          <small class="field-note">
            Leave this blank if you just want to generate the label first.
          </small>
        </label>

        <div class="editor-columns">
          <label class="field">
            <span>Room</span>
            <select bind:value={form.room_id} name="room_id">
              <option value="">Not set</option>
              {#each roomOptions as room}
                <option value={room.id}>{room.name}</option>
              {/each}
            </select>
          </label>

          <label class="field">
            <span>Tag</span>
            <select bind:value={form.label_id} name="label_id">
              <option value="">Not set</option>
              {#each labelOptions as label}
                <option value={label.id}>{label.name}</option>
              {/each}
            </select>
          </label>
        </div>
      </div>

      <aside class="editor-side">
        <div class="support-card">
          <span class="eyebrow">Recommended Flow</span>
          <h3>Generate, print, attach</h3>
          <p>
            After the record is created you can download the QR label immediately. Add the packed
            contents and photos later from the detail page.
          </p>
        </div>

        {#if submitError}
          <div class="diagnostics">
            <h3>Could not generate label</h3>
            <p>{submitError}</p>
          </div>
        {/if}

        <div class="form-actions">
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Generating…' : 'Generate Container Label'}
          </button>
          <a class="text-link" href="/">Cancel</a>
        </div>
      </aside>
    </form>
  </article>
</section>
