<script>
  import { createApi } from '$lib/api';

  export let data;

  const api = createApi(fetch);

  let rooms = [...data.rooms];
  let roomName = '';
  let notice = null;
  let error = null;
  let isCreatingRoom = false;
  let deletingRoomIds = new Set();

  async function handleCreateRoom() {
    const normalizedName = roomName.trim();
    if (!normalizedName) {
      error = 'Enter a room name.';
      return;
    }

    error = null;
    notice = null;
    isCreatingRoom = true;

    try {
      const createdRoom = await api.createRoom({ name: normalizedName });
      rooms = [...rooms, createdRoom].sort((left, right) => left.name.localeCompare(right.name));
      roomName = '';
      notice = `Added room ${createdRoom.name}.`;
    } catch (requestError) {
      error = requestError.detail ?? requestError.message ?? 'Unable to create the room.';
    } finally {
      isCreatingRoom = false;
    }
  }

  async function handleDeleteRoom(room) {
    error = null;
    notice = null;
    deletingRoomIds = new Set([...deletingRoomIds, room.id]);

    try {
      await api.deleteRoom(room.id);
      rooms = rooms.filter((entry) => entry.id !== room.id);
      notice = `Removed room ${room.name}.`;
    } catch (requestError) {
      error = requestError.detail ?? requestError.message ?? 'Unable to remove the room.';
    } finally {
      const nextDeletingIds = new Set(deletingRoomIds);
      nextDeletingIds.delete(room.id);
      deletingRoomIds = nextDeletingIds;
    }
  }
</script>

<svelte:head>
  <title>HomeIndex | Rooms</title>
</svelte:head>

<section class="content-grid rooms-page-grid">
  <article class="panel panel-wide">
    <div class="panel-heading">
      <span class="eyebrow">Add Room</span>
      <h2>Create a room for container storage</h2>
    </div>

    {#if notice}
      <div class="notice-banner">{notice}</div>
    {/if}

    {#if error}
      <div class="diagnostics">
        <h3>Room update failed</h3>
        <p>{error}</p>
      </div>
    {/if}

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
  </article>

  <article class="panel panel-wide">
    <div class="panel-heading">
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
  </article>
</section>
