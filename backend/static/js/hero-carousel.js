document.addEventListener('DOMContentLoaded', () => {
  // Ensure GSAP and Observer are loaded
  if (typeof gsap === 'undefined' || typeof Observer === 'undefined') {
    console.warn('GSAP or Observer plugin not loaded.');
    return;
  }

  gsap.registerPlugin(Observer);

  const container = document.getElementById('hero-carousel');

  // SAFETY CHECK: If this element isn't on the current page, stop here.
  if (!container) return;

  const slides = container.querySelectorAll('.hero-slide');
  const dots = container.querySelectorAll('.nav-dot');
  
  // If no slides found, stop
  if (slides.length === 0) return;

  let currentIndex = 0;
  let animating = false;
  
  // Initialize state
  gsap.set(slides[0], { autoAlpha: 1, zIndex: 10 });
  if(dots.length) gsap.set(dots[0], { opacity: 1, scale: 1.2 });

  const wrap = gsap.utils.wrap(0, slides.length);

  const goTo = (index, direction) => {
    if (animating || index === currentIndex) return;
    animating = true;
    
    index = wrap(index);
    
    const currentSlide = slides[currentIndex];
    const nextSlide = slides[index];
    
    // Animate Dots (if they exist)
    if (dots.length) {
      gsap.to(dots, { opacity: 0.5, scale: 1, duration: 0.3 });
      gsap.to(dots[index], { opacity: 1, scale: 1.2, duration: 0.3 });
    }

    // Determine direction
    // If 'down' or 'right' -> Slide comes from Top (-100%)
    // If 'up' or 'left'    -> Slide comes from Bottom (100%)
    let yPercentEnter = 100; 
    
    if (direction === 'down' || direction === 'right') {
        yPercentEnter = -100;
    }

    // Set initial state for incoming slide
    gsap.set(nextSlide, { 
      autoAlpha: 1, 
      zIndex: 10,
      yPercent: yPercentEnter 
    });
    
    gsap.set(currentSlide, { zIndex: 1 });

    // Timeline
    const tl = gsap.timeline({
      defaults: { duration: 0.8, ease: 'power3.inOut' },
      onComplete: () => {
        animating = false;
        // Hide the old slide completely after animation
        gsap.set(currentSlide, { autoAlpha: 0, transform: 'none' }); 
      }
    });

    tl.to(currentSlide, { yPercent: 0, scale: 0.95 }, 0) // Slight scale effect
      .to(nextSlide, { yPercent: 0 }, 0);
      
    currentIndex = index;
  };

  // Create Observer for Touch/Drag
  Observer.create({
    target: container,
    type: "touch,pointer", // No wheel (scrolling) to avoid bad UX
    tolerance: 10,
    preventDefault: true,
    onUp: () => goTo(currentIndex + 1, 'up'),
    onDown: () => goTo(currentIndex - 1, 'down'),
    onLeft: () => goTo(currentIndex + 1, 'up'),
    onRight: () => goTo(currentIndex - 1, 'down'),
  });

  // Auto-Play Logic
  let autoPlay = setInterval(() => goTo(currentIndex + 1, 'up'), 4000);

  // Pause Auto-Play on interaction
  container.addEventListener('mouseenter', () => clearInterval(autoPlay));
  container.addEventListener('touchstart', () => clearInterval(autoPlay));
  
  container.addEventListener('mouseleave', () => {
    clearInterval(autoPlay);
    autoPlay = setInterval(() => goTo(currentIndex + 1, 'up'), 4000);
  });
  
  container.addEventListener('touchend', () => {
    clearInterval(autoPlay);
    autoPlay = setInterval(() => goTo(currentIndex + 1, 'up'), 4000);
  });
});