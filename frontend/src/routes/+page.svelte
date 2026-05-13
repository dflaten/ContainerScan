<script>
  import { goto } from '$app/navigation';
  import { navigating } from '$app/state';

  export let data;

  let filters = {
    search: data.filters.search
  };
  let lastSyncedFilters = {
    search: data.filters.search
  };
  let searchTimer;
  let createError = null;
  let isCreatingEmptyLabel = false;

  function primaryImageFor(container) {
    return container.images.find((image) => image.is_primary) ?? container.images[0] ?? null;
  }

  function tagsFor(container) {
    return container.tags ?? [];
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
    return Boolean(data.filters.search);
  }

  function createdContainer() {
    return data.containers.find((container) => container.id === data.createdContainerId) ?? null;
  }

  async function handleCreateEmptyLabel() {
    createError = null;
    isCreatingEmptyLabel = true;

    try {
      const emptyLabel = pendingContainers[0] ?? null;

      if (emptyLabel) {
        await goto(`/containers/${emptyLabel.id}`);
      } else {
        const shouldRedirectToPrint = window.confirm(
          'No empty labels are currently available. Print a new sheet of labels before continuing?'
        );

        if (!shouldRedirectToPrint) {
          return;
        }

        await goto('/print?missingEmptyLabels=1');
      }
    } catch (error) {
      createError = error.detail ?? error.message ?? 'Unable to open an empty label.';
    } finally {
      isCreatingEmptyLabel = false;
    }
  }

  function buildDashboardQuery(nextFilters) {
    const params = new URLSearchParams();

    if (nextFilters.search) {
      params.set('search', nextFilters.search);
    }

    const query = params.toString();
    return query ? `/?${query}` : '/';
  }

  async function applyFilters() {
    await goto(buildDashboardQuery(filters), {
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
    data.filters.search !== lastSyncedFilters.search
  ) {
    filters = {
      search: data.filters.search
    };
    lastSyncedFilters = {
      search: data.filters.search
    };
  }

  $: pendingContainers = data.containers.filter(isPendingContainer);
  $: documentedContainers = data.containers.filter((container) => !isPendingContainer(container));
</script>

<svelte:head>
  <title>HomeIndex | Dashboard</title>
</svelte:head>

<section class="content-grid">
  <article class="panel panel-full dashboard-overview">
    <div class="panel-heading dashboard-overview-heading">
      <span class="eyebrow">Inventory Snapshot</span>

      <button
        class="dashboard-overview-action"
        type="button"
        on:click={handleCreateEmptyLabel}
        disabled={isCreatingEmptyLabel}
      >
        {isCreatingEmptyLabel ? 'Opening Empty Label…' : 'Get Empty Label'}
      </button>
    </div>

    <div class="dashboard-stats">
      <article class="dashboard-stat">
        <span class="dashboard-stat-label">Containers tracked</span>
        <strong>{data.containers.length}</strong>
      </article>

      <article class="dashboard-stat">
        <span class="dashboard-stat-label">Needs details</span>
        <strong>{pendingContainers.length}</strong>
      </article>
    </div>

    {#if createError}
      <div class="diagnostics">
        <h3>Could not open empty label</h3>
        <p>{createError}</p>
      </div>
    {/if}
  </article>

  <article class="panel">
    <div class="panel-heading">
      <span class="eyebrow">Search</span>
    </div>

    <form class="dashboard-form" method="GET">
      <label class="field">
        <input
          type="search"
          name="search"
          aria-label="Search"
          placeholder="lights, manuals, EL-03"
          bind:value={filters.search}
          on:input={handleSearchInput}
        />
      </label>

      <div class="form-actions">
        <a class="text-link" href="/advanced-search">Advanced Search</a>
        <a class="text-link" href="/">Clear</a>
      </div>
    </form>
  </article>

  <article class="panel panel-wide">
    <div class="panel-heading">
      <span class="eyebrow">Inventory</span>
    </div>

    {#if createdContainer()}
      <div class="notice-banner">
        Created {createdContainer().code}.
        <a class="text-link" href={`/containers/${createdContainer().id}`}>Open detail view</a>
      </div>
    {/if}

    {#if data.deletedContainerCode}
      <div class="notice-banner">Deleted container {data.deletedContainerCode}.</div>
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
            Create your first container to start building the inventory.
          {/if}
        </p>
      </div>
    {:else}
      {#if documentedContainers.length > 0}
        {#if pendingContainers.length > 0}
          <div class="panel-heading">
            <span class="eyebrow">Documented</span>
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
                    <p>{container.images.length} image{container.images.length === 1 ? '' : 's'} saved</p>
                  </div>
                </div>
              </a>
            </article>
          {/each}
        </div>
      {/if}

      {#if pendingContainers.length > 0}
        {#if documentedContainers.length > 0}
          <div class="panel-heading">
            <span class="eyebrow">Needs Details</span>
          </div>
        {/if}

        <div class="dashboard-grid">
          {#each pendingContainers as container}
            <article class="container-card">
              <a class="card-link" href={`/containers/${container.id}`}>
                <div class="card-content-box">
                  <div class="card-image-wrap">
                    <div class="card-image card-image-empty">Ready for label download</div>
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
    {/if}
  </article>
</section>
