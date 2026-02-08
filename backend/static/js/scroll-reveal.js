/**
 * scroll-reveal.js
 * GSAP ScrollTrigger entrance animations.
 * Loaded once globally — works with HTMX partial swaps.
 */
(function () {
  "use strict";

  function init() {
    if (
      typeof gsap === "undefined" ||
      typeof ScrollTrigger === "undefined"
    ) {
      // No GSAP — show everything immediately
      document
        .querySelectorAll(
          ".reveal,.reveal-up,.reveal-scale,.reveal-left,.reveal-right"
        )
        .forEach(function (el) {
          el.classList.add("is-visible");
        });
      return;
    }

    gsap.registerPlugin(ScrollTrigger);

    var defaults = {
      ease: "power3.out",
      once: true,
    };

    // ── Reveal-up ──
    gsap.utils.toArray(".reveal-up").forEach(function (el, i) {
      // Skip already-animated elements (HTMX re-init safety)
      if (el.dataset.revealed) return;
      el.dataset.revealed = "1";

      gsap.to(el, {
        y: 0,
        opacity: 1,
        duration: 0.9,
        delay: i * 0.06,
        ease: defaults.ease,
        scrollTrigger: {
          trigger: el,
          start: "top 90%",
          once: defaults.once,
        },
      });
    });

    // ── Reveal-scale ──
    gsap.utils.toArray(".reveal-scale").forEach(function (el) {
      if (el.dataset.revealed) return;
      el.dataset.revealed = "1";

      gsap.to(el, {
        scale: 1,
        opacity: 1,
        duration: 1.1,
        ease: defaults.ease,
        scrollTrigger: {
          trigger: el,
          start: "top 85%",
          once: defaults.once,
        },
      });
    });

    // ── Reveal-left / Reveal-right ──
    gsap.utils.toArray(".reveal-left,.reveal-right").forEach(function (el) {
      if (el.dataset.revealed) return;
      el.dataset.revealed = "1";

      gsap.to(el, {
        x: 0,
        opacity: 1,
        duration: 0.9,
        ease: defaults.ease,
        scrollTrigger: {
          trigger: el,
          start: "top 88%",
          once: defaults.once,
        },
      });
    });

    // ── Generic reveal (fade only) ──
    gsap.utils.toArray(".reveal").forEach(function (el) {
      if (el.dataset.revealed) return;
      el.dataset.revealed = "1";

      gsap.to(el, {
        opacity: 1,
        duration: 0.8,
        ease: "power2.out",
        scrollTrigger: {
          trigger: el,
          start: "top 90%",
          once: defaults.once,
        },
      });
    });
  }

  // Run on first load
  document.addEventListener("DOMContentLoaded", init);

  // Re-run after HTMX swaps
  document.addEventListener("htmx:afterSwap", function () {
    ScrollTrigger.refresh();
    init();
  });
})();