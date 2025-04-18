<script lang="ts">
  import { repository } from '$site/package.json'
  import { click_outside } from 'svelte-zoo/actions'

  interface Props {
    tips_title?: string
    dialog?: HTMLDialogElement | null
    btn?: HTMLButtonElement | null
  }
  let {
    tips_title = `Usage Tips`,
    dialog = $bindable(null),
    btn = $bindable(null),
  }: Props = $props()

  function toggle(event: KeyboardEvent) {
    if (!dialog) return
    if (event.key == `Escape`) dialog.open = false
    if (event.key == `j` && event.metaKey) dialog.open = !dialog.open
  }
</script>

<svelte:window onkeydown={toggle} />

<footer>
  <nav>
    <a href="{repository}/issues">
      <svg><use href="#icon-issues" /></svg>
      Issues
    </a>
    <a href="mailto:janosh.riebesell@gmail.com?subject=Matbench Discovery">
      <svg><use href="#icon-contact" /></svg>
      Contact
    </a>
    <a href="/changelog">
      <svg><use href="#catppuccin-changelog" /></svg>
      Changelog
    </a>
    <a href="/rss.xml" title="Subscribe to model updates">
      <svg><use href="#icon-rss" /></svg>
      RSS
    </a>
    <button
      onclick={() => {
        if (dialog) dialog.open = true
      }}
      bind:this={btn}
      title={tips_title}
      aria-label={tips_title}
      style="padding: 0; transform: scale(1.2); font-weight: bold;"
    >
      <svg><use href="#icon-info" /></svg>
    </button>
  </nav>
  <img src="/favicon.svg" alt="Logo" width="30px" style="vertical-align: middle;" />
  &ensp;Matbench Discovery (2023)
</footer>

<dialog
  bind:this={dialog}
  use:click_outside={{
    callback: (node) => {
      if (node.open) node.open = false
    },
  }}
>
  <h3>{tips_title}</h3>
  <p title="For keyboard-only site navigation">
    <kbd>cmd</kbd> + <kbd>k</kbd> to bring up a nav palette.
  </p>
  <p title="For keyboard-only site navigation">
    <kbd>cmd</kbd> + <kbd>j</kbd> to bring up these site options.
  </p>
  <p title="single click to hide a trace">
    <kbd>single click</kbd> a figure legend handle to hide its corresponding trace in a plot
  </p>
  <p title="double click to hide all other traces">
    <kbd>double click</kbd> the figure legend handle of any trace in a plot to hide all others.
    double click again to show all.
  </p>
</dialog>

<style>
  footer {
    padding: 3vh 3vw;
    background: #00061a;
    text-align: center;
  }
  footer nav {
    display: flex;
    gap: 2em;
    justify-content: center;
    margin: 2em 0;
  }
  footer > nav svg {
    margin-right: 3pt;
  }
  footer > nav > button {
    background: none;
    color: var(--blue);
  }
  dialog {
    visibility: hidden;
    opacity: 0;
    position: fixed;
    top: 40%;
    background: var(--light-bg);
    color: var(--text-color);
    display: grid;
    border: none;
    border-radius: 3pt;
    padding: 1ex 2ex;
    transition: 0.2s;
  }
  dialog[open] {
    visibility: visible;
    opacity: 1;
  }
  dialog > :is(:global(p, h3)) {
    margin: 0;
  }
</style>
