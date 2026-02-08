/**
 * hero-carousel.js
 * GSAP Observer-based vertical/horizontal swipe carousel.
 * Reads captions from [data-caption] and updates #hero-caption-text.
 */
(function () {
  "use strict";

  function initHeroCarousel() {
    if (typeof gsap === "undefined" || typeof Observer === "undefined") {
      return;
    }

    gsap.registerPlugin(Observer);

    var container = document.getElementById("hero-carousel");
    if (!container) return;

    var slides = container.querySelectorAll(".hero-slide");
    if (slides.length < 2) return;

    var counter = document.getElementById("hero-counter");
    var captionEl = document.getElementById("hero-caption-text");
    var prevBtn = container.querySelector('[data-hero="prev"]');
    var nextBtn = container.querySelector('[data-hero="next"]');

    var currentIndex = 0;
    var total = slides.length;
    var animating = false;
    var autoPlayId = null;

    // Build captions array
    var captions = Array.from(slides).map(function (s) {
      return s.dataset.caption || "";
    });

    // Initial state
    gsap.set(slides[0], { autoAlpha: 1, zIndex: 10 });

    var wrap = gsap.utils.wrap(0, total);

    function updateUI(index) {
      if (counter) {
        counter.textContent = index + 1 + " / " + total;
      }
      if (captionEl && captions[index]) {
        captionEl.textContent = captions[index];
      }
    }

    function goTo(index, direction) {
      if (animating || index === currentIndex) return;
      animating = true;

      index = wrap(index);

      var current = slides[currentIndex];
      var next = slides[index];

      var yEnter =
        direction === "down" || direction === "right" ? -100 : 100;

      gsap.set(next, {
        autoAlpha: 1,
        zIndex: 10,
        yPercent: yEnter,
      });
      gsap.set(current, { zIndex: 1 });

      var tl = gsap.timeline({
        defaults: { duration: 0.8, ease: "power3.inOut" },
        onComplete: function () {
          animating = false;
          gsap.set(current, { autoAlpha: 0, clearProps: "transform" });
        },
      });

      tl.to(current, { yPercent: 0, scale: 0.96 }, 0).to(
        next,
        { yPercent: 0 },
        0
      );

      currentIndex = index;
      updateUI(index);
    }

    // ── Observer (touch + pointer drag) ──
    Observer.create({
      target: container,
      type: "touch,pointer",
      tolerance: 10,
      preventDefault: true,
      onUp: function () {
        goTo(currentIndex + 1, "up");
      },
      onDown: function () {
        goTo(currentIndex - 1, "down");
      },
      onLeft: function () {
        goTo(currentIndex + 1, "up");
      },
      onRight: function () {
        goTo(currentIndex - 1, "down");
      },
    });

    // ── Prev / Next buttons ──
    if (prevBtn) {
      prevBtn.addEventListener("click", function () {
        goTo(currentIndex - 1, "down");
        restartAutoplay();
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener("click", function () {
        goTo(currentIndex + 1, "up");
        restartAutoplay();
      });
    }

    // ── Autoplay ──
    function startAutoplay() {
      autoPlayId = setInterval(function () {
        goTo(currentIndex + 1, "up");
      }, 5000);
    }

    function stopAutoplay() {
      clearInterval(autoPlayId);
    }

    function restartAutoplay() {
      stopAutoplay();
      startAutoplay();
    }

    container.addEventListener("mouseenter", stopAutoplay);
    container.addEventListener("touchstart", stopAutoplay, {
      passive: true,
    });
    container.addEventListener("mouseleave", restartAutoplay);
    container.addEventListener("touchend", restartAutoplay, {
      passive: true,
    });

    startAutoplay();
  }

  document.addEventListener("DOMContentLoaded", initHeroCarousel);
})();