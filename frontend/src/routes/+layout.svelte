<script>
  import { afterNavigate, goto } from '$app/navigation';
  import { page } from '$app/state';
  import '../app.css';

  export let data;

  let isMenuOpen = false;
  let isStatusPopupOpen = false;

  function isPendingContainer(container) {
    return (
      !container.description &&
      !container.room_id &&
      (!container.tag_ids || container.tag_ids.length === 0) &&
      container.images.length === 0 &&
      container.name === `Container ${container.code}`
    );
  }

  function dashboardContainers() {
    return Array.isArray(page.data.containers) ? page.data.containers : [];
  }

  function apiStatusLabel() {
    return data.bootstrap.apiOnline ? 'Online' : 'Offline';
  }

  async function handleCreateEmptyLabel() {
    const emptyLabel = dashboardContainers().find(isPendingContainer) ?? null;

    if (emptyLabel) {
      await goto(`/containers/${emptyLabel.id}`);
      return;
    }

    const shouldRedirectToPrint = window.confirm(
      'No empty labels are currently available. Print a new sheet of labels before continuing?'
    );

    if (!shouldRedirectToPrint) {
      return;
    }

    await goto('/print?missingEmptyLabels=1');
  }

  function closeSiteMenu() {
    isMenuOpen = false;
  }

  afterNavigate(() => {
    isMenuOpen = false;
    isStatusPopupOpen = false;
  });
</script>

<svelte:head>
  <title>HomeIndex</title>
  <meta
    name="description"
    content="A LAN-only system for labeling, browsing, and scanning storage containers."
  />
</svelte:head>

<div
  class="site-frame"
  class:site-frame-scan={page.url.pathname.startsWith('/scan/')}
  class:site-frame-print={page.url.pathname.startsWith('/print')}
>
  <header class="site-header" class:site-header-hidden={page.url.pathname.startsWith('/scan/')}>
    <div class="site-header-row">
      <div class="site-header-main">
        <a class="brand-mark" href="/">
          <span class="brand-kicker">HomeIndex</span>
        </a>
      </div>

      <div class="site-header-actions">
        <div class="api-status-wrap">
          <button
            class="api-indicator"
            class:api-indicator-offline={!data.bootstrap.apiOnline}
            type="button"
            aria-label={`API status: ${apiStatusLabel()}. Click for details`}
            aria-expanded={isStatusPopupOpen}
            on:click={() => {
              isStatusPopupOpen = !isStatusPopupOpen;
            }}
          >
            <span class="api-indicator-dot" aria-hidden="true"></span>
          </button>

          {#if isStatusPopupOpen}
            <div class="api-status-popup" role="status">
              {apiStatusLabel()}
            </div>
          {/if}
        </div>

        {#if page.url.pathname === '/'}
          <button
            class="dashboard-overview-action site-header-empty-label-action"
            type="button"
            on:click={handleCreateEmptyLabel}
          >
            Get Label
          </button>
        {/if}

        <div class="site-menu">
          <button
            class="site-menu-toggle"
            type="button"
            aria-label="Open navigation menu"
            aria-expanded={isMenuOpen}
            on:click={() => {
              isMenuOpen = !isMenuOpen;
            }}
          >
            <span></span>
            <span></span>
            <span></span>
          </button>

          {#if isMenuOpen}
            <div class="site-menu-panel">
              <a class="site-menu-link" href="/rooms" on:click={closeSiteMenu}>Manage Rooms, Tags & Colors</a>
              <a class="site-menu-link" href="/advanced-search" on:click={closeSiteMenu}>Advanced Search</a>
              <a class="site-menu-link" href="/print" on:click={closeSiteMenu}>Create/Print Labels</a>
            </div>
          {/if}
        </div>

        {#if isMenuOpen}
          <button
            class="site-menu-backdrop"
            type="button"
            aria-label="Close navigation menu"
            on:click={closeSiteMenu}
          ></button>
        {/if}
      </div>
    </div>

  </header>

  <main
    class="app-shell"
    class:app-shell-scan={page.url.pathname.startsWith('/scan/')}
    class:app-shell-print={page.url.pathname.startsWith('/print')}
  >
    <slot />
  </main>
</div>
