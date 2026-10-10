/* Convert Franklin's \( ... \) and \[ ... \] delimiters to KaTeX.
   Loading the KaTeX stylesheet alone is not sufficient. */
(() => {
  'use strict';

  function renderNoteMath() {
    const main = document.querySelector('.franklin-content') || document.querySelector('.page-content');
    if (!main || typeof window.renderMathInElement !== 'function') return;
    window.renderMathInElement(main, {
      delimiters: [
        { left: '\\[', right: '\\]', display: true },
        { left: '\\(', right: '\\)', display: false },
        { left: '$$', right: '$$', display: true },
        { left: '$', right: '$', display: false },
      ],
      ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'option'],
      ignoredClasses: ['katex', 'katex-display'],
      throwOnError: false,
      strict: 'warn',
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderNoteMath, { once: true });
  } else {
    renderNoteMath();
  }
})();
