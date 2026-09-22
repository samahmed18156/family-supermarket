/* Family Supermarket - Modern Motion JS
   Smooth, performant, no libraries
*/

// ===== NAVBAR SCROLL BEHAVIOR =====
let lastScroll = 0;
const navbar = document.querySelector('.navbar');

window.addEventListener('scroll', () => {
  const current = window.pageYOffset;

  // Add shadow on scroll
  if (current > 20) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }

  // Hide on scroll down, show on scroll up
  if (current > lastScroll && current > 400) {
    navbar.classList.add('hidden');
  } else {
    navbar.classList.remove('hidden');
  }
  lastScroll = current;
}, { passive: true });

// ===== REVEAL ON SCROLL - Stagger =====
const observerOptions = {
  threshold: 0.1,
  rootMargin: '0px 0px -50px 0px'
};

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry, index) => {
    if (entry.isIntersecting) {
      // Stagger delay
      setTimeout(() => {
        entry.target.classList.add('active', 'revealed');
      }, index * 80);
      revealObserver.unobserve(entry.target);
    }
  });
}, observerOptions);

document.querySelectorAll('.reveal, .product-card').forEach(el => {
  revealObserver.observe(el);
});

// ===== PRODUCT CARDS - 3D TILT EFFECT =====
document.querySelectorAll('.product-card').forEach(card => {
  card.addEventListener('mousemove', (e) => {
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = (y - centerY) / 10;
    const rotateY = (centerX - x) / 10;

    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
  });

  card.addEventListener('mouseleave', () => {
    card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
  });
});

// ===== SEARCH - Live filter with smooth animation =====
const searchInput = document.querySelector('.search-input');
const productCards = document.querySelectorAll('.product-card');

if (searchInput) {
  let timeout;
  searchInput.addEventListener('input', (e) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      const query = e.target.value.toLowerCase();

      productCards.forEach(card => {
        const name = card.dataset.name?.toLowerCase() || '';
        const category = card.dataset.category?.toLowerCase() || '';
        const match = name.includes(query) || category.includes(query);

        if (match || query === '') {
          card.style.display = 'block';
          // Animate in
          requestAnimationFrame(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0) scale(1)';
          });
        } else {
          card.style.opacity = '0';
          card.style.transform = 'translateY(20px) scale(0.95)';
          setTimeout(() => {
            card.style.display = 'none';
          }, 300);
        }
      });
    }, 200);
  });
}

// ===== MAGNETIC BUTTONS =====
document.querySelectorAll('.btn-primary').forEach(btn => {
  btn.addEventListener('mousemove', (e) => {
    const rect = btn.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;

    btn.style.transform = `translate(${x * 0.15}px, ${y * 0.15}px) translateY(-2px)`;
  });

  btn.addEventListener('mouseleave', () => {
    btn.style.transform = 'translate(0, 0)';
  });
});

// ===== FORM - Smooth validation =====
const form = document.querySelector('form');
if (form) {
  form.addEventListener('submit', (e) => {
    const btn = form.querySelector('button[type="submit"]');
    btn.innerHTML = '<span>✨ Sending...</span>';
    btn.style.pointerEvents = 'none';

    // Let form submit naturally (Flask will handle)
    setTimeout(() => {
      btn.innerHTML = '<span>✓ Sent!</span>';
    }, 800);
  });
}

// ===== PARALLAX HERO BLOBS =====
window.addEventListener('scroll', () => {
  const scrolled = window.pageYOffset;
  const blobs = document.querySelectorAll('.hero-blob');

  blobs.forEach((blob, i) => {
    const speed = 0.2 + (i * 0.1);
    blob.style.transform = `translateY(${scrolled * speed}px)`;
  });
}, { passive: true });

// ===== SMOOTH PAGE TRANSITIONS =====
document.querySelectorAll('a[href^="/"], a[href^="#"]').forEach(link => {
  link.addEventListener('click', (e) => {
    const href = link.getAttribute('href');
    if (href.startsWith('#')) return; // Let hash links work normally

    // Add exit animation
    if (!href.includes('?') && !link.classList.contains('no-transition')) {
      e.preventDefault();
      document.body.style.opacity = '0';
      document.body.style.transform = 'translateY(10px)';
      document.body.style.transition = 'all 0.3s ease';

      setTimeout(() => {
        window.location.href = href;
      }, 300);
    }
  });
});

// Page enter animation
window.addEventListener('load', () => {
  document.body.style.opacity = '0';
  document.body.style.transform = 'translateY(10px)';

  requestAnimationFrame(() => {
    document.body.style.transition = 'all 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
    document.body.style.opacity = '1';
    document.body.style.transform = 'translateY(0)';
  });
});

// ===== CART MICRO-INTERACTION =====
document.querySelectorAll('.add-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    // Bounce animation
    btn.style.transform = 'scale(0.8)';
    setTimeout(() => {
      btn.style.transform = 'scale(1.2)';
      btn.innerHTML = '✓';
      setTimeout(() => {
        btn.style.transform = 'scale(1)';
        btn.innerHTML = '+';
      }, 400);
    }, 150);

    // Haptic feedback if available
    if (navigator.vibrate) navigator.vibrate(50);
  });
});

// ===== LUXURY POLISH LAYER v2.5 - Progress + Custom Cursor =====
// Progress bar
const progressBar = document.getElementById('progressBar');
if (progressBar) {
  window.addEventListener('scroll', () => {
    const scrollTop = window.pageYOffset;
    const docHeight = document.body.scrollHeight - window.innerHeight;
    const progress = (scrollTop / docHeight) * 100;
    progressBar.style.width = progress + '%';
  }, { passive: true });
}

// Custom cursor - luxury dot + ring (desktop only, respects reduced motion)
const cursorDot = document.getElementById('cursorDot');
const cursorRing = document.getElementById('cursorRing');
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

if (cursorDot && cursorRing && !prefersReducedMotion && !isTouch && window.innerWidth > 900) {
  let mouseX = 0, mouseY = 0;
  let ringX = 0, ringY = 0;

  document.body.classList.add('cursor-active');

  document.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;

    cursorDot.style.left = mouseX + 'px';
    cursorDot.style.top = mouseY + 'px';
  }, { passive: true });

  // Smooth ring follow with RAF
  function animateRing() {
    ringX += (mouseX - ringX) * 0.15;
    ringY += (mouseY - ringY) * 0.15;

    cursorRing.style.left = ringX + 'px';
    cursorRing.style.top = ringY + 'px';

    requestAnimationFrame(animateRing);
  }
  animateRing();

  // Hover states
  const hoverElements = document.querySelectorAll('a, button, .product-card, .pill, .add-btn');
  hoverElements.forEach(el => {
    el.addEventListener('mouseenter', () => document.body.classList.add('cursor-hover'));
    el.addEventListener('mouseleave', () => document.body.classList.remove('cursor-hover'));
  });

  // Hide cursor when leaving window
  document.addEventListener('mouseleave', () => {
    cursorDot.style.opacity = '0';
    cursorRing.style.opacity = '0';
  });
  document.addEventListener('mouseenter', () => {
    cursorDot.style.opacity = '1';
    cursorRing.style.opacity = '1';
  });
}

// Luxury reveal for hero-content line
const heroContent = document.querySelector('.hero-content');
if (heroContent) {
  setTimeout(() => heroContent.classList.add('revealed'), 600);
}

console.log('✨ Family Supermarket Modern UI Loaded - Smooth & Fast');
console.log('💎 Luxury Polish v2.5 - Progress + Cursor + Gold accents - 1027 lines, 26K');