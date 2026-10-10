(() => {
  'use strict';

  const toggle = document.querySelector('.site-nav-toggle');
  const nav = document.getElementById('site-nav');
  if (toggle && nav) {
    const closeMenu = () => {
      toggle.setAttribute('aria-expanded', 'false');
      nav.classList.remove('is-open');
    };
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('is-open', open);
    });
    nav.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
    window.addEventListener('resize', () => {
      if (window.innerWidth > 760) closeMenu();
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') closeMenu();
    });

    const current = window.location.pathname.replace(/\/?$/, '/');
    nav.querySelectorAll('a').forEach(link => {
      const path = new URL(link.href, window.location.origin).pathname.replace(/\/?$/, '/');
      const section = path !== '/' && current.startsWith(path);
      if (current === path || section) link.setAttribute('aria-current', 'page');
    });
  }

  let lastTrigger = null;
  document.querySelectorAll('button[data-dialog]').forEach(trigger => {
    const dialog = document.getElementById(trigger.dataset.dialog);
    if (!(dialog instanceof HTMLDialogElement)) return;
    trigger.addEventListener('click', () => {
      lastTrigger = trigger;
      if (typeof dialog.showModal === 'function') dialog.showModal();
    });
  });

  document.querySelectorAll('dialog.publication-dialog').forEach(dialog => {
    dialog.addEventListener('click', event => {
      if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener('close', () => {
      if (lastTrigger && document.contains(lastTrigger)) lastTrigger.focus();
      lastTrigger = null;
    });
  });

  document.querySelectorAll('[data-copy-bibtex]').forEach(button => {
    button.addEventListener('click', async () => {
      const code = button.closest('.publication-citation')?.querySelector('pre code');
      if (!code) return;
      const label = button.textContent;
      try {
        await navigator.clipboard.writeText(code.textContent);
        button.textContent = 'Copied';
        setTimeout(() => { button.textContent = label; }, 1800);
      } catch (_) {
        const range = document.createRange();
        range.selectNodeContents(code);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        button.textContent = 'Select & copy';
        setTimeout(() => { button.textContent = label; }, 1800);
      }
    });
  });
})();
