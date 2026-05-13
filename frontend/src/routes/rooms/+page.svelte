<script>
  import { createApi } from '$lib/api';

  export let data;

  const api = createApi(fetch);
  const tagColourOptions = [
    { value: '#3B82F6', label: 'Blue' },
    { value: '#FACC15', label: 'Yellow' },
    { value: '#EF4444', label: 'Red' },
    { value: '#22C55E', label: 'Green' }
  ];

  let rooms = [...data.rooms];
  let tags = [...data.tags];
  let roomName = '';
  let tagName = '';
  let tagColour = '#3B82F6';
  let roomNotice = null;
  let roomError = null;
  let tagNotice = null;
  let tagError = null;
  let isCreatingRoom = false;
  let isCreatingTag = false;
  let deletingRoomIds = new Set();
  let deletingTagIds = new Set();

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
      const createdTag = await api.createTag({ name: normalizedName, colour: tagColour });
      tags = [...tags, createdTag].sort((left, right) => left.name.localeCompare(right.name));
      tagName = '';
      tagColour = '#3B82F6';
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
</script>

<svelte:head>
  <title>HomeIndex | Rooms & Tags</title>
</svelte:head>

<section class="content-grid rooms-page-grid">
  <article class="panel panel-wide">
    {#if roomNotice}
      <div class="notice-banner">{roomNotice}</div>
    {/if}

    {#if roomError}
      <div class="diagnostics">
        <h3>Room update failed</h3>
        <p>{roomError}</p>
      </div>
    {/if}

    <section class="resource-section">
      <div class="panel-heading resource-section-heading">
        <span class="eyebrow">Rooms</span>
        <h2>Create a room for container storage</h2>
      </div>

      <form class="room-create-form" on:submit|preventDefault={handleCreateRoom}>
        <label class="field field-stack">
          <span>Room Name</span>
          <input bind:value={roomName} type="text" placeholder="enter room name here" />
          <small class="field-note">
            Use room names that will be easy to recognize later when assigning containers.
          </small>
        </label>

        <div class="form-actions">
          <button type="submit" disabled={isCreatingRoom}>
            {isCreatingRoom ? 'Adding…' : 'Add Room'}
          </button>
        </div>
      </form>
    </section>

    <section class="resource-section resource-section-secondary">
      <div class="panel-heading resource-section-heading">
        <span class="eyebrow">Remove Rooms</span>
        <h2>Current room list</h2>
      </div>

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
    </section>
  </article>

  <article class="panel panel-wide">
    {#if tagNotice}
      <div class="notice-banner">{tagNotice}</div>
    {/if}

    {#if tagError}
      <div class="diagnostics">
        <h3>Tag update failed</h3>
        <p>{tagError}</p>
      </div>
    {/if}

    <section class="resource-section">
      <div class="panel-heading resource-section-heading">
        <span class="eyebrow">Tags</span>
        <h2>Create and remove tags for container organization</h2>
      </div>

      <form class="label-create-form" on:submit|preventDefault={handleCreateTag}>
        <div class="editor-columns">
          <label class="field field-stack">
            <span>Tag Name</span>
            <input bind:value={tagName} type="text" placeholder="enter tag name here" />
          </label>

          <label class="field field-stack">
            <span>Tag Colour</span>
            <div class="tag-colour-options" role="radiogroup" aria-label="Tag Colour">
              {#each tagColourOptions as option}
                <label class:tag-colour-option-selected={tagColour === option.value} class="tag-colour-option">
                  <input bind:group={tagColour} type="radio" name="tag_colour" value={option.value} />
                  <span class="label-swatch" style={`background: ${option.value};`}></span>
                  <span>{option.label}</span>
                </label>
              {/each}
            </div>
          </label>
        </div>

        <div class="form-actions">
          <button type="submit" disabled={isCreatingTag}>
            {isCreatingTag ? 'Adding…' : 'Add Tag'}
          </button>
        </div>
      </form>
    </section>

    <section class="resource-section resource-section-secondary">
      <div class="panel-heading resource-section-heading room-list-heading">
        <span class="eyebrow">Remove Tags</span>
        <h2>Current tag list</h2>
      </div>

      {#if tags.length === 0}
        <div class="empty-state">
          <h3>No tags yet.</h3>
          <p>Add your first tag above so it can be assigned to containers.</p>
        </div>
      {:else}
        <div class="room-list">
          {#each tags as tag (tag.id)}
            <article class="room-list-item">
              <div class="room-list-copy room-list-copy-labelled">
                <strong>{tag.name}</strong>
                <span class="container-label-chip">
                  <span class="label-swatch" style={`background: ${tag.colour};`}></span>
                  {tag.colour}
                </span>
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
    </section>
  </article>
</section>
