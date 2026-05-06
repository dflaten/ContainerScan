<svelte:head>
  <title>ContainerScan</title>
  <meta
    name="description"
    content="A LAN-only system for labeling, browsing, and scanning storage containers."
  />
</svelte:head>

<section class="hero">
  <span class="eyebrow">Task 1 Scaffold</span>
  <h1>ContainerScan</h1>
  <p>
    The project skeleton is in place. FastAPI, SvelteKit, and Nginx are wired together so you can
    start building the real features without first solving structure and routing.
  </p>

  <div class="status-grid">
    <article class="status-card">
      <strong>Backend</strong>
      <span>FastAPI container with `/api/health`.</span>
    </article>

    <article class="status-card">
      <strong>Frontend</strong>
      <span>SvelteKit shell ready for Skeleton-based UI work.</span>
    </article>

    <article class="status-card">
      <strong>Proxy</strong>
      <span>Nginx serves a single LAN-facing origin.</span>
    </article>
  </div>
</section>
