document.documentElement.classList.add("js-ready");

document.querySelectorAll("[data-delay]").forEach((item) => {
  const delay = item.getAttribute("data-delay");
  item.style.animationDelay = delay;
});

document.querySelectorAll(".photo-carousel").forEach((carousel) => {
  const track = carousel.querySelector(".carousel-track");
  if (!track) return;

  const slides = Array.from(track.querySelectorAll(".slide"));
  if (slides.length === 0) return;

  track.querySelectorAll("img").forEach((image, index) => {
    image.loading = index === 0 ? "eager" : "lazy";
    image.decoding = "async";
    if (index > 0) {
      image.fetchPriority = "low";
    }
  });

  let wheelLocked = false;
  let settleTimer = 0;
  let touchResumeTimer = 0;
  let currentIndex = 0;
  let isMoving = false;
  let touchStartX = 0;
  let touchStartY = 0;
  let touchPointerId = null;
  let touchMode = "";
  let suppressClick = false;
  let userPaused = false;
  let touchPaused = false;
  let isVisible = false;
  let autoplayTimer = 0;

  const updateActiveSlides = () => {
    const previousIndex = (currentIndex - 1 + slides.length) % slides.length;
    const nextIndex = (currentIndex + 1) % slides.length;

    slides.forEach((slide, index) => {
      slide.classList.toggle("is-active", index === currentIndex);
      slide.classList.toggle("is-neighbor", index === previousIndex || index === nextIndex);
      slide.classList.toggle("is-prev", index === previousIndex);
      slide.classList.toggle("is-next", index === nextIndex);
    });
  };

  const moveBySlide = (direction) => {
    if (isMoving) return;
    isMoving = true;
    currentIndex = (currentIndex + direction + slides.length) % slides.length;
    carousel.classList.add("is-stepping");
    window.clearTimeout(settleTimer);
    updateActiveSlides();

    settleTimer = window.setTimeout(() => {
      carousel.classList.remove("is-stepping");
      isMoving = false;
    }, 560);
  };

  const updatePausedClass = () => {
    carousel.classList.toggle("is-paused", userPaused || touchPaused);
  };

  const stopAutoplay = () => {
    window.clearTimeout(autoplayTimer);
    autoplayTimer = 0;
  };

  const scheduleAutoplay = () => {
    stopAutoplay();
    if (!isVisible || userPaused || touchPaused || document.hidden) return;

    autoplayTimer = window.setTimeout(() => {
      moveBySlide(1);
      scheduleAutoplay();
    }, 3000);
  };

  const pauseForTouch = () => {
    window.clearTimeout(touchResumeTimer);
    touchPaused = true;
    stopAutoplay();
    updatePausedClass();
  };

  const resumeAfterTouch = () => {
    window.clearTimeout(touchResumeTimer);
    touchResumeTimer = window.setTimeout(() => {
      touchPaused = false;
      updatePausedClass();
      scheduleAutoplay();
    }, 1500);
  };

  carousel.addEventListener("mouseenter", () => {
    userPaused = true;
    stopAutoplay();
    updatePausedClass();
  });

  carousel.addEventListener("mouseleave", () => {
    userPaused = false;
    updatePausedClass();
    scheduleAutoplay();
  });

  carousel.addEventListener("wheel", (event) => {
    if (!userPaused) return;
    event.preventDefault();
    if (wheelLocked) return;

    const delta = Math.abs(event.deltaY) >= Math.abs(event.deltaX) ? event.deltaY : event.deltaX;
    if (Math.abs(delta) < 2) return;

    wheelLocked = true;
    moveBySlide(delta > 0 ? 1 : -1);
    window.setTimeout(() => {
      wheelLocked = false;
    }, 620);
  }, { passive: false });

  carousel.addEventListener("pointerdown", (event) => {
    if (event.pointerType !== "touch") return;
    touchPointerId = event.pointerId;
    touchStartX = event.clientX;
    touchStartY = event.clientY;
    touchMode = "";
    suppressClick = false;
    pauseForTouch();
  });

  carousel.addEventListener("pointermove", (event) => {
    if (event.pointerType !== "touch" || event.pointerId !== touchPointerId) return;

    const deltaX = event.clientX - touchStartX;
    const deltaY = event.clientY - touchStartY;
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);

    if (!touchMode && (absX > 12 || absY > 12)) {
      touchMode = absX > absY * 1.25 ? "horizontal" : "vertical";
    }

    if (touchMode === "horizontal") {
      event.preventDefault();
    }
  }, { passive: false });

  const finishTouch = (event) => {
    if (event.pointerType !== "touch" || event.pointerId !== touchPointerId) return;

    const deltaX = event.clientX - touchStartX;
    const deltaY = event.clientY - touchStartY;
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);

    if (touchMode === "horizontal" && absX > 42 && absX > absY * 1.2) {
      suppressClick = true;
      moveBySlide(deltaX < 0 ? 1 : -1);
    }

    touchPointerId = null;
    touchMode = "";
    resumeAfterTouch();
  };

  carousel.addEventListener("pointerup", finishTouch);
  carousel.addEventListener("pointercancel", finishTouch);

  carousel.addEventListener("click", (event) => {
    if (suppressClick) {
      suppressClick = false;
      return;
    }

    const slide = event.target.closest(".slide");
    if (!slide) return;
    if (slide.classList.contains("is-prev")) {
      moveBySlide(-1);
    } else if (slide.classList.contains("is-next")) {
      moveBySlide(1);
    }
  });

  updateActiveSlides();

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      stopAutoplay();
    } else {
      scheduleAutoplay();
    }
  });

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      const entry = entries[0];
      isVisible = Boolean(entry && entry.isIntersecting);
      if (isVisible) {
        scheduleAutoplay();
      } else {
        stopAutoplay();
      }
    }, { rootMargin: "220px 0px", threshold: 0.01 });

    observer.observe(carousel);
  } else {
    isVisible = true;
    scheduleAutoplay();
  }
});
