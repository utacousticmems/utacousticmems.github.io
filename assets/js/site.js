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
