(() => {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Header solid state
  const header = document.getElementById('siteHeader');
  const updateHeader = () => {
    if (!header) return;
    header.classList.toggle('scrolled', window.scrollY > 30);
  };
  updateHeader();
  window.addEventListener('scroll', updateHeader, { passive: true });

  // Reveal on view
  const revealTargets = document.querySelectorAll('.reveal-up, .reveal-photo');
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  revealTargets.forEach(el => revealObserver.observe(el));

  // Business image/title scroll sync
  // IntersectionObserver 방식은 여러 항목이 동시에 화면에 걸칠 때
  // 콜백 순서에 따라 이미지와 제목이 어긋날 수 있어,
  // 화면의 고정 기준선(anchor)을 각 제목이 통과하는 순간에만 순서대로 전환한다.
  const bizItems = [...document.querySelectorAll('[data-biz]')];
  const bizImages = [...document.querySelectorAll('[data-biz-image]')];
  const bizCounter = document.getElementById('bizCounter');
  let activeBizIndex = -1;
  let bizTicking = false;

  const activateBiz = index => {
    if (index === activeBizIndex) return;
    activeBizIndex = index;

    bizItems.forEach((item, i) => item.classList.toggle('active', i === index));
    bizImages.forEach((img, i) => img.classList.toggle('active', i === index));

    if (bizCounter) {
      bizCounter.textContent = `${String(index + 1).padStart(2, '0')} / ${String(bizItems.length).padStart(2, '0')}`;
    }
  };

  const updateBusinessByScroll = () => {
    if (!bizItems.length) {
      bizTicking = false;
      return;
    }

    // 데스크톱: 화면 중앙 부근에서 전환
    // 모바일/태블릿: 상단 sticky 이미지 아래의 텍스트 가시영역에 맞춰 더 낮은 위치에서 전환
    const isCompact = window.matchMedia('(max-width: 1050px)').matches;
    const anchor = window.innerHeight * (isCompact ? 0.74 : 0.52);

    let nextIndex = 0;

    // 다음 제목의 상단이 기준선을 넘는 순간 정확히 다음 이미지로 전환
    for (let i = 0; i < bizItems.length; i++) {
      const rect = bizItems[i].getBoundingClientRect();
      if (rect.top <= anchor) nextIndex = i;
    }

    activateBiz(nextIndex);
    bizTicking = false;
  };

  const requestBusinessUpdate = () => {
    if (!bizTicking) {
      requestAnimationFrame(updateBusinessByScroll);
      bizTicking = true;
    }
  };

  if (bizItems.length) {
    activateBiz(0);
    window.addEventListener('scroll', requestBusinessUpdate, { passive: true });
    window.addEventListener('resize', requestBusinessUpdate);
    requestBusinessUpdate();
  }

  // Scroll-linked image motion
  if (!reducedMotion) {
    const heroImage = document.getElementById('heroImage');
    const closingImage = document.getElementById('closingImage');
    let ticking = false;

    const updateParallax = () => {
      const y = window.scrollY;
      const vh = window.innerHeight;

      if (heroImage) {
        const heroProgress = Math.min(1, y / Math.max(vh, 1));
        const scale = 1.08 - heroProgress * 0.045;
        const translate = heroProgress * 24;
        heroImage.style.transform = `translate3d(0, ${translate}px, 0) scale(${scale})`;
      }

      if (closingImage) {
        const section = closingImage.closest('.closing');
        const rect = section.getBoundingClientRect();
        if (rect.top < vh && rect.bottom > 0) {
          const progress = (vh - rect.top) / (vh + rect.height);
          const translate = (progress - .5) * 46;
          const scale = 1.07 - progress * .025;
          closingImage.style.transform = `translate3d(0, ${translate}px, 0) scale(${scale})`;
        }
      }
      ticking = false;
    };

    const requestTick = () => {
      if (!ticking) {
        requestAnimationFrame(updateParallax);
        ticking = true;
      }
    };
    window.addEventListener('scroll', requestTick, { passive: true });
    window.addEventListener('resize', requestTick);
    requestTick();
  }
})();