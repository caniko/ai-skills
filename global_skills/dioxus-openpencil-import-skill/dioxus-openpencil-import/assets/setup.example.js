// Async function body evaluated after each route loads.
// The current route is available as window.__DIOXUS_OPENPENCIL_ROUTE__.

if (window.__DIOXUS_OPENPENCIL_ROUTE__ === "/settings") {
  const darkMode = document.querySelector('[data-testid="dark-mode"]');
  if (darkMode && darkMode.getAttribute("aria-checked") !== "true") {
    darkMode.click();
  }
}

const ready = document.querySelector('[data-testid="screen-ready"]');
if (ready) await new Promise((resolve) => setTimeout(resolve, 250));
