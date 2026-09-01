(function() {
  // Smooth scroll to sections
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href === '#') return;

      e.preventDefault();
      const target = document.querySelector(href);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
        updateActiveNav(href);
      }
    });
  });

  // Learn More button
  const learnMoreBtn = document.getElementById('learnMoreBtn');
  if (learnMoreBtn) {
    learnMoreBtn.addEventListener('click', () => {
      document.querySelector('#about').scrollIntoView({ behavior: 'smooth' });
      updateActiveNav('#about');
    });
  }

  // Update active nav link based on scroll position
  function updateActiveNav(href) {
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.remove('active');
    });
    const activeLink = document.querySelector(`a[href="${href}"]`);
    if (activeLink) {
      activeLink.classList.add('active');
    }
  }

  // Highlight nav link on scroll
  window.addEventListener('scroll', () => {
    const sections = document.querySelectorAll('section[id]');
    let current = '';

    sections.forEach(section => {
      const sectionTop = section.offsetTop;
      const sectionHeight = section.clientHeight;
      if (window.pageYOffset >= sectionTop - 200) {
        current = section.getAttribute('id');
      }
    });

    if (current) {
      updateActiveNav(`#${current}`);
    }
  });

  // Initialize
  updateActiveNav('#home');
})();