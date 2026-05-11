<script>
  import { page } from '$app/state';
  import '../app.css';

  export let data;
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
        <div class="api-indicator" class:api-indicator-offline={!data.bootstrap.apiOnline} aria-label="API status">
          <span class="api-indicator-dot" aria-hidden="true"></span>
          <span>API {data.bootstrap.apiOnline ? 'Online' : 'Offline'}</span>
        </div>

        <details class="site-menu">
          <summary class="site-menu-toggle" aria-label="Open navigation menu">
            <span></span>
            <span></span>
            <span></span>
          </summary>

          <div class="site-menu-panel">
            <a class="site-menu-link" href="/containers/new">Generate Label</a>
            <a class="site-menu-link" href="/rooms">Add/Remove Rooms</a>
            <a class="site-menu-link" href="/advanced-search">Advanced Search</a>
            <a class="site-menu-link" href="/print">Print Labels</a>
          </div>
        </details>
      </div>
    </div>

    {#if page.url.pathname === '/'}
      <p class="brand-summary">
        Label boxes, track where they live, and pull them up quickly from any device on your local network.
      </p>
    {/if}
  </header>

  <main
    class="app-shell"
    class:app-shell-scan={page.url.pathname.startsWith('/scan/')}
    class:app-shell-print={page.url.pathname.startsWith('/print')}
  >
    <slot />
  </main>
</div>
