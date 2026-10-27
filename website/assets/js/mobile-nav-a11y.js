/**
 * USWDS mobile nav sets aria-hidden + data-nav-hidden on non-nav content
 * (including .usa-navbar / logo) without removing those nodes from tab order.
 * ANDI then reports focusable-inside-aria-hidden.
 *
 * While the menu is open:
 *  1. Drop aria-hidden on USWDS-hidden nodes (keep data-nav-hidden)
 *  2. Mark them inert (data-nav-inert for tests)
 *
 * Do not strip href, disable controls, or set tabindex=-1. Those create
 * other ANDI alerts ("<a> has no href", "disabled elements", "focusable
 * but not in tab order"). Removing aria-hidden + inert is enough once the
 * attribute ANDI keys off is gone; .usa-navbar is also display:none.
 *
 * A short interval is enough: USWDS only writes these attrs on open/close,
 * and polling wins that race without MutationObserver thrash.
 */
(function () {
  const OPEN = "usa-js-mobile-nav--active";

  function sync() {
    if (!document.body.classList.contains(OPEN)) {
      document.querySelectorAll("[data-nav-inert]").forEach((el) => {
        el.removeAttribute("inert");
        el.removeAttribute("data-nav-inert");
      });
      document.body.removeAttribute("data-mobile-nav-a11y");
      return;
    }

    document.querySelectorAll("[data-nav-hidden], .usa-navbar").forEach((el) => {
      if (el.closest(".usa-nav")) {
        return;
      }
      el.removeAttribute("aria-hidden");
      el.setAttribute("inert", "");
      el.setAttribute("data-nav-inert", "");
    });
    document.body.setAttribute("data-mobile-nav-a11y", "fixed");
  }

  setInterval(sync, 200);
  sync();
})();
