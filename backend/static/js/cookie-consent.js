;(function () {
  "use strict";

  /* ── bail if already consented ── */
  if (localStorage.getItem("art-leptis-cookies")) return;

  gsap.registerPlugin(ScrollTrigger);

  /* ── DOM refs ── */
  const wrapper = document.querySelector("[data-cookie-consent]");
  const bar = document.querySelector("[data-cookie-bar]");
  const pill = document.querySelector("[data-cookie-pill]");

  if (!wrapper || !bar || !pill) return;

  /* ── state ── */
  let current = "hidden"; // hidden | bar | pill | dismissed
  let scrollTriggered = false;

  /* ── initial positions (hidden, but layout-ready) ── */
  gsap.set(wrapper, { visibility: "visible" });
  gsap.set(bar, { yPercent: 110, opacity: 0 });
  gsap.set(pill, { scale: 0, opacity: 0, visibility: "hidden" });

  /* ────────────────────────────────
     SHOW BAR  — slides up from bottom
     ──────────────────────────────── */
  function showBar() {
    if (current === "dismissed") return;
    current = "bar";

    const tl = gsap.timeline();

    /* if pill is visible, shrink it first */
    tl.to(pill, {
      scale: 0,
      opacity: 0,
      duration: 0.25,
      ease: "power2.in",
      onComplete() {
        gsap.set(pill, { visibility: "hidden" });
      },
    });

    /* slide bar in */
    tl.to(
      bar,
      {
        yPercent: 0,
        opacity: 1,
        duration: 0.55,
        ease: "power3.out",
      },
      ">-0.1"
    );

    return tl;
  }

  /* ────────────────────────────────
     SHOW PILL — bar slides down, pill pops in
     ──────────────────────────────── */
  function showPill() {
    if (current === "dismissed") return;
    current = "pill";

    const tl = gsap.timeline();

    /* bar exits */
    tl.to(bar, {
      yPercent: 110,
      opacity: 0,
      duration: 0.4,
      ease: "power3.in",
    });

    /* pill enters */
    tl.set(pill, { visibility: "visible" });
    tl.fromTo(
      pill,
      { scale: 0, opacity: 0 },
      {
        scale: 1,
        opacity: 1,
        duration: 0.5,
        ease: "back.out(3)",
      },
      ">-0.15"
    );

    /* subtle idle pulse so users notice it */
    tl.to(
      pill,
      {
        scale: 1.08,
        duration: 0.6,
        ease: "sine.inOut",
        yoyo: true,
        repeat: 1,
      },
      ">0.3"
    );

    return tl;
  }

  /* ────────────────────────────────
     DISMISS — both elements exit, wrapper removed
     ──────────────────────────────── */
  function dismiss(type) {
    current = "dismissed";
    localStorage.setItem("art-leptis-cookies", type);

    /* kill any ScrollTrigger so it won't fire again */
    if (scrollWatcher) scrollWatcher.kill();

    const tl = gsap.timeline({
      onComplete() {
        wrapper.remove();
      },
    });

    /* bar: slide down */
    tl.to(bar, {
      yPercent: 110,
      opacity: 0,
      duration: 0.35,
      ease: "power3.in",
    });

    /* pill: shrink */
    tl.to(
      pill,
      {
        scale: 0,
        opacity: 0,
        duration: 0.3,
        ease: "power2.in",
      },
      0 // start at same time
    );

    return tl;
  }

  /* ────────────────────────────────
     SCROLL WATCHER
     collapse to pill after 80px of scroll
     ──────────────────────────────── */
  const scrollWatcher = ScrollTrigger.create({
    start: "top -80",
    onEnter() {
      if (current === "bar") {
        scrollTriggered = true;
        showPill();
      }
    },
    /* Optional: expand bar again if user scrolls back to very top */
    // onLeaveBack() {
    //   if (current === 'pill') showBar();
    // },
  });

  /* ────────────────────────────────
     WIRE UP EVENTS
     ──────────────────────────────── */

  /* pill click → expand to full bar */
  pill.addEventListener("click", () => {
    if (current === "pill") showBar();
  });

  /* accept */
  wrapper.querySelectorAll("[data-cookie-accept]").forEach((btn) => {
    btn.addEventListener("click", () => dismiss("all"));
  });

  /* reject / essentials */
  wrapper.querySelectorAll("[data-cookie-reject]").forEach((btn) => {
    btn.addEventListener("click", () => dismiss("essential"));
  });

  /* ────────────────────────────────
     ENTRANCE — show bar after 1.2s
     ──────────────────────────────── */
  gsap.delayedCall(1.2, () => {
    /* if user already scrolled past threshold before bar appeared,
       go straight to pill */
    if (window.scrollY > 80) {
      showPill();
    } else {
      showBar();
    }
  });
})();