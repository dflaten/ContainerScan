<script>
  import { createApi } from '$lib/api';

  export let data;

  const api = createApi(fetch);

  let rooms = [...data.rooms];
  let labels = [...data.labels];
  let roomName = '';
  let labelName = '';
  let labelColour = '#A86720';
  let roomNotice = null;
  let roomError = null;
  let labelNotice = null;
  let labelError = null;
  let isCreatingRoom = false;
  let isCreatingLabel = false;
  let deletingRoomIds = new Set();
  let deletingLabelIds = new Set();

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

  async function handleCreateLabel() {
    const normalizedName = labelName.trim();
    if (!normalizedName) {
      labelError = 'Enter a label name.';
      return;
    }

    labelError = null;
    labelNotice = null;
    isCreatingLabel = true;

    try {
      const createdLabel = await api.createLabel({ name: normalizedName, colour: labelColour });
      labels = [...labels, createdLabel].sort((left, right) => left.name.localeCompare(right.name));
      labelName = '';
      labelColour = '#A86720';
      labelNotice = `Added label ${createdLabel.name}.`;
    } catch (requestError) {
      labelError = requestError.detail ?? requestError.message ?? 'Unable to create the label.';
    } finally {
      isCreatingLabel = false;
    }
  }

  async function handleDeleteLabel(label) {
    labelError = null;
    labelNotice = null;
    deletingLabelIds = new Set([...deletingLabelIds, label.id]);

    try {
      await api.deleteLabel(label.id);
      labels = labels.filter((entry) => entry.id !== label.id);
      labelNotice = `Removed label ${label.name}.`;
    } catch (requestError) {
      labelError = requestError.detail ?? requestError.message ?? 'Unable to remove the label.';
    } finally {
      const nextDeletingIds = new Set(deletingLabelIds);
      nextDeletingIds.delete(label.id);
      deletingLabelIds = nextDeletingIds;
    }
  }
</script>

<svelte:head>
  <title>HomeIndex | Rooms & Labels</title>
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
    {#if labelNotice}
      <div class="notice-banner">{labelNotice}</div>
    {/if}

    {#if labelError}
      <div class="diagnostics">
        <h3>Label update failed</h3>
        <p>{labelError}</p>
      </div>
    {/if}

    <section class="resource-section">
      <div class="panel-heading resource-section-heading">
        <span class="eyebrow">Labels</span>
        <h2>Create and remove labels for container organization</h2>
      </div>

      <form class="label-create-form" on:submit|preventDefault={handleCreateLabel}>
        <div class="editor-columns">
          <label class="field field-stack">
            <span>Label Name</span>
            <input bind:value={labelName} type="text" placeholder="enter label name here" />
          </label>

          <label class="field field-stack">
            <span>Label Colour</span>
            <input bind:value={labelColour} class="label-colour-input" type="color" />
            <small class="field-note">{labelColour}</small>
          </label>
        </div>

        <div class="form-actions">
          <button type="submit" disabled={isCreatingLabel}>
            {isCreatingLabel ? 'Adding…' : 'Add Label'}
          </button>
        </div>
      </form>
    </section>

    <section class="resource-section resource-section-secondary">
      <div class="panel-heading resource-section-heading room-list-heading">
        <span class="eyebrow">Remove Labels</span>
        <h2>Current label list</h2>
      </div>

      {#if labels.length === 0}
        <div class="empty-state">
          <h3>No labels yet.</h3>
          <p>Add your first label above so it can be assigned to containers.</p>
        </div>
      {:else}
        <div class="room-list">
          {#each labels as label (label.id)}
            <article class="room-list-item">
              <div class="room-list-copy room-list-copy-labelled">
                <strong>{label.name}</strong>
                <span class="container-label-chip">
                  <span class="label-swatch" style={`background: ${label.colour};`}></span>
                  {label.colour}
                </span>
              </div>

              <button
                class="room-remove-button"
                type="button"
                disabled={deletingLabelIds.has(label.id)}
                on:click={() => handleDeleteLabel(label)}
              >
                {deletingLabelIds.has(label.id) ? 'Removing…' : 'Remove'}
              </button>
            </article>
          {/each}
        </div>
      {/if}
    </section>
  </article>
</section>
