/*
 * StockSense shared JavaScript (runs on every page).
 *  1. Mobile sidebar: open/close with the hamburger button
 *  2. Async sections: any element with data-src loads its HTML after the page
 *     appears, showing a loading skeleton first and an error box if it fails
 *  3. Icons: turns <i data-lucide="..."> tags into SVG icons
 */

// Small helpers other scripts (like chart.js) can use
window.StockSense = {
  // Draw any new <i data-lucide> icons that were added to the page
  refreshIcons() {
    if (window.lucide) window.lucide.createIcons();
  },

  // Replace an element's contents with the error box + a Retry button
  showError(element, message, onRetry) {
    const template = document.getElementById("load-error-template");
    if (!template) {
      element.textContent = message;
      return;
    }
    const errorBox = template.content.cloneNode(true);
    errorBox.querySelector("[data-error-text]").textContent = message;
    errorBox.querySelector("[data-retry]").addEventListener("click", onRetry);
    element.replaceChildren(errorBox);
    window.StockSense.refreshIcons();
  },
};


// ---------- 1. Mobile sidebar ----------
(function setUpSidebar() {
  const sidebar = document.getElementById("sidebar");
  const openButton = document.getElementById("sidebar-open");
  const closeButton = document.getElementById("sidebar-close");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (!sidebar || !openButton) return;

  function open() {
    sidebar.classList.remove("-translate-x-full");
    backdrop.classList.remove("hidden");
    document.body.classList.add("overflow-hidden"); // stop the page scrolling behind
    openButton.setAttribute("aria-expanded", "true");
  }

  function close() {
    sidebar.classList.add("-translate-x-full");
    backdrop.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
    openButton.setAttribute("aria-expanded", "false");
  }

  openButton.addEventListener("click", open);
  closeButton.addEventListener("click", close);
  backdrop.addEventListener("click", close);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
  });
})();


// ---------- 2. Async sections (news, AI summary) ----------
(function setUpAsyncSections() {
  // Remember each section's skeleton so "Retry" can show it again
  const skeletons = new WeakMap();

  async function load(section) {
    if (!skeletons.has(section)) skeletons.set(section, section.innerHTML);
    section.innerHTML = skeletons.get(section);
    section.setAttribute("aria-busy", "true");

    try {
      const response = await fetch(section.dataset.src);
      if (!response.ok) throw new Error(`Server responded with ${response.status}`);
      section.innerHTML = await response.text();
      window.StockSense.refreshIcons();
    } catch (error) {
      console.error(`Failed to load ${section.dataset.src}:`, error);
      window.StockSense.showError(section, section.dataset.errorMessage, () => load(section));
    } finally {
      section.setAttribute("aria-busy", "false");
    }
  }

  document.querySelectorAll("[data-src]").forEach(load);
})();


// ---------- 3. Icons ----------
window.StockSense.refreshIcons();
