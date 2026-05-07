<script>
  import '../app.css';

  export let data;
</script>

<svelte:head>
  <title>ContainerScan</title>
  <meta
    name="description"
    content="A LAN-only system for labeling, browsing, and scanning storage containers."
  />
</svelte:head>

<div class="site-frame">
  <header class="site-header">
    <div>
      <a class="brand-mark" href="/">
        <span class="brand-kicker">ContainerScan</span>
        <strong>Admin frontend bootstrap</strong>
      </a>
      <p class="brand-summary">
        SvelteKit app shell configured for the single-origin LAN deployment model.
      </p>
    </div>

    <dl class="status-strip" aria-label="Application status">
      <div>
        <dt>API</dt>
        <dd class:status-live={data.bootstrap.apiOnline}>
          {data.bootstrap.apiOnline ? 'Online' : 'Unavailable'}
        </dd>
      </div>
      <div>
        <dt>Rooms</dt>
        <dd>{data.bootstrap.roomCount ?? 'n/a'}</dd>
      </div>
      <div>
        <dt>Labels</dt>
        <dd>{data.bootstrap.labelCount ?? 'n/a'}</dd>
      </div>
    </dl>
  </header>

  <main class="app-shell">
    <slot />
  </main>
</div>
