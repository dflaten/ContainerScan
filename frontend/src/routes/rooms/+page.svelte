<script>
  import { createApi } from '$lib/api';

  export let data;

  const api = createApi(fetch);

  let rooms = [...data.rooms];
  let tags = [...data.tags];
  let colors = [...data.colors];
  let roomName = '';
  let tagName = '';
  let colorName = '';
  let colorValue = '#3B82F6';
  let roomNotice = null;
  let roomError = null;
  let tagNotice = null;
  let tagError = null;
  let colorNotice = null;
  let colorError = null;
  let isCreatingRoom = false;
  let isCreatingTag = false;
  let isCreatingColor = false;
  let deletingRoomIds = new Set();
  let deletingTagIds = new Set();
  let deletingColorIds = new Set();

  async function handleCreateRoom() {
    const normalizedName = roomName.trim();
    if (!normalizedName) {
      roomError = 'Enter a room name.';
      return;
    }

    roomError = null;
    roomNotice = null;
    isCreatingRoom = true;

    try {
      const createdRoom = await api.createRoom({ name: normalizedName });
      rooms = [...rooms, createdRoom].sort((left, right) => left.name.localeCompare(right.name));
      roomName = '';
      roomNotice = `Added room ${createdRoom.name}.`;
    } catch (requestError) {
      roomError = requestError.detail ?? requestError.message ?? 'Unable to create the room.';
    } finally {
      isCreatingRoom = false;
    }
  }

  async function handleDeleteRoom(room) {
    roomError = null;
    roomNotice = null;
    deletingRoomIds = new Set([...deletingRoomIds, room.id]);

    try {
      await api.deleteRoom(room.id);
      rooms = rooms.filter((entry) => entry.id !== room.id);
      roomNotice = `Removed room ${room.name}.`;
    } catch (requestError) {
      roomError = requestError.detail ?? requestError.message ?? 'Unable to remove the room.';
    } finally {
      const nextDeletingIds = new Set(deletingRoomIds);
      nextDeletingIds.delete(room.id);
      deletingRoomIds = nextDeletingIds;
    }
  }

  async function handleCreateTag() {
    const normalizedName = tagName.trim();
    if (!normalizedName) {
      tagError = 'Enter a tag name.';
      return;
    }

    tagError = null;
    tagNotice = null;
    isCreatingTag = true;

    try {
      const createdTag = await api.createTag({ name: normalizedName });
      tags = [...tags, createdTag].sort((left, right) => left.name.localeCompare(right.name));
      tagName = '';
      tagNotice = `Added tag ${createdTag.name}.`;
    } catch (requestError) {
      tagError = requestError.detail ?? requestError.message ?? 'Unable to create the tag.';
    } finally {
      isCreatingTag = false;
    }
  }

  async function handleDeleteTag(tag) {
    tagError = null;
    tagNotice = null;
    deletingTagIds = new Set([...deletingTagIds, tag.id]);

    try {
      await api.deleteTag(tag.id);
      tags = tags.filter((entry) => entry.id !== tag.id);
      tagNotice = `Removed tag ${tag.name}.`;
    } catch (requestError) {
      tagError = requestError.detail ?? requestError.message ?? 'Unable to remove the tag.';
    } finally {
      const nextDeletingIds = new Set(deletingTagIds);
      nextDeletingIds.delete(tag.id);
      deletingTagIds = nextDeletingIds;
    }
  }

  async function handleCreateColor() {
    const normalizedName = colorName.trim();
    const normalizedValue = colorValue.trim().toUpperCase();
    if (!normalizedName) {
      colorError = 'Enter a color name.';
      return;
    }

    colorError = null;
    colorNotice = null;
    isCreatingColor = true;

    try {
      const createdColor = await api.createColor({ name: normalizedName, value: normalizedValue });
      colors = [...colors, createdColor].sort((left, right) => left.name.localeCompare(right.name));
      colorName = '';
      colorValue = '#3B82F6';
      colorNotice = `Added color ${createdColor.name}.`;
    } catch (requestError) {
      colorError = requestError.detail ?? requestError.message ?? 'Unable to create the color.';
    } finally {
      isCreatingColor = false;
    }
  }

  async function handleDeleteColor(color) {
    colorError = null;
    colorNotice = null;
    deletingColorIds = new Set([...deletingColorIds, color.id]);

    try {
      await api.deleteColor(color.id);
      colors = colors.filter((entry) => entry.id !== color.id);
      colorNotice = `Removed color ${color.name}.`;
    } catch (requestError) {
      colorError = requestError.detail ?? requestError.message ?? 'Unable to remove the color.';
    } finally {
      const nextDeletingIds = new Set(deletingColorIds);
      nextDeletingIds.delete(color.id);
      deletingColorIds = nextDeletingIds;
    }
  }
</script>

<svelte:head>
  <title>HomeIndex | Rooms, Tags & Colors</title>
</svelte:head>

<section class="content-grid rooms-page-grid">
  <article class="panel">
    {#if roomNotice}
      <div class="notice-banner">{roomNotice}</div>
    {/if}

    {#if roomError}
      <div class="diagnostics">
        <h3>Room update failed</h3>
        <p>{roomError}</p>
      </div>
    {/if}

    <div class="panel-heading">
      <span class="eyebrow">Rooms</span>
    </div>

    <form class="room-create-form" on:submit|preventDefault={handleCreateRoom}>
      <label class="field field-stack">
        <span>Room Name</span>
        <input bind:value={roomName} type="text" placeholder="enter room name here" />
      </label>

      <div class="form-actions">
        <button type="submit" disabled={isCreatingRoom}>
          {isCreatingRoom ? 'Adding…' : 'Add Room'}
        </button>
      </div>
    </form>

    <div class="resource-list-divider" aria-hidden="true"></div>

    {#if rooms.length === 0}
      <div class="empty-state">
        <h3>No rooms yet.</h3>
        <p>Add your first storage location above so it can be used in container details.</p>
      </div>
    {:else}
      <div class="room-list">
        {#each rooms as room (room.id)}
          <article class="room-list-item">
            <div class="room-list-copy">
              <strong>{room.name}</strong>
            </div>

            <button
              class="room-remove-button"
              type="button"
              disabled={deletingRoomIds.has(room.id)}
              on:click={() => handleDeleteRoom(room)}
            >
              {deletingRoomIds.has(room.id) ? 'Removing…' : 'Remove'}
            </button>
          </article>
        {/each}
      </div>
    {/if}
  </article>

  <article class="panel">
    {#if tagNotice}
      <div class="notice-banner">{tagNotice}</div>
    {/if}

    {#if tagError}
      <div class="diagnostics">
        <h3>Tag update failed</h3>
        <p>{tagError}</p>
      </div>
    {/if}

    <div class="panel-heading">
      <span class="eyebrow">Tags</span>
    </div>

    <form class="label-create-form" on:submit|preventDefault={handleCreateTag}>
      <label class="field field-stack">
        <span>Tag Name</span>
        <input bind:value={tagName} type="text" placeholder="enter tag name here" />
      </label>

      <div class="form-actions">
        <button type="submit" disabled={isCreatingTag}>
          {isCreatingTag ? 'Adding…' : 'Add Tag'}
        </button>
      </div>
    </form>

    <div class="resource-list-divider" aria-hidden="true"></div>

    {#if tags.length === 0}
      <div class="empty-state">
        <h3>No tags yet.</h3>
        <p>Add your first tag above so it can be assigned to containers.</p>
      </div>
    {:else}
      <div class="room-list">
        {#each tags as tag (tag.id)}
          <article class="room-list-item">
            <div class="room-list-copy">
              <strong>{tag.name}</strong>
            </div>

            <button
              class="room-remove-button"
              type="button"
              disabled={deletingTagIds.has(tag.id)}
              on:click={() => handleDeleteTag(tag)}
            >
              {deletingTagIds.has(tag.id) ? 'Removing…' : 'Remove'}
            </button>
          </article>
        {/each}
      </div>
    {/if}
  </article>

  <article class="panel">
    {#if colorNotice}
      <div class="notice-banner">{colorNotice}</div>
    {/if}

    {#if colorError}
      <div class="diagnostics">
        <h3>Color update failed</h3>
        <p>{colorError}</p>
      </div>
    {/if}

    <div class="panel-heading">
      <span class="eyebrow">Colors</span>
    </div>

    <form class="label-create-form" on:submit|preventDefault={handleCreateColor}>
      <label class="field field-stack">
        <span>Color Name</span>
        <input bind:value={colorName} type="text" placeholder="enter color name here" />
      </label>

      <label class="field field-stack">
        <span>Hex Value</span>
        <div class="color-picker-row">
          <input bind:value={colorValue} type="color" aria-label="Hex Value" />
          <span class="container-label-chip">{colorValue}</span>
        </div>
      </label>

      <div class="form-actions">
        <button type="submit" disabled={isCreatingColor}>
          {isCreatingColor ? 'Adding…' : 'Add Color'}
        </button>
      </div>
    </form>

    <div class="resource-list-divider" aria-hidden="true"></div>

    {#if colors.length === 0}
      <div class="empty-state">
        <h3>No colors yet.</h3>
        <p>Add your first container color above.</p>
      </div>
    {:else}
      <div class="room-list">
        {#each colors as color (color.id)}
          <article class="room-list-item">
            <div class="room-list-copy">
              <strong>{color.name}</strong>
              <span class="container-label-chip">
                <span class="label-swatch" style={`background: ${color.value};`}></span>
                {color.value}
              </span>
            </div>

            <button
              class="room-remove-button"
              type="button"
              disabled={deletingColorIds.has(color.id)}
              on:click={() => handleDeleteColor(color)}
            >
              {deletingColorIds.has(color.id) ? 'Removing…' : 'Remove'}
            </button>
          </article>
        {/each}
      </div>
    {/if}
  </article>
</section>
