<script>
  import { navigating } from '$app/state';

  export let data;

  function roomNameFor(roomId) {
    return data.rooms.find((room) => room.id === roomId)?.name ?? 'Unknown room';
  }

  function labelFor(labelId) {
    return data.labels.find((label) => label.id === labelId) ?? null;
  }

  function primaryImageFor(container) {
    return container.images.find((image) => image.is_primary) ?? container.images[0] ?? null;
  }

  function isFilterActive() {
    return Boolean(data.filters.search || data.filters.room_id || data.filters.label_id);
  }

  function createdContainer() {
    return data.containers.find((container) => container.id === data.createdContainerId) ?? null;
  }
</script>

<svelte:head>
  <title>ContainerScan | Dashboard</title>
</svelte:head>

<section class="hero-panel">
  <span class="eyebrow">Tasks 13-15</span>
  <h1>Browse containers from one dashboard.</h1>
  <p>
    Search by contents or code, narrow by room or label, and scan the current inventory without
    leaving the main admin route.
  </p>

  <div class="hero-actions">
    <a class="primary-link" href="/containers/new">New Container</a>
  </div>

  <div class="hero-meta">
    <article>
      <span>Containers</span>
      <strong>{data.containers.length}</strong>
    </article>
    <article>
      <span>Rooms</span>
      <strong>{data.rooms.length}</strong>
    </article>
    <article>
      <span>Labels</span>
      <strong>{data.labels.length}</strong>
    </article>
  </div>
</section>

<section class="content-grid">
  <article class="panel">
    <div class="panel-heading">
      <span class="eyebrow">Filters</span>
      <h2>Find the right container</h2>
    </div>

    <form class="dashboard-form" method="GET">
      <label class="field">
        <span>Search</span>
        <input
          type="search"
          name="search"
          placeholder="lights, manuals, EL-03"
          value={data.filters.search}
        />
      </label>

      <label class="field">
        <span>Room</span>
        <select name="room_id" value={data.filters.room_id}>
          <option value="">All rooms</option>
          {#each data.rooms as room}
            <option value={room.id}>{room.name}</option>
          {/each}
        </select>
      </label>

      <label class="field">
        <span>Label</span>
        <select name="label_id" value={data.filters.label_id}>
          <option value="">All labels</option>
          {#each data.labels as label}
            <option value={label.id}>{label.name}</option>
          {/each}
        </select>
      </label>

      <div class="form-actions">
        <button type="submit">Apply Filters</button>
        <a class="text-link" href="/">Clear</a>
      </div>
    </form>
  </article>

  <article class="panel panel-muted">
    <div class="panel-heading">
      <span class="eyebrow">Status</span>
      <h2>Dashboard state</h2>
    </div>

    <div class="readiness-list">
      <article class="readiness-card">
        <div>
          <span>API Query</span>
          <strong>{data.containerError ? 'Failed' : 'Loaded'}</strong>
        </div>
        <p>
          {#if data.containerError}
            {data.containerError}
          {:else if navigating.to}
            Refreshing results for the current filters.
          {:else if isFilterActive()}
            Showing filtered results for the current dashboard query.
          {:else}
            Showing the full container inventory.
          {/if}
        </p>
      </article>

      <article class="readiness-card">
        <div>
          <span>Reference Data</span>
          <strong>{data.rooms.length} rooms / {data.labels.length} labels</strong>
        </div>
        <p>Room and label metadata are available for filter controls and container badges.</p>
      </article>
    </div>
  </article>

  <article class="panel panel-wide">
    <div class="panel-heading">
      <span class="eyebrow">Inventory</span>
      <h2>Container listing</h2>
    </div>

    {#if createdContainer()}
      <div class="notice-banner">
        Created {createdContainer().code} for {createdContainer().name}.
        <a class="text-link" href={`/containers/${createdContainer().id}`}>Open detail view</a>
      </div>
    {/if}

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
            Add sample data or create your first container to populate the dashboard.
          {/if}
        </p>
      </div>
    {:else}
      <div class="dashboard-grid">
        {#each data.containers as container}
          {@const label = labelFor(container.label_id)}
          {@const image = primaryImageFor(container)}
          <article class="container-card">
            <a class="card-link" href={`/containers/${container.id}`}>
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
                  {#if label}
                    <span class="container-label-chip">
                      <span class="label-swatch" style={`background: ${label.colour};`}></span>
                      {label.name}
                    </span>
                  {/if}
                </div>

                <h3>{container.name}</h3>
                <p>{container.description || 'No description recorded yet.'}</p>

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
            </a>
          </article>
        {/each}
      </div>
    {/if}
  </article>
</section>
