/* NEURAL_FEED — main.js */

document.addEventListener('DOMContentLoaded', () => {

  // ── Search toggle ────────────────────────────────────────────────────────
  const searchToggle = document.getElementById('search-toggle');
  const searchForm   = document.getElementById('navbar-search-form');
  if (searchToggle && searchForm) {
    searchToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      searchForm.classList.toggle('open');
      if (searchForm.classList.contains('open')) searchForm.querySelector('input')?.focus();
    });
    document.addEventListener('click', (e) => {
      if (!searchForm.contains(e.target) && e.target !== searchToggle)
        searchForm.classList.remove('open');
    });
  }

  // ── Mobile nav (with backdrop) ───────────────────────────────────────────
  const mobileBtn      = document.getElementById('mobile-menu-btn');
  const mobileClose    = document.getElementById('mobile-menu-close');
  const mobileNav      = document.getElementById('mobile-nav');
  const mobileBackdrop = document.getElementById('mobile-nav-backdrop');

  function openMobileNav() {
    mobileNav?.classList.add('open');
    mobileBackdrop?.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeMobileNav() {
    mobileNav?.classList.remove('open');
    mobileBackdrop?.classList.remove('open');
    document.body.style.overflow = '';
  }

  mobileBtn?.addEventListener('click', openMobileNav);
  mobileClose?.addEventListener('click', closeMobileNav);
  mobileBackdrop?.addEventListener('click', closeMobileNav);

  // Escape key closes mobile nav and search
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeMobileNav();
      searchForm?.classList.remove('open');
    }
  });

  // ── Scroll-to-top ────────────────────────────────────────────────────────
  const scrollBtn = document.getElementById('scroll-top');
  if (scrollBtn) {
    window.addEventListener('scroll', () => scrollBtn.classList.toggle('show', window.scrollY > 400));
    scrollBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  // ── TOC active state ─────────────────────────────────────────────────────
  const tocLinks = document.querySelectorAll('.toc-link');
  if (tocLinks.length) {
    const observer = new IntersectionObserver(
      (entries) => entries.forEach(entry => {
        const link = document.querySelector(`.toc-link[href="#${entry.target.id}"]`);
        if (link) link.classList.toggle('active', entry.isIntersecting);
      }),
      { rootMargin: '-10% 0px -80% 0px' }
    );
    document.querySelectorAll('h2[id], h3[id]').forEach(h => observer.observe(h));
  }

  // ── Like button ──────────────────────────────────────────────────────────
  const likeBtn = document.getElementById('like-btn');
  if (likeBtn) {
    likeBtn.addEventListener('click', async () => {
      const postId    = likeBtn.dataset.postId;
      const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
      try {
        const res  = await fetch(`/post/like/${postId}/`, { method: 'POST', headers: { 'X-CSRFToken': csrfToken } });
        const data = await res.json();
        if (data.action) {
          const count      = likeBtn.querySelector('.like-count');
          const display    = document.getElementById('like-display');
          if (count) count.textContent = data.likes;
          if (display) display.textContent = data.likes;
          likeBtn.classList.toggle('liked', data.action === 'liked');
        } else if (data.error === 'login_required') {
          window.location.href = `/auth/login/?next=${window.location.pathname}`;
        }
      } catch (e) { console.error(e); }
    });
  }

  // ── Reply toggle ─────────────────────────────────────────────────────────
  document.querySelectorAll('.reply-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const parentInput  = document.getElementById('parent-id-input');
      const replyNotice  = document.getElementById('reply-notice');
      const commentForm  = document.getElementById('comment-form');
      if (parentInput) parentInput.value = btn.dataset.commentId;
      if (replyNotice) replyNotice.textContent = `Replying to @${btn.dataset.author}`;
      commentForm?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      commentForm?.querySelector('textarea')?.focus();
    });
  });

  // ── Newsletter AJAX ───────────────────────────────────────────────────────
  document.querySelectorAll('.newsletter-form-ajax').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const csrfToken  = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
      const submitBtn  = form.querySelector('[type="submit"]');
      const origText   = submitBtn?.innerHTML;
      if (submitBtn) { submitBtn.disabled = true; submitBtn.innerHTML = 'Sending…'; }
      const data = new FormData(form);
      data.append('consent', '1');
      try {
        const res  = await fetch('/newsletter/subscribe/', { method: 'POST', headers: { 'X-CSRFToken': csrfToken }, body: data });
        const json = await res.json();
        const msg  = form.querySelector('.newsletter-msg');
        if (msg) {
          msg.textContent = json.message;
          msg.style.display = 'block';
          msg.className = `newsletter-msg alert ${json.status === 'ok' ? 'alert-success' : 'alert-error'}`;
        }
        if (json.status === 'ok') form.reset();
      } catch (e) { console.error(e); }
      finally {
        if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = origText; }
      }
    });
  });

  // ── Confirm delete ────────────────────────────────────────────────────────
  document.querySelectorAll('.confirm-delete').forEach(btn => {
    btn.addEventListener('click', (e) => {
      if (!confirm('Are you sure? This cannot be undone.')) e.preventDefault();
    });
  });

  // ── Auto-dismiss alerts ───────────────────────────────────────────────────
  document.querySelectorAll('.auto-dismiss').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.4s';
      el.style.opacity    = '0';
      setTimeout(() => el.style.display = 'none', 400);
    }, 4000);
  });

});
