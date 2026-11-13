// Fade-up on scroll (Apple-style). Content stays visible without JS or with reduced motion.
(function () {
  var els = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) { els.forEach(function (e) { e.classList.add('in'); }); return; }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  els.forEach(function (e) { io.observe(e); });
})();

// Mobile nav toggle
(function () {
  var btn = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
    });
  }
})();

// Publications: type filter + text search
(function () {
  var search = document.getElementById('pub-search');
  if (!search) return;
  var chips = document.querySelectorAll('.pub-tools .chip');
  var items = document.querySelectorAll('.pub');
  var years = document.querySelectorAll('.pub-year');
  var empty = document.getElementById('pub-empty');
  var type = 'all';

  function apply() {
    var q = search.value.trim().toLowerCase();
    var shown = 0;
    items.forEach(function (li) {
      var ok = (type === 'all' || li.dataset.type === type) &&
               (!q || li.textContent.toLowerCase().indexOf(q) !== -1);
      li.hidden = !ok;
      if (ok) shown++;
    });
    years.forEach(function (sec) {
      sec.hidden = !sec.querySelector('.pub:not([hidden])');
    });
    var early = document.getElementById('pub-early');
    if (early) {
      var earlyHits = early.querySelector('.pub:not([hidden])');
      early.hidden = !earlyHits;
      if (q && earlyHits) early.open = true;
    }
    empty.hidden = shown !== 0;
  }
  chips.forEach(function (c) {
    c.addEventListener('click', function () {
      chips.forEach(function (x) { x.classList.remove('is-on'); });
      c.classList.add('is-on');
      type = c.dataset.type;
      apply();
    });
  });
  search.addEventListener('input', apply);
})();

// Gallery: album filter chips + full-screen photo viewer.
// Without JS the chips jump to each album and each photo opens as a plain image.
(function () {
  var albums = document.querySelectorAll('.album');
  if (!albums.length) return;

  // Album filter
  var chips = document.querySelectorAll('.gallery-chips .chip');
  function show(id) {
    var found = false;
    albums.forEach(function (a) { if (a.dataset.album === id) found = true; });
    if (!found) id = 'all';
    albums.forEach(function (a) { a.hidden = id !== 'all' && a.dataset.album !== id; });
    chips.forEach(function (c) {
      var on = c.dataset.album === id;
      c.classList.toggle('is-on', on);
      if (on) c.setAttribute('aria-current', 'true'); else c.removeAttribute('aria-current');
    });
    return id;
  }
  chips.forEach(function (c) {
    c.addEventListener('click', function (e) {
      e.preventDefault();
      var id = show(c.dataset.album);
      if (history.replaceState) history.replaceState(null, '', id === 'all' ? location.pathname : '#' + id);
    });
  });
  function fromHash() { if (chips.length) show(decodeURIComponent(location.hash.slice(1)) || 'all'); }
  if (location.hash.length > 1) fromHash();
  window.addEventListener('hashchange', fromHash);

  // Photo viewer
  if (!window.HTMLDialogElement) return;
  var box = document.createElement('dialog');
  box.className = 'lightbox';
  box.setAttribute('aria-label', 'Photo viewer');
  box.innerHTML =
    '<button type="button" class="lb-btn lb-close" aria-label="Close">×</button>' +
    '<button type="button" class="lb-btn lb-prev" aria-label="Previous photo">‹</button>' +
    '<button type="button" class="lb-btn lb-next" aria-label="Next photo">›</button>' +
    '<figure class="lb-stage"><img alt=""><figcaption><span class="lb-cap"></span><span class="lb-count" aria-live="polite"></span></figcaption></figure>';
  document.body.appendChild(box);
  var img = box.querySelector('img');
  var cap = box.querySelector('.lb-cap');
  var count = box.querySelector('.lb-count');
  var prev = box.querySelector('.lb-prev');
  var next = box.querySelector('.lb-next');
  var set = [], at = 0, opener = null;

  function render() {
    var a = set[at];
    img.src = a.href;
    img.alt = a.querySelector('img').alt;
    cap.textContent = a.dataset.caption || '';
    count.textContent = (at + 1) + ' / ' + set.length;
    prev.hidden = next.hidden = set.length < 2;
    if (set.length > 1) { new Image().src = set[(at + 1) % set.length].href; }
  }
  function step(d) { if (set.length > 1) { at = (at + d + set.length) % set.length; render(); } }

  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a.photo') : null;
    if (!a || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button) return;
    e.preventDefault();
    set = Array.prototype.slice.call(document.querySelectorAll('.album:not([hidden]) a.photo'));
    at = Math.max(0, set.indexOf(a));
    opener = a;
    render();
    document.documentElement.style.overflow = 'hidden';
    box.showModal();
  });
  prev.addEventListener('click', function () { step(-1); });
  next.addEventListener('click', function () { step(1); });
  box.querySelector('.lb-close').addEventListener('click', function () { box.close(); });
  box.addEventListener('click', function (e) {
    if (e.target === box || e.target.classList.contains('lb-stage')) box.close();
  });
  box.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowLeft') step(-1);
    if (e.key === 'ArrowRight') step(1);
  });
  box.addEventListener('close', function () {
    document.documentElement.style.overflow = '';
    img.removeAttribute('src');
    if (opener) opener.focus();
  });

  // Swipe left or right on touch screens
  var x0 = null;
  box.addEventListener('touchstart', function (e) { x0 = e.touches.length === 1 ? e.touches[0].clientX : null; }, { passive: true });
  box.addEventListener('touchend', function (e) {
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0;
    x0 = null;
    if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
  }, { passive: true });
})();
