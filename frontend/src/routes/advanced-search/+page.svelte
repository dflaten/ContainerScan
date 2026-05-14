<script>
  import { goto } from '$app/navigation';
  import { navigating } from '$app/state';

  export let data;

  let filters = {
    search: data.filters.search,
    room_id: data.filters.room_id,
    tag_id: data.filters.tag_id
  };
  let lastSyncedFilters = {
    search: data.filters.search,
    room_id: data.filters.room_id,
    tag_id: data.filters.tag_id
  };
  let searchTimer;

  function roomNameFor(roomId) {
    return data.rooms.find((room) => room.id === roomId)?.name ?? 'Not set';
  }

  function tagsFor(container) {
    return container.tags ?? [];
  }

  function primaryImageFor(container) {
    return container.images.find((image) => image.is_primary) ?? container.images[0] ?? null;
  }

  function isPendingContainer(container) {
    return (
      !container.description &&
      !container.room_id &&
      (!container.tag_ids || container.tag_ids.length === 0) &&
      container.images.length === 0 &&
      container.name === `Container ${container.code}`
    );
  }

  function isFilterActive() {
    return Boolean(data.filters.search || data.filters.room_id || data.filters.tag_id);
  }

  function buildAdvancedSearchQuery(nextFilters) {
    const params = new URLSearchParams();

    if (nextFilters.search) {
      params.set('search', nextFilters.search);
    }
    if (nextFilters.room_id) {
      params.set('room_id', nextFilters.room_id);
    }
    if (nextFilters.tag_id) {
      params.set('tag_id', nextFilters.tag_id);
    }

    const query = params.toString();
    return query ? `/advanced-search?${query}` : '/advanced-search';
  }

  async function applyFilters() {
    await goto(buildAdvancedSearchQuery(filters), {
      replaceState: true,
      keepFocus: true,
      noScroll: true
    });
  }

  function handleSearchInput() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      applyFilters();
    }, 250);
  }

  function handleFilterChange() {
    clearTimeout(searchTimer);
    applyFilters();
  }

  $: if (
    data.filters.search !== lastSyncedFilters.search ||
    data.filters.room_id !== lastSyncedFilters.room_id ||
    data.filters.tag_id !== lastSyncedFilters.tag_id
  ) {
    filters = {
      search: data.filters.search,
      room_id: data.filters.room_id,
      tag_id: data.filters.tag_id
    };
    lastSyncedFilters = {
      search: data.filters.search,
      room_id: data.filters.room_id,
      tag_id: data.filters.tag_id
    };
  }

  $: pendingContainers = data.containers.filter(isPendingContainer);
  $: documentedContainers = data.containers.filter((container) => !isPendingContainer(container));
</script>

<svelte:head>
  <title>HomeIndex | Advanced Search</title>
</svelte:head>

<section class="content-grid">
  <article class="panel">
    <div class="panel-heading">
      <span class="eyebrow">Filters</span>
      <h2>Advanced Search</h2>
    </div>

    <form class="dashboard-form" method="GET">
      <label class="field">
        <span>Search</span>
        <input
          type="search"
          name="search"
          placeholder="lights, manuals, EL-03"
          bind:value={filters.search}
          on:input={handleSearchInput}
        />
      </label>

      <label class="field">
        <span>Room</span>
        <select name="room_id" bind:value={filters.room_id} on:change={handleFilterChange}>
          <option value="">All rooms</option>
          {#each data.rooms as room}
            <option value={room.id}>{room.name}</option>
          {/each}
        </select>
      </label>

      <label class="field">
        <span>Tag</span>
        <select name="tag_id" bind:value={filters.tag_id} on:change={handleFilterChange}>
          <option value="">All tags</option>
          {#each data.tags as tag}
            <option value={tag.id}>{tag.name}</option>
          {/each}
        </select>
      </label>

      <div class="form-actions">
        <a class="text-link" href="/">Back to Search</a>
        <a class="text-link" href="/advanced-search">Clear</a>
      </div>
    </form>
  </article>

  <article class="panel panel-wide">
    <div class="panel-heading">
      <span class="eyebrow">Inventory</span>
      <h2>Container list</h2>
    </div>

    {#if navigating.to}
      <div class="loading-banner">Loading updated results…</div>
    {/if}

    {#if data.containerError}
      <div class="diagnostics">
        <h3>Could not load containers</h3>
        <p>{data.containerError}</p>
      </div>
    {:else if data.containers.length === 0}
      <div class="empty-state">
        <h3>No containers matched.</h3>
        <p>
          {#if isFilterActive()}
            Try clearing one of the filters or broadening the search terms.
          {:else}
            Create your first container to start building the inventory.
          {/if}
        </p>
      </div>
    {:else}
      {#if pendingContainers.length > 0}
        <div class="panel-heading">
          <span class="eyebrow">Empty Labels</span>
          <h3>Labels created, waiting to be filled in</h3>
        </div>

        <div class="dashboard-grid">
          {#each pendingContainers as container}
            <article class="container-card">
              <a class="card-link" href={`/containers/${container.id}`}>
                <div class="card-content-box">
                  <div class="card-image-wrap">
                    <div class="card-image card-image-empty">Ready for use</div>
                  </div>

                  <div class="card-body">
                    <div class="card-topline">
                      <span class="container-code">{container.code}</span>
                    </div>

                    <h3>{container.name}</h3>
                    <p>Print the label now, then add the contents, room, tags, and photos later.</p>
                  </div>
                </div>
              </a>
            </article>
          {/each}
        </div>
      {/if}

      {#if documentedContainers.length > 0}
        {#if pendingContainers.length > 0}
          <div class="panel-heading">
            <span class="eyebrow">Documented</span>
            <h3>Containers with saved details</h3>
          </div>
        {/if}

        <div class="dashboard-grid">
          {#each documentedContainers as container}
            {@const image = primaryImageFor(container)}
            {@const tags = tagsFor(container)}
            <article class="container-card">
              <a class="card-link" href={`/containers/${container.id}`}>
                <div class="card-content-box">
                  <div class="card-image-wrap">
                    {#if image}
                      <img class="card-image" src={image.url} alt={image.caption ?? container.name} />
                    {:else}
                      <div class="card-image card-image-empty">No photo yet</div>
                    {/if}
                  </div>

                  <div class="card-body">
                    <div class="card-topline">
                      <span class="container-code">{container.code}</span>
                      {#each tags as tag}
                        <span class="container-label-chip">
                          <span class="label-swatch" style={`background: ${tag.colour};`}></span>
                          {tag.name}
                        </span>
                      {/each}
                    </div>

                    <h3>{container.name}</h3>
                    <p>{container.description || 'No description saved yet.'}</p>

                    <dl class="card-meta">
                      <div>
                        <dt>Room</dt>
                        <dd>{roomNameFor(container.room_id)}</dd>
                      </div>
                      <div>
                        <dt>Images</dt>
                        <dd>{container.images.length}</dd>
                      </div>
                    </dl>
                  </div>
                </div>
              </a>
            </article>
          {/each}
        </div>
      {/if}
    {/if}
  </article>
</section>
